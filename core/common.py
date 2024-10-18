import asyncio
import json
import os
import random
from typing import Tuple, Union, List
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Importing discord modules
import discord
from discord import ButtonStyle, ui, SelectOption

# Importing core modules
from core import database
from core.logging_module import get_log

# Setting up logger
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

config, config_file = load_config()

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
    def __init__(self, label: str, button_user=None, coroutine=None, **kwargs):
        self.button_user = button_user
        self.coroutine = coroutine
        self.view_response = None
        super().__init__(label=label, **kwargs)  # Pass the remaining kwargs to the parent class

    async def callback(self, interaction: discord.Interaction):
        # Check if the interaction is from the correct user
        if self.button_user is None or interaction.user == self.button_user:
            self.view_response = self.label if self.custom_id is None else self.custom_id
            if self.coroutine:
                await self.coroutine(interaction, self.view)
        else:
            _log.warning(f"Unauthorized button interaction by {interaction.user}")
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)


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


def return_applyfornewrealm_modal(
    bot,
    realm_name: str,
    type_of_realm: str,
    emoji: str,
    member_count: str,
    community_duration: str,
    world_duration: str,
    reset_schedule: str
):
    class ApplyForNewRealmForm(ui.Modal, title="Realm Application"):
        def __init__(self):
            super().__init__(timeout=None)
            self.bot = bot
            self.realm_name = realm_name
            self.type_of_realm = type_of_realm
            self.emoji = emoji
            self.member_count = member_count
            self.community_duration = community_duration
            self.world_duration = world_duration
            self.reset_schedule = reset_schedule

            # Define form inputs
            self.short_description = ui.TextInput(
                label="Short Description",
                style=discord.TextStyle.short,
                placeholder="Short description of the realm",
                required=True
            )

            self.long_description = ui.TextInput(
                label="Long Description",
                style=discord.TextStyle.long,
                placeholder="Long description of the realm",
                required=True
            )

            self.application_process = ui.TextInput(
                label="Application Process",
                style=discord.TextStyle.long,
                placeholder="Application process for the realm",
                required=True
            )

            self.foreseeable_future = ui.TextInput(
                label="Foreseeable Future",
                style=discord.TextStyle.long,
                placeholder="Will your Realm/Server have the ability to continue for the foreseeable future?",
                required=True
            )

            self.admin_team = ui.TextInput(
                label="Admin Team",
                style=discord.TextStyle.long,
                placeholder="Who is on your admin team and how long have they been with you?",
                required=True
            )

        async def on_submit(self, interaction: discord.Interaction):
            try:
                await self.save_realm_application(interaction)
                embed = self.create_application_embed(interaction.user, interaction.guild)
                log_channel = self.bot.get_channel(config['realmChannelResponse'])
                admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

                # Send embed to the log channel
                await log_channel.send(content=admin_role.mention, embed=embed)

                # Confirmation response to the user
                await interaction.response.send_message("Realm application submitted successfully!", ephemeral=True)

            except Exception as e:
                _log.error(f"Error submitting realm application: {e}")
                await interaction.response.send_message("An error occurred while submitting your application.", ephemeral=True)

        async def save_realm_application(self, interaction: discord.Interaction):
            """Save the realm application to the database."""
            q = database.RealmApplications.create(
                discord_id=interaction.user.id,
                realm_name=self.realm_name,
                type_of_realm=self.type_of_realm,
                emoji=self.emoji,
                member_count=self.member_count,
                realm_age=self.community_duration,
                world_age=self.world_duration,
                reset_schedule=self.reset_schedule,
                short_desc=self.short_description.value,
                long_desc=self.long_description.value,
                application_process=self.application_process.value,
                foreseeable_future=self.foreseeable_future.value,
                admin_team=self.admin_team.value
            )
            q.save()

        def create_application_embed(self, user, guild):
            """Create the embed message for the application."""
            embed = discord.Embed(
                title="Realm Application",
                description=f"__**Realm Owner:**__\n{user.mention}\n============================================",
                color=0xb10d9f
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png"
            )
            embed.add_field(name="__**Realm Name**__", value=self.realm_name, inline=True)
            embed.add_field(name="__**Realm or Server?**__", value=self.type_of_realm, inline=True)
            embed.add_field(name="__**Emoji**__", value=self.emoji, inline=True)
            embed.add_field(name="__**Short Description**__", value=self.short_description.value, inline=False)
            embed.add_field(name="__**Long Description**__", value=self.long_description.value, inline=False)
            embed.add_field(name="__**Application Process**__", value=self.application_process.value, inline=False)
            embed.add_field(name="__**Current Member Count**__", value=self.member_count, inline=True)
            embed.add_field(name="__**Age of Community**__", value=self.community_duration, inline=True)
            embed.add_field(name="__**Age of Current World**__", value=self.world_duration, inline=True)
            embed.add_field(name="__**Reset Schedule**__", value=self.reset_schedule, inline=True)
            embed.add_field(name="__**Foreseeable Future**__", value=self.foreseeable_future.value, inline=True)
            embed.add_field(name="__**Admin Team**__", value=self.admin_team.value, inline=False)
            embed.add_field(name="__**Reaction Codes**__", value="React with 💚 for Approved, 💛 for More Time, ❤️ for Rejected", inline=False)
            embed.set_footer(text=f"Realm Application #{self.realm_name} | Submitted on {datetime.now().strftime('%Y-%m-%d')}")
            return embed

    return ApplyForNewRealmForm()

