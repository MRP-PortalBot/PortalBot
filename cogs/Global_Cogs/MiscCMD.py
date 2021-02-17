from core.common import load_config
from pathlib import Path
import discord
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
from core import database
import aiohttp
import random
import json
import requests
import ast
import random
from datetime import datetime
from discord_slash import cog_ext
from discord_slash import SlashCommand
from discord_slash import SlashContext
from discord_slash.utils import manage_commands
rules = [":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!", ":two: **No spamming** in chat or direct messages!", ":three: **No religious or political topics**, those don’t usually end well!", ":four: **Keep pinging to a minimum**, it is annoying!", ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!",
         ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**", ":seven: **No realm or server is better than another!** It is **not** a competition.", ":eight: **Have fun** and happy crafting!", ":nine: **Discord Terms of Service apply!** You must be at least **13** years old."]
config, _ = load_config()
'''
import sentry_sdk
sentry_sdk.init(
    "https://75b468c0a2e34f8ea4b724ca2a5e68a1@o500070.ingest.sentry.io/5579376",
    traces_sample_rate=1.0
)
'''

import logging

logger = logging.getLogger(__name__)

async def random_rgb(ctx, seed=None):
    if seed is not None:
        random.seed(seed)

    d = datetime.datetime.utcnow()
    print (d)

    d.hour
    print (d.hour)

    if d.hour == 17:
        embed = discord.Embed(title="time stuff", description=d.hour, color=discord.Colour.from_rgb(random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))())
        await ctx.send(embed=embed)

