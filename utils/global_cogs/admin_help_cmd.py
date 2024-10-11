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
    @slash_is_bot_admin  # Only admins with permit level 1 or higher can use this
    async def help_admin(self, interaction: discord.Interaction):
        try:
            _log.info(f"{interaction.user} requested the admin help command.")

            # Group commands based on their check levels
            admin_level_1_cmds = []
            admin_level_2_cmds = []
            admin_level_3_cmds = []
            admin_level_4_cmds = []

            # Helper function to collect commands
            def collect_commands(cmds):
                for cmd in cmds:
                    _log.debug(
                        f"Checking command: {cmd.name}"
                    )  # Log the command being processed
                    if isinstance(cmd, app_commands.Command):
                        # Check the command's checks using __name__
                        check_names = [c.__name__ for c in cmd.checks]

                        if "slash_is_bot_admin" in check_names:
                            admin_level_1_cmds.append(cmd)
                        elif "slash_is_bot_admin_2" in check_names:
                            admin_level_2_cmds.append(cmd)
                        elif "slash_is_bot_admin_3" in check_names:
                            admin_level_3_cmds.append(cmd)
                        elif "slash_is_bot_admin_4" in check_names:
                            admin_level_4_cmds.append(cmd)
                    elif isinstance(cmd, app_commands.Group):
                        # Recursively collect commands from groups
                        collect_commands(cmd.commands)

            # Collect commands from the bot
            collect_commands(self.bot.tree.walk_commands())

            # Log the collected commands
            _log.debug(f"Admin Level 1 Commands: {admin_level_1_cmds}")
            _log.debug(f"Admin Level 2 Commands: {admin_level_2_cmds}")
            _log.debug(f"Admin Level 3 Commands: {admin_level_3_cmds}")
            _log.debug(f"Admin Level 4 Commands: {admin_level_4_cmds}")

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
                    )
                    or "No commands available",
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
                    )
                    or "No commands available",
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
                    )
                    or "No commands available",
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
                    )
                    or "No commands available",
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
