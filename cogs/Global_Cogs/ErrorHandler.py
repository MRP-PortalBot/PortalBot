from discord.ext import commands
import discord
from typing import List
import traceback
from pathlib import Path
import core.common
import asyncio
import requests
import yarl
import os
import json
from core.common import query
import logging
import random

logger = logging.getLogger(__name__)

def random_rgb(seed=None):
    if seed is not None:
        random.seed(seed)
    return discord.Colour.from_rgb(random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))


def stackoverflow(q):
    q = str(q)
    baseUrl = "https://stackoverflow.com/search?q="
    error = q.replace(" ","+")
    error = error.replace(".","")
    stackURL = baseUrl + error 
    return stackURL

class GithubError(commands.CommandError):
    pass


class CustomError(Exception):
    def __init__(self, times: int, msg: str):
        self.times = times
        self.msg = msg
        self.pre = "This is a custom error:"
        self.message = f"{self.pre} {self.msg*self.times}"
        super().__init__(self.message)


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        logger.info("ErrorHandler: Cog Loaded!")

    @commands.command()
    async def error(self, ctx, times: int = 20, msg="error"):
        raise CustomError(int(times), msg)

    # Checks if the command has a local error handler.
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: Exception):
        dev_role = discord.utils.get(ctx.guild.roles, name='Bot Manager')
        tb = error.__traceback__
        etype = type(error)
        exception = traceback.format_exception(etype, error, tb, chain=True)
        exception_msg = ""
        sturl = stackoverflow(error)
        for line in exception:
            exception_msg += line
        
        if isinstance(error, commands.CheckFailure) or isinstance(error, commands.CheckAnyFailure):
            return

        if hasattr(ctx.command, 'on_error'):
            return

        elif isinstance(error, commands.CommandNotFound):
            config, _ = core.common.load_config()
            em = discord.Embed(title = "Invalid Command!", description = f"This command doesn't exist!", color = 0xf5160a)
            em.set_thumbnail(url = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png")
            em.set_footer(text = "Consult the Help Command if you are having trouble or call over a Bot Manager!")
            await ctx.send(embed = em)
            print("Ignored error: " + str(ctx.command))

        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.TooManyArguments):
            em = discord.Embed(title = "Missing/Extra Required Arguments Passed In!", description = f"You have missed one or several arguments in this command", color = 0xf5160a)
            em.set_thumbnail(url = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png")
            em.set_footer(text = "Consult the Help Command if you are having trouble or call over a Bot Manager!")
            await ctx.send(embed = em)
            return

        elif isinstance(error, commands.BadArgument):
            em = discord.Embed(title = "Bad Argument!", description = f"Unable to parse arguments, check what arguments you provided.", color = 0xf5160a)
            em.set_thumbnail(url = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png")
            em.set_footer(text = "Consult the Help Command if you are having trouble or call over a Bot Manager!")
            await ctx.send(embed = em)
            return

        elif isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
            em = discord.Embed(title = "Unauthorized Access!", description = f"You are not allowed to run this command!", color = 0xf5160a)
            em.set_thumbnail(url = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png")
            em.set_footer(text = "Consult the Help Command if you are having trouble or call over a Bot Manager!")
            await ctx.send(embed = em)
            return




        else:
            if len(exception_msg)+160 > 1024:
                error_file = Path("error.txt")
                error_file.touch()
                with error_file.open("w") as f:
                    f.write(exception_msg)
                with error_file.open("r") as f:
                    config, _ = core.common.load_config()
                    data = "\n".join([l.strip() for l in f])

                    GITHUB_API="https://api.github.com"
                    API_TOKEN=os.getenv("GIST")
                    url=GITHUB_API+"/gists"
                    print(f"Request URL: {url}")                    
                    headers={'Authorization':'token %s'%API_TOKEN}
                    params={'scope':'gist'}
                    payload={"description":"PortalBot encountered a Traceback!","public":True,"files":{"error":{"content": f"{data}"}}}
                    res=requests.post(url,headers=headers,params=params,data=json.dumps(payload))
                    j=json.loads(res.text)
                    ID = j['id']
                    gisturl = f"https://gist.github.com/{ID}"
                    print(gisturl)

                    if dev_role not in ctx.author.roles:
                        embed = discord.Embed(title = "Traceback Detected!", description = f"**Hey you!** *Mr. Turtle here has found an error, and boy is it a big one! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!", color = 0xfc3d03)
                        embed.add_field(name = "Bug Reporting", value = f"Have any extra information that could help resolve this issue? Feel free to use the **{config['prefix']}bug** command! \nUsage: `{config['prefix']}bug (extra valuable information here!)` \n\n**⚠️ Tracebacks get automatically reported! Feel free to add in a bug report though!** \n\nExamples of helpful information! \n\n- Any arguments you provided with the command\n- What the actual problem was (What went wrong?)\n- Any other information that could help!")
                        embed.set_footer(text = f"Error: {str(error)}")
                        await ctx.send(embed = embed)
                        guild = self.bot.get_guild(448488274562908170)
                        channel = guild.get_channel(797193549992165456)
                        embed2 = discord.Embed(title = "Traceback Detected!", description = f"**Information**\n**Server:** {ctx.message.guild.name}\n**User:** {ctx.message.author.mention}\n**Command:** {ctx.command.name}", color= 0xfc3d03)
                        embed2.add_field(name = "Gist URL", value = f"[Uploaded Traceback to GIST](https://gist.github.com/{ID})")
                        await channel.send(embed = embed2)
    
                    else:
                        embed = discord.Embed(title = "Beep Boop", description = "🚨 *I've ran into an issue!* 🚨\nThe Developers should get back to fixing that!", color = random_rgb())
                        embed.add_field(name = "Gist URL", value = f"**https://gist.github.com/{ID}**")
                        embed.add_field(name = "Stack Overflow", value = f"**{sturl}**", inline = False)
                        embed.set_footer(text = f"Error: {str(error)}")
                        await ctx.send(embed = embed)
                    error_file.unlink()
            else:
                GITHUB_API="https://api.github.com"
                API_TOKEN=os.getenv("GIST")
                url=GITHUB_API+"/gists"
                print(f"Request URL: {url}")                    
                headers={'Authorization':'token %s'%API_TOKEN}
                params={'scope':'gist'}
                payload={"description":"PortalBot encountered a Traceback!","public":True,"files":{"error":{"content": f"{data}"}}}
                res=requests.post(url,headers=headers,params=params,data=json.dumps(payload))
                j=json.loads(res.text)
                ID = j['id']
                gisturl = f"https://gist.github.com/{ID}"
                print(gisturl)

                if dev_role not in ctx.author.roles:
                    config, _ = core.common.load_config()
                    embed = discord.Embed(title = "Traceback Detected!", description = f"**Hey you!** *Mr. Turtle here has found an error! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!", color = 0xfc3d03)
                    embed.add_field(name = "Bug Reporting", value = f"Have any extra information that could help resolve this issue? Feel free to use the **{config['prefix']}bug** command! \nUsage: `{config['prefix']}bug (extra valuable information here!)` \n\n**⚠️ Tracebacks get automatically reported! Feel free to add in a bug report though!** \n\nExamples of helpful information! \n\n- Any arguments you provided with the command\n- What the actual problem was (What went wrong?)\n- Any other information that could help!")
                    embed.set_footer(text = f"Error: {str(error)}")
                    await ctx.send(embed = embed)
                    guild = self.bot.get_guild(448488274562908170)
                    channel = guild.get_channel(797193549992165456)
                    embed2 = discord.Embed(title = "Traceback Detected!", description = f"**Information:**\n**Server:** {ctx.message.guild.name}\n**User:** {ctx.message.author.mention}", color= 0xfc3d03)
                    embed2.add_field(name = "Traceback", value = f"```\n{exception_msg}\n```")
                    await channel.send(embed = embed2)
                else:
                    embed = discord.Embed(title = "Beep Boop", description = "🚨 *I've ran into an issue!* 🚨\nThe Developers should get back to fixing that!", color = random_rgb())
                    embed.add_field(name = "Gist URL", value = f"**https://gist.github.com/{ID}**")
                    embed.add_field(name = "Stack Overflow", value = f"**{sturl}**", inline = False)
                    embed.set_footer(text = f"Error: {str(error)}")
                    await ctx.send(embed = embed)
            print(error)
        raise error

    @commands.command()
    async def report(self, ctx): 
        msg = await ctx.send("Select What Type of Feedback to Send!\n🐞 - Bug Report\n📇 - Suggestion/Feedback")
        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user and m.author == author
        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '🐞' or str(reaction.emoji) == '📇')
        reactions = ['🐞', '📇']
        for emoji in reactions:
            await msg.add_reaction(emoji)
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=150.0, check=check2)
            if str(reaction.emoji) == '🐞':
                await msg.delete()
                author = ctx.message.author
                channel = ctx.message.channel
                responseguild = ctx.message.guild
                await channel.send("Enter you're bug report here!:")
                suggestion = await self.bot.wait_for('message', check=check)

                embed = discord.Embed(title = "Ready to Submit?", description = "Make sure the follwing response is an actual bug report!", color = 0x4c594b)
                embed.add_field(name = "Submit Feedback", value = "✅ - SUBMIT\n❌ - CANCEL")
                message = await ctx.send(embed = embed)
                reactions = ['✅', '❌']
                for emoji in reactions:
                    await message.add_reaction(emoji)

                def check2(reaction, user):
                    return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=100.0, check=check2)
                    if str(reaction.emoji) == "❌":
                        await channel.send("Ended Task")
                        await message.delete()
                        return
                    else:
                        await message.delete()
                        query(author.name, author.id, responseguild, channel.name, suggestion.content, "BUG")
                        guild = self.bot.get_guild(448488274562908170)
                        channel = guild.get_channel(797193549992165456)
                        embed = discord.Embed(title = "User Bug Report!", description = f"Author: {author.mention}\nChannel: {channel.name}\nServer: {responseguild.name}", color=0xfc8003)
                        embed.add_field(name = "Feedback", value = "[Trello URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)")
                        await channel.send(embed = embed)
                        embed = discord.Embed(title = "I have sent in your bug report!", description = f"You can view your report's progress here! [Trello URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)", color = 0x4c594b)
                        await ctx.send(embed = embed)

                except asyncio.TimeoutError:
                    await channel.send("Looks like you didn't react in time, please try again later!")

                
                
            else: 
                await msg.delete()
                author = ctx.message.author
                authorname = ctx.message.author.display_name
                ID = ctx.message.author.id
                server = ctx.message.guild.name
                channel = ctx.message.channel
                await channel.send("Enter you're Suggestion/Feedback here!:")
                suggestion = await self.bot.wait_for('message', check=check)

                embed = discord.Embed(title = "Ready to Submit?", description = "Before you submit!\nPlease make sure that the following response is **not** a BUG REPORT!", color = 0x4c594b)
                embed.add_field(name = "Submit Feedback", value = "✅ - SUBMIT\n❌ - CANCEL")
                message = await ctx.send(embed = embed)
                reactions = ['✅', '❌']
                for emoji in reactions:
                    await message.add_reaction(emoji)

                def check2(reaction, user):
                    return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=100.0, check=check2)
                    if str(reaction.emoji) == "❌":
                        await channel.send("Ended Task")
                        await message.delete()
                        return
                    else:
                        await message.delete()
                        query(authorname, ID, server, channel.name, suggestion.content, "Suggestion")
                        embed = discord.Embed(title = "I have sent in your suggestion!", description = f"You can view your suggestion's progress here! [Trello URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)", color = 0x4c594b)
                        await ctx.send(embed = embed)
                        guild = self.bot.get_guild(448488274562908170)
                        channel = guild.get_channel(797193549992165456)
                        responseguild = ctx.message.guild.name
                        embed = discord.Embed(title = "User Suggestion!", description = f"Author: {author.mention}\nChannel: {channel.name}\nServer: {responseguild}", color=0xfc8003)
                        embed.add_field(name = "Feedback", value = "[Trello URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)")
                        await channel.send(embed = embed)

                except asyncio.TimeoutError:
                    await channel.send("Looks like you didn't react in time, please try again later!")
        except asyncio.TimeoutError:
            await ctx.send("Looks like you didn't react in time, please try again later!")

    @commands.command()
    async def bug(self, ctx):
        await ctx.send("This command has moved to `>report` *No arguments*")

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))

