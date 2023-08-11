import ast
import json
import random
from datetime import datetime
from pathlib import Path

import discord
import requests
from discord import app_commands
from discord.ext import commands

from core import database


rules = [":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!", ":two: **No spamming** in chat or direct messages!", ":three: **No religious or political topics**, those don’t usually end well!", ":four: **Keep pinging to a minimum**, it is annoying!", ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!",
         ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**", ":seven: **No realm or server is better than another!** It is **not** a competition.", ":eight: **Have fun** and happy crafting!", ":nine: **Discord Terms of Service apply!** You must be at least **13** years old."]

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
        self.bot = bot
        logger.info("MiscCMD: Cog Loaded!")

##======================================================Commands===========================================================

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

    @commands.command()
    @commands.has_role('Bot Manager')
    async def requestdb(self, ctx):
        """Request the database file for manual inspection"""
        db = Path("data.db")
        if not db.exists():
            await ctx.send("Database does not exist yet.")
            return
        with db.open(mode="rb") as f:
            file=discord.File(f, "database.db")
            await ctx.author.send(file=file)
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


##======================================================Slash Commands===========================================================

    # Removes your nickname.
    """@slash_command(name="rememoji", description = "Reverts your nickname back to your username!", guild_ids=[config['SlashServer1'],config['SlashServer2'],config['SlashServer3']])
    async def removeemoji(self, ctx):
        author = ctx.author
        name = author.name
        await author.edit(nick=str(name))
        await ctx.respond(content = "Removed your nickname!")

    # Add's an emoji to your nickname.
    @slash_command(name="addemoji", description = "Add's an emoji to your nickname!", guild_ids=[config['SlashServer1'],config['SlashServer2'],config['SlashServer3']])
    async def addemoji(self, ctx, channel: discord.TextChannel = None):
        author = ctx.author
        name = author.display_name
        channel = channel.name.split('-')
        if len(channel) == 2:  # real-emoji
            realm, emoji = channel
        else:  # realm-name-emoji
            realm, emoji = channel[0], channel[-1]
        await author.edit(nick=str(name) + str(emoji))
        await ctx.respond(content = "Changed your nickname!")"""


    # Rule Command [INT]
    @app_commands.command(name="rule", description = "Sends out MRP Server Rules")
    async def rule(self, interaction: discord.Interaction, number: int = None):
        await interaction.response.send_message(rules[int(number)-1])
        

async def setup(bot):
    await bot.add_cog(MiscCMD(bot))



