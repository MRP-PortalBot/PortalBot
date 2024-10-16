import subprocess
import sys
from pathlib import Path
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from core.logging_module import get_log

from core import database
from core.checks import (
    slash_is_bot_admin_2,
    slash_is_bot_admin_4,
    slash_is_bot_admin_3,
    slash_is_bot_admin_1,
)

# Load environment variables
load_dotenv()

# Logger setup
_log = get_log(__name__)


def get_extensions():
    extensions = ["jishaku"]
    for file in Path("utils").glob("**/*.py"):
        if "!" in file.name or "DEV" in file.name:
            continue
        extensions.append(str(file).replace("/", ".").replace(".py", ""))
    return extensions


class CoreBotConfig(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _log.info("CoreBotConfig cog initialized successfully.")

    PM = app_commands.Group(
        name="permit",
        description="Configure the bot's permit settings.",
    )

    async def fetch_admins_by_level(self, level: int):
        """Fetch administrators by level from the database."""
        try:
            _log.debug(f"Fetching administrators with permit level {level}")
            database.db.connect(reuse_if_open=True)
            query = database.Administrators.select().where(
                database.Administrators.TierLevel == level
            )
            admin_list = []
            for admin in query:
                try:
                    user = self.bot.get_user(
                        admin.discordID
                    ) or await self.bot.fetch_user(admin.discordID)
                    admin_list.append(f"`{user.name}` -> `{user.id}`")
                except Exception as e:
                    _log.error(f"Error fetching user with ID {admin.discordID}: {e}")
                    continue
            _log.debug(
                f"Fetched {len(admin_list)} administrators for permit level {level}"
            )
            return admin_list
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed after fetching admins.")

    @PM.command(description="Lists all permit levels and users.")
    @slash_is_bot_admin_1
    async def list(self, interaction: discord.Interaction):
        try:
            _log.info(f"{interaction.user} requested the permit list.")
            levels = [1, 2, 3, 4]
            level_names = ["Moderators", "Administrators", "Bot Manager", "Owners"]
            embeds = []

            for level, level_name in zip(levels, level_names):
                admin_list = await self.fetch_admins_by_level(level)
                if not admin_list:
                    admin_list = ["None"]
                embeds.append(
                    f"**Permit {level}: {level_name}**\n" + "\n".join(admin_list)
                )

            embed = discord.Embed(
                title="Bot Administrators",
                description="\n\n".join(embeds),
                color=discord.Color.green(),
            )
            embed.set_footer(
                text="Only Owners/Permit 4's can modify Bot Administrators. | Permit 4 is the HIGHEST Level"
            )
            await interaction.response.send_message(embed=embed)
            _log.info("Sent permit list successfully.")
        except Exception as e:
            _log.error(f"Error listing permit levels: {e}")
            await interaction.response.send_message(
                "An error occurred while retrieving the permit list.", ephemeral=True
            )

    @PM.command(description="Remove a user from the Bot Administrators list.")
    @app_commands.describe(user="The user to remove from the Bot Administrators list.")
    @slash_is_bot_admin_4
    async def remove(self, interaction: discord.Interaction, user: discord.User):
        try:
            _log.info(f"{interaction.user} is attempting to remove {user}.")
            database.db.connect(reuse_if_open=True)
            query = database.Administrators.get_or_none(
                database.Administrators.discordID == user.id
            )

            if query:
                query.delete_instance()
                embed = discord.Embed(
                    title="Successfully Removed User!",
                    description=f"{user.name} has been removed from the database!",
                    color=discord.Color.green(),
                )
                _log.info(
                    f"{user} was removed from the database by {interaction.user}."
                )
            else:
                embed = discord.Embed(
                    title="Invalid User!",
                    description="No record found for the provided user.",
                    color=discord.Color.red(),
                )
                _log.warning(
                    f"Failed to remove {user}, no record found in the database."
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            _log.error(f"Error removing {user} from the database: {e}")
            await interaction.response.send_message(
                "An error occurred while removing the user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed after removing user.")

    @PM.command(description="Add a user to the Bot Administrators list.")
    @app_commands.describe(
        user="The user to add to the Bot Administrators list.",
        level="Permit level to assign.",
    )
    @slash_is_bot_admin_4
    async def add(
        self, interaction: discord.Interaction, user: discord.User, level: int
    ):
        try:
            _log.info(
                f"{interaction.user} is attempting to add {user} with permit level {level}."
            )
            database.db.connect(reuse_if_open=True)

            query = database.Administrators.get_or_none(
                database.Administrators.discordID == user.id
            )

            if query:
                query.TierLevel = level
                query.discord_name = user.name
                query.save()
                _log.info(f"Updated permit level for {user.name} to {level}.")
                embed = discord.Embed(
                    title="Successfully Updated User!",
                    description=f"{user.name}'s permit level has been updated to `{level}`.",
                    color=discord.Color.gold(),
                )
            else:
                database.Administrators.create(
                    discordID=user.id, discord_name=user.name, TierLevel=level
                )
                _log.info(
                    f"Added {user.name} to the database with permit level {level}."
                )
                embed = discord.Embed(
                    title="Successfully Added User!",
                    description=f"{user.name} has been added with permit level `{level}`.",
                    color=discord.Color.gold(),
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(
                f"Error adding/updating {user.name} in the Bot Administrators list: {e}"
            )
            await interaction.response.send_message(
                "An error occurred while adding/updating the user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed after adding/updating user.")

    # Helper function to fetch bot data
    async def get_bot_data(self):
        return database.BotData.get_or_none(
            database.BotData.id == 1
        )  # Fetch the bot data row (assuming a single row for config)

    # Group for bot configuration commands
    BC = app_commands.Group(
        name="configure",
        description="Configure the bot's settings.",
    )

    # Command to set the cooldown time
    @BC.command(
        name="set_cooldown",
        description="Set the server score cooldown time (in seconds).",
    )
    @slash_is_bot_admin_3
    async def set_cooldown(self, interaction: discord.Interaction, cooldown: int):
        bot_data = await self.get_bot_data()
        if bot_data:
            bot_data.cooldown_time = cooldown
            bot_data.save()
            await interaction.response.send_message(
                f"Cooldown time updated to {cooldown} seconds."
            )
            _log.info(
                f"Cooldown time updated to {cooldown} seconds by {interaction.user}."
            )
        else:
            await interaction.response.send_message("BotData not found.")
            _log.error(
                f"BotData not found while setting cooldown by {interaction.user}."
            )

    # Command to set points per message
    @BC.command(
        name="set_points",
        description="Set the server score points per message, Set the min (max = min * 3).",
    )
    @slash_is_bot_admin_3
    async def set_points(self, interaction: discord.Interaction, points: int):
        bot_data = await self.get_bot_data()
        if bot_data:
            bot_data.points_per_message = points
            bot_data.save()
            await interaction.response.send_message(
                f"Points per message updated to {points}."
            )
            _log.info(f"Points per message updated to {points} by {interaction.user}.")
        else:
            await interaction.response.send_message("BotData not found.")
            _log.error(f"BotData not found while setting points by {interaction.user}.")

    # Command to add a blocked channel
    @BC.command(
        name="add_blocked_channel",
        description="Add a channel to the block list for server score.",
    )
    @slash_is_bot_admin_3
    async def add_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = await self.get_bot_data()
        if bot_data:
            blocked_channels = bot_data.get_blocked_channels()
            if channel.id not in blocked_channels:
                blocked_channels.append(channel.id)
                bot_data.set_blocked_channels(blocked_channels)
                bot_data.save()
                await interaction.response.send_message(
                    f"Channel {channel.mention} has been added to the blocked list."
                )
                _log.info(
                    f"Channel {channel.name} added to blocked list by {interaction.user}."
                )
            else:
                await interaction.response.send_message(
                    f"Channel {channel.mention} is already in the blocked list."
                )
        else:
            await interaction.response.send_message("BotData not found.")
            _log.error(
                f"BotData not found while adding blocked channel by {interaction.user}."
            )

    # Command to remove a blocked channel
    @BC.command(
        name="remove_blocked_channel",
        description="Remove a channel from the block list for server score.",
    )
    @slash_is_bot_admin_3
    async def remove_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = await self.get_bot_data()
        if bot_data:
            blocked_channels = bot_data.get_blocked_channels()
            if channel.id in blocked_channels:
                blocked_channels.remove(channel.id)
                bot_data.set_blocked_channels(blocked_channels)
                bot_data.save()
                await interaction.response.send_message(
                    f"Channel {channel.mention} has been removed from the blocked list."
                )
                _log.info(
                    f"Channel {channel.name} removed from blocked list by {interaction.user}."
                )
            else:
                await interaction.response.send_message(
                    f"Channel {channel.mention} is not in the blocked list."
                )
        else:
            await interaction.response.send_message("BotData not found.")
            _log.error(
                f"BotData not found while removing blocked channel by {interaction.user}."
            )


async def setup(bot):
    await bot.add_cog(CoreBotConfig(bot))
    _log.info("CoreBotConfig Cog has been set up and is ready.")
