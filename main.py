import discord
import logging
from discord.ext import commands
from datetime import datetime
import asyncio
from pathlib import Path

from core.common import prompt_config, load_config
import core.keep_alive as keep_alive
import core.bcolors as bcolors

prompt_config("Enter bot token here: ", "token")
prompt_config("Enter bot prefix here: ", "prefix")
prompt_config(
    "Enter channel (ID) to display blacklist responses: ", "blacklistChannel")
prompt_config("Enter channel (ID) to display question suggestions: ",
              "questionSuggestChannel")
prompt_config("Enter bot-spam channel (ID)", "botspamChannel")
prompt_config("Enter channel (ID) to display realm channel applications: ",
              "realmChannelResponse")
prompt_config("Enter bot type (Stable/Beta)", "BotType")
config, _ = load_config()

intents = discord.Intents.default()  # we use intents in BlacklistCMD
intents.reactions = True
intents.members = True
intents.presences = True

client = commands.Bot(command_prefix=config['prefix'], intents=intents)
client.remove_command("help")

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


@client.event
async def on_ready():
    print(f"{bcolors.WARNING}Attempting to connect to Discord API...{bcolors.ENDC}")
    await asyncio.sleep(1)
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

client.run(config['token'])
