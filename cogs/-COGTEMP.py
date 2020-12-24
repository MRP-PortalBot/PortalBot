from discord.ext import commands
from datetime import datetime

class DailyCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot


def setup(bot):
  bot.add_cog(DailyCMD(bot))

'''
logfile = open("commandlog.txt", "a")
logfile.write(author + " used C \n")
logfile.close()
'''