import asyncio
from asyncio import Lock
import json
import os
import random
from typing import Tuple, Union, List
from pathlib import Path
from datetime import datetime
import functools
import inspect

import discord
from discord import ButtonStyle, ui, SelectOption

from utils.database import database
from utils.helpers.logging_module import get_log

from utils.helpers.cache_state import bot_data_cache, cache_lock
from utils.database.database import BotData

# Logger
_log = get_log(__name__)

# Local fallback cache for bot data
cache_lock = Lock()
bot_data_cache = {}


async def get_bot_data_for_server(server_id: Union[int, str]):
    """
    Fetch and cache BotData for a given server.
    Uses string-based ID comparison to support TextField storage.
    """
    async with cache_lock:
        if str(server_id) in bot_data_cache:
            _log.info(f"Returning cached bot data for server {server_id}")
            return bot_data_cache[str(server_id)]

    try:
        # Fetch outside lock to avoid blocking
        bot_info = (
            database.BotData.select()
            .where(database.BotData.server_id == str(server_id))
            .get()
        )
        async with cache_lock:
            bot_data_cache[str(server_id)] = bot_info
        _log.info(
            f"Bot data fetched and cached for guild {server_id}: "
            f"Prefix: {bot_info.prefix}, Server ID: {bot_info.server_id}"
        )
        return bot_info
    except database.DoesNotExist:
        _log.error(f"No BotData found for server ID: {server_id}")
        return None
    except Exception as e:
        _log.error(
            f"Error fetching bot data for server ID {server_id}: {e}", exc_info=True
        )
        return None


def get_cached_bot_data(server_id: Union[int, str]):
    """
    Return cached BotData for the given server ID if it exists.
    """
    bot_data = bot_data_cache.get(str(server_id))
    if bot_data:
        _log.info(
            f"Cached bot data fetched for guild {server_id}: "
            f"Prefix: {bot_data.prefix}, Server ID: {bot_data.server_id}"
        )
    else:
        _log.warning(f"No cached bot data found for guild {server_id}")
    return bot_data


def refresh_bot_data_cache(guild_id: int):
    """Refresh the bot_data_cache entry for a specific guild from the DB."""

    bot_data = BotData.get_or_none(BotData.server_id == str(guild_id))
    if bot_data:
        bot_data_cache[str(guild_id)] = bot_data


def load_config() -> Tuple[dict, Path]:
    """
    Load config from botconfig.json.

    Returns:
        Tuple[dict, Path]: The config dictionary and the Path object.
    """
    config_file = Path("botconfig.json")
    try:
        config_file.touch(exist_ok=True)
        if config_file.read_text() == "":
            config_file.write_text("{}")
        with config_file.open("r") as f:
            config = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        _log.error(f"Failed to load configuration: {e}")
        raise e
    return config, config_file


# Load on startup
config, config_file = load_config()


def solve(s: str) -> str:
    """
    Capitalizes each word in a string.

    Args:
        s (str): The string to capitalize.

    Returns:
        str: The capitalized string.
    """
    return " ".join(word.capitalize() for word in s.split())


class SelectMenuHandler(ui.Select):
    """
    Discord Select Menu handler with optional user lock and coroutine execution.
    """

    def __init__(
        self,
        options: List[SelectOption],
        select_user: Union[discord.User, None] = None,
        coroutine: callable = None,
        **kwargs,
    ):
        self.select_user = select_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(options=options, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if not self._is_authorized_user(interaction.user):
            _log.warning(f"Unauthorized user interaction: {interaction.user}")
            return

        self.view.value = self.values[0]
        self.view_response = self.values[0]

        if self.coroutine:
            _log.info(f"Executing coroutine for user: {interaction.user}")
            await self.coroutine(interaction, self.view)

    def _is_authorized_user(self, user: discord.User) -> bool:
        return self.select_user is None or user == self.select_user


class ButtonHandler(ui.Button):
    """
    Discord Button handler with optional user lock and coroutine execution.
    """

    def __init__(self, label: str, button_user=None, coroutine=None, **kwargs):
        self.button_user = button_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.button_user is None or interaction.user == self.button_user:
            self.view_response = (
                self.label if self.custom_id is None else self.custom_id
            )
            if self.coroutine:
                await self.coroutine(interaction, self.view)
        else:
            _log.warning(f"Unauthorized button interaction by {interaction.user}")
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )


def calculate_level(score: int) -> Tuple[int, float, int]:
    """
    Calculate level and progress based on score.

    Returns:
        Tuple of (level, percent to next, score for next level)
    """
    level = int((score // 100) ** 0.5)
    next_level_score = (level + 1) ** 2 * 100
    prev_level_score = level**2 * 100
    progress = (
        (score - prev_level_score) / (next_level_score - prev_level_score)
        if next_level_score != prev_level_score
        else 0.0
    )
    return level, progress, next_level_score


def get_user_rank(server_id: Union[int, str], user_id: Union[int, str]):
    """
    Returns the 1-based rank of a user in a given server based on score.
    """
    try:
        query = (
            database.ServerScores.select(database.ServerScores.DiscordLongID)
            .where(database.ServerScores.ServerID == str(server_id))
            .order_by(database.ServerScores.Score.desc())
        )
        rank = 1
        for entry in query:
            if entry.DiscordLongID == str(user_id):
                return rank
            rank += 1
    except Exception as e:
        _log.error(f"Error retrieving user rank: {e}")
        return None

    return None


def get_bot_data_for_guild(interaction: discord.Interaction):
    """
    Returns BotData from database for the given interaction's guild.
    """
    try:
        guild_id = str(interaction.guild.id)
        bot_data = database.BotData.get(database.BotData.server_id == guild_id)
        return bot_data
    except database.BotData.DoesNotExist:
        return None
    except Exception as e:
        _log.error(f"Error fetching bot data for guild {guild_id}: {e}")
        return None


def get_permitlist(min_level=3):
    """
    Returns a list of Discord IDs of administrators with at least the given level.
    """
    return [
        admin.discordID
        for admin in database.Administrators.select().where(
            database.Administrators.TierLevel >= min_level
        )
    ]


def ensure_profile_exists(profile: object) -> database.PortalbotProfile | None:
    """
    Ensure the given Discord Member has a profile in the database.
    Creates one if missing. Returns the profile or None on failure.
    """
    user_id = str(profile.id)
    discordname = f"{profile.name}#{profile.discriminator}"

    try:
        database.db.connect(reuse_if_open=True)
        profile_record, created = database.PortalbotProfile.get_or_create(
            DiscordLongID=user_id, defaults={"DiscordName": discordname}
        )
        if created:
            _log.info(f"Auto-created profile for {discordname}")
        return profile_record

    except Exception as e:
        _log.error(f"Failed to ensure profile for {discordname}: {e}", exc_info=True)
        return None

    finally:
        if not database.db.is_closed():
            database.db.close()
            
def get_profile_record(self, user_id: str):
    return database.PortalbotProfile.get(
        database.PortalbotProfile.DiscordLongID == user_id
    )

