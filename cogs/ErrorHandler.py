from discord.ext import commands
from discord import File
from typing import List
import traceback
from pathlib import Path

class CustomError(Exception):
    def __init__(self, chars: int):
      self.chars = chars
      self.pre = "This is a custom error:"
      self.message = f"{self.pre} {'b'*self.chars}"
      super().__init__(self.message)

class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def error(self, ctx, chars: int=100):
      raise CustomError(int(chars))

    #Checks if the command has a local error handler. 
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: Exception):
      tb = error.__traceback__
      etype = type(error)
      exception = traceback.format_exception(etype, error, tb, chain=True)
      exception_msg = ""
      for line in exception:
        exception_msg += line

      if hasattr(ctx.command, 'on_error'):
        return
      elif isinstance(error, commands.CommandNotFound):
        await ctx.send("No such command! Please contact the only **Lord Turtle** if you are having trouble! \nPlease also refer to the help command! `!help`")
        print("ingored error: " + str(ctx.command))
      else:
        if len(exception_msg)+160 > 2000:
          error_file = Path("error.txt")
          error_file.touch()
          with error_file.open("r+") as f:
            f.write(exception_msg)
            await ctx.send(f"**Hey you!** *Mr. Turtle here has found an error, and boy is it a big one!* You might want to doublecheck what you sent and/or check out the help command!\nI've attached the file below:", file=File(f, "error"))
            error_file.unlink()
        else:
          await ctx.send(f"**Hey you!** *Mr. Turtle here has found an error!*\nYou might want to doublecheck what you sent and/or check out the help command!\n**Error:** ```\n{exception_msg}\n```")
        print(error)

def setup(bot):
  bot.add_cog(CommandErrorHandler(bot))
