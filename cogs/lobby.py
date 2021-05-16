import discord
from discord.ext import commands
from app import CONFIGS, DATABASE


class Lobby(commands.Cog):

    def __init__(self, client):
        self.client = client


    # Create Lobby
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Exit if this is the bot adding reactions
        if payload.member.bot:
            return
        
        # Get some fields
        guild_data = DATABASE['guilds'].find_one({"guild_id": payload.guild_id})
        guild = self.client.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = channel.get_partial_message(payload.message_id)
        allow_vc = guild_data['allow_vc']
        allow_tc = guild_data['allow_tc']

        # Exit if the guild does not have a create_lobby_id set.
        if guild_data['create_lobby_channel'] == -1 or guild_data['lobby_category'] == -1:
            await channel.send('This server has not set up lobby creation.', delete_after=CONFIGS['delete_after'])
            return

        # Exit if the reacted message is not a Generator
        for gen in guild_data['generators']:
            if gen['message_id'] == payload.message_id:
                generator = gen
                break
        else:
            return

        # Remove the reaction
        await message.remove_reaction(payload.emoji, payload.member)

        # Exit if the user is not in the correct vc
        create_lobby_id = guild_data['create_lobby_channel']
        if (not payload.member.voice) or (payload.member.voice.channel.id != create_lobby_id):
            await channel.send(content=f'Please join {guild.get_channel(create_lobby_id).mention} to create a lobby.', delete_after=CONFIGS['delete_after'])
            return

        # Create Overwrites
        creator_overwrite = discord.PermissionOverwrite(
            move_members=True,
            manage_messages=True,
            connect=True,
            speak=True,
            stream=True,
            send_messages=True
        )
        default_overwrite = discord.PermissionOverwrite(
            connect=True,
            speak=True,
            stream=True,
            send_messages=True
        )

        # Get channel name and cateogry
        lobby_index = len(guild_data['lobbies']) + 1
        for pair in generator['pairs']:
            if pair[0] == str(payload.emoji):
                lobby_name = pair[1]
                break
        category = guild.get_channel(guild_data['lobby_category'])
        
        # Create Channels
        lobby_vc = None
        lobby_tc = None
        if allow_vc:
            lobby_vc = await guild.create_voice_channel(
                f'{lobby_index} | {lobby_name}',
                category=category,
                overwrites={
                    payload.member: creator_overwrite, 
                    guild.default_role: default_overwrite
                },
                user_limit=10
            )
            # Move user to vc
            await payload.member.move_to(lobby_vc)

        if allow_tc:
            lobby_tc = await guild.create_text_channel(
                f'{lobby_index}:{lobby_name}',
                category=category,
                overwrites={
                    payload.member: creator_overwrite, 
                    guild.default_role: default_overwrite
                }
            ) 

        # Add lobby to MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": payload.guild_id}, 
            {"$push": {"lobbies": {
                "vc_id": None if (lobby_vc is None) else lobby_vc.id,
                "tc_id": None if (lobby_tc is None) else lobby_tc.id,
                "creator_id": payload.member.id
            }}}
        )       


    # Delete Lobby
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        # Exit if the user is not leaving a vc
        if before is None:
            return

        guild_data = DATABASE['guilds'].find_one({"guild_id": member.guild.id})

        # Exit if the user is not the creator of the vc they are leaving
        for lobby in guild_data['lobbies']:
            if lobby['creator_id'] != member.id:
                continue
            if lobby['vc_id'] == before.channel.id:
                
                lobby_vc = member.guild.get_channel(lobby['vc_id'])
                lobby_tc = member.guild.get_channel(lobby['tc_id'])
                break
        else:
            return

        # Delete Lobby
        if guild_data['allow_vc']:
            await lobby_vc.delete()
        if guild_data['allow_tc']:
            await lobby_tc.delete()

        # Update MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": member.guild.id}, 
            {"$pull": {"lobbies": {"creator_id": member.id}}}
        )   


    # Subcommands
    @commands.command()
    async def lobby(self, ctx, command, *args):

        guild_data = DATABASE['guilds'].find_one({"guild_id": ctx.guild.id})
        
        # Exit if the user does not have a lobby
        for lobby in guild_data['lobbies']:
            if lobby['creator_id'] == ctx.author.id:

                lobby_vc = ctx.guild.get_channel(lobby['vc_id'])
                break
        else:
            await ctx.send('You do not have a lobby.', delete_after=CONFIGS['delete_after'])
            return

        # Subcommands
        if command in command_dictionary:
            await command_dictionary[command](ctx, lobby_vc, args)

    
    # Toggle lock
    @staticmethod
    async def lock(ctx, lobby_vc, args):

        # Get Overwrite
        default_overwrites = lobby_vc.overwrites_for(ctx.guild.default_role)
        connect = default_overwrites.connect

        # Set Overwrite
        default_overwrites.update(connect=not connect)
        await lobby_vc.set_permissions(ctx.guild.default_role, overwrite=default_overwrites)

        # Send confirmation message
        await ctx.send(f'Lobby {"Unlocked." if (not connect) else "Locked."}', delete_after=CONFIGS['delete_after'])


    # Toggle spectate mode
    @staticmethod
    async def spectate(ctx, lobby_vc, args):

        # Get Overwrite
        default_overwrites = lobby_vc.overwrites_for(ctx.guild.default_role)
        speak = default_overwrites.speak
        stream = default_overwrites.stream

        # Set Overwrite
        default_overwrites.update(speak=not speak, stream=not stream)
        await lobby_vc.set_permissions(ctx.guild.default_role, overwrite=default_overwrites)

        # Send confirmation message
        await ctx.send(f'Spectate Mode {"Disabled." if (not speak) else "Enabled"}', delete_after=CONFIGS['delete_after'])


    # Change VC size
    @staticmethod
    async def size(ctx, lobby_vc, args):

        # Get a new size
        try:
            new_size = int(args[0])
        except ValueError:
            ctx.send('Please enter a valid size.', delete_after=CONFIGS['delete_after'])
            return
        except Exception:
            ctx.send(CONFIGS['exception_message'], delete_after=CONFIGS['delete_after'])
            return
        
        if new_size < 1:
            ctx.send('Please enter a valid size.', delete_after=CONFIGS['delete_after'])
            return

        # Edit VC
        await lobby_vc.edit(user_limit=args[0])

        # Send confirmation message
        await ctx.send(f'Lobby size changed to {new_size}', delete_after=CONFIGS['delete_after'])


    # Change VC name
    @staticmethod
    async def name(ctx, lobby_vc, args):

        # Edit VC
        new_name = ' '.join(args)
        await lobby_vc.edit(name=new_name)

        # Send confirmation message
        await ctx.send(f'Lobby name changed to {new_name}', delete_after=CONFIGS['delete_after'])


command_dictionary = {
    'lock': Lobby.lock,
    'unlock': Lobby.lock,

    'spectate': Lobby.spectate,
    'spectatemode': Lobby.spectate,
    'spectate_mode': Lobby.spectate,
    'spectate-mode': Lobby.spectate,

    'size': Lobby.size,

    'name': Lobby.name,
}
        

def setup(client):
    client.add_cog(Lobby(client))