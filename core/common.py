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

# Importing discord modules
import discord
from discord import ButtonStyle, ui, SelectOption

# Importing core modules
from core import database
from core.logging_module import get_log

from core.cache_state import bot_data_cache, cache_lock

# Setting up logger
_log = get_log(__name__)


cache_lock = Lock()
bot_data_cache = {}


async def get_bot_data_for_server(server_id):
    async with cache_lock:
        if server_id in bot_data_cache:
            _log.info(f"Returning cached bot data for server {server_id}")
            return bot_data_cache[server_id]

    try:
        # Fetch outside lock to avoid blocking others during DB fetch
        bot_info = (
            database.BotData.select()
            .where(database.BotData.server_id == server_id)
            .get()
        )

        async with cache_lock:
            bot_data_cache[server_id] = bot_info
        _log.info(
            f"Bot data fetched and cached for guild {server_id}: Prefix: {bot_info.prefix}, Server ID: {bot_info.server_id}"
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


def get_cached_bot_data(server_id):
    bot_data = bot_data_cache.get(server_id)
    if bot_data:
        _log.info(
            f"Cached bot data fetched for guild {server_id}: Prefix: {bot_data.prefix}, Server ID: {bot_data.server_id}"
        )
    else:
        _log.warning(f"No cached bot data found for guild {server_id}")
    return bot_data


# Loading Configuration Functions
def load_config() -> Tuple[dict, Path]:
    """
    Load data from the botconfig.json file.

    Returns:
        Tuple[dict, Path]: Configuration data as a dictionary and the Path of the config file.
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


config, config_file = load_config()


# Utility Functions
def solve(s: str) -> str:
    """
    Capitalizes each word in a string.

    Args:
        s (str): The string to capitalize.

    Returns:
        str: The capitalized string.
    """
    return " ".join(word.capitalize() for word in s.split())


# Discord UI Component Handlers (SelectMenu & Button)
class SelectMenuHandler(ui.Select):
    """
    Handler for creating a SelectMenu in Discord with custom logic.
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
        # Check if the interaction user is allowed
        if not self._is_authorized_user(interaction.user):
            _log.warning(f"Unauthorized user interaction: {interaction.user}")
            return

        # Set view response
        self.view.value = self.values[0]
        self.view_response = self.values[0]

        # Execute coroutine if provided
        if self.coroutine:
            _log.info(f"Executing coroutine for user: {interaction.user}")
            await self.coroutine(interaction, self.view)

    def _is_authorized_user(self, user: discord.User) -> bool:
        """
        Helper method to check if the user is authorized for the interaction.
        """
        return self.select_user is None or user == self.select_user


class ButtonHandler(ui.Button):
    """
    Handler for adding a Button to a specific message and invoking a custom coroutine on click.
    """

    def __init__(self, label: str, button_user=None, coroutine=None, **kwargs):
        self.button_user = button_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(
            label=label, **kwargs
        )  # Pass the remaining kwargs to the parent class

    async def callback(self, interaction: discord.Interaction):
        # Check if the interaction is from the correct user
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


# Function to Calculate Level Based on Score
def calculate_level(score: int) -> Tuple[int, float, int]:
    """
    Calculate the user's level and progress to the next level based on their score.

    Args:
        score (int): The user's current score.

    Returns:
        Tuple[int, float, int]: The user's level, progress percentage, and next level score.
    """
    level = int((score // 100) ** 0.5)
    next_level_score = (level + 1) ** 2 * 100
    prev_level_score = level**2 * 100
    if next_level_score == prev_level_score:
        progress = 0.0
    else:
        progress = (score - prev_level_score) / (next_level_score - prev_level_score)
    return level, progress, next_level_score


def get_user_rank(server_id, user_id):
    """
    Retrieve the user's rank in a specific server based on score.

    Args:
        server_id (int or str): The ID of the Discord server.
        user_id (int or str): The Discord user ID.

    Returns:
        int or None: The rank of the user (1-based), or None if not found or an error occurred.
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


def get_bot_data_for_guild(interaction):
    """
    Retrieve bot configuration data for the current guild based on the interaction context.

    Args:
        interaction (discord.Interaction): The Discord interaction object.

    Returns:
        BotData or None: The bot data for the guild, or None if not found or an error occurs.
    """
    try:
        guild_id = interaction.guild.id
        bot_data = database.BotData.get(database.BotData.server_id == guild_id)
        return bot_data
    except database.BotData.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error fetching bot data for guild {guild_id}: {e}")
        return None


def get_permitlist(min_level=3):
    return [
        admin.discordID
        for admin in database.Administrators.select().where(
            database.Administrators.TierLevel >= min_level
        )
    ]
