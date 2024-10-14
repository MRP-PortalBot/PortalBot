"""
Copyright (C) Minecraft Realm Portal - All Rights Reserved
 * Permission is granted to use this application as a code reference for educational purposes.
 * Written by Minecraft Realm Portal, Development Team. August 2023
"""

__author__ = "M.R.P Bot Development"

import logging
import os
import time
from pathlib import Path

import discord
import xbox
from alive_progress import alive_bar
from discord import app_commands
from discord.ext import commands
from discord_sentry_reporting import use_sentry
from dotenv import load_dotenv
from pygit2 import Repository, GIT_DESCRIBE_TAGS
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from core import database
from core.common import get_bot_data_id
from core.logging_module import get_log
from core.special_methods import (
    on_app_command_error_,
    initialize_db,
    on_ready_,
    on_command_error_,
    on_command_,
)

# Setup logging
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

_log = get_log(__name__)
_log.info("Starting PortalBot...")

# Load environment variables
load_dotenv()

# Fetch bot information from the database
row_id = get_bot_data_id()
try:
    bot_info: database.BotData = (
        database.BotData.select().where(database.BotData.id == row_id).get()
    )
    _log.info(f"Bot data retrieved from database: {bot_info}")
except Exception as e:
    _log.error(f"Failed to retrieve bot data from the database: {e}")
    raise

# Xbox authentication
try:
    xbox.client.authenticate(
        login=os.getenv("xbox_u"),
        password=os.getenv("xbox_p"),
    )
    _log.info(os.getenv("xbox_u"))
    _log.info(os.getenv("xbox_p"))
    _log.info("Authenticated with Xbox successfully.")
except Exception as e:
    _log.critical(
        f"ERROR: Unable to authenticate with Xbox! Exception: {type(e).__name__} | Details: {e}"
    )


# Function to dynamically load extensions (cogs)
def get_extensions():
    extensions = ["jishaku"]
    for file in Path("utils").glob("**/*.py"):
        if "!" in file.name or "__" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace(".py", ""))
    _log.info(f"Extensions found: {extensions}")
    return extensions


# Custom Command Tree with error handling
class PBCommandTree(app_commands.CommandTree):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.avatar is None:
            await interaction.response.send_message(
                "Due to a Discord limitation, you must have an avatar set to use this command."
            )
            _log.warning(
                f"User {interaction.user} cannot use commands due to missing avatar."
            )
            return False
        return True

    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        _log.error(f"App command error: {error}")
        await on_app_command_error_(self.bot, interaction, error)


# Main bot class
class PortalBot(commands.Bot):
    """
    Generates a PortalBot Instance.
    """

    def __init__(self, uptime: time.time):
        super().__init__(
            command_prefix=commands.when_mentioned_or(bot_info.prefix),
            intents=discord.Intents.all(),
            case_insensitive=True,
            tree_cls=PBCommandTree,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over the Portal! | {bot_info.prefix}help",
            ),
        )
        self.help_command = None
        self._start_time = uptime
        _log.info("PortalBot instance created.")

    async def on_ready(self):
        await on_ready_(self)
        _log.info("PortalBot is ready.")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        await on_command_error_(self, ctx, error)

    async def on_command(self, ctx: commands.Context):
        await on_command_(self, ctx)

    async def setup_hook(self) -> None:
        _log.info("Initializing cogs...")
        with alive_bar(
            len(get_extensions()),
            ctrl_c=False,
            bar="bubbles",
            title="Initializing Cogs:",
        ) as bar:
            for ext in get_extensions():
                try:
                    await self.load_extension(ext)
                    _log.info(f"Successfully loaded extension: {ext}")
                except commands.ExtensionAlreadyLoaded:
                    await self.unload_extension(ext)
                    await self.load_extension(ext)
                    _log.warning(f"Reloaded extension: {ext}")
                except commands.ExtensionNotFound:
                    _log.error(f"Extension not found: {ext}")
                    raise commands.ExtensionNotFound(ext)
                bar()

    async def is_owner(self, user: discord.User):
        database.db.connect(reuse_if_open=True)
        query = database.Administrators.select().where(
            (database.Administrators.TierLevel >= 3)
            & (database.Administrators.discordID == user.id)
        )
        is_owner = query.exists()
        database.db.close()
        _log.info(f"User {user} owner check: {'Yes' if is_owner else 'No'}")
        return is_owner or await super().is_owner(user)

    @property
    def version(self):
        """
        Returns the current version of the bot based on the Git repository.
        """
        try:
            repo = Repository(".")
            current_commit = repo.head
            current_branch = repo.head.shorthand

            if current_branch == "HEAD":
                current_tag = repo.describe(
                    committish=current_commit, describe_strategy=GIT_DESCRIBE_TAGS
                )
                version = f"{current_tag} (stable)"
            else:
                version = "development"
            version += f" | {str(current_commit.target)[:7]}"
            _log.info(f"Bot version: {version}")
            return version
        except Exception as e:
            _log.error(f"Error retrieving bot version: {e}")
            return "Unknown"

    @property
    def author(self):
        return __author__

    @property
    def start_time(self):
        return self._start_time


bot = PortalBot(time.time())

# Sentry configuration for error reporting
if os.getenv("sentry_dsn"):
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    use_sentry(
        bot,
        dsn=os.getenv("sentry_dsn"),
        traces_sample_rate=1.0,
        integrations=[FlaskIntegration(), sentry_logging],
    )
    _log.info("Sentry integration enabled.")

# Initialize the database
initialize_db(bot)

if __name__ == "__main__":
    try:
        _log.info("Running PortalBot...")
        bot.run(os.getenv("token"))
    except Exception as e:
        _log.exception(f"Failed to run PortalBot: {e}")
