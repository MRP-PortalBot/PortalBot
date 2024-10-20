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
from discord import app_commands
from discord.ext import commands

from core import database
from core.common import (
    ConsoleColors,
    Colors,
    Others,
    get_bot_data_id,
    load_config,
)
from core.logging_module import get_log

# Load configuration
config, _ = load_config()

if TYPE_CHECKING:
    from main import PortalBot

# Logger setup
_log = get_log(__name__)


async def on_ready_(bot: "PortalBot"):
    """
    Called when the bot is ready and fully connected.
    Initializes views, fetches version info, and logs bot status.
    """
    now = datetime.now()
    row_id = get_bot_data_id()
    _log.info(f"Bot ready at {now}. Fetching bot data for row_id: {row_id}.")

    # Fetch the bot data from the database
    try:
        query: database.BotData = database.BotData.get_or_none(
            database.BotData.id == row_id
        )
        if query:
            _log.info("Bot data successfully retrieved from the database.")
        else:
            _log.warning("Bot data not found for the given row_id.")
    except Exception as e:
        _log.error(
            f"Error fetching bot data from the database: {str(e)}", exc_info=True
        )

    # Ensure persistent views are initialized
    initialize_persistent_views(bot=bot, query=query)

    # Determine the database source (external or local)
    database_source = "External" if not os.getenv("USEREAL") else "localhost"
    db_message_color = (
        ConsoleColors.OKGREEN if database_source == "External" else ConsoleColors.FAIL
    )
    db_warning_message = (
        f"{ConsoleColors.WARNING}WARNING: Not recommended to use SQLite.{ConsoleColors.ENDC}"
        if database_source == "localhost"
        else ""
    )

    database_message = f"{db_message_color}Selected Database: {database_source} {ConsoleColors.ENDC}\n{db_warning_message}"
    _log.info(f"Database source determined: {database_source}")

    # Fetch Git version (asynchronously)
    try:
        _log.info("Attempting to fetch Git version.")
        process = await asyncio.create_subprocess_shell(
            "git describe --always",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            git_version = stdout.decode().strip()
            _log.info(f"Git version fetched: {git_version}")
        else:
            git_version = "ERROR"
            _log.error(f"Git version fetch failed. Stderr: {stderr.decode().strip()}")
    except Exception as e:
        git_version = f"ERROR: {str(e)}"
        _log.error(f"Error fetching Git version: {str(e)}", exc_info=True)

    # Log bot details to console
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
    _log.info("Bot initialization complete. Stats logged.")

    # Send a message to the GitHub log channel
    try:
        _log.info("Attempting to send sync message to 'github-log' channel.")
        guild = bot.get_guild(
            config["PBtest"]
        )  # Replace 'PBtest' with actual guild ID or logic
        github_channel = discord.utils.get(guild.channels, name="github-log")

        if github_channel:
            await github_channel.send("Github Synced, and bot is restarted")
            _log.info("Sync message sent to 'github-log' channel.")
        else:
            _log.error("'github-log' channel not found in the guild.")
    except Exception as e:
        _log.error(
            f"Error sending message to 'github-log' channel: {str(e)}", exc_info=True
        )


# Function that needs QuestionSuggestionManager
def initialize_persistent_views(bot, query):
    from utils.MRP_Cogs.daily_questions import QuestionSuggestionManager

    # Ensure persistent views are initialized
    if query and not query.persistent_views:
        bot.add_view(QuestionSuggestionManager())
        query.persistent_views = True
        query.save()
        _log.info("Persistent views initialized and saved to the database.")


async def on_command_error_(bot, ctx: commands.Context, error: Exception):
    # Gather traceback details
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))
    error = getattr(error, "original", error)  # Unwrap command invocation errors

    # Log the full error traceback
    _log.error(f"Error in command '{ctx.command}': {exception_msg}")

    # Early exit for the rule command
    if ctx.command and ctx.command.name == "rule":
        return await ctx.send("No Rule...")

    # Command-specific error handling
    if isinstance(error, commands.CheckFailure):
        _log.warning(f"Check failed for user {ctx.author.id} on command {ctx.command}.")
        return

    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.invoked_with
        cmds = [cmd.name for cmd in bot.commands]
        matches = get_close_matches(cmd, cmds)
        if matches:
            _log.info(f"Command '{cmd}' not found. Suggesting '{matches[0]}'.")
            return await ctx.send(
                f'Command "{cmd}" not found. Did you mean "{matches[0]}"?'
            )
        return await ctx.message.add_reaction("❌")

    if isinstance(error, (commands.MissingRequiredArgument, commands.TooManyArguments)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        em = discord.Embed(
            title="Missing or Extra Arguments",
            description=f"You missed or provided too many arguments.\n\nUsage:\n`{signature}`",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command if needed.")
        _log.info(f"Missing or extra arguments in command '{ctx.command}'.")
        return await ctx.send(embed=em)

    if isinstance(
        error,
        (
            commands.MissingPermissions,
            commands.MissingRole,
            commands.errors.MissingAnyRole,
        ),
    ):
        em = discord.Embed(
            title="Insufficient Permissions",
            description="You don't have the required role or permissions for this command. Contact an admin if this is an error.",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command for more details.")
        _log.warning(
            f"Permission error for user {ctx.author.id} on command {ctx.command}."
        )
        return await ctx.send(embed=em)

    if isinstance(error, (commands.BadArgument, commands.BadLiteralArgument)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        em = discord.Embed(
            title="Bad Argument",
            description=f"Invalid argument provided.\n\nUsage:\n`{signature}`",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(text="Refer to the Help Command for more information.")
        _log.warning(
            f"Bad argument provided by user {ctx.author.id} on command {ctx.command}."
        )
        return await ctx.send(embed=em)

    if isinstance(
        error, (commands.CommandOnCooldown, commands.errors.CommandOnCooldown)
    ):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)
        msg = f"This command is on cooldown. Try again in {int(h)} hours, {int(m)} minutes, and {int(s)} seconds."
        em = discord.Embed(
            title="Command On Cooldown",
            description=msg,
            color=discord.Color.red(),
        )
        _log.info(f"Command on cooldown for user {ctx.author.id}: {msg}")
        return await ctx.send(embed=em)

    # Default error handling (create Gist and notify developers)
    _log.error(f"Unhandled error for command '{ctx.command}': {exception_msg}")
    gist_url = await _create_gist(exception_msg)

    permitlist = [
        admin.discordID
        for admin in database.Administrators.select().where(
            database.Administrators.TierLevel >= 3
        )
    ]

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

    raise error


async def on_app_command_error_(
    bot: "PortalBot",
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    """
    Handles errors that occur during the execution of app commands.
    """
    # Capture and format the traceback
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))

    _log.error(f"Error in command '{interaction.command}': {exception_msg}")

    # Command on Cooldown
    if isinstance(error, app_commands.CommandOnCooldown):
        h, m = divmod(int(error.retry_after // 60), 60)
        s = round(error.retry_after % 60)
        cooldown_msg = f"This command cannot be used again for {h} hours, {m} minutes, and {s} seconds."
        embed = discord.Embed(
            title="Command On Cooldown",
            description=cooldown_msg,
            color=discord.Color.red(),
        )
        _log.info(
            f"Command {interaction.command} is on cooldown for user {interaction.user.id}: {cooldown_msg}"
        )
        await _send_response(interaction, embed)
        return

    # Command Check Failure
    if isinstance(error, app_commands.CheckFailure):
        failure_msg = "You cannot run this command!"
        _log.warning(
            f"Check failure for user {interaction.user.id} on command {interaction.command}"
        )
        await _send_response(interaction, failure_msg, ephemeral=True)
        return

    # Command Not Found
    if isinstance(error, app_commands.CommandNotFound):
        _log.error(f"Command {interaction.command} not found.")
        await interaction.response.send_message(
            f"Command /{interaction.command.name} not found."
        )
        return

    # Unhandled Errors: Create a Gist and notify developers
    gist_url = await _create_gist(exception_msg)
    await _notify_error(interaction, error, gist_url)

    raise error  # Re-raise the error after handling


# Helper function to send responses, handling both response and follow-up cases
async def _send_response(
    interaction: discord.Interaction,
    content: Union[discord.Embed, str],
    ephemeral=False,
):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(
                content=content, ephemeral=ephemeral
            )
    except Exception as e:
        _log.error(f"Error sending response to user {interaction.user.id}: {e}")


# Reusing the previous helper function to create a Gist and return the URL
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
        gist_id = res.json()["id"]
        _log.info(f"Created Gist for error: https://gist.github.com/{gist_id}")
        return f"https://gist.github.com/{gist_id}"
    except Exception as e:
        _log.error(f"Error creating Gist: {e}")
        return "Unable to create Gist"


# Helper function to notify users or admins about errors
async def _notify_error(
    interaction: discord.Interaction, error: Exception, gist_url: str
):
    permitlist = [
        user.discordID
        for user in database.Administrators.select().where(
            database.Administrators.TierLevel >= 3
        )
    ]

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
        _log.warning(f"User {interaction.user.id} encountered an error: {error}")
        await _send_response(interaction, error_embed)
    else:
        admin_embed = discord.Embed(
            title="Traceback Detected!",
            description="An error occurred in PortalBot. Traceback details have been attached below.",
            color=discord.Color.red(),
        )
        if gist_url:
            admin_embed.add_field(name="GIST URL", value=gist_url)
        admin_embed.set_footer(text=f"Error: {str(error)}")
        _log.error(
            f"Admin {interaction.user.id} encountered an error: {error} (Gist URL: {gist_url})"
        )
        await _send_response(interaction, admin_embed)


async def on_command_(bot: "PortalBot", ctx: commands.Context):
    # List of commands that should bypass the message
    bypass_commands = {"sync", "ping", "kill", "jsk", "py", "jishaku"}

    # Log the command that was invoked
    _log.info(f"User {ctx.author} invoked command: {ctx.command.name}")

    # Return early if the command is in the bypass list
    if ctx.command.name in bypass_commands:
        _log.info(f"Command {ctx.command.name} is in the bypass list, no message sent.")
        return

    # Notify user that this command is deprecated and suggest the slash equivalent
    deprecated_msg = f"❌ The command `{ctx.command.name}` is deprecated. Please use the slash command `/{ctx.command.name}` instead."
    _log.info(f"Sending deprecated message to user {ctx.author}: {deprecated_msg}")

    await ctx.reply(deprecated_msg)


from __future__ import annotations

import json
import os
import subprocess
import traceback
import asyncio
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING, Union

import discord
import requests
from discord import app_commands
from discord.ext import commands

from core import database
from core.common import (
    ConsoleColors,
    Colors,
    Others,
    get_cached_bot_data,
    get_bot_data_for_server,
)
from core.logging_module import get_log

# Logger setup
_log = get_log(__name__)

if TYPE_CHECKING:
    from main import PortalBot


async def on_ready_(bot: "PortalBot"):
    """
    Called when the bot is ready and fully connected.
    Initializes views, fetches version info, and logs bot status.
    """
    now = datetime.now()
    _log.info(f"Bot ready at {now}. Preloading bot data for guilds.")

    # Preload bot data for all guilds
    await preload_bot_data(bot)

    # Ensure persistent views are initialized
    for guild in bot.guilds:
        bot_data = get_cached_bot_data(guild.id)
        if not bot_data:
            _log.warning(
                f"Bot data not found for guild {guild.id}. Skipping view initialization."
            )
            continue
        initialize_persistent_views(bot, bot_data)

    # Determine the database source (external or local)
    database_source = "External" if not os.getenv("USEREAL") else "localhost"
    db_message_color = (
        ConsoleColors.OKGREEN if database_source == "External" else ConsoleColors.FAIL
    )
    db_warning_message = (
        f"{ConsoleColors.WARNING}WARNING: Not recommended to use SQLite.{ConsoleColors.ENDC}"
        if database_source == "localhost"
        else ""
    )

    database_message = f"{db_message_color}Selected Database: {database_source} {ConsoleColors.ENDC}\n{db_warning_message}"
    _log.info(f"Database source determined: {database_source}")

    # Fetch Git version (asynchronously)
    try:
        _log.info("Attempting to fetch Git version.")
        process = await asyncio.create_subprocess_shell(
            "git describe --always",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            git_version = stdout.decode().strip()
            _log.info(f"Git version fetched: {git_version}")
        else:
            git_version = "ERROR"
            _log.error(f"Git version fetch failed. Stderr: {stderr.decode().strip()}")
    except Exception as e:
        git_version = f"ERROR: {str(e)}"
        _log.error(f"Error fetching Git version: {str(e)}", exc_info=True)

    # Log bot details to console
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
    _log.info("Bot initialization complete. Stats logged.")

    # Send a message to the GitHub log channel
    try:
        _log.info("Attempting to send sync message to 'github-log' channel.")
        guild = bot.get_guild(
            config["PBtest"]
        )  # Replace 'PBtest' with actual guild ID or logic
        github_channel = discord.utils.get(guild.channels, name="github-log")

        if github_channel:
            await github_channel.send("Github Synced, and bot is restarted")
            _log.info("Sync message sent to 'github-log' channel.")
        else:
            _log.error("'github-log' channel not found in the guild.")
    except Exception as e:
        _log.error(
            f"Error sending message to 'github-log' channel: {str(e)}", exc_info=True
        )


# Preload bot data for all guilds
async def preload_bot_data(bot: "PortalBot"):
    _log.info("Preloading bot data for all guilds...")
    for guild in bot.guilds:
        await get_bot_data_for_server(guild.id)
    _log.info("Bot data preloaded for all guilds.")


# Function that needs QuestionSuggestionManager
def initialize_persistent_views(bot, query):
    from utils.MRP_Cogs.daily_questions import QuestionSuggestionManager

    # Ensure persistent views are initialized
    if query and not query.persistent_views:
        bot.add_view(QuestionSuggestionManager())
        query.persistent_views = True
        query.save()
        _log.info("Persistent views initialized and saved to the database.")


# Initialize the database
def initialize_db(bot):
    """
    Initializes the database and creates the needed table data if they don't exist.
    """
    try:
        # Log the start of the database initialization
        _log.info("Initializing database...")

        # Ensure the database is connected
        database.db.connect(reuse_if_open=True)
        _log.info("Database connected successfully.")

        # Fetch the bot data for each guild
        for guild in bot.guilds:
            bot_data = database.BotData.select().where(
                database.BotData.server_id == guild.id
            )

            # If no bot data exists, create it
            if not bot_data.exists():
                _create_bot_data(guild.id)
                _log.info(f"Created initial BotData entry for guild {guild.id}.")

        # Check if Administrator entries exist, and create them if not
        if database.Administrators.select().count() == 0:
            _create_administrators(bot.owner_ids)
            _log.info("Created Administrator entries for bot owners.")

    except Exception as e:
        _log.error(f"Error during database initialization: {e}")
    finally:
        # Always close the database connection
        if not database.db.is_closed():
            database.db.close()
            _log.info("Database connection closed.")


def _create_bot_data(server_id, initial_channel_id):
    """Creates the initial BotData entry for the given server."""
    _log.info(f"Creating initial BotData entry in the database for server {server_id}.")
    database.BotData.create(
        server_id=server_id,
        prefix=">",
        persistent_views=False,
        bannedlist_response_channel=initial_channel_id,
        question_suggest_channel=initial_channel_id,
        bot_spam_channel=initial_channel_id,
        realm_channel_response=initial_channel_id,
        last_question_posted=None,
        last_question_posted_time=None,
        daily_question_channel=initial_channel_id,
        welcome_message_channel=initial_channel_id,
        mod_log_channel=initial_channel_id,
    )
    _log.info(f"Initial BotData entry created successfully for server {server_id}.")


def _create_administrators(owner_ids):
    """Creates Administrator entries based on the bot owner IDs."""
    _log.info(f"Creating Administrator entries for bot owner IDs: {owner_ids}.")

    for owner_id in owner_ids:
        database.Administrators.create(discordID=owner_id, TierLevel=4)
        _log.info(f"Administrator entry created for owner ID: {owner_id}.")

    # Ensure specific admin entry is created
    specific_admin_id = 306070011028439041
    database.Administrators.create(discordID=specific_admin_id, TierLevel=4)
    _log.info(f"Administrator entry created for specific ID: {specific_admin_id}.")
