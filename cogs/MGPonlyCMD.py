from logging import exception
import discord
from discord.ext import commands
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from core.common import load_config
config, _ = load_config()
i = 1
time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

# -------------------------------------------------------

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

sheet = client.open(
    "Minecraft Realm Portal Channel Application (Responses)").sheet1

sheet2 = client.open("MRPCommunityRealmApp").sheet1
# -------------------------------------------------------

def check_MRP():
    def predicate(ctx):
        return ctx.message.guild.id == 587495640502763521 or ctx.message.guild.id == 448488274562908170
    return commands.check(predicate)


def check_MGP():
    def predicate(ctx):
        return ctx.message.guild.id == 192052103017922567 or ctx.message.guild.id == 448488274562908170
    return commands.check(predicate)

def convert(time):
    try:
        return int(time[:-1]) * time_convert[time[-1]]
    except:
        return time


class MGPonlyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @check_MGP()
    @commands.cooldown(1, 3600, commands.BucketType.channel)
    async def gametime(self, ctx):
        author = ctx.message.author
        channel = ctx.message.channel
        authorname = author.nick
        gamename = channel.name
        print("works")
        callembed = discord.Embed(
            title="Players are being called by", description=author.mention, color=0xFFCE41)

        callembed.add_field(name=authorname + " wants to play " + gamename, value="Is there anyone here that would like to join?", inline=True)
        callembed.set_footer(text="This command cannot be used again for 1 hour!")

        await channel.send("@here")
        await channel.send(embed=callembed)

    @gametime.error
    async def gametime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            msg = "Try again in {} hours {} minutes and {} seconds" \
                .format(round(h), round(m), round(s))
            await ctx.send(msg)

        else:
            raise error

def setup(bot):
    bot.add_cog(MGPonlyCMD(bot))
