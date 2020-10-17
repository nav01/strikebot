import re
import os
from datetime import datetime, timedelta

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from session import Session
import operations
import strike_helper

class Client(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.command_matcher = re.compile('<:([a-zA-Z0-9_]+):[0-9]{18}> <@!([0-9]{17,18})> (.{4,})')
        self.clear_strikes.start()
            
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        command_match = self.command_matcher.match(message.content)
        
        if (command_match is not None):
            if (command_match.group(1) == 'strike'):
                session = Session()
                try:
                    await strike_helper.propose_strike(session, message, int(command_match.group(2)), command_match.group(3))
                    session.commit()
                except Exception as e:
                    print(e)
                    session.rollback()
                    raise
                finally:
                    session.close()
    
    async def on_raw_reaction_add(self, payload):
        #TODO add this as a customizable user setting
        PROPONENTS_REQUIRED = 1
        
        if payload.emoji.name == 'strike':
            session = Session()
            try:
                strike = operations.add_strike_proponent(session, payload.message_id, payload.user_id)
                if strike is not None:
                    if len(strike.proponents) >= PROPONENTS_REQUIRED:
                        guild = self.get_guild(payload.guild_id)
                        channel = guild.get_channel(payload.channel_id)
                        await strike_helper.strike_success(guild, channel, strike)
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
        TIME_BEFORE_DECAY = 60
        session = Session()
        try:
            decayed_strikes = operations.get_decayed_strikes(session, TIME_BEFORE_DECAY)
            
            for strike in decayed_strikes:
                guild = self.get_guild(strike.server.discord_server_id)
                user = guild.get_member(strike.targeted_user.discord_user_id)
                await strike_helper.clear_strike(user, strike.strike_level_modified)
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