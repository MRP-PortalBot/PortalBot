from discord.ext import commands


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #Checks if the command has a local error handler. 
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
      error = getattr(error, 'original', error)
      if hasattr(ctx.command, 'on_error'):
        return
      
      #No command that exists
      elif isinstance(error, commands.CommandNotFound):
        await ctx.send("No such command! Please contact the only **Lord Turtle** if you are having trouble! \nPlease also refer to the help command! `>help`")
        print("ingored error: " + str(ctx.command))

      #Return Error
      else:
        print(error)
        await ctx.send("**Hey you!** *Mr. Turtle here has found an error!*\nYou might want to doublecheck what you sent and/or check out the help command!\n**Error:** ```\n" + str(error) + "\n```")

def setup(bot):
  bot.add_cog(CommandErrorHandler(bot))
