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
from core.special_methods import on_app_command_error_, initialize_db, on_ready_, on_command_error_, on_command_, \
    before_invoke_

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

_log = get_log(__name__)
_log.info("Starting PortalBot...")
load_dotenv()
try:
    xbox.client.authenticate(
        login=os.getenv('xbox_u'),
        password=os.getenv('xbox_p'),
    )
except:
    logger.critical("ERROR: Unable to authenticate with XBOX!")


def get_extensions():  # Gets extension list dynamically
    extensions = ["jishaku"]
    for file in Path("utils").glob("**/*.py"):
        if "!" in file.name or "__" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace(".py", ""))
    return extensions


class PBCommandTree(app_commands.CommandTree):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        #blacklisted_users = [p.discordID for p in database.Blacklist]
        if interaction.user.avatar is None:
            await interaction.response.send_message(
                "Due to a discord limitation, you must have an avatar set to use this command.")
            return False
        """if interaction.user.id in blacklisted_users:
            await interaction.response.send_message(
                "You have been blacklisted from using commands!", ephemeral=True
            )
            return False"""
        return True

    async def on_error(
            self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await on_app_command_error_(self.bot, interaction, error)


class PortalBot(commands.Bot):
    """
    Generates a Timmy Instance.
    """

    def __init__(self, uptime: time.time):
        row_id = get_bot_data_id()
        bot_info: database.BotData = database.BotData.select().where(
            database.BotData.id == row_id).get()
        super().__init__(
            command_prefix=commands.when_mentioned_or(bot_info.prefix),
            intents=discord.Intents.all(),
            case_insensitive=True,
            tree_cls=PBCommandTree,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over the Portal! | {bot_info.prefix}help")
        )
        self.help_command = None
        #self.add_check(self.check)
        self._start_time = uptime

    async def on_ready(self):
        await on_ready_(self)

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        await on_command_error_(self, ctx, error)

    async def on_command(self, ctx: commands.Context):
        await on_command_(self, ctx)

    """async def analytics_before_invoke(self, ctx: commands.Context):
        await before_invoke_(ctx)"""

    async def setup_hook(self) -> None:
        with alive_bar(
                len(get_extensions()),
                ctrl_c=False,
                bar="bubbles",
                title="Initializing Cogs:",
        ) as bar:

            for ext in get_extensions():
                try:
                    await bot.load_extension(ext)
                except commands.ExtensionAlreadyLoaded:
                    await bot.unload_extension(ext)
                    await bot.load_extension(ext)
                except commands.ExtensionNotFound:
                    raise commands.ExtensionNotFound(ext)
                bar()
        # await bot.tree.set_translator(TimmyTranslator())

    async def is_owner(self, user: discord.User):
        admin_ids = []
        query = database.Administrators.select().where(
            database.Administrators.TierLevel >= 3
        )
        for admin in query:
            admin_ids.append(admin.discordID)

        if user.id in admin_ids:
            return True

        return await super().is_owner(user)

    @property
    def version(self):
        """
        Returns the current version of the bot.
        """
        repo = Repository(".")
        current_commit = repo.head
        current_branch = repo.head.shorthand

        version = ...  # type: str
        if current_branch == "HEAD":
            current_tag = repo.describe(committish=current_commit, describe_strategy=GIT_DESCRIBE_TAGS)
            version = f"{current_tag} (stable)"
        else:
            version = "development"
        version += f" | {str(current_commit.target)[:7]}"

        return version

    @property
    def author(self):
        """
        Returns the author of the bot.
        """
        return __author__

    @property
    def start_time(self):
        """
        Returns the time the bot was started.
        """
        return self._start_time


bot = PortalBot(time.time())

if os.getenv('sentry_dsn') is not None:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    # Traceback tracking, DO NOT MODIFY THIS
    use_sentry(
        bot,
        dsn=os.getenv('sentry_dsn'),
        traces_sample_rate=1.0,
        integrations=[FlaskIntegration(), sentry_logging],
    )

initialize_db(bot)


if __name__ == '__main__':
    try:
        bot.run(os.getenv('TOKEN'))
    except Exception as e:
        _log.exception(e)
