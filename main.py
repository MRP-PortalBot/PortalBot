#Importing Modules
import discord
import logging
from discord.ext import commands
from datetime import datetime
import asyncio
from pathlib import Path
from discord_slash.utils import manage_commands
import os
from core.common import prompt_config, load_config
import core.keep_alive as keep_alive
import core.bcolors as bcolors
from discord_slash import SlashCommand
from discord_slash import SlashContext
import subprocess
import time
import sys
import aiohttp
import xbox

xbox.client.authenticate(login=os.getenv("XBOXU"), password=os.getenv("XBOXP"))

'''
- Incase REPL has problems finding packages: (Manual PIP Install)
pip install discord-py-slash-command
pip install --upgrade sentry-sdk
pip install discord-sentry-reporting
'''

#Filling botconfig incase the file is missing
prompt_config("Enter bot prefix here: ", "prefix")
prompt_config(
    "Enter channel (ID) to display blacklist responses: ", "blacklistChannel")
prompt_config("Enter channel (ID) to display question suggestions: ",
              "questionSuggestChannel")
prompt_config("Enter bot-spam channel (ID)", "botspamChannel")
prompt_config("Enter channel (ID) to display realm channel applications: ",
              "realmChannelResponse")
prompt_config("Enter bot type (Stable/Beta)", "BotType")
prompt_config("Other bot's ID", "OtherBotID")
prompt_config("Bot's ID","BotID")
prompt_config("Slash Commands Server ID","ServerID")
config, _ = load_config()

#Applying towards intents
intents = discord.Intents.default()  
intents.reactions = True
intents.members = True
intents.presences = True

#Defining client and SlashCommands
client = commands.Bot(command_prefix=config['prefix'], intents=intents)
client.slash = SlashCommand(client, auto_register=True)  #TODO: Fix Slash Commands
client.remove_command("help")

#Sentry Panel Stuff - 
from discord_sentry_reporting import use_sentry

use_sentry(
    client,  # it is typically named client or bot
    dsn="https://75b468c0a2e34f8ea4b724ca2a5e68a1@o500070.ingest.sentry.io/5579376",
    traces_sample_rate=1.0    
)

#Logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_extensions():  # Gets extension list dynamically
    extensions = []
    for file in Path("cogs").glob("**/*.py"):
        if "!" in file.name or "__" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace(".py", ""))
    return extensions

def force_restart():  #Forces REPL to apply changes to everything
    subprocess.run("python main.py", shell=True, text=True, capture_output=True, check=True)
    sys.exit(0)

@client.event
async def on_ready():
    print(discord.__version__)
    print(f"{bcolors.OKGREEN}Successfully connected to Discord!{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}BOT INFORMATION: {bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>{bcolors.ENDC}")
    print(f"{bcolors.OKGREEN}BOT TYPE: {bcolors.ENDC}" + config['BotType'])
    print(f"{bcolors.WARNING}ID: {client.user.id}{bcolors.ENDC}")
    print(f"{bcolors.WARNING}URL: https://discord.com/oauth2/authorize?client_id={client.user.id}&scope=bot&permissions=8{bcolors.ENDC}")
    now = datetime.now().strftime("%H:%M:%S")
    print("Current Time =", now)
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=f"over the Portal! | {config['prefix']}help"))
    channel = client.get_channel(792485617954586634)
    embed = discord.Embed(title = f"{client.user.name} is back up!", description = "Time: " + now, color = 0x3df5a2)
    await channel.send(embed=embed)

keep_alive.keep_alive()  # webserver setup, used w/ REPL

if __name__ == '__main__':
    for ext in get_extensions():
        client.load_extension(ext)




@client.group(aliases=['cog'])
@commands.has_role('Bot Manager')
async def cogs(ctx):
    pass


@cogs.command()
@commands.has_role('Bot Manager')
async def unload(ctx, ext):
    if "cogs." not in ext:
        ext = f"cogs.{ext}"
    if ext in get_extensions():
        client.unload_extension(ext)
        embed = discord.Embed(
            title="Cogs - Unload", description=f"Unloaded cog: {ext}", color=0xd6b4e8)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Cogs Reloaded", description=f"Cog '{ext}' not found", color=0xd6b4e8)
        await ctx.send(embed=embed)


@cogs.command()
@commands.has_role('Bot Manager')
async def load(ctx, ext):
    if "cogs." not in ext:
        ext = f"cogs.{ext}"
    if ext in get_extensions():
        client.load_extension(ext)
        embed = discord.Embed(title="Cogs - Load",
                              description=f"Loaded cog: {ext}", color=0xd6b4e8)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Cogs - Load", description=f"Cog '{ext}' not found.", color=0xd6b4e8)
        await ctx.send(embed=embed)


