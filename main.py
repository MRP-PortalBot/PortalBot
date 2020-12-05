import discord
import keep_alive
import logging
from discord.ext import commands
from TOKENPASS import TOKENPASS
import time



#Line

client = commands.Bot(command_prefix=">")
client.remove_command("help")

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@client.event
async def on_ready():
  print("Logged in!")
  await client.change_presence(status=discord.Status.idle,activity=discord.Activity(type=discord.ActivityType.watching, name="over the Portal! | >help"))

keep_alive.keep_alive()


extensions = ['cogs.RealmCMD', 'cogs.HelpCMD', 'cogs.BlacklistCMD', 'cogs.MiscCMD', 'cogs.OperatorCMD',  'cogs.DailyQuestionCMD', 'cogs.BetaCMD', 'cogs.ModeratorCMD'] 

if __name__ == '__main__':
  for ext in extensions:
    client.load_extension(ext)

@client.command()
async def restart(ctx):
  author = ctx.message.author
  if author.id == 409152798609899530:
    if __name__ == '__main__':
      await ctx.send("**RESTARTING!** \n*Please wait until the bot **fully** reloads everything!*")
      msg = await ctx.send("**Progress:** `0.00%`")
      cog = await ctx.send("**File:** `Preparing...`")
      client.reload_extension('cogs.RealmCMD')
      await msg.edit(content = "**Progress:** `12.50%`")
      await cog.edit(content = "**File:** `cogs.RealmCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.HelpCMD')
      await msg.edit(content = "**Progress:** `25.00%`")
      await cog.edit(content = "**File:** `cogs.HelpCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.BlacklistCMD')
      await msg.edit(content = "**Progress:** `37.50%`")
      await cog.edit(content = "**File:** `cogs.BlacklistCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.MiscCMD')
      await msg.edit(content = "**Progress:** `50.00%`")
      await cog.edit(content = "**File:** `cogs.MiscCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.OperatorCMD')
      await msg.edit(content = "**Progress:** `62.50%`")
      await cog.edit(content = "**File:** `cogs.OperatorCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.DailyQuestionCMD')
      await msg.edit(content = "**Progress:** `75.00%`")
      await cog.edit(content = "**File:** `cogs.DailyQuestionCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.BetaCMD')
      await msg.edit(content = "**Progress:** `87.50%`")
      await cog.edit(content = "**File:** `cogs.BetaCMD`")
      time.sleep(0.1)
      client.reload_extension('cogs.ModeratorCMD')
      await msg.edit(content = "**Progress:** `100.00%`")
      await cog.edit(content = "**File:** `cogs.ModeratorCMD`")
      time.sleep(0.25)
      await msg.edit(content = "**Progress:** `Verifying COGS...`")
      await cog.edit(content = "**File:** `N/A`")
      time.sleep(0.25)
      await msg.edit(content = "**Progress:** `COMPLETE`")
      await cog.edit(content = "**File:** `Loaded All Extensions!`")
      
  
client.run(TOKENPASS)
