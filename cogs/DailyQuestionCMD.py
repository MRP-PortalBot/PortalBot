import discord
from discord.ext import commands
from datetime import datetime
import random
import typing
#f = open("DailyQuestions.txt", "r")
#fa = open("DailyQuestions.txt", "a")

 
def LineCount():
  file = open("DailyQuestions.txt", "r")
  line_count = 0
  for line in file:
    if line != "\n":
      line_count += 1
  file.close()
  print(line_count)




class DailyCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command()
  async def dailyq(self, ctx):
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used DAILYQ \n")
    logfile.close()
    file = open("DailyQuestions.txt", "r")
    line_count = 0
    for line in file:
      if line != "\n":
        line_count += 1
    print(line_count)
    file.close()
    intrandom = random.randint(0, int(line_count))
    with open('DailyQuestions.txt') as file:
      for i, line in enumerate(file):
        if i == intrandom:
          if line != "\n":
            Dailyq = discord.Embed(title = "❓ QUESTION OF THE DAY ❓", description = line, color = 0x88f216)
            await ctx.send(embed = Dailyq)
  
  @commands.command()
  async def dailyqf(self, ctx, amount):
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used DAILYQF \n")
    logfile.close()
    with open('DailyQuestions.txt') as file:
      for i, line in enumerate(file):
        if i == int(amount):
          if line != "\n":
            Dailyq = discord.Embed(title = "❓ QUESTION OF THE DAY ❓", description = line, color = 0x88f216)
            await ctx.send(embed = Dailyq)
  
  @commands.command()
  async def reply(self, ctx, message):
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used REPLY \n")
    logfile.close()
    await message.reply('Test', mention_author=True)

  



def setup(bot):
  bot.add_cog(DailyCMD(bot))