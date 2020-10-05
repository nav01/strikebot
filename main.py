import re
import os

import discord
from dotenv import load_dotenv

class Client(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        self.command_matcher = re.compile('<:([a-zA-Z0-9_]+):[0-9]{18}> <@!([0-9]{17,18})> ([a-zA-Z0-9 ]{4,})')
        self.strike_role_matcher = re.compile('strike ([1-9]{1})', re.IGNORECASE)
       
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
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        command_match = self.command_matcher.match(message.content)
        
        if (command_match is not None):
            if (command_match.group(1) == 'strike'):
                user_to_strike = message.guild.get_member(int(command_match.group(2)))
                await self.strike(user_to_strike, message.guild.roles, command_match.group(3))
                  
if __name__ == '__main__':
    load_dotenv()
    intents = discord.Intents.default()
    intents.members = True
    client = Client(intents=intents)
    client.run(os.getenv('DISCORD_BOT_TOKEN'))