def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + " -" + json_data[0]['a']
    return(quote)


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class MiscCMD(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)
        logger.info("MiscCMD: Cog Loaded!")

    # DM Command

    @commands.command()
    @commands.has_role("Moderator")
    async def DM(self, ctx, user: discord.User, *, message=None):
        message = message or "This Message is sent via DM"
        author = ctx.message.author
        await user.send(message)
        #await user.send("Sent by: " + author.name)

    @DM.error
    async def DM_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Moderator role!")

    # Ping Command
    @cog_ext.cog_slash(name="ping", description = "Shows the bots latency", guild_ids=[config['ServerID']])
    async def ping(self, ctx):
        # await ctx.send(f'**__Latency is__ ** {round(client.latency * 1000)}ms')
        pingembed = discord.Embed(
            title="Pong! ⌛", color=0xb10d9f, description="Current Discord API Latency")
        pingembed.add_field(name="Current Ping:",
                            value=f'{round(self.bot.latency * 1000)}ms')
        await ctx.send(embeds=[pingembed])

    # Uptime Command
    @commands.command()
    async def uptime(self, ctx):
        author = ctx.message.author
        await ctx.send("Really long time, lost track. ")

    # Purge Command
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=2):
        author = ctx.message.author
        await ctx.channel.purge(limit=amount)

    # Embed Command
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def embed(self, ctx, channel: discord.TextChannel, color: discord.Color, *, body):
        author = ctx.message.author
        title, bottom = body.split(" | ")
        embed = discord.Embed(title=title, description=bottom, color=color)
        await channel.send(embed=embed)

    # Nick Commamd
    @commands.command()
    @commands.has_role("Moderator")
    async def nick(self, ctx, user: discord.Member, channel: discord.TextChannel):
        author = ctx.message.author
        name = user.display_name
        channel = channel.name.split('-')
        if len(channel) == 2:  # real-emoji
            realm, emoji = channel
        else:  # realm-name-emoji
            realm, emoji = channel[0], channel[-1]
        await user.edit(nick=str(name) + " " + str(emoji))
        await ctx.send("Changed nickname!")

    @nick.error
    async def nick_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Moderator role!")

    # Removes your nickname.
    @cog_ext.cog_slash(name="rememoji", description = "Reverts your nickname back to your username!", guild_ids=[config['ServerID']])
    async def rememoji(self, ctx):
        author = ctx.author
        name = author.name
        await author.edit(nick=str(author.name))
        await ctx.send(content = "Removed your nickname!")

    # Add's an emoji to your nickname.
    @cog_ext.cog_slash(name="addemoji", description = "Add's an emoji to your nickname!", guild_ids=[config['ServerID']], options=[manage_commands.create_option(name = "channel" , description = "Channel's Emoji", option_type = 7, required = True)])
    async def addemoji(self, ctx, channel: discord.TextChannel = None):
        author = ctx.author
        name = author.display_name
        channel = channel.name.split('-')
        if len(channel) == 2:  # real-emoji
            realm, emoji = channel
        else:  # realm-name-emoji
            realm, emoji = channel[0], channel[-1]
        await author.edit(nick=str(name) + str(emoji))
        await ctx.send(content = "Changed your nickname!")


    # Rule Command [INT]
    @cog_ext.cog_slash(name="rule", description = "Sends out MRP Server Rules", guild_ids=[config['ServerID']], options=[manage_commands.create_option(name = "number" , description = "Rule Number", option_type = 4, required = True)])
    async def rule(self, ctx, number = None):
        await ctx.send(content = rules[int(number)-1])

    # Add's a gamertag to the database.

    @commands.command()
    async def gamertag(self, ctx, gamertag):
        author = ctx.message.author
        channel = ctx.message.channel
        GamerTag = open("Gamertags.txt", "a")
        GamerTag.write(gamertag + " " + str(author.id) + "\n")

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        await channel.send("Success! \nWould you like to change your nickname to your gamertag? (If so, you may have to add your emojis to your nickname again!)\n> *Reply with:* **YES** or **NO**")
        answer7 = await self.bot.wait_for('message', check=check)

        if answer7.content == "YES":
            await author.edit(nick=gamertag)
            await ctx.send("Success!")

        elif answer7.content == "NO":
            await ctx.send("Okay, canceled it...")

    @gamertag.error
    async def gamertag_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Uh oh, you didn't include all the arguments! ")

    @commands.command()
    @commands.has_role('Bot Manager')
    async def requestdb(self, ctx):
        """Request the database file for manual inspection"""
        db = Path("data.db")
        if not db.exists():
            await ctx.send("Database does not exist yet.")
            return
        with db.open(mode="rb") as f:
            await ctx.author.send(file=discord.File(f, "database.db"))
        await ctx.send("Database file sent to your DMs.")

    @commands.command()
    @commands.has_role('Bot Manager')
    async def deletedb(self, ctx):
        """Delete database file"""
        if database.db.is_closed():
            db = Path("data.db")
            if not db.exists():
                await ctx.send("Database file does not exist.")
                return
            db.unlink()
            await ctx.send("Database file has been deleted.")
        else:
            await ctx.send("Cannot delete; database is currently in use.")

    @commands.command()
    @commands.has_role("Bot Manager")
    async def replacedb(self, ctx):
        """Replace database file with attachment"""
        if database.db.is_closed():
            db = Path("data.db")
            if db.exists():
                db.unlink()
            with db.open(mode="wb+") as f:
                await ctx.message.attachments.save(f)
        else:
            await ctx.send("Cannot replace; database is currently in use.")

    @commands.command()
    @commands.has_role("Moderator")
    async def say(self, ctx, *, msg):
        await ctx.channel.purge(limit = 1)
        await ctx.send(msg)
    
    @commands.command(description="Rock Paper Scissors")
    async def rps(self, msg: str):
        """Rock paper scissors. Example : /rps Rock if you want to use the rock."""
        # Les options possibles
        t = ["rock", "paper", "scissors"]
        # random choix pour le bot
        computer = t[random.randint(0, 2)]
        player = msg.lower()
        print(msg)
        if player == computer:
            await self.bot.say("Tie!")
        elif player == "rock":
            if computer == "paper":
                await self.bot.say("You lose! {0} covers {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} smashes {1}".format(player, computer))
        elif player == "paper":
            if computer == "scissors":
                await self.bot.say("You lose! {0} cut {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} covers {1}".format(player, computer))
        elif player == "scissors":
            if computer == "rock":
                await self.bot.say("You lose! {0} smashes {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} cut {1}".format(player, computer))
        else:
            await self.bot.say("That's not a valid play. Check your spelling!")

    @commands.command()
    async def inspire(self, ctx):
        quote = get_quote()
        author = ctx.message.author
        embed = discord.Embed(title="Inspirational Quotes", description="Here is your quote {0}".format(
            author.mention), color=0xffe74d)
        embed.add_field(name="Quote", value=quote)
        await ctx.send(embed=embed)
    
    @commands.command() 
    async def reply(self, ctx):
        id = ctx.message.id
        await ctx.reply(content = "content") 
        

def setup(bot):
    bot.add_cog(MiscCMD(bot))



