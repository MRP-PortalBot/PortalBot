import discord
import keep_alive
import logging
from discord.ext import commands
from datetime import datetime
import asyncio

from pathlib import Path
import json
#-----------------------------------------------
'''
Tips/Board

1. Use await asyncio.sleep()




'''
#-----------------------------------------------
''''
typelog = input("Start with OnBoard Discord Error Handler?: (y/n) ")
if typelog == "y":
  extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD', 'cogs.ErrorHandler'] 
elif typelog == "n":
  extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD'] 
else:
  print("Didn't understand that, proceeding with Discord Error Handler...")
  extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD', 'cogs.ErrorHandler']
'''
#We need Intents as we are checking for reactions in cogs.DailyQuestions.py
intents = discord.Intents.default()
intents.reactions = True

#Ensures botconfig.json exists
config_file = Path("botconfig.json")
config_file.touch(exist_ok=True)
if config_file.read_text() == "":
  config_file.write_text("{}")
with config_file.open("r") as f:
  config = json.load(f)
if "token" not in config:
  config['token'] = input("Enter bot token here: ")
  with config_file.open("w+") as f:
    json.dump(config, f, indent=4)
if "prefix" not in config:
  config['prefix'] = input("Enter bot prefix here: ")
  with config_file.open("w+") as f:
    json.dump(config, f, indent=4)

#Define Client and remove help command since the predefined help command sucks.
client = commands.Bot(command_prefix=config['prefix'], intents = intents)
client.remove_command("help")

#Logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#Colorful Text!
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#Confirmation that we have logged in.
@client.event
async def on_ready():
  print(f"{bcolors.WARNING}Attempting to connect to Discord API...{bcolors.ENDC}")
  await asyncio.sleep(2)
  print(f"{bcolors.OKGREEN}Successfully connected to Discord!{bcolors.ENDC}")
  print(f"{bcolors.OKCYAN}BOT INFORMATION: {bcolors.ENDC}")
  print(f"{bcolors.OKCYAN}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>{bcolors.ENDC}")
  print("PORTALBOT Stable")
  print(f"{bcolors.WARNING}ID: 777361919211732993 \n{bcolors.ENDC}")
  print(f"{bcolors.WARNING}URL: https://discord.com/oauth2/authorize?client_id=777361919211732993&scope=bot&permissions=8{bcolors.ENDC}")


  #Status Stuff
  await client.change_presence(status=discord.Status.idle,activity=discord.Activity(type=discord.ActivityType.watching, name="over the Portal! | >help"))

  #Time
  now = datetime.now()
  current_time = now.strftime("%H:%M:%S")
  print("Current Time =", current_time)

#Webserver setup, 
keep_alive.keep_alive()

#Loading every cog. 
extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD']
if __name__ == '__main__':
  for ext in extensions:
    client.load_extension(ext)

#Manual Restart Command
# - Basically reloads every cog file. 
@client.command()
async def restart(ctx, typerestart = None):
  author = ctx.message.author
  channel = ctx.message.channel
  if author.id == 409152798609899530 or 306070011028439041:
    if typerestart == "1":
      extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD', 'cogs.ErrorHandler'] 
      if __name__ == '__main__':
        try:
          client.load_extension('cogs.ErrorHandler')
        finally:
          for ext in extensions:
            client.reload_extension(ext)
          await ctx.send("Done! \n*-Loaded Local Error Handler.*")
    elif typerestart == "2":
      extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD'] 
      if __name__ == '__main__':
        for ext in extensions:
          client.reload_extension(ext)
        try:
          client.unload_extension('cogs.ErrorHandler')
        finally:
          await ctx.send("Done! \n*-Forwarding Errors to the console!*")

  
    else:
      def check(m):
        return m.content is not None and m.channel == channel and m.author is not client.user
      await ctx.send("**You have not provided a restart value, please pick one!** \n**1:** Load Discord Error Handler\n**2:** Unload Discord Error Handler and forward errors to the console. *(Provides more detailed errors)*")
      ans = await client.wait_for('message', check=check)
      if ans.content == "1":
        extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD'] 
        try:
          client.load_extension('cogs.ErrorHandler')
        finally:
          if __name__ == '__main__':
            for ext in extensions:
              client.reload_extension(ext)
            await ctx.send("Done! \n*-Loaded Local Error Handler.*")
      elif ans.content == "2":
        extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD'] 
        try:
          client.unload_extension('cogs.ErrorHandler')
        finally: 
          if __name__ == '__main__':
            for ext in extensions:
              client.reload_extension(ext)
            await ctx.send("Done! \n*-Forwarding Errors to the console!*")
      else:
        await ctx.send("Sorry I didn't get that, please try again later.")

      
#.env File.
client.run(config['token'])

