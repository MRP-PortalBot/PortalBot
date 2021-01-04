from discord.ext import commands
import discord
from typing import List
import traceback
from pathlib import Path
import core.common


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
            if len(exception_msg)+160 > 2000:
                error_file = Path("error.txt")
                error_file.touch()
                with error_file.open("w") as f:
                    f.write(exception_msg)
                with error_file.open("r") as f:
                    if dev_role not in ctx.author.roles:
                        await ctx.send(f"**Hey you!** *Mr. Turtle here has found an error, and boy is it a big one! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!\nThe traceback file is attached below:", file=discord.File(f, "error.txt"))
                    else:
                        await ctx.send(f"**Hey guys look!** *A developer broke something big!* They should probably get to fixing that.\nThe traceback might be helpful though, good thing it's attached:", file=discord.File(f, "error.txt"))
                    error_file.unlink()
            else:
                if dev_role not in ctx.author.roles:
                    await ctx.send(f"**Hey you!** *Mr. Turtle here has found an error! I'll let the {dev_role.mention}'s know!*\nYou might also want to doublecheck what you sent and/or check out the help command!\n**Error:** ```\n{exception_msg}\n```")
                else:
                    await ctx.send(f"**Hey guys look!** *A developer broke something!* They should probably get to fixing that.\nThe traceback could be useful: ```\n{exception_msg}\n```")
            print(error)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
