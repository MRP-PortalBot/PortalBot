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
from string import capwords
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id == 587495640502763521:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = discord.utils.get(guild.channels, name="games-selection")
        if payload.user_id != self.bot.user.id:
            if payload.channel_id == channel.id:
                print(channel.id)
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                embed = msg.embeds[0]
                game = embed.title
                game = game.replace("__","")
                print(game)
                emoji = msg.reactions[0]
                author = discord.utils.get(guild.members, id=payload.user_id)
                if str(payload.emoji) == str(emoji):
                    role = discord.utils.get(guild.roles, name=str(game))
                    print(role)
                    await author.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id == 587495640502763521:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = discord.utils.get(guild.channels, name="games-selection")
        if payload.user_id != self.bot.user.id:
            if payload.channel_id == channel.id:
                print(channel.id)
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                embed = msg.embeds[0]
                game = embed.title
                game = game.replace("__","")
                print(game)
                emoji = msg.reactions[0]
                author = discord.utils.get(guild.members, id=payload.user_id)
                if str(payload.emoji) == str(emoji):
                    role = discord.utils.get(guild.roles, name=str(game))
                    print(role)
                    await author.remove_roles(role)

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
    async def newgame(self, ctx, game, emoji, imageurl, *, gamedesc):
        # Status set to null
        RoleCreate = "FALSE"
        CategoryCreate = "FALSE"
        ChannelCreate = "FALSE"
        EmbedPosted = "FALSE"
        ReactionsAdded = "FALSE"
        author = ctx.message.author
        guild = ctx.message.guild
        channel = ctx.message.channel
        try:    
            Muted = discord.utils.get(ctx.guild.roles, name="muted")
            Admin = discord.utils.get(ctx.guild.roles, name="Admin")
            Moderator = discord.utils.get(ctx.guild.roles, name="Moderators")
            Botmanager = discord.utils.get(ctx.guild.roles, name="Bot Manager")
            Bots = discord.utils.get(ctx.guild.roles, name="Bots")
        except Exception as e:
            await ctx.send(f"**ERROR:**\nSomething happened when trying to fetch the required roles!\n{e}")
        
        roletest = discord.utils.get(ctx.guild.roles, name=game)
        if game == str(roletest):
            role = roletest
            RoleCreate = "EXISTING"
            print(role)
        else:
            role = await guild.create_role(name=game, color=random_rgb(), mentionable=False)
            RoleCreate = "CREATED"
            print(role)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False,connect=False),
            Muted: discord.PermissionOverwrite(view_channel=False,send_messages=False,add_reactions=False,connect=False),
            role: discord.PermissionOverwrite(view_channel=True,connect=True),
            Admin: discord.PermissionOverwrite(view_channel=True,connect=True),
            Moderator: discord.PermissionOverwrite(view_channel=True,connect=True),
            Botmanager: discord.PermissionOverwrite(view_channel=True,connect=True),
            Bots: discord.PermissionOverwrite(view_channel=True,connect=True)

        }
        category = await guild.create_category(name=game, overwrites=overwrites)
        CategoryCreate = "Done"
        channel = await guild.create_text_channel(name=game, category=category)
        await channel.edit(topic=gamedesc)
        ChannelCreate = "DONE"

        gschannel = discord.utils.get(ctx.guild.channels, name="games-selection")

        gsembed = discord.Embed(title="__" + game + "__", description=gamedesc, color=0xFFCE41)
        gsembed.set_image(url = imageurl)
        gsmessage = await gschannel.send(embed=gsembed)
        EmbedPosted = "DONE"

        reactions = [str(emoji)]
        for emoji in reactions:
            await gsmessage.add_reaction(emoji)
        ReactionsAdded = "DONE"

        embed = discord.Embed(title="Game Creation Output", description="game Requested by: " + author.mention, color=0x38ebeb)
        embed.add_field(name="**Console Logs**", value="**Role Created:** " + RoleCreate + " -> " + role.mention + "\n**Category Created:** " + CategoryCreate + "->\n**Channel Created:** " + ChannelCreate +" -> <#" + str(channel.id) + ">\n**Embed Posted:** " + EmbedPosted + "\n**Reaction Role Added:** " + ReactionsAdded)
        embed.set_footer(text = "The command has finished all of its tasks")
        embed.set_thumbnail(url = author.avatar_url)
        await ctx.send(embed=embed)
        

    @newgame.error
    async def newgame_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Uh oh, looks like I can't execute this command because you don't have permissions!")

        if isinstance(error, commands.TooManyArguments):
            await ctx.send("You sent too many arguments! Did you use quotes for game names over 2 words?")

        if isinstance(error, commands.CheckFailure):
            await ctx.send("This Command was not designed for this server!")

        if isinstance(error, commands.BadArgument):
            await ctx.send("You didn't include all of the arguments!")

        else:
            raise error 

    @commands.command()
    @check_MGP()
    @commands.has_permissions(manage_roles=True)
    async def gamelist(self, ctx, channel: discord.TextChannel):
        roles = ([str(r.name) for r in ctx.guild.roles])
        del roles[0]
        roles.sort(key = lambda k : k.lower())
        answer = roles[-1]
        roles = ", ".join(roles)
        games = []
        async for embed_history in channel.history().filter(lambda m: m.embeds):
            channel = self.bot.get_channel(803345523758727179)
            msg = embed_history
            embed = msg.embeds[0]
            game = str(embed.title)
            game = game.replace("__","")
            game = game.replace(".","")
            #game = game.replace("Embed.Empty","")
            games.append(game)
        
        games.sort(key = lambda k : k.lower())
        answer = games[-1]
        games = ", ".join(games)


        
        #author = ctx.message.author
        #guild = ctx.message.guild
        #channel = ctx.message.channel
        #gamechannel = discord.utils.get(guild.channels, name="games-selection")

        #embed_history = await gamechannel.history(limit=None).flatten
        #print (embed_history)
        

        
        embed = discord.Embed(title = "Sorted Gamelist!", description = roles, color = random_rgb())
        embed.add_field(name = "List 2", value = games)
        await ctx.send(embed = embed)

        #embed = discord.Embed(title="Game Creation Output", description="game Requested by: " + author.mention, color=0x38ebeb)
        #embed.add_field(name="**Console Logs**", value="**Role Created:** " + RoleCreate + " -> " + role.mention + "\n**Category Created:** " + CategoryCreate + "->\n**Channel Created:** " + ChannelCreate +" -> <#" + str(channel.id) + ">\n**Embed Posted:** " + EmbedPosted + "\n**Reaction Role Added:** " + ReactionsAdded)
        #embed.set_footer(text = "The command has finished all of its tasks")
        #embed.set_thumbnail(url = author.avatar_url)
        


    @gamelist.error
    async def gamelist_error(self, ctx, error):
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
