from __future__ import annotations

import json
import os
import subprocess
import traceback
import asyncio
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING

import discord
import requests
import sentry_sdk
from discord import app_commands
from discord.ext import commands

from core import database
from core.common import ConsoleColors, Colors, Others, QuestionSuggestionManager, get_bot_data_id, load_config
from core.logging_module import get_log

# Load configuration
config, _ = load_config()

if TYPE_CHECKING:
    from main import PortalBot

# Logger setup
_log = get_log(__name__)


async def before_invoke_(ctx: commands.Context):
    pass
    """sentry_sdk.set_user(None)
    sentry_sdk.set_user({"id": ctx.author.id, "username": ctx.author.name})
    sentry_sdk.set_tag("username", f"{ctx.author.name}#{ctx.author.discriminator}")
    if ctx.command is None:
        sentry_sdk.set_context(
            "user",
            {
                "name": ctx.author.name,
                "id": ctx.author.id,
                "command": ctx.command,
                "guild": ctx.guild.name,
                "guild_id": ctx.guild.id,
                "channel": ctx.channel.name,
                "channel_id": ctx.channel.id,
            },
        )
    else:
        sentry_sdk.set_context(
            "user",
            {
                "name": ctx.author.name,
                "id": ctx.author.id,
                "command": "Unknown",
                "guild": ctx.guild.name,
                "guild_id": ctx.guild.id,
                "channel": ctx.channel.name,
                "channel_id": ctx.channel.id,
            },
        )"""


