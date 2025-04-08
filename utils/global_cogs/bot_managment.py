import subprocess
import sys
from pathlib import Path
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from core.logging_module import get_log
import json

from core.common import get_bot_data_for_server
from core import database
from core.checks import has_admin_level

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
                        int(admin.discordID)
                    ) or await self.bot.fetch_user(int(admin.discordID))
                    admin_list.append(f"`{user.name}` -> `{user.id}`")
                except Exception as e:
                    _log.error(f"Error fetching user with ID {admin.discordID}: {e}")
                    continue
            return admin_list or ["None"]
        finally:
            if not database.db.is_closed():
                database.db.close()

    @PM.command(description="Lists all permit levels and users.")
    @has_admin_level(1)
    async def list(self, interaction: discord.Interaction):
        try:
            _log.info(f"{interaction.user} requested the permit list.")
            levels = [1, 2, 3, 4]
            level_names = ["Moderators", "Administrators", "Bot Manager", "Owners"]
            embeds = []

            for level, name in zip(levels, level_names):
                admin_list = await self.fetch_admins_by_level(level)
                embeds.append(f"**Permit {level}: {name}**\n" + "\n".join(admin_list))

            embed = discord.Embed(
                title="Bot Administrators",
                description="\n\n".join(embeds),
                color=discord.Color.green(),
            )
            embed.set_footer(
                text="Only Owners/Permit 4's can modify Bot Administrators. | Permit 4 is the HIGHEST Level"
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error listing permit levels: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while retrieving the permit list.", ephemeral=True
            )

    @PM.command(description="Remove a user from the Bot Administrators list.")
    @app_commands.describe(user="The user to remove from the Bot Administrators list.")
    @has_admin_level(4)
    async def remove(self, interaction: discord.Interaction, user: discord.User):
        try:
            _log.info(f"{interaction.user} is attempting to remove {user}.")
            database.db.connect(reuse_if_open=True)

            query = database.Administrators.get_or_none(
                database.Administrators.discordID == str(user.id)
            )

            if query:
                query.delete_instance()
                embed = discord.Embed(
                    title="Successfully Removed User!",
                    description=f"{user.name} has been removed from the database!",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="Invalid User!",
                    description="No record found for the provided user.",
                    color=discord.Color.red(),
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            _log.error(f"Error removing {user} from the database: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while removing the user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()

    @PM.command(description="Add a user to the Bot Administrators list.")
    @app_commands.describe(
        user="The user to add to the Bot Administrators list.",
        level="Permit level to assign.",
    )
    @has_admin_level(4)
    async def add(
        self, interaction: discord.Interaction, user: discord.User, level: int
    ):
        if level not in (1, 2, 3, 4):
            await interaction.response.send_message(
                "Permit level must be 1–4.", ephemeral=True
            )
            return

        try:
            _log.info(f"{interaction.user} is adding {user} at permit level {level}.")
            database.db.connect(reuse_if_open=True)

            query = database.Administrators.get_or_none(
                database.Administrators.discordID == str(user.id)
            )

            if query:
                query.TierLevel = level
                query.discord_name = user.name
                query.save()
                embed = discord.Embed(
                    title="Successfully Updated User!",
                    description=f"{user.name}'s permit level updated to `{level}`.",
                    color=discord.Color.gold(),
                )
            else:
                database.Administrators.create(
                    discordID=str(user.id), discord_name=user.name, TierLevel=level
                )
                embed = discord.Embed(
                    title="Successfully Added User!",
                    description=f"{user.name} added with permit level `{level}`.",
                    color=discord.Color.gold(),
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error adding/updating {user.name}: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while adding/updating the user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()

    BC = app_commands.Group(
        name="configure",
        description="Configure the bot's settings.",
    )

    @BC.command(
        name="set_cooldown",
        description="Set the server score cooldown time (in seconds).",
    )
    @has_admin_level(3)
    async def set_cooldown(self, interaction: discord.Interaction, cooldown: int):
        bot_data = await get_bot_data_for_server(str(interaction.guild.id))
        if bot_data:
            bot_data.cooldown_time = cooldown
            bot_data.save()
            await interaction.response.send_message(
                f"Cooldown time updated to {cooldown} seconds."
            )
        else:
            await interaction.response.send_message("BotData not found.")

    @BC.command(
        name="set_points", description="Set points per message for server score."
    )
    @has_admin_level(3)
    async def set_points(self, interaction: discord.Interaction, points: int):
        bot_data = await get_bot_data_for_server(str(interaction.guild.id))
        if bot_data:
            bot_data.points_per_message = points
            bot_data.save()
            await interaction.response.send_message(
                f"Points per message updated to {points}."
            )
        else:
            await interaction.response.send_message("BotData not found.")

    @BC.command(
        name="add_blocked_channel",
        description="Add a channel to the blocked list.",
    )
    @has_admin_level(3)
    async def add_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = await get_bot_data_for_server(str(interaction.guild.id))
        if not bot_data:
            await interaction.response.send_message("BotData not found.")
            return

        try:
            blocked_channels = json.loads(bot_data.blocked_channels or "[]")
            blocked_channels = [str(c) for c in blocked_channels]

            if str(channel.id) not in blocked_channels:
                blocked_channels.append(str(channel.id))
                bot_data.blocked_channels = json.dumps(blocked_channels)
                bot_data.save()
                await interaction.response.send_message(
                    f"Channel {channel.mention} added to the blocked list."
                )
            else:
                await interaction.response.send_message(
                    f"Channel {channel.mention} is already blocked."
                )
        except Exception as e:
            _log.error(f"Error blocking channel: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to update blocked channel list.", ephemeral=True
            )

    @BC.command(
        name="remove_blocked_channel",
        description="Remove a channel from the blocked list.",
    )
    @has_admin_level(3)
    async def remove_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = await get_bot_data_for_server(str(interaction.guild.id))
        if not bot_data:
            await interaction.response.send_message("BotData not found.")
            return

        blocked_channels = bot_data.get_blocked_channels()
        if channel.id in blocked_channels:
            blocked_channels.remove(channel.id)
            bot_data.set_blocked_channels(blocked_channels)
            bot_data.save()
            await interaction.response.send_message(
                f"Channel {channel.mention} has been unblocked."
            )
        else:
            await interaction.response.send_message(
                f"Channel {channel.mention} is not in the blocked list."
            )

    @BC.command(name="view", description="View current bot config.")
    @has_admin_level(3)
    async def view_config(self, interaction: discord.Interaction):
        bot_data = await get_bot_data_for_server(str(interaction.guild.id))

        if not bot_data:
            await interaction.response.send_message(
                "BotData not found.", ephemeral=True
            )
            return

        try:
            blocked_channel_ids = bot_data.get_blocked_channels()
        except Exception as e:
            _log.error(f"Failed to parse blocked_channels: {e}")
            blocked_channel_ids = []

        blocked_mentions = []
        for cid in blocked_channel_ids:
            channel = interaction.guild.get_channel(int(cid))
            blocked_mentions.append(channel.mention if channel else f"`{cid}`")

        embed = discord.Embed(
            title=f"🔧 Bot Configuration: {interaction.guild.name}",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="⏱️ Cooldown Time",
            value=f"{bot_data.cooldown_time} seconds",
            inline=True,
        )
        embed.add_field(
            name="🏅 Points per Message",
            value=str(bot_data.points_per_message),
            inline=True,
        )
        embed.add_field(
            name="🚫 Blocked Channels",
            value=(
                "\n".join(blocked_mentions)
                if blocked_mentions
                else "*None configured.*"
            ),
            inline=False,
        )
        embed.set_footer(text="Use /configure to update these settings.")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(CoreBotConfig(bot))
    _log.info("CoreBotConfig Cog has been set up and is ready.")
