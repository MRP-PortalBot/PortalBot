import discord
import flask
import keep_alive
import logging
from discord.ext import commands
import json 
from datetime import datetime
import os
#-----------------------------------------------
'''
Tips/Board

1. Use await asyncio.sleep()




'''
#-----------------------------------------------

#We need Intents as we are checking for reactions in cogs.DailyQuestions.py
intents = discord.Intents.default()
intents.reactions = True

#Define Client and remove help command since the predefined help command sucks.
client = commands.Bot(command_prefix=">", intents = intents)
client.remove_command("help")

#Logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#Confirmation that we have logged in.
@client.event
async def on_ready():
  print("Logged in!")
  await client.change_presence(status=discord.Status.idle,activity=discord.Activity(type=discord.ActivityType.watching, name="over the Portal! | >help"))

  now = datetime.now()
  current_time = now.strftime("%H:%M:%S")
  print("Current Time =", current_time)

#Webserver setup, 
keep_alive.keep_alive()

#Loading every cog. 
extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.TaskLoops', 'cogs.MusicCMD',  'cogs.OnCommandlog', 'cogs.ErrorHandler'] 
if __name__ == '__main__':
  for ext in extensions:
    client.load_extension(ext)

#Manual Restart Command
# - Basically reloads every cog file. 
@client.command()
async def restart(ctx):
  author = ctx.message.author
  if author.id == 409152798609899530:
    if __name__ == '__main__':
      for ext in extensions:
        client.load(ext)
      await ctx.send("Done!")
      
#.env File.
client.run(os.getenv("Token"))
