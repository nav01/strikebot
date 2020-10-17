import re
from datetime import datetime, timedelta

import operations

strike_role_matcher = re.compile('strike ([1-9]{1})', re.IGNORECASE)

async def strike_success(guild, channel, strike):    
    target_user = guild.get_member(strike.targeted_user.discord_user_id)
    strike_level_modified = await add_strike(target_user, guild.roles, strike.reason)
    strike.mark_success(strike_level_modified)
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

def get_next_strike_role(member_roles, guild_roles):
    current_strike = 0
    for role in member_roles:
        role_match = strike_role_matcher.match(role.name)
        if (role_match is not None and int(role_match.group(1)) > current_strike):
            current_strike = int(role_match.group(1))
    
    next_strike_role_name = 'strike {}'.format(current_strike + 1)
    return next((role for role in guild_roles if role.name.lower() == next_strike_role_name), None)
    
async def add_strike(user_to_strike, guild_roles, strike_reason):
    next_strike_role = get_next_strike_role(user_to_strike.roles, guild_roles)
    if (next_strike_role is not None):
        await user_to_strike.add_roles(next_strike_role, reason=strike_reason)
        return int(strike_role_matcher.match(next_strike_role.name).group(1))
    else:
        return None
        
async def clear_strike(discord_user, strike_level, reason='Decay'):
    role_to_remove_name = 'strike {}'.format(strike_level)
    role_to_remove = next((role for role in discord_user.roles if role.name.lower() == role_to_remove_name), None)
    
    if role_to_remove is not None:
        await discord_user.remove_roles(role_to_remove, reason=reason)
        
async def propose_strike(session, message, target_user_discord_id, reason):
    target_user = message.guild.get_member(target_user_discord_id)
  
    if get_next_strike_role(target_user.roles, message.guild.roles) is None:
        await message.channel.send('**{} ({})** is at the max strike level.'.format(target_user.display_name, target_user.name))
        return
        
    pending_strike = operations.user_has_pending_strike(session, target_user.id)
    
    if pending_strike is not None:
        await message.channel.send('**{} ({})** has pending strike.\n{}'.format(target_user.display_name, target_user.name, pending_strike.watched_message_jump_url))
        return
  
    voting_expiration_date = datetime.now() + timedelta(hours=6)
    bot_message = await message.channel.send(
        content='```haskell\n{} ({}) is proposing a strike against {} ({}), react with strike to support\nReason: {}\nVoting ends at {}```'
            .format(
                message.author.display_name,
                message.author.name,
                target_user.display_name,
                target_user.name,
                reason,
                voting_expiration_date.replace(microsecond=0),
            )
    )
    operations.propose_strike(
        session, 
        message.guild, 
        message.author, 
        target_user,
        reason,
        bot_message.channel.id,
        bot_message.id, 
        bot_message.jump_url,
        voting_expiration_date,
    )