import asyncio
import discord
import json
import os
import random
from typing import Tuple, Union, List
from pathlib import Path
from discord import ButtonStyle, ui, SelectOption
from dotenv import load_dotenv
from core import database
from datetime import datetime
from core.logging_module import get_log

_log = get_log(__name__)

# Loading Configuration Functions
def load_config() -> Tuple[dict, Path]:
    """
    Load data from the botconfig.json file.

    Returns:
        Tuple[dict, Path]: Configuration data as a dictionary and the Path of the config file.
    """
    config_file = Path("botconfig.json")
    config_file.touch(exist_ok=True)
    if config_file.read_text() == "":
        config_file.write_text("{}")
    with config_file.open("r") as f:
        config = json.load(f)
    return config, config_file

def prompt_config(msg, key):
    """
    Ensure a value exists in the botconfig.json. If not, prompt the bot owner to input via the console.

    Args:
        msg (str): The message to display when prompting for input.
        key (str): The key to look for in the config file.
    """
    config, config_file = load_config()
    if key not in config:
        config[key] = input(msg)
        with config_file.open("w+") as f:
            json.dump(config, f, indent=4)

# Pagination System for Embeds
async def paginate_embed(bot: discord.Client,
                         interaction: discord.Interaction,
                         embed: discord.Embed,
                         population_func,
                         end: int,
                         begin: int = 1,
                         page=1):
    """
    Paginate through embeds.

    Args:
        bot (discord.Client): The Discord bot instance.
        interaction (discord.Interaction): The interaction that triggered the pagination.
        embed (discord.Embed): The initial embed to populate.
        population_func (function): A function to populate the embed for each page.
        end (int): The number of pages to paginate through.
        begin (int, optional): The starting page number. Defaults to 1.
        page (int, optional): The current page. Defaults to 1.
    """
    emotes = ["◀️", "▶️"]

    async def check_reaction(reaction, user):
        return await user == interaction.user and str(reaction.emoji) in emotes

    embed = await population_func(embed, page)
    message = await interaction.response.send_message(embed=embed)

    await message.add_reaction(emotes[0])
    await message.add_reaction(emotes[1])

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check_reaction)
            if user == bot.user:
                continue
            if str(reaction.emoji) == emotes[1] and page < end:
                page += 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
            elif str(reaction.emoji) == emotes[0] and page > begin:
                page -= 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

# Utility Functions
def solve(s: str) -> str:
    """
    Capitalizes each word in a string.

    Args:
        s (str): The string to capitalize.

    Returns:
        str: The capitalized string.
    """
    return ' '.join(word.capitalize() for word in s.split())

# Discord UI Component Handlers (SelectMenu & Button)
class SelectMenuHandler(ui.Select):
    """
    Handler for creating a SelectMenu in Discord with custom logic.
    """
    def __init__(self, options: List[SelectOption], select_user=None, coroutine=None, **kwargs):
        self.select_user = select_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(options=options, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.select_user is None or interaction.user == self.select_user:
            self.view.value = self.values[0]
            self.view_response = self.values[0]
            if self.coroutine:
                await self.coroutine(interaction, self.view)

class ButtonHandler(ui.Button):
    """
    Handler for adding a Button to a specific message and invoking a custom coroutine on click.
    """
    def __init__(self, label: str, button_user=None, coroutine=None, **kwargs):
        self.button_user = button_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.button_user is None or interaction.user == self.button_user:
            self.view_response = self.label if self.custom_id is None else self.custom_id
            if self.coroutine:
                await self.coroutine(interaction, self.view)

# Console Colors for Logging Output
class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Other Utility Classes
class Colors:
    red = discord.Color.red()

class Others:
    error_png = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png"

# Function to Calculate Level Based on Score
def calculate_level(score: int) -> Tuple[int, float]:
    """
    Calculate the user's level and progress to the next level based on their score.

    Args:
        score (int): The user's current score.

    Returns:
        Tuple[int, float]: The user's level and their progress percentage towards the next level.
    """
    level = int((score // 100) ** 0.5)
    next_level_score = (level + 1) ** 2 * 100
    prev_level_score = level ** 2 * 100
    progress = (score - prev_level_score) / (next_level_score - prev_level_score)
    return level, progress, next_level_score

def get_user_rank(server_id, user_id):
    """
    Get the rank of a user based on their score in a specific server.
    """
    query = (database.ServerScores
             .select(database.ServerScores.DiscordLongID)
             .where(database.ServerScores.ServerID == str(server_id))
             .order_by(database.ServerScores.Score.desc()))  # Order by score (high to low)

    # Find the user's position in the ranking
    rank = 1
    for entry in query:
        if entry.DiscordLongID == str(user_id):
            return rank  # Return the rank of the user
        rank += 1

    return None  # If user is not found