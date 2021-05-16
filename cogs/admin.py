import discord
from discord.ext import commands
from discord.ext.commands.errors import ChannelNotFound
from app import CONFIGS, DATABASE


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client


    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def admin(self, ctx, command, *args):

        # Subcommands
        if command in command_dictionary:
            await command_dictionary[command](ctx, args)


    @staticmethod
    async def toggle_vc(ctx, args):
        
        # Toggle VC disallowed for now
        return

        # Get fields
        guild_data = DATABASE['guilds'].find_one({"guild_id": ctx.guild.id})
        allow = guild_data['allow_vc']

        # Update MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": ctx.guild.id}, 
            {"$set": {"allow_vc": not allow}}
        )

        await ctx.send(f'Creating Voice Channel lobbies is now {"enabled" if (not allow) else "disabled"}.')


    @staticmethod
    async def toggle_tc(ctx, args):

        # Get fields
        guild_data = DATABASE['guilds'].find_one({"guild_id": ctx.guild.id})
        allow = guild_data['allow_tc']

        # Update MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": ctx.guild.id}, 
            {"$set": {"allow_tc": not allow}}
        )

        await ctx.send(f'Creating Text Channel lobbies is now {"enabled" if (not allow) else "disabled"}.')


    @staticmethod
    async def set_create_lobby_channel(ctx, args):
        
        # Get channel
        try:
            if not (channel := ctx.guild.get_channel(int(args[0]))):
                await ctx.send('Channel not found.', delete_after=CONFIGS['delete_after'])
                return
        except ValueError:
            await ctx.send('Invalid channel ID', delete_after=CONFIGS['delete_after'])
            return
        except Exception:
            await ctx.send(CONFIGS['exception_message'], delete_after=CONFIGS['delete_after'])
            return

        # Update MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": ctx.guild.id}, 
            {"$set": {"create_lobby_channel": channel.id}}
        )

        await ctx.send('Create Lobby VC has been updated.', delete_after=CONFIGS['delete_after'])


    @staticmethod
    async def set_lobby_category(ctx, args):
        
        # Get channel
        try:
            if not (category := ctx.guild.get_channel(int(args[0]))):
                await ctx.send('Category not found.', delete_after=CONFIGS['delete_after'])
                return
        except ValueError:
            await ctx.send('Invalid category ID', delete_after=CONFIGS['delete_after'])
            return
        except Exception:
            await ctx.send(CONFIGS['exception_message'], delete_after=CONFIGS['delete_after'])
            return

        # Update MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": ctx.guild.id}, 
            {"$set": {"lobby_category": category.id}}
        )

        await ctx.send('Lobby Category has been updated.', delete_after=CONFIGS['delete_after'])



command_dictionary = {
    'toggle_vc': Admin.toggle_vc,
    'toggle-vc': Admin.toggle_vc,
    'togglevc': Admin.toggle_vc,
    'tvc': Admin.toggle_vc,

    'toggle_tc': Admin.toggle_tc,
    'toggle-tc': Admin.toggle_tc,
    'toggletc': Admin.toggle_tc,
    'ttc': Admin.toggle_tc,

    'set_create_lobby_channel': Admin.set_create_lobby_channel,
    'set-create-lobby-channel': Admin.set_create_lobby_channel,
    'create_lobby_channel': Admin.set_create_lobby_channel,
    'create-lobby-channel': Admin.set_create_lobby_channel,
    'lobby_channel': Admin.set_create_lobby_channel,
    'lobby-channel': Admin.set_create_lobby_channel,
    'sclc': Admin.set_create_lobby_channel,
    'clc': Admin.set_create_lobby_channel,

    'set_lobby_category': Admin.set_lobby_category,
    'set-lobby-category':  Admin.set_lobby_category,
    'lobby_category': Admin.set_lobby_category,
    'lobby-category': Admin.set_lobby_category,
    'slc': Admin.set_lobby_category,
}

def setup(client):
    client.add_cog(Admin(client))