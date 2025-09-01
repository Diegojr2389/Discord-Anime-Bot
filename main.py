import discord
from discord.ui import View, Select
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from scrape import get_anime
from scrape import get_top_10
from scrape import get_genre
from scrape import get_song
from fetchSong import get_song_url
import datetime

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
channel_id = os.getenv('DISCORD_TOKEN')

# Set up basic logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# specify the intents
intents = discord.Intents.default()
# manually enable the required intents
intents.message_content = True
intents.members = True

# command_prefix is used to reference the bot
bot = commands.Bot(command_prefix='!', intents=intents)

secret_role = "weeb"

@tasks.loop(minutes=1)
async def weekly_task():
    now = datetime.datetime.now()
    if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
        channel = bot.get_channel(channel_id)

        # make fake context to pass in
        ctx = await bot.get_context(
            await channel.send("Running weekly top10...")
        )

        cmd = bot.get_command("top10")
        ctx.command = cmd

        await bot.invoke(ctx)

# HANDLING EVENTS
@bot.event
async def on_ready():
    weekly_task.start()
    print(f'Logged in as {bot.user.name}')

@ bot.event 
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")

@ bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    banned_words = ["shit", "fuck", "bitch", "hoe", "dick", "pussy", "bastard"]
    message_content = message.content.lower()
    if any(word in message_content for word in banned_words):
        await message.delete()
        # .mention after author, tags/pings the user in the server
        await message.channel.send(f"{message.author.mention} No profanity!")

    # continue handling all messages in the server
    # cotinutes handling the rest of the commands
    # we need this if we are overriding a function
    await bot.process_commands(message)

# ADDING COMMANDS
@ bot.command()
# !hello
async def hello(ctx): # get context on what triggered the command
    # ctx.send is used to send a message in the channel where the command was invoked
    await ctx.send(f"Hello {ctx.author.mention}!")

# assinging a role to the user
# !assign
@ bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send(f"Role {secret_role} doesn't exist")

# removing a role from the user
# !remove
@ bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {secret_role} role removed")
    else:
        await ctx.send(f"Role {secret_role} doesn't exist")

# sending direct message to users
@ bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

# reply to message
@ bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

# embedded message
@ bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍") # Windows Key + Period (.)
    await poll_message.add_reaction("👎")

# get top 10 anime
@ bot.command()
async def top10(ctx):
    top_anime = get_top_10()
    message = "Top 10 Anime:\n" + "\n".join([f"{i+1}. {english_title} - Score: {score}\n{url}\n" for i, (title, score, url, english_title) in enumerate(top_anime)])
    await ctx.reply(message, suppress_embeds=True)

# get specific genre anime
@ bot.command()
async def genre(ctx, *, specified_genre):
    genre_anime = get_genre(specified_genre)
    if genre_anime:
        message = f"{specified_genre} Anime this season:\n" + "\n".join([f"{english_title}\n{url}\n" for title, url, english_title in genre_anime])
        await ctx.reply(message, suppress_embeds=True)
    else:
        await ctx.reply(f"No {specified_genre} anime this season")

# A Discord UI view that dynamically creates a button for each anime in `anime_list`.
# When a user clicks a button, the `button_callback` is triggered:
#   - Stores the clicked anime's name in `self.value`
#   - Sends a confirmation message to the user
#   - Stops the view so the bot can continue after the user's choice
# The view uses `discord.ui.Button` objects with their callbacks bound at creation time.
class AnimeDropdown(discord.ui.View):
    def __init__(self, anime_list):
        super().__init__()
        self.value = None

        options = [discord.SelectOption(label=anime) for anime in anime_list]
        select = Select(placeholder="Choose an anime", options=options)
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        self.value = interaction.data['values'][0]
        await interaction.response.send_message(f"You selected {self.value}", ephemeral=True)
        self.stop()

# get opening song for an anime    
@bot.command()
async def song(ctx):
    anime_list = get_anime(25) # Get the top 25 anime
    # to show the user a dropdown menu with the anime list
    view = AnimeDropdown(anime_list)
    await ctx.send("Select an anime:", view=view)
    await view.wait()

    if view.value:
        song = get_song(view.value)
        if not song[0]:
            await ctx.reply(f"No song found for {view.value}")
            return
        song_url = get_song_url(song)
        await ctx.reply(f"Theme song for {view.value}: {song[0]}\n Listen here: {song_url}")
        
@ bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club!")

@ secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"{ctx.author.mention} You do not have permission to do that!")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
# USE RENDER to run the bot
# https://render.com/docs/deploy-python-discord-bot