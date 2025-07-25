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

from utils.database import __database as database
from utils.helpers.__logging_module import get_log

from utils.database.__database import BotData

# Logger
_log = get_log(__name__)

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
