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


# Note: Other functions like `on_command_error_`, `on_app_command_error_`, etc. remain unchanged.


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


def _create_bot_data(server_id):
    """Creates the initial BotData entry for the given server."""
    _log.info(f"Creating initial BotData entry in the database for server {server_id}.")
    database.BotData.create(
        server_id=server_id,
        prefix=">",
        persistent_views=False,
        bannedlist_response_channel=995819431538217093,
        question_suggest_channel=787803726168588318,
        bot_spam_channel=588728994661138494,
        realm_channel_response=588408514796322816,
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
