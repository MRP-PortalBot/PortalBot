from core.common import load_config
from pathlib import Path
import discord
from discord.ext import commands
from discord.commands import slash_command
from core import database
import aiohttp
import random
import json
import requests
import ast
import random
from datetime import datetime

config, _ = load_config()

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
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)
        logger.info("MiscCMD: Cog Loaded!")

    # Ping Command
    @slash_command(name="ping", description = "Shows the bots latency", guild_ids=[config['PBtest']])
    async def ping(self, ctx):
        # await ctx.send(f'**__Latency is__ ** {round(client.latency * 1000)}ms')
        pingembed = discord.Embed(
            title="Pong! ⌛", color=0x20F6B3, description="Current Discord API Latency")
        pingembed.add_field(name="Current Ping:",
                            value=f'{round(self.bot.latency * 1000)}ms')
        await ctx.send(embed=pingembed)

def setup(bot):
    bot.add_cog(MiscCMD(bot))



