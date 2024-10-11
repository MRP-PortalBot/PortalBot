import discord
from discord import app_commands
from discord.ext import commands
from core.checks import (
    slash_is_bot_admin_1,
    slash_is_bot_admin_2,
    slash_is_bot_admin_3,
    slash_is_bot_admin_4,
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
    @slash_is_bot_admin_1  # Only admins with permit level 1 or higher can use this
    async def help_admin(self, interaction: discord.Interaction):
        try:
            _log.info(f"{interaction.user} requested the admin help command.")

            # Create lists to group commands based on permission levels
            admin_level_1_cmds = []
            admin_level_2_cmds = []
            admin_level_3_cmds = []
            admin_level_4_cmds = []

            # Map known check function names to admin level lists
            check_level_map = {
                "slash_is_bot_admin_4": admin_level_4_cmds,
                "slash_is_bot_admin_3": admin_level_3_cmds,
                "slash_is_bot_admin_2": admin_level_2_cmds,
                "slash_is_bot_admin_1": admin_level_1_cmds,
            }

            # Iterate over all app commands in the bot
            for command in self.bot.tree.walk_commands():
                _log.debug(f"Checking command: {command.name}")

                # Check the command's checks to categorize by permission level
                command_checks = getattr(command, "checks", [])
                _log.debug(f"Command checks: {command_checks}")

                assigned = False
                for check in command_checks:
                    check_name = check.__qualname__
                    _log.debug(f"Checking check: {check_name}")

                    # If it's one of the known check levels, assign it
                    if check_name in check_level_map:
                        check_level_map[check_name].append(
                            f"/{command.name} - {command.description}"
                        )
                        assigned = True
                        break  # Exit loop once assigned to a level

                if not assigned:
                    _log.debug(
                        f"Command {command.name} does not have a recognized admin check."
                    )

            # Create the embed for displaying the commands
            embed = discord.Embed(
                title="Admin Commands",
                description="These are the available admin commands grouped by permission level.",
                color=discord.Color.purple(),
            )

            # Add fields to the embed based on each admin level
            if admin_level_4_cmds:
                embed.add_field(
                    name="Permit Level 4 - Owners:",
                    value="\n".join(admin_level_4_cmds),
                    inline=False,
                )
            if admin_level_3_cmds:
                embed.add_field(
                    name="Permit Level 3 - Bot Managers:",
                    value="\n".join(admin_level_3_cmds),
                    inline=False,
                )
            if admin_level_2_cmds:
                embed.add_field(
                    name="Permit Level 2 - Administrators:",
                    value="\n".join(admin_level_2_cmds),
                    inline=False,
                )
            if admin_level_1_cmds:
                embed.add_field(
                    name="Permit Level 1 - Moderators:",
                    value="\n".join(admin_level_1_cmds),
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
            _log.error(f"Error in help_admin command: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while fetching the admin commands.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminHelpCMD(bot))
