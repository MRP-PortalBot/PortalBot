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
from utils.database.__database import init_database
from utils.admin.bot_management.__bm_logic import get_bot_data_for_server
from utils.core_features.__constants import DEFAULT_PREFIX
from utils.helpers.__logging_module import get_log

# Centralized error handlers (new)
from utils.core_features.__errors import (
    on_app_command_error_,
    on_command_error_,
)

# Setup logging
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

_log = get_log(__name__)
_log.info("Starting PortalBot...")

# Load environment variables
load_dotenv()

# Ensure DB schema exists before anything else
init_database()


def get_extensions():
    """
    Auto-discovers non-dunder utility modules under utils/ and loads them as extensions.
    We still explicitly load some dunder-named management cogs before this (see setup_hook).
    """
    extensions = ["jishaku"]
    for file in Path("utils").glob("**/*.py"):
        # Skip private/dunder helpers and explicit skips
        if "!" in file.name or "__" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace("\\", ".").replace(".py", ""))
    _log.info(f"Extensions found: {extensions}")
    return extensions


class PBCommandTree(app_commands.CommandTree):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.display_avatar == interaction.user.default_avatar:
            # Keep your existing UX for avatar requirement
            try:
                await interaction.response.send_message(
                    "Due to a Discord limitation, you must have an avatar set to use this command.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass
            _log.warning(f"User {interaction.user} cannot use commands due to missing avatar.")
            return False
        return True

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        _log.error(f"App command error: {error}")
        await on_app_command_error_(self.bot, interaction, error)


class PortalBot(commands.Bot):
    def __init__(self, uptime: float):
        super().__init__(
            command_prefix=self.get_prefix,
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

    async def get_prefix(self, message: discord.Message):
        if message.guild:
            bot_data = get_bot_data_for_server(message.guild.id)
            if bot_data and bot_data.prefix:
                return commands.when_mentioned_or(bot_data.prefix)(self, message)
        return commands.when_mentioned_or(DEFAULT_PREFIX)(self, message)

    async def on_ready(self):
        # Heavy lifting happens in the bot-management bootstrap Cog's on_ready.
        _log.info("PortalBot is ready.")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        await on_command_error_(self, ctx, error)

    async def on_command(self, ctx: commands.Context):
        # Keep your deprecation redirect for legacy prefix commands
        bypass = {"sync", "ping", "kill", "jsk", "py", "jishaku"}
        if ctx.command and ctx.command.name in bypass:
            return
        if ctx.command:
            try:
                await ctx.reply(
                    f"❌ The command `{ctx.command.name}` is deprecated. Please use the slash command `/{ctx.command.name}` instead."
                )
            except discord.HTTPException:
                pass

    async def setup_hook(self) -> None:
        _log.info("Initializing cogs...")

        # 1) Load critical dunder-named management cogs explicitly
        #    They are skipped by the auto-loader and contain on_ready bootstrap and join listeners
        critical_exts = [
            "utils.admin.bot_management.__bm_bootstrap",
            "utils.admin.bot_management.__bm_listeners",
        ]
        for ext in critical_exts:
            try:
                await self.load_extension(ext)
                _log.info(f"Loaded critical extension: {ext}")
            except commands.ExtensionAlreadyLoaded:
                await self.unload_extension(ext)
                await self.load_extension(ext)
                _log.warning(f"Reloaded critical extension: {ext}")
            except Exception:
                _log.exception(f"Failed to load critical extension: {ext}")
                raise

        # 2) Load the rest via discovery
        exts = get_extensions()
        with alive_bar(len(exts), ctrl_c=False, bar="bubbles", title="Initializing Cogs:") as bar:
            for ext in exts:
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
                except Exception:
                    _log.exception(f"Failed to load extension: {ext}")
                    raise
                bar()

        # 3) Sync app commands once after all cogs are loaded
        try:
            synced = await self.tree.sync()
            _log.info(f"✅ Synced {len(synced)} slash commands with Discord.")
        except Exception as e:
            _log.error(f"❌ Failed to sync application commands: {e}", exc_info=True)

    async def is_owner(self, user: discord.User):
        # Your Administrators.discordID is a TextField — compare to str(user.id)
        database.db.connect(reuse_if_open=True)
        try:
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= 3)
                & (database.Administrators.discordID == str(user.id))
            )
            is_owner = query.exists()
        finally:
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

if __name__ == "__main__":
    try:
        token = os.getenv("token")
        if not token:
            _log.error("Bot token not found in environment variables.")
            raise SystemExit(1)

        _log.info("Running PortalBot...")
        bot.run(token)
    except Exception as e:
        _log.exception(f"Failed to run PortalBot: {e}")
