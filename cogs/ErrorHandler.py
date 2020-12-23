from discord.ext import commands
from typing import List
import traceback

class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def error(self, ctx):
      raise ZeroDivisionError

    #Checks if the command has a local error handler. 
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: Exception):
      exc_traceback = error.__traceback__
      exception: List[str] = traceback.format_tb(exc_traceback).reverse()
      exception_msg: str = ""
      for line in exception:
          exception_msg += f"{line.strip()}\n"

      if hasattr(ctx.command, 'on_error'):
        return
      
      #No command that exists
      elif isinstance(error, commands.CommandNotFound):
        await ctx.send("No such command! Please contact the only **Lord Turtle** if you are having trouble! \nPlease also refer to the help command! `>help`")
        print("ingored error: " + str(ctx.command))

      #Return Error
      else:
        print(error)
        await ctx.send(f"**Hey you!** *Mr. Turtle here has found an error!*\nYou might want to doublecheck what you sent and/or check out the help command!\n**Error:** ```\n{exception_msg}\n```")

def setup(bot):
  bot.add_cog(CommandErrorHandler(bot))
