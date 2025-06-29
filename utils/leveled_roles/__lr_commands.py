import discord
from discord.ext import commands
from discord import app_commands

from utils.admin.admin_core.__admin_commands import has_admin_level
from utils.leveled_roles.__lr_logic import create_and_order_roles
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class LeveledRolesSetup(commands.GroupCog, name="leveledroles"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup", description="Create and order leveled roles for this server."
    )
    @has_admin_level(3)
    async def setup_roles(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        _log.info(f"{interaction.user} started role setup in {guild.name} ({guild.id})")

        try:
            await create_and_order_roles(guild)
            await interaction.response.send_message(
                "✅ Leveled roles have been set up."
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to manage roles.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Error setting up roles: {e}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "An unexpected error occurred.", ephemeral=True
            )
            _log.exception(f"Unexpected error during role setup in {guild.name}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(LeveledRolesSetup(bot))
    _log.info("✅ LeveledRolesSetup slash group loaded.")
