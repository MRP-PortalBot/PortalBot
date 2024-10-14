import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
from core import database
from core.checks import slash_is_bot_admin_4
from core.logging_module import get_log

# Initialize logging
_log = get_log(__name__)


class AdminCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("AdminCMD: Cog Loaded!")

    # Grouping all admin-level commands
    Admin = app_commands.Group(name="admin", description="Administrative commands.")

    # Command to request the database file
    @Admin.command(
        name="requestdb", description="Request the database file for manual inspection"
    )
    @slash_is_bot_admin_4
    async def requestdb(self, interaction: discord.Interaction):
        """Request the database file for manual inspection."""
        try:
            db = Path("data.db")
            _log.info(f"{interaction.user} has requested the database file.")

            if not db.exists():
                _log.warning("Database file does not exist.")
                await interaction.response.send_message(
                    "Database does not exist yet.", ephemeral=True
                )
                return

            with db.open(mode="rb") as f:
                file = discord.File(f, "database.db")
                await interaction.user.send(file=file)

            await interaction.response.send_message(
                "Database file sent to your DMs.", ephemeral=True
            )
            _log.info(f"Database file successfully sent to {interaction.user}.")

        except Exception as e:
            _log.error(f"Error in sending the database file: {e}")
            await interaction.response.send_message(
                "An error occurred while sending the database file.", ephemeral=True
            )

    # Command to delete the database file
    @Admin.command(name="deletedb", description="Delete the database file")
    @slash_is_bot_admin_4
    async def deletedb(self, interaction: discord.Interaction):
        """Delete the database file."""
        try:
            _log.info(f"{interaction.user} is attempting to delete the database file.")

            if not database.db.is_closed():
                _log.warning("Database file is currently in use and cannot be deleted.")
                await interaction.response.send_message(
                    "Cannot delete; database is currently in use.", ephemeral=True
                )
                return

            db = Path("data.db")
            if not db.exists():
                _log.warning("Database file does not exist.")
                await interaction.response.send_message(
                    "Database file does not exist.", ephemeral=True
                )
                return

            db.unlink()
            await interaction.response.send_message(
                "Database file has been deleted.", ephemeral=True
            )
            _log.info(f"Database file successfully deleted by {interaction.user}.")

        except Exception as e:
            _log.error(f"Error in deleting the database file: {e}")
            await interaction.response.send_message(
                "An error occurred while deleting the database file.", ephemeral=True
            )

    # Command to replace the database file with an attachment
    @Admin.command(
        name="replacedb", description="Replace the database file with attachment"
    )
    @slash_is_bot_admin_4
    async def replacedb(self, interaction: discord.Interaction):
        """Replace the database file with an attachment."""
        try:
            _log.info(f"{interaction.user} is attempting to replace the database file.")

            if not database.db.is_closed():
                _log.warning(
                    "Database file is currently in use and cannot be replaced."
                )
                await interaction.response.send_message(
                    "Cannot replace; database is currently in use.", ephemeral=True
                )
                return

            if not interaction.message.attachments:
                _log.warning(
                    f"{interaction.user} attempted to replace the database file but no file was attached."
                )
                await interaction.response.send_message(
                    "No file attached for replacement.", ephemeral=True
                )
                return

            db = Path("data.db")
            if db.exists():
                db.unlink()  # Delete the existing database file
                _log.info("Existing database file deleted.")

            # Save the new database file from attachment
            with db.open(mode="wb+") as f:
                await interaction.message.attachments[0].save(f)

            await interaction.response.send_message(
                "Database file replaced.", ephemeral=True
            )
            _log.info(f"Database file successfully replaced by {interaction.user}.")

        except Exception as e:
            _log.error(f"Error in replacing the database file: {e}")
            await interaction.response.send_message(
                "An error occurred while replacing the database file.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminCMD(bot))
    _log.info("AdminCMD Cog has been set up and is ready.")
