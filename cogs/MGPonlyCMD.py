from logging import exception
import discord
from discord.ext import commands
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import random
from core.common import load_config
config, _ = load_config()
i = 1
time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

import logging

logger = logging.getLogger(__name__)

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

def random_rgb(seed=None):
    if seed is not None:
        random.seed(seed)
    return discord.Colour.from_rgb(random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))


class MGPonlyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("MGPonlyCMD.py: Cog Loaded!")

    @commands.command()
    @check_MGP()
    @commands.cooldown(1, 3600, commands.BucketType.channel)
    async def gametime(self, ctx):
        author = ctx.message.author
        channel = ctx.message.channel
        category = ctx.channel.category
        categoryname = category.name
        role = discord.utils.get(
            ctx.guild.roles, name=categoryname)
        if author.nick == None:
            authorname = author.name
        else:
            authorname = author.nick
        gamename = channel.name
        print("works")
        callembed = discord.Embed(
            title="Players are being called by", description=author.mention, color=0xFFCE41)

        callembed.add_field(name=authorname + " wants to play " + gamename, value="Is there anyone here that would like to join?", inline=True)
        callembed.set_footer(text="This command cannot be used again for 1 hour!")

        await channel.send(role.mention)
        await channel.send(embed=callembed)

    @gametime.error
    async def gametime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            msg = "This command cannot be used again for {} hours {} minutes and {} seconds" \
                .format(round(h), round(m), round(s))
            await ctx.send(msg)

        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("This command is not designed for this channel!")

        else:
            raise error

    @commands.command()
    @check_MGP()
    @commands.has_permissions(manage_roles=True)
    async def newgame(self, ctx, *, game, gamedesc):
        # Status set to null
        RoleCreate = "FALSE"
        CategoryCreate = "FALSE"
        ChannelCreate = "FALSE"
        RoleGiven = "FALSE"
        ChannelPermissions = "FALSE"
        DMStatus = "FALSE"
        author = ctx.message.author
        guild = ctx.message.guild
        channel = ctx.message.channel
        Muted = discord.utils.get(ctx.guild.roles, name="muted")
        Admin = discord.utils.get(ctx.guild.roles, name="Admin")
        Moderator = discord.utils.get(ctx.guild.roles, name="Moderators")
        Botmanager = discord.utils.get(ctx.guild.roles, name="Bot Manager")
        Bots = discord.utils.get(ctx.guild.roles, name="Bots")
        color = discord.Colour.from_rgb(random_rgb)
        role = await guild.create_role(name=game, color=color, mentionable=False)
        RoleCreate = "DONE"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
            Muted.me: discord.PermissionOverwrite(view_channel=False,send_messages=False,add_reactions=False,connect=False),
            role.me: discord.PermissionOverwrite(view_channel=True,connect=False),
            Admin.me: discord.PermissionOverwrite(view_channel=True,connect=False),
            Moderator.me: discord.PermissionOverwrite(view_channel=True,connect=False),
            Botmanager.me: discord.PermissionOverwrite(view_channel=True,connect=False),
            Bots.me: discord.PermissionOverwrite(view_channel=True,connect=False)

        }
        category = guild.create_category(name=game, overwrites=overwrites)
        CategoryCreate = "Done"
        channel = await category.create_text_channel(name=game)
        await channel.edit(topic=gamedesc)
        await channel.set_permissions(Muted, overwrite=overwrites)
        ChannelCreate = "DONE"

        embed = discord.Embed(title="Game Creation Output", description="game Requested by: " + author.mention, color=0x38ebeb)
        embed.add_field(name="**Console Logs**", value="**Role Created:** " + RoleCreate + " -> " + role.mention + "\n**Category Created:** " + CategoryCreate + ">\n**Channel Created:** " + ChannelCreate +" -> <#" + str(channel.id) + ">\n**Role Given:** " + RoleGiven + "\n**Channel Permissions:** " + ChannelPermissions + "\n**DMStatus:** " + DMStatus)
        embed.set_footer(text = "The command has finished all of its tasks")
        embed.set_thumbnail(url = user.avatar_url)
        await ctx.send(embed=embed)

    @newgame.error
    async def newgame_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Uh oh, looks like I can't execute this command because you don't have permissions!")

        if isinstance(error, commands.TooManyArguments):
            await ctx.send("You sent too many arguments! Did you use quotes for game names over 2 words?")

        if isinstance(error, commands.CheckFailure):
            await ctx.send("This Command was not designed for this server!")

        else:
            raise error 

def setup(bot):
    bot.add_cog(MGPonlyCMD(bot))
