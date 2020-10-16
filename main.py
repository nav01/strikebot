import re
import os
from datetime import datetime, timedelta

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from session import Session
import operations

class Client(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.command_matcher = re.compile('<:([a-zA-Z0-9_]+):[0-9]{18}> <@!([0-9]{17,18})> (.{4,})')
        self.strike_role_matcher = re.compile('strike ([1-9]{1})', re.IGNORECASE)
        self.clear_strikes.start()
       
    def get_next_strike_role(self, member_roles, guild_roles):
        current_strike = 0
        for role in member_roles:
            role_match = self.strike_role_matcher.match(role.name)
            if (role_match is not None and int(role_match.group(1)) > current_strike):
                current_strike = int(role_match.group(1))
        
        next_strike_role_name = 'strike {}'.format(current_strike + 1)
        return next((role for role in guild_roles if role.name.lower() == next_strike_role_name), None)
    
    async def strike(self, user_to_strike, guild_roles, strike_reason):
        next_strike_role = self.get_next_strike_role(user_to_strike.roles, guild_roles)
        if (next_strike_role is not None):
            await user_to_strike.add_roles(next_strike_role, reason=strike_reason)
            return int(self.strike_role_matcher.match(next_strike_role.name).group(1))
        else:
            return None
            
    async def clear_strike(self, discord_user, strike_level, reason='Decay'):
        role_to_remove_name = 'strike {}'.format(strike_level)
        role_to_remove = next((role for role in discord_user.roles if role.name.lower() == role_to_remove_name), None)
        
        if role_to_remove is not None:
            await discord_user.remove_roles(role_to_remove, reason=reason)
            
        
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        command_match = self.command_matcher.match(message.content)
        
        if (command_match is not None):
            if (command_match.group(1) == 'strike'):
                target_user = message.guild.get_member(int(command_match.group(2)))
      
                if self.get_next_strike_role(target_user.roles, message.guild.roles) is None:
                    await message.channel.send('**{} ({})** is at the max strike level.'.format(target_user.display_name, target_user.name))
                    return
                
                session = Session()
                pending_strike = operations.user_has_pending_strike(session, target_user.id)
                
                if pending_strike is not None:
                    await message.channel.send('**{} ({})** has pending strike.\n{}'.format(target_user.display_name, target_user.name, pending_strike.watched_message_jump_url))
                    return
              
                try:
                    voting_expiration_date = datetime.now() + timedelta(hours=6)
                    bot_message = await message.channel.send(
                        content='```haskell\n{} ({}) is proposing a strike against {} ({}), react with strike to support\nReason: {}\nVoting ends at {}```'
                            .format(
                                message.author.display_name,
                                message.author.name,
                                target_user.display_name,
                                target_user.name,
                                command_match.group(3),
                                voting_expiration_date.replace(microsecond=0),
                            )
                    )
                    operations.propose_strike(
                        session, 
                        message.guild, 
                        message.author, 
                        target_user,
                        command_match.group(3),
                        bot_message.channel.id,
                        bot_message.id, 
                        bot_message.jump_url,
                        voting_expiration_date,
                    )
                    session.commit()
                except Exception as e:
                    print(e)
                    session.rollback()
                finally:
                    session.close()
    
    async def on_raw_reaction_add(self, payload):
        #TODO add this as a customizable user setting
        PROPONENTS_REQUIRED = 2
        
        if payload.emoji.name == 'strike':
            session = Session()
            try:
                strike = operations.add_strike_proponent(session, payload.message_id, payload.user_id)
                
                if strike is not None:
                    if len(strike.proponents) >= PROPONENTS_REQUIRED:
                        guild = self.get_guild(payload.guild_id)
                        target_user = guild.get_member(strike.targeted_user.discord_user_id)
                        strike_level_modified = await self.strike(target_user, guild.roles, strike.reason)
                        strike = operations.mark_strike_operation_successful(session, payload.message_id, strike_level_modified)
                        channel = guild.get_channel(payload.channel_id)
                        discord_proposing_user = guild.get_member(strike.proposing_user.discord_user_id)
                        discord_target_user = guild.get_member(strike.targeted_user.discord_user_id)
                        await channel.send('Strike proposed by **{} ({})** against **{} ({})** was successful. Strike {} applied.'.\
                            format(
                                discord_proposing_user.display_name,
                                discord_proposing_user.name,
                                discord_target_user.display_name, 
                                discord_target_user.name,
                                strike.strike_level_modified
                            )
                        )
                    session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                raise
            finally:
                session.close()
            
    async def on_guild_join(self, guild):
        session = Session()
        try:
            operations.create_server(session, guild.id)
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()
            
    @tasks.loop(seconds=60)
    async def clear_strikes(self):
        #TODO add this as a customizable user setting
        TIME_BEFORE_DECAY = 1
        session = Session()
        try:
            decayed_strikes = operations.get_decayed_strikes(session, TIME_BEFORE_DECAY)
            for strike in decayed_strikes:
                guild = self.get_guild(strike.server.discord_server_id)
                user = guild.get_member(strike.targeted_user.discord_user_id)
                await self.clear_strike(user, strike.strike_level_modified)
                strike.decay()
                await guild.get_channel(strike.watched_message_channel_id).send(
                    'Strike **{}** on {} ({}) has expired.'.format(
                        strike.strike_level_modified, 
                        user.display_name, 
                        user.name
                    )
                )
                
            session.commit()   
        except Exception as e:
            print(e)
        finally:
            session.close()
        
                  
if __name__ == '__main__':
    load_dotenv()
    intents = discord.Intents.default()
    intents.members = True
    intents.reactions = True
    client = Client(intents=intents)
    client.run(os.getenv('DISCORD_BOT_TOKEN'))