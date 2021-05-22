import os
import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Global variables
CONFIGS = {
    'prefix': '!',
    'timeout': 60,
    'delete_after': 20,
    'exception_message': 'Something went wrong. If you are not sure what happened, please read the documentation or contact support.'
}
MONGO_CLIENT = MongoClient(os.environ.get('MONGODB_URI'))
DATABASE = MONGO_CLIENT['database']


# Set bot permissions
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=CONFIGS['prefix'], intents=intents)


# Help Command
class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        prefix = self.context.prefix

        embed = discord.Embed(title='**Help**', color=0x00C700)
        commands = f'''
**Admin Commands**

{prefix}admin toggle_tc
(Toggles Text Channel Lobbies)
Aliases:
toggle-tc, toggletc, ttc

{prefix}admin set_create_lobby_channel <Channel ID>
(Sets the VC that a user must be in to create a Lobby)
Aliases:
set-create-lobby-channel, create_lobby_channel, create-lobby-channel, lobby_channel, lobby-channel, sclc

{prefix}admin set_lobby_category <Category ID>
(Sets the Category that a Lobby is created in)
Aliases:
set-lobby-category, lobby_category, lobby-category, slc

**Generator Commands**

{prefix}generator create <#channel>
(Creates a Lobby Generator)

**Lobby Commands**

{prefix}lobby lock
(Toggles a Lobby lock (in the same way as Grove Gaming) )

{prefix}lobby spectate_mode
(Toggles a Lobby Spectate Mode (in the same way as Grove Gaming) )
Aliases:
spectate-mode, spectatemode, spectate

{prefix}lobby size <new size>
(Sets the capacity of a Lobby VC)

{prefix}lobby name <new name>
(Changes the name of a Lobby VC)
'''
        support = f'''
For additional support or questions, join the bot's home here:
https://discord.gg/M2ry8MN7bd
To invite this bot to your own server, use this link:
{discord.utils.oauth_url(client_id=client.user.id, permissions=discord.Permissions(permissions=8))}        
'''

        embed.add_field(name='***Commands***', value=commands, inline=True)
        embed.add_field(name='***Support***', value=support, inline=True)
        await channel.send(embed=embed)


client.help_command = MyHelp()


# Confirm Bot is live
@client.event
async def on_ready():
    print('Bot is online.')


# Add a guild document to the database
@client.event
async def on_guild_join(guild):
    DATABASE.guilds.insert_one({
        "guild_id": guild.id,
        "allow_vc": True,
        "allow_tc": False,
        "create_lobby_channel": -1,
        "lobby_category": -1,
        "lobbies": [],
        "generators": []
    })


# Load Cogs
for filename in os.listdir('./cogs'):
    if filename != '__init__.py' and filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


# Run Bot
client.run(os.environ.get('BOT_TOKEN'))
