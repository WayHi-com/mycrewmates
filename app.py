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
        "create_lobby_category": -1,
        "lobbies": [],
        "generators": []
    })


# Load Cogs
for filename in os.listdir('./cogs'):
    if filename != '__init__.py' and filename.endswith('.py'):
        client.load_extension(f'app/cogs.{filename[:-3]}')


# Run Bot
client.run(os.environ.get('BOT_TOKEN'))
