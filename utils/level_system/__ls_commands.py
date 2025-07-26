# utils/level_system/__ls_commands.py

import discord
from discord.ext import commands
from discord import app_commands

from utils.database import __database as database
from utils.admin.admin_core.__admin_commands import has_admin_level
from utils.admin.bot_management.__bm_logic import config
from utils.helpers.__logging_module import get_log
from .__ls_logic import create_and_order_roles, sync_tatsu_score_for_user

from .__ls_views import LeaderboardView  # Add this import at the top

_log = get_log(__name__)


class LevelSystemCommands(commands.GroupCog, name="levels"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup", description="Create and organize leveled roles for this server."
    )
    @has_admin_level(3)
    async def setup_roles(self, interaction: discord.Interaction):
        """Creates roles from the level chart and inserts them into the database."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        _log.info(
            f"{interaction.user} initiated level role setup in {guild.name} ({guild.id})"
        )

        try:
            await create_and_order_roles(guild)
            await interaction.response.send_message(
                "✅ Leveled roles have been set up."
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage roles.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Error setting up roles: {e}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "❌ An unexpected error occurred.", ephemeral=True
            )
            _log.exception(f"Unexpected error during setup in {guild.name}: {e}")

    @app_commands.command(
        name="sync_tatsu",
        description="Sync scores from Tatsu for all users (MRP guild only).",
    )
    async def sync_tatsu_scores(self, interaction: discord.Interaction):
        """Fetches current Tatsu XP and updates local ServerScores for all users."""
        await interaction.response.defer(ephemeral=True)

        MRPguild_id = config.get("MRP")
        if interaction.guild.id != MRPguild_id:
            await interaction.followup.send(
                "This command is restricted to the MRP guild.", ephemeral=True
            )
            return

        members = [m for m in interaction.guild.members if not m.bot]
        _log.info(
            f"Starting Tatsu sync for {len(members)} members in {interaction.guild.name}"
        )

        for member in members:
            await sync_tatsu_score_for_user(
                self.bot,
                guild_id=member.guild.id,
                user_id=member.id,
                user_name=member.name,
            )

        await interaction.followup.send("✅ Tatsu scores updated.", ephemeral=True)

    @app_commands.command(
        name="leaderboard",
        description="View the top XP earners in this server (paginated).",
    )
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        top_scores = (
            database.ServerScores.select()
            .where(database.ServerScores.ServerID == str(interaction.guild.id))
            .order_by(database.ServerScores.Score.desc())
        )

        entries = list(top_scores)
        if not entries:
            await interaction.followup.send("No users with XP found for this server.")
            return

        view = LeaderboardView(interaction, entries)
        view.update_buttons()

        await interaction.followup.send(embed=view.get_embed(), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelSystemCommands(bot))
    _log.info("🛠️ LevelSystemCommands slash group loaded.")
