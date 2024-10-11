import discord
from discord import app_commands
from discord.ext import commands
from core.checks import (
    slash_is_bot_admin_2,
    slash_is_bot_admin_3,
    slash_is_bot_admin_4,
    slash_is_bot_admin,
)
from core.logging_module import get_log

_log = get_log(__name__)


class AdminHelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help_admin",
        description="Shows admin-only commands grouped by permission level.",
    )
    @is_botAdmin  # Only admins with permit level 1 or higher can use this
    async def help_admin(self, interaction: discord.Interaction):
        try:
            _log.info(f"{interaction.user} requested the admin help command.")

            # Group commands based on their check levels
            admin_level_1_cmds = []
            admin_level_2_cmds = []
            admin_level_3_cmds = []
            admin_level_4_cmds = []

            for cmd in self.bot.tree.walk_commands():
                if any(c.name == "slash_is_bot_admin" for c in cmd.checks):
                    admin_level_1_cmds.append(cmd)
                elif any(c.name == "slash_is_bot_admin_2" for c in cmd.checks):
                    admin_level_2_cmds.append(cmd)
                elif any(c.name == "slash_is_bot_admin_3" for c in cmd.checks):
                    admin_level_3_cmds.append(cmd)
                elif any(c.name == "slash_is_bot_admin_4" for c in cmd.checks):
                    admin_level_4_cmds.append(cmd)

            embed = discord.Embed(
                title="Admin Commands",
                description="These are the available admin commands based on their permission levels.",
                color=discord.Color.purple(),
            )

            # Populate commands for each permit level
            if admin_level_4_cmds:
                embed.add_field(
                    name="Permit Level 4 - Owners:",
                    value="\n".join(
                        [
                            f"/{cmd.name} - {cmd.description}"
                            for cmd in admin_level_4_cmds
                        ]
                    ),
                    inline=False,
                )
            if admin_level_3_cmds:
                embed.add_field(
                    name="Permit Level 3 - Bot Managers:",
                    value="\n".join(
                        [
                            f"/{cmd.name} - {cmd.description}"
                            for cmd in admin_level_3_cmds
                        ]
                    ),
                    inline=False,
                )
            if admin_level_2_cmds:
                embed.add_field(
                    name="Permit Level 2 - Administrators:",
                    value="\n".join(
                        [
                            f"/{cmd.name} - {cmd.description}"
                            for cmd in admin_level_2_cmds
                        ]
                    ),
                    inline=False,
                )
            if admin_level_1_cmds:
                embed.add_field(
                    name="Permit Level 1 - Moderators:",
                    value="\n".join(
                        [
                            f"/{cmd.name} - {cmd.description}"
                            for cmd in admin_level_1_cmds
                        ]
                    ),
                    inline=False,
                )

            if not (
                admin_level_1_cmds
                or admin_level_2_cmds
                or admin_level_3_cmds
                or admin_level_4_cmds
            ):
                embed.description = "No admin commands found."

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error in help_admin command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the admin commands.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminHelpCMD(bot))
