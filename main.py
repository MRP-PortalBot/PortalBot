import discord
import logging
from discord.ext import commands
from datetime import datetime
import asyncio

from core.config import prompt_config, load_config
import core.keep_alive as keep_alive
import core.bcolors as bcolors

prompt_config("Enter bot token here: ", "token")
prompt_config("Enter bot prefix here: ", "prefix")
config, _ = load_config()

intents = discord.Intents.default()  # we use intents in BlacklistCMD
intents.reactions = True

client = commands.Bot(command_prefix=config['prefix'], intents = intents)
client.remove_command("help")

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@client.event
async def on_ready():
  print(f"{bcolors.WARNING}Attempting to connect to Discord API...{bcolors.ENDC}")
  await asyncio.sleep(2)
  print(f"{bcolors.OKGREEN}Successfully connected to Discord!{bcolors.ENDC}")
  print(f"{bcolors.OKCYAN}BOT INFORMATION: {bcolors.ENDC}")
  print(f"{bcolors.OKCYAN}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>{bcolors.ENDC}")
  print(f"{bcolors.WARNING}ID: {client.user.id} \n{bcolors.ENDC}")
  print(f"{bcolors.WARNING}URL: https://discord.com/oauth2/authorize?client_id={client.user.id}&scope=bot&permissions=8{bcolors.ENDC}")

  now = datetime.now().strftime("%H:%M:%S")
  print("Current Time =", now)

  await client.change_presence(status=discord.Status.idle,activity=discord.Activity(type=discord.ActivityType.watching, name="over the Portal! | >help"))

keep_alive.keep_alive() # webserver setup, used w/ REPL

extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.MusicCMD', 'cogs.OnCommandlog', 'cogs.GamertagCMD']
if __name__ == '__main__':
  for ext in extensions:
    client.load_extension(ext)

@client.group()
@commands.has_role('Bot Manager')
async def cogs(ctx):
  pass

@cogs.command()
@commands.has_role('Bot Manager')
async def unload(ctx, ext):
  if ext in extensions:
    client.unload_extension(ext)
    ctx.send(f"Unloaded cog: {ext}")
  else:
    ctx.send("Cog '{ext}' not found.")

@cogs.command()
@commands.has_role('Bot Manager')
async def load(ctx, ext):
  if ext in extensions:
    client.load_extension(ext)
    ctx.send(f"Loaded cog: {ext}")
  else:
    ctx.send("Cog '{ext}' not found.")

@cogs.command()
@commands.has_role('Bot Manager')
async def reload(ctx, ext):
  if ext == "all":
    for extension in extensions:
      client.reload_extension(extension)
    ctx.send("Reloaded all cogs!")
  elif ext in extensions:
      client.reload_extension(ext)
      ctx.send("Reloaded cog: {ext}")
  else:
    ctx.send("Cog '{ext}' not found.")

@cogs.command()
@commands.has_role('Bot Manager')
async def view(ctx):
  msg = " ".join(extensions)
  ctx.send(msg)

client.run(config['token'])
