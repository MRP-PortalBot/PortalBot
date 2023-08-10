import asyncio
import json
import logging
import os
import random
import traceback
from pathlib import Path

import discord
import requests
from discord.ext import commands

import core.common
from core.common import query

logger = logging.getLogger(__name__)

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


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))

