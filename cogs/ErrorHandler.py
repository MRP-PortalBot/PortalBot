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

    async def github_request(self, method, url, *, params=None, data=None, headers=None):
        hdrs = {
            'Accept': 'application/vnd.github.inertia-preview+json',
            'User-Agent': 'RoboDanny DPYExclusive Cog',
            'Authorization': f'token {os.getenv("GIST")}'
        }

        req_url = yarl.URL('https://api.github.com') / url

        if headers is not None and isinstance(headers, dict):
            hdrs.update(headers)


        async with self.bot.session.request(method, req_url, params=params, json=data, headers=hdrs) as r:
            remaining = r.headers.get('X-Ratelimit-Remaining')
            js = await r.json()
            if r.status == 429 or remaining == '0':
                # wait before we release the lock
                delta = discord.utils._parse_ratelimit_header(r)
                await asyncio.sleep(delta)
                self._req_lock.release()
                return await self.github_request(method, url, params=params, data=data, headers=headers)
            elif 300 > r.status >= 200:
                return js
            else:
                raise GithubError(js['message'])


    async def create_gist(self, content, *, description=None, filename=None, public=True):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
        }

        filename = filename or 'output.txt'
        data = {
            'public': public,
            'files': {
                filename: {
                    'content': content
                }
            }
        }

        description = 'PortalBot Traceback'

        js = await self.github_request('POST', 'gists', data=data, headers=headers)
        return js['html_url']

    async def redirect_attachments(self, message):
        attachment = message.attachments[0]
        if not attachment.filename.endswith(('.txt', '.py', '.json')):
            return

        # If this file is more than 2MiB then it's definitely too big
        if attachment.size > (2 * 1024 * 1024):
            return

        try:
            contents = await attachment.read()
            contents = contents.decode('utf-8')
        except (UnicodeDecodeError, discord.HTTPException):
            return

        gist = await self.create_gist(contents, description = 'PortalBot Traceback', filename=attachment.filename)
        await message.channel.send(f'File automatically uploaded to gist: <{gist}>')

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

        if hasattr(ctx.command, 'on_error'):
            return
        elif isinstance(error, commands.CommandNotFound):
            config, _ = core.common.load_config()
            await ctx.send(f"No such command! Please contact a Bot Manager if you are having trouble! \nPlease also refer to the help command! `{config['prefix']}help`")
            print("ingored error: " + str(ctx.command))
        else:
            if len(exception_msg)+160 > 1024:
                error_file = Path("error.txt")
                error_file.touch()
                with error_file.open("w") as f:
                    f.write(exception_msg)
                with error_file.open("r") as f:
                    if dev_role not in ctx.author.roles:
                        embed = discord.Embed(title = "Traceback Detected!", description = f"**Hey you!** *Mr. Turtle here has found an error, and boy is it a big one! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!", color = 0xfc3d03)
                        embed.add_field(name = "Bug Reporting", value = "Have any extra information that could help resolve this issue? Feel free to use the **>bug** command! \nUsage: `>bug (extra valuable information here!)` \n\nExamples of helpful information! \n\n- Any arguments you provided with the command\n- What the actual problem was (What went wrong?)\n- Any other information that could help!")
                        embed.set_footer(text = f"Error: {str(error)}")
                        await ctx.send(embed = embed)
                        guild = self.bot.get_guild(448488274562908170)
                        channel = guild.get_channel(797193549992165456)
                        embed2 = discord.Embed(title = "Traceback Detected!", description = f"**Information:**\n**Server:** {ctx.message.guild.name}\n**User:** {ctx.message.author.mention}\n**Traceback:** *Download Below*", color= 0xfc3d03)
                        await channel.send(embed = embed2)
                        message = await channel.send(file=discord.File(f, "error.txt"))
                        await self.redirect_attachments(message)


                    else:
                        await ctx.send(f"**Hey guys look!** *A developer broke something big!* They should probably get to fixing that.\nThe traceback might be helpful though, good thing it's attached:", file=discord.File(f, "error.txt"))
                    error_file.unlink()
            else:
                if dev_role not in ctx.author.roles:
                    embed = discord.Embed(title = "Traceback Detected!", description = f"**Hey you!** *Mr. Turtle here has found an error! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!", color = 0xfc3d03)
                    embed.add_field(name = "Bug Reporting", value = "Have any extra information that could help resolve this issue? Feel free to use the **>bug** command! \nUsage: `>bug (extra valuable information here!)` \n\nExamples of helpful information! \n\n- Any arguments you provided with the command\n- What the actual problem was (What went wrong?)\n- Any other information that could help!")
                    embed.set_footer(text = f"Error: {str(error)}")
                    await ctx.send(embed = embed)
                    guild = self.bot.get_guild(448488274562908170)
                    channel = guild.get_channel(797193549992165456)
                    embed2 = discord.Embed(title = "Traceback Detected!", description = f"**Information:**\n**Server:** {ctx.message.guild.name}\n**User:** {ctx.message.author.mention}", color= 0xfc3d03)
                    embed2.add_field(name = "Traceback", value = f"```\n{exception_msg}\n```")
                    await channel.send(embed = embed2)
                else:
                    await ctx.send(f"**Hey guys look!** *A developer broke something!* They should probably get to fixing that.\nThe traceback could be useful: ```\n{exception_msg}\n```")
            print(error)
        raise error

    @commands.command()
    async def bug(self, ctx, *, bug : str):
        author = ctx.message.author
        channel = ctx.message.channel
        guild = self.bot.get_guild(448488274562908170)
        channel = guild.get_channel(797193549992165456)
        embed = discord.Embed(title = "User Bug Report!", description = f"Author: {author.mention}\nChannel: {channel.name}", color=0xfc8003)
        embed.add_field(name = "Feedback", value = bug)
        channel.send(embed = embed)



def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
