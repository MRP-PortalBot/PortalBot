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
from datetime import datetime
rules = [":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!", ":two: **No spamming** in chat or direct messages!", ":three: **No religious or political topics**, those don’t usually end well!", ":four: **Keep pinging to a minimum**, it is annoying!", ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!",
         ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**", ":seven: **No realm or server is better than another!** It is **not** a competition.", ":eight: **Have fun** and happy crafting!", ":nine: **Discord Terms of Service apply!** You must be at least **13** years old."]
config, _ = load_config()


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
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.id == 777361919211732993:
            if after.status == discord.Status.offline and before.status != discord.Status.offline:
                channel = self.bot.get_channel(792485617954586634)
                now = datetime.now().strftime("%H:%M:%S")
                embed = discord.Embed(title = "⚠️ PortalBot is offline!", description = "Recorded Downtime (start): " + str(now) , color = 0xf03224)
                embed.add_field(name = "Restart Link", value = "__https://repl.it/join/ohvpqkio-rohitturtle0__")
                await channel.send(embed = embed)


    # DM Command
    @commands.command()
    @commands.has_role("Moderator")
    async def DM(self, ctx, user: discord.User, *, message=None):
        message = message or "This Message is sent via DM"
        author = ctx.message.author
        await user.send(message)
        await user.send("Sent by: " + author.name)

    @DM.error
    async def DM_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Moderator role!")

    # Ping Command
    @commands.command()
    async def ping(self, ctx):
        author = ctx.message.author
        # await ctx.send(f'**__Latency is__ ** {round(client.latency * 1000)}ms')
        pingembed = discord.Embed(
            title="Pong! ⌛", color=0xb10d9f, description="Current Discord API Latency")
        pingembed.add_field(name="Current Ping:",
                            value=f'{round(self.bot.latency * 1000)}ms')
        await ctx.send(embed=pingembed)

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

    # Say Command
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def say(self, ctx, *, reason):
        author = ctx.message.author
        await ctx.channel.purge(limit=1)
        await ctx.send(reason)

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
    @commands.command()
    async def rememoji(self, ctx):
        author = ctx.message.author
        name = author.name
        await author.edit(nick=str(author.name))
        await ctx.send("Removed your nickname!")

    # Add's an emoji to your nickname.
    @commands.command()
    async def addemoji(self, ctx, channel: discord.TextChannel):
        author = ctx.message.author
        name = author.display_name
        channel = channel.name.split('-')
        if len(channel) == 2:  # real-emoji
            realm, emoji = channel
        else:  # realm-name-emoji
            realm, emoji = channel[0], channel[-1]
        await author.edit(nick=str(name) + str(emoji))
        await ctx.send("Changed your nickname!")

    @addemoji.error
    async def addemoji_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Hmm, you didn't give me all the arguments.")

    # Rule Command [INT]
    @commands.command()
    async def rule(self, ctx, *, number):
        author = ctx.message.author
        await ctx.send(rules[int(number)-1])

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
        with db.open() as f:
            ctx.user.send(file=discord.File(f, "database.db"))
        await ctx.send("Database file sent to your DMs.")

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


def setup(bot):
    bot.add_cog(MiscCMD(bot))
