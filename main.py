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
from alive_progress import alive_bar
from discord import app_commands
from discord.ext import commands
from discord_sentry_reporting import use_sentry
from dotenv import load_dotenv
from pygit2 import Repository, GIT_DESCRIBE_TAGS
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from utils.database import __database as database
from utils.core_features.__common import get_bot_data_for_server, get_cached_bot_data
from utils.core_features.__constants import DEFAULT_PREFIX
from utils.helpers.__logging_module import get_log
from utils.core_features.__special_methods import (
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

# Ensure all tables are created
database.iter_table(database.tables)


async def preload_bot_data(bot):
    for guild in bot.guilds:
        await get_bot_data_for_server(guild.id)


def get_extensions():
    extensions = ["jishaku"]
    for file in Path("utils").glob("**/*.py"):
        if "!" in file.name or "__" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace(".py", ""))
    _log.info(f"Extensions found: {extensions}")
    return extensions


class PBCommandTree(app_commands.CommandTree):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.display_avatar == interaction.user.default_avatar:
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


class PortalBot(commands.Bot):
    def __init__(self, uptime: float):
        super().__init__(
            command_prefix=commands.when_mentioned_or(DEFAULT_PREFIX),
            intents=discord.Intents.all(),
            tree_cls=PBCommandTree,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over the Portal! | {DEFAULT_PREFIX}help",
            ),
        )
        self.help_command = None
        self._start_time = uptime
        _log.info("PortalBot instance created.")

    async def on_ready(self):
        await on_ready_(self)
        await preload_bot_data(self)

        for guild in self.guilds:
            cached_bot_data = get_cached_bot_data(guild.id)
            if cached_bot_data:
                self.command_prefix = commands.when_mentioned_or(cached_bot_data.prefix)
                self.activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"over the Portal! | {cached_bot_data.prefix}help",
                )
                _log.info(
                    f"Bot prefix set for server {guild.id}: {cached_bot_data.prefix}"
                )

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
                    raise
                bar()

        try:
            synced = await self.tree.sync()
            _log.info(f"✅ Synced {len(synced)} slash commands with Discord.")
        except Exception as e:
            _log.error(f"❌ Failed to sync application commands: {e}", exc_info=True)

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

if os.getenv("sentry_dsn"):
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )
    use_sentry(
        bot,
        dsn=os.getenv("sentry_dsn"),
        traces_sample_rate=1.0,
        integrations=[FlaskIntegration(), sentry_logging],
    )
    _log.info("Sentry integration enabled.")

initialize_db(bot)

if __name__ == "__main__":
    try:
        token = os.getenv("token")
        if not token:
            _log.error("Bot token not found in environment variables.")
            exit(1)

        _log.info("Running PortalBot...")
        bot.run(token)
    except Exception as e:
        _log.exception(f"Failed to run PortalBot: {e}")
