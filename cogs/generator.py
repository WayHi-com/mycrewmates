import discord
import asyncio
from discord.ext import commands
from discord.ext.commands.errors import ChannelNotFound
from app import CONFIGS, DATABASE


class Generator(commands.Cog):

    def __init__(self, client):
        self.client = client


    # Delete Generator
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):

        guild_data = DATABASE['guilds'].find_one({"guild_id": payload.guild_id})

        # Exit if the deleted message is not a Generator
        for gen in guild_data['generators']:
            if gen['message_id'] == payload.message_id:
                break
        else:
            return
        
        # Remove Generator from MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": payload.guild_id}, 
            {"$pull": {"generators": {"message_id": payload.message_id}}}
        )


    # Subcommands
    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def generator(self, ctx, command, *args):

        # Subcommands
        if command in command_dictionary:
            await command_dictionary[command](ctx, args)


    @staticmethod
    async def create(ctx, args):

        guild_data = DATABASE['guilds'].find_one({"guild_id": ctx.guild.id})

        await ctx.send('Creating a new Lobby Generator.')

        # Get a channel for the Generator
        try:
            channel = await commands.TextChannelConverter().convert(ctx, args[0])
        except ChannelNotFound:
            await ctx.send('Channel not found.')
            return
        except Exception:
            await ctx.send(CONFIGS['exception_message'])
            return

        # Get Generator title
        while (title := await get_user_response(ctx, 'Enter Title.')) is None:
            continue
 
        # Get Generator description
        while (description := await get_user_response(ctx, 'Enter Description.')) is None:
            continue

        # Get emoji-name pairs
        pairs = []
        while True:

            # Get response
            if (response := await get_user_response(ctx, 'Enter an emoji followed by your associated name (e.g. 👍 Thumgs Up!). Or type `done` to finish.')) == 'done':
                break

            if response is None:
                continue
            
            # Split response
            pair = response.split(' ')
            emoji = pair[0]
            name = ' '.join(pair[1:])

            # Append pair
            pairs.append((emoji, name))

        # Create Embed Message
        embed_message = ''
        for pair in pairs:
            embed_message += f'{pair[0]}: {pair[1]}\n'
        
        # Create Embed
        embed = discord.Embed(
            title=title, 
            color=0x00C700,
            description = f'''
            **{description}**
            
            {embed_message}
            '''
        )
        embed.set_footer(text='With ❤️ MyCrewmates')

        # Send Embed
        message = await channel.send(embed=embed)
        for pair in pairs:
            await message.add_reaction(pair[0])

        # Add Generator to MongoDB database
        DATABASE['guilds'].update_one(
            {"guild_id": ctx.guild.id}, 
            {"$push": {"generators": {
                "message_id": message.id,
                "pairs": pairs
            }}}
        )
        

async def get_user_response(ctx, prompt):
    await ctx.send(prompt)

    # Get response from the user and handle errors
    try:
        response = (await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=CONFIGS['timeout'])).content
    except asyncio.TimeoutError:
        ctx.send('Timed Out.', delete_after=CONFIGS['delete_after'])
        return
    except Exception:
        ctx.send(CONFIGS['exception_message'], delete_after=CONFIGS['delete_after'])
        return



    # Return Response
    return response


command_dictionary = {
    'create': Generator.create
}
        

def setup(client):
    client.add_cog(Generator(client))
