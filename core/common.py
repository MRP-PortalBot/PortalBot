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
        try:
            with config_file.open("w+") as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            _log.error(f"Error writing to config file: {e}")
            raise e

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
    def __init__(self, options: List[SelectOption], select_user: Union[discord.User, None] = None, coroutine: callable = None, **kwargs):
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
    def __init__(self, label: str, allowed_user: discord.User = None, action: callable = None, **kwargs):
        """
        Initialize the button with the specified label and parameters.

        Args:
            label (str): The label of the button.
            allowed_user (discord.User, optional): The user who is allowed to interact with the button. Defaults to None.
            action (callable, optional): The coroutine function to be called when the button is clicked. Defaults to None.
        """
        self.allowed_user = allowed_user
        self.action = action
        self.view_response = None
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        """
        The callback function triggered when the button is clicked.

        Args:
            interaction (discord.Interaction): The interaction object for the button press.
        """
        try:
            if self.allowed_user is None or interaction.user == self.allowed_user:
                # Capture the button response based on its label or custom ID
                self.view_response = self.label if self.custom_id is None else self.custom_id
                if self.action:
                    # Invoke the provided coroutine (action)
                    await self.action(interaction, self.view)
            else:
                _log.warning(f"Unauthorized button interaction by {interaction.user}")
                await interaction.response.send_message(
                    "You are not authorized to use this button.", ephemeral=True
                )
        except Exception as e:
            _log.error(f"Error in ButtonHandler callback: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your action.", ephemeral=True
            )

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
    
class Me:
    TracebackChannel = 797193549992165456
    
def get_bot_data_id():
    load_dotenv()
    os.getenv("bot_type")
    key_value = {
        "STABLE": 1,
        "BETA": 2
    }

    return key_value[os.getenv("bot_type")]

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
    prev_level_score = level ** 2 * 100
    progress = (score - prev_level_score) / (next_level_score - prev_level_score)
    return level, progress, next_level_score

def get_user_rank(server_id, user_id):
    """
    Get the rank of a user based on their score in a specific server.

    Returns:
        int: The rank of the user, or None if not found.
    """
    try:
        query = (database.ServerScores
                 .select(database.ServerScores.DiscordLongID)
                 .where(database.ServerScores.ServerID == str(server_id))
                 .order_by(database.ServerScores.Score.desc()))  # Order by score (high to low)

        rank = 1
        for entry in query:
            if entry.DiscordLongID == str(user_id):
                return rank  # Return the rank of the user
            rank += 1
    except Exception as e:
        _log.error(f"Error retrieving user rank: {e}")
        return None

    return None  # If user is not found
