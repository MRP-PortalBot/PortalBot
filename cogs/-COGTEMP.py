import discord
import logging
from discord.ext import commands
import json 
import datetime
from datetime import timedelta, datetime

class DailyCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot


def setup(bot):
  bot.add_cog(DailyCMD(bot))

#Old Logging Method, don't use this as logging is automatic
'''
logfile = open("commandlog.txt", "a")
logfile.write(author + " used C \n")
logfile.close()
'''