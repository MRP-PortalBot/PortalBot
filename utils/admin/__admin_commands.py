# utils/admin/__admin_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
from core import database
from core.checks import has_admin_level
from core.logging_module import get_log
from core.common import (
    get_cached_bot_data,
    get_bot_data_for_server,
    refresh_bot_data_cache,
)

_log = get_log(__name__)


class AdminCommands(commands.GroupCog, name="admin"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="requestdb", description="Request the database file for manual inspection."
    )
    @has_admin_level(4)
    async def requestdb(self, interaction: discord.Interaction):
        try:
            db_file = Path("data.db")
            if not db_file.exists():
                await interaction.response.send_message("Database does not exist yet.", ephemeral=True)
                return

            with db_file.open("rb") as f:
                file = discord.File(f, filename="database.db")
                try:
                    await interaction.user.send(file=file)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "I couldn't DM you the file. Please enable DMs.", ephemeral=True
                    )
                    return

            await interaction.response.send_message("Database file sent to your DMs.", ephemeral=True)
            _log.info(f"{interaction.user} requested and received database file.")

        except Exception as e:
            _log.error(f"requestdb error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to send database file.", ephemeral=True)

    @app_commands.command(name="deletedb", description="Delete the database file.")
    @has_admin_level(4)
    async def deletedb(self, interaction: discord.Interaction):
        try:
            if not database.db.is_closed():
                await interaction.response.send_message("Database is in use. Cannot delete.", ephemeral=True)
                return

            db_file = Path("data.db")
            if db_file.exists():
                db_file.unlink()
                await interaction.response.send_message("Database file deleted.", ephemeral=True)
                _log.info(f"{interaction.user} deleted the database file.")
            else:
                await interaction.response.send_message("Database file does not exist.", ephemeral=True)

        except Exception as e:
            _log.error(f"deletedb error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to delete database file.", ephemeral=True)

    @app_commands.command(name="replacedb", description="Replace the database file via upload.")
    @has_admin_level(4)
    async def replacedb(self, interaction: discord.Interaction):
        try:
            if not database.db.is_closed():
                await interaction.response.send_message("Database is in use. Cannot replace.", ephemeral=True)
                return

            if not interaction.attachments:
                await interaction.response.send_message("Attach a `.db` file to replace.", ephemeral=True)
                return

            attachment = interaction.attachments[0]
            if not attachment.filename.endswith(".db"):
                await interaction.response.send_message("Only `.db` files are allowed.", ephemeral=True)
                return

            if attachment.size > 10 * 1024 * 1024:
                await interaction.response.send_message("File too large (10MB max).", ephemeral=True)
                return

            db_file = Path("data.db")
            if db_file.exists():
                db_file.unlink()

            with db_file.open("wb+") as f:
                await attachment.save(f)

            await interaction.response.send_message("Database replaced successfully.", ephemeral=True)
            _log.info(f"{interaction.user} replaced the database file.")

        except Exception as e:
            _log.error(f"replacedb error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to replace database file.", ephemeral=True)

    @app_commands.command(name="view", description="View cached bot data for this server.")
    @has_admin_level(2)
    async def view_bot_cache(self, interaction: discord.Interaction):
        try:
            bot_data = get_cached_bot_data(interaction.guild.id)
            if not bot_data:
                await interaction.response.send_message("No bot data found for this server.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📊 Cached Bot Data",
                color=discord.Color.blurple(),
                description=f"Server ID: `{interaction.guild.id}`"
            )
            for field, value in bot_data.__data__.items():
                embed.add_field(name=field, value=str(value), inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            _log.error(f"view_bot_cache error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to view cache.", ephemeral=True)

    @app_commands.command(name="update-cache", description="Refresh cache from database.")
    @has_admin_level(4)
    async def update_cache(self, interaction: discord.Interaction):
        try:
            get_bot_data_for_server(interaction.guild.id)
            await interaction.response.send_message("Cache refreshed from database.", ephemeral=True)
            _log.info(f"Cache refreshed for {interaction.guild.id}.")
        except Exception as e:
            _log.error(f"update_cache error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to update cache.", ephemeral=True)

    @app_commands.command(name="update_bot_data", description="Force-refresh cached bot data.")
    @has_admin_level(2)
    async def update_bot_data(self, interaction: discord.Interaction):
        try:
            refresh_bot_data_cache(interaction.guild.id)
            await interaction.response.send_message("Bot data cache updated.", ephemeral=True)
            _log.info(f"Bot data cache updated for {interaction.guild.id}.")
        except Exception as e:
            _log.error(f"update_bot_data error: {e}", exc_info=True)
            await interaction.response.send_message("Failed to update bot data.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
    _log.info("✅ AdminCommands cog loaded.")