@cogs.command(aliases=['restart'])
@commands.has_role('Bot Manager')
async def reload(ctx, ext):
    if ext == "all":
        embed = discord.Embed(
            title="Cogs - Reload", description="Reloaded all cogs", color=0xd6b4e8)
        for extension in get_extensions():
            client.reload_extension(extension)
        await ctx.send(embed=embed)
        return

    if "cogs." not in ext:
        ext = f"cogs.{ext}"

    if ext in get_extensions():
        client.reload_extension(ext)
        embed = discord.Embed(
            title="Cogs - Reload", description=f"Reloaded cog: {ext}", color=0xd6b4e8)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Cogs - Reload", description=f"Cog '{ext}' not found.", color=0xd6b4e8)
        await ctx.send(embed=embed)


@cogs.command()
@commands.has_role('Bot Manager')
async def view(ctx):
    msg = " ".join(get_extensions())
    embed = discord.Embed(title="Cogs - View", description=msg, color=0xd6b4e8)
    await ctx.send(embed=embed)


@client.group(invoke_without_command=True)
@commands.has_role('Bot Manager')
async def slashm(ctx):
    embed = discord.Embed(title = "Slash Management Commands", description = "Slash Commands", color = 0x1ebdf7)
    embed.add_field(name = "Commands:", value = "**get** - Get's current slash commands in the API \n**remove** - Remove's slash commands from the API. (Needs commandid and guildid)")
    await ctx.send(embed = embed)

@slashm.command()
@commands.has_role('Bot Manager')
async def get(ctx, guildid = None):
    if guildid == None:
        guildid == ctx.message.guild.id
        await ctx.send("```\n" + str(await(manage_commands.get_all_commands(client.user.id, os.getenv("TOKEN"), guildid))) + "\n```")
    else:
        await ctx.send("```\n" + str(await(manage_commands.get_all_commands(client.user.id, os.getenv("TOKEN"), guildid))) + "\n```")


@slashm.command()
@commands.has_role('Bot Manager')
async def remove(ctx, commandid, guildid = None):
    try:
        await ctx.send("Response: " + str(await(manage_commands.remove_slash_command(config['BotID'], os.getenv("TOKEN"), guildid, commandid))))
    except:
        await ctx.send("Something went wrong!")

@client.command()
@commands.has_role('Bot Manager')
async def gitpull(ctx):
    typebot = config['BotType']
    output = ''
    if typebot == "BETA":
        p = subprocess.run("git fetch --all", shell=True, text=True, capture_output=True, check=True)
        output += p.stdout
        p = subprocess.run("git reset --hard origin/TestingInstance", shell=True, text=True, capture_output=True, check=True)
        output += p.stdout
        embed = discord.Embed(title = "GitHub Local Reset", description = "Local Files changed to match PortalBot/TestingInstance", color = 0x3af250)
        embed.add_field(name = "Shell Output", value = f"```shell\n$ {output}\n```")
        embed.set_footer(text = "Attempting to restart the bot...")
        msg = await ctx.send(embed=embed)
        force_restart()

    elif typebot == "STABLE":
        p = subprocess.run("git fetch --all", shell=True, text=True, capture_output=True, check=True)
        output += p.stdout
        p = subprocess.run("git reset --hard origin/master", shell=True, text=True, capture_output=True, check=True)
        output += p.stdout
        embed = discord.Embed(title = "GitHub Local Reset", description = "Local Files changed to match PortalBot/Main", color = 0x3af250)
        embed.add_field(name = "Shell Output", value = f"```shell\n$ {output}\n```")
        embed.set_footer(text = "Attempting to restart the bot...")
        msg = await ctx.send(embed=embed)
        force_restart()

@client.command()
@commands.has_role('Bot Manager')
async def shell(ctx, * , command):
    timestamp = datetime.now()
    author = ctx.message.author
    guild = ctx.message.guild
    output = ""
    p = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
    output += p.stdout
    embed = discord.Embed(title = "Shell Process", description = f"Shell Process started by {author.mention}", color = 0x4c594b)
    num_of_fields = len(output)//1014 + 1
    for i in range(num_of_fields):
        embed.add_field(name="Output" if i == 0 else "\u200b",  value="```bash\n" + output[i*1014:i+1*1014] + "\n```")
    embed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
    await ctx.send(embed = embed)
    
@client.command()
@commands.has_role('Bot Manager')
async def sentry(ctx):
    embed = discord.Embed(title = 'Sentry Traceback Logging', description = f"TYPE: PortalBot -{config['BotType']}", color = 0x4c594b)
    embed.set_thumbnail(url = "http://myovchev.github.io/sentry-slack/images/logo32.png")
    embed.add_field(name = "Sentry Project", value = "**BETA:** https://sentry.io/organizations/space-turtle0/issues/?project=5579376 \n**STABLE:** https://sentry.io/organizations/space-turtle0/issues/?project=5579425")
    await ctx.send(embed = embed)

client.run(os.getenv("TOKEN"))