async def on_ready_(bot: 'PortalBot'):
    """
    Called when the bot is ready and fully connected.
    Initializes views, fetches version info, and logs bot status.
    """
    now = datetime.now()
    row_id = get_bot_data_id()

    # Fetch the bot data from the database
    query: database.BotData = database.BotData.get_or_none(database.BotData.id == row_id)

    # Ensure persistent views are initialized
    if query and not query.persistent_views:
        bot.add_view(QuestionSuggestionManager())
        query.persistent_views = True
        query.save()

    # Determine the database source (external or local)
    database_source = "External" if not os.getenv("USEREAL") else "localhost"
    db_message_color = ConsoleColors.OKGREEN if database_source == "External" else ConsoleColors.FAIL
    db_warning_message = (
        f"{ConsoleColors.WARNING}WARNING: Not recommended to use SQLite.{ConsoleColors.ENDC}"
        if database_source == "localhost" else ""
    )

    database_message = (
        f"{db_message_color}Selected Database: {database_source} {ConsoleColors.ENDC}\n{db_warning_message}"
    )

    # Fetch Git version (asynchronously)
    try:
        process = await asyncio.create_subprocess_shell(
            "git describe --always",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        git_version = stdout.decode().strip() if stdout else "ERROR"
    except Exception as e:
        git_version = f"ERROR: {str(e)}"

    # Log bot details
    print(
        f"""
          _____           _        _ ____        _   
         |  __ \         | |      | |  _ \      | |  
         | |__) |__  _ __| |_ __ _| | |_) | ___ | |_ 
         |  ___/ _ \| '__| __/ _` | |  _ < / _ \| __|
         | |  | (_) | |  | || (_| | | |_) | (_) | |_ 
         |_|   \___/|_|   \__\__,_|_|____/ \___/ \__|

        Bot Account: {bot.user.name} | {bot.user.id}
        {ConsoleColors.OKCYAN}Discord API Version: {discord.__version__}{ConsoleColors.ENDC}
        {ConsoleColors.WARNING}PortalBot Version: {git_version}{ConsoleColors.ENDC}
        {database_message}

        {ConsoleColors.OKCYAN}Current Time: {now}{ConsoleColors.ENDC}
        {ConsoleColors.OKGREEN}Initialization complete: Cogs, libraries, and views have successfully been loaded.{ConsoleColors.ENDC}
        ==================================================
        {ConsoleColors.WARNING}Statistics{ConsoleColors.ENDC}
        Guilds: {len(bot.guilds)}
        Members: {len(bot.users)}
        """
    )

    # Send a message to the GitHub log channel
    guild = bot.get_guild(config['PBtest'])  # Replace 'PBtest' with actual guild ID or logic
    github_channel = discord.utils.get(guild.channels, name="github-log")

    if github_channel:
        await github_channel.send("Github Synced, and bot is restarted")
    else:
        _log.error("'github-log' channel not found!")


async def on_command_error_(bot, ctx: commands.Context, error: Exception):
    # Gather traceback details
    tb = error.__traceback__
    etype = type(error)
    exception_msg = ''.join(traceback.format_exception(etype, error, tb, chain=True))

    # Handle specific error types
    error = getattr(error, "original", error)
    
    if ctx.command and ctx.command.name == "rule":
        return "No Rule..."

    if isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
        return

    if hasattr(ctx.command, "on_error"):
        return

    # Handle 'CommandNotFound'
    if isinstance(error, (commands.CommandNotFound, commands.errors.CommandNotFound)):
        cmd = ctx.invoked_with
        cmds = [cmd.name for cmd in bot.commands]
        matches = get_close_matches(cmd, cmds)
        if matches:
            return await ctx.send(f'Command "{cmd}" not found. Did you mean "{matches[0]}"?')
        return await ctx.message.add_reaction("❌")

    # Handle missing or extra arguments
    if isinstance(error, (commands.MissingRequiredArgument, commands.TooManyArguments)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        em = discord.Embed(
            title="Missing or Extra Arguments",
            description=f"You missed or provided too many arguments.\n\nUsage:\n`{signature}`",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command if needed.")
        return await ctx.send(embed=em)

    # Handle permission-related issues
    if isinstance(error, (
        commands.MissingAnyRole,
        commands.MissingRole,
        commands.MissingPermissions,
        commands.errors.MissingAnyRole,
        commands.errors.MissingRole,
        commands.errors.MissingPermissions
    )):
        em = discord.Embed(
            title="Insufficient Permissions",
            description="You don't have the required role or permissions for this command. Please contact an administrator if this is a mistake.",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command for more details.")
        return await ctx.send(embed=em)

    # Handle bad argument errors
    if isinstance(error, (commands.BadArgument, commands.BadLiteralArgument, commands.BadUnionArgument)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        em = discord.Embed(
            title="Bad Argument",
            description=f"Invalid argument provided.\n\nUsage:\n`{signature}`",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command for more information.")
        return await ctx.send(embed=em)

    # Handle command cooldowns
    if isinstance(error, (commands.CommandOnCooldown, commands.errors.CommandOnCooldown)):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)
        msg = f"This command is on cooldown. Try again in {int(h)} hours, {int(m)} minutes, and {int(s)} seconds."
        em = discord.Embed(
            title="Command On Cooldown",
            description=msg,
            color=discord.Color.red(),
        )
        return await ctx.send(embed=em)

    # Default error handling with error logging via Gist
    error_file = Path("error.txt")
    error_file.touch()
    error_file.write_text(exception_msg)

    with error_file.open("r") as f:
        data = f.read()

    try:
        GITHUB_API = "https://api.github.com"
        API_TOKEN = os.getenv("github_gist")
        url = f"{GITHUB_API}/gists"
        headers = {"Authorization": f"token {API_TOKEN}"}
        payload = {
            "description": "PortalBot Traceback",
            "public": True,
            "files": {"error": {"content": data}},
        }
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        res.raise_for_status()
        gist_id = res.json()["id"]
        gist_url = f"https://gist.github.com/{gist_id}"
    except Exception as e:
        _log.error(f"Error creating Gist: {str(e)}")
        gist_url = None

    permitlist = [
        admin.discordID for admin in database.Administrators.select().where(database.Administrators.TierLevel >= 3)
    ]

    # Handle error message visibility based on user permissions
    if ctx.author.id not in permitlist:
        em = discord.Embed(
            title="An Error Occurred",
            description="An unexpected error occurred. The developers have been notified.",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text=f"Error: {str(error)}")
        await ctx.send(embed=em)
    else:
        em = discord.Embed(
            title="Traceback Detected",
            description="An error occurred in PortalBot. Traceback details have been attached below.",
            color=Colors.red,
        )
        if gist_url:
            em.add_field(name="Gist URL", value=gist_url)
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text=f"Error: {str(error)}")
        await ctx.send(embed=em)

    error_file.unlink()

    raise error


async def on_app_command_error_(
    bot: 'PortalBot',
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    # Capture traceback and format the exception
    tb = error.__traceback__
    etype = type(error)
    exception_msg = ''.join(traceback.format_exception(etype, error, tb, chain=True))

    # Command on Cooldown
    if isinstance(error, app_commands.CommandOnCooldown):
        h, m = divmod(int(error.retry_after // 60), 60)
        s = round(error.retry_after % 60)
        cooldown_msg = f"This command cannot be used again for {h} hours, {m} minutes, and {s} seconds."
        embed = discord.Embed(
            title="Command On Cooldown", description=cooldown_msg, color=discord.Color.red()
        )
        await _send_response(interaction, embed)
        return

    # Command Check Failure
    if isinstance(error, app_commands.CheckFailure):
        failure_msg = "You cannot run this command!"
        await _send_response(interaction, failure_msg, ephemeral=True)
        return

    # Command Not Found
    if isinstance(error, app_commands.CommandNotFound):
        await interaction.response.send_message(f"Command /{interaction.command.name} not found.")
        return

    # Unhandled Errors: Create a Gist and notify developers
    gist_url = await _create_gist(exception_msg)
    await _notify_error(interaction, error, gist_url)

    raise error


# Helper function to send responses, handling both response and followup cases
async def _send_response(interaction: discord.Interaction, content: Union[discord.Embed, str], ephemeral=False):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content=content, ephemeral=ephemeral)
    except Exception as e:
        _log.error(f"Error sending response: {e}")

# Helper function to create a Gist and return the URL
async def _create_gist(exception_msg: str) -> str:
    try:
        GITHUB_API = "https://api.github.com/gists"
        API_TOKEN = os.getenv("GITHUB")
        headers = {"Authorization": f"token {API_TOKEN}"}
        payload = {
            "description": "PortalBot encountered a Traceback!",
            "public": True,
            "files": {"error.txt": {"content": exception_msg}},
        }
        res = requests.post(GITHUB_API, headers=headers, data=json.dumps(payload))
        res.raise_for_status()
        return f"https://gist.github.com/{res.json()['id']}"
    except Exception as e:
        _log.error(f"Error creating Gist: {e}")
        return "Unable to create Gist"

# Helper function to notify users or admins about errors
async def _notify_error(interaction: discord.Interaction, error: Exception, gist_url: str):
    permitlist = [user.discordID for user in database.Administrators.select().where(database.Administrators.TierLevel >= 3)]
    
    if interaction.user.id not in permitlist:
        error_embed = discord.Embed(
            title="Error Detected!",
            description="An unexpected error occurred. The developers have been notified.",
            color=discord.Color.brand_red(),
        )
        error_embed.add_field(
            name="Error Message",
            value="Please double check your command. The developers have been notified and are investigating the issue.",
        )
        error_embed.set_footer(text="Submit a bug report or feedback below!")
        await _send_response(interaction, error_embed)
    else:
        admin_embed = discord.Embed(
            title="Traceback Detected!",
            description="An error occurred in PortalBot. Traceback details have been attached below.",
            color=discord.Color.red(),
        )
        admin_embed.add_field(name="GIST URL", value=gist_url)
        admin_embed.set_footer(text=f"Error: {str(error)}")
        await _send_response(interaction, admin_embed)



async def on_command_(bot: 'PortalBot', ctx: commands.Context):
    # List of commands that should bypass the message
    bypass_commands = {"sync", "ping", "kill", "jsk", "py", "jishaku"}
    
    # Return early if the command is in the bypass list
    if ctx.command.name in bypass_commands:
        return
    
    # Notify user that this command is deprecated and suggest the slash equivalent
    await ctx.reply(
        f"❌ The command `{ctx.command.name}` is deprecated. Please use the slash command `/{ctx.command.name}` instead."
    )


def initialize_db(bot):
    """
    Initializes the database, and creates the needed table data if they don't exist.
    """
    try:
        # Ensure the database is connected
        database.db.connect(reuse_if_open=True)

        # Fetch the bot data row based on the unique ID
        row_id = get_bot_data_id()
        bot_data = database.BotData.select().where(database.BotData.id == row_id)

        # If no bot data exists, create it
        if not bot_data.exists():
            _create_bot_data()
            _log.info("Created initial BotData entry.")

        # Check if Administrator entries exist, and create them if not
        if database.Administrators.select().count() == 0:
            _create_administrators(bot.owner_ids)
            _log.info("Created Administrator entries.")

    except Exception as e:
        _log.error(f"Error during database initialization: {e}")
    finally:
        # Always close the database connection
        if not database.db.is_closed():
            database.db.close()

def _create_bot_data():
    """Creates the initial BotData entry."""
    database.BotData.create(
        prefix=">",
        persistent_views=False,
        blacklist_response_channel=995819431538217093,
        question_suggest_channel=787803726168588318,
        bot_spam_channel=588728994661138494,
        realm_channel_response=588408514796322816,
        server_id=587495640502763521
    )

def _create_administrators(owner_ids):
    """Creates Administrator entries based on the bot owner IDs."""
    for owner_id in owner_ids:
        database.Administrators.create(discordID=owner_id, TierLevel=4)
    # Ensure specific admin entry
    database.Administrators.create(discordID=409152798609899530, TierLevel=4)
