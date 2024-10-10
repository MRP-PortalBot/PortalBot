import logging
import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
from core import database
from core.checks import slash_is_bot_admin_4

logger = logging.getLogger(__name__)


class AdminCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("AdminCMD: Cog Loaded!")

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
            if not db.exists():
                await interaction.response.send_message("Database does not exist yet.")
                return
            with db.open(mode="rb") as f:
                file = discord.File(f, "database.db")
                await interaction.user.send(file=file)
            await interaction.response.send_message(
                "Database file sent to your DMs.", ephemeral=True
            )
            logger.info(f"Database file sent to {interaction.user}")
        except Exception as e:
            logger.error(f"Error in sending the database file: {e}")
            await interaction.response.send_message(
                "An error occurred while sending the database file.", ephemeral=True
            )

    # Command to delete the database file
    @Admin.command(name="deletedb", description="Delete the database file")
    @slash_is_bot_admin_4
    async def deletedb(self, interaction: discord.Interaction):
        """Delete the database file."""
        try:
            if database.db.is_closed():
                db = Path("data.db")
                if not db.exists():
                    await interaction.response.send_message(
                        "Database file does not exist."
                    )
                    return
                db.unlink()
                await interaction.response.send_message(
                    "Database file has been deleted."
                )
                logger.info(f"Database file deleted by {interaction.user}")
            else:
                await interaction.response.send_message(
                    "Cannot delete; database is currently in use."
                )
        except Exception as e:
            logger.error(f"Error in deleting the database file: {e}")
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
            if database.db.is_closed():
                db = Path("data.db")
                if db.exists():
                    db.unlink()
                with db.open(mode="wb+") as f:
                    await interaction.message.attachments[0].save(f)
                await interaction.response.send_message("Database file replaced.")
                logger.info(f"Database file replaced by {interaction.user}")
            else:
                await interaction.response.send_message(
                    "Cannot replace; database is currently in use."
                )
        except Exception as e:
            logger.error(f"Error in replacing the database file: {e}")
            await interaction.response.send_message(
                "An error occurred while replacing the database file.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminCMD(bot))
