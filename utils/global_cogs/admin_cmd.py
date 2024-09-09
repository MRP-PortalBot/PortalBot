import subprocess
from discord import app_commands
from discord.ext import commands
from typing import Literal
import discord

from core import database
from core.checks import (
    slash_is_bot_admin_2,
    slash_is_bot_admin_4,
    slash_is_bot_admin_3,
    slash_is_bot_admin,
)

load_dotenv()

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gitpull")
    @slash_is_bot_admin_2
    async def gitpull(
        self,
        interaction: discord.Interaction,
        mode: Literal["-a", "-c"] = "-a",  # Mode for action or cogs reload
        sync_commands: bool = False,       # Option to sync commands after pulling
    ) -> None:
        """
        Fetch and reset the bot's codebase from Git. Be careful: This can break things!
        """
        output = ""
        branch = "origin/main"

        # Step 1: Fetch the latest changes from the remote repository
        try:
            p = subprocess.run(
                ["git", "fetch", "--all"],
                text=True,
                capture_output=True,
                check=True,
            )
            output += p.stdout
        except subprocess.CalledProcessError as e:
            await interaction.response.send_message(
                f"⛔️ Unable to fetch the current repo header!\n**Error:**\n{e}"
            )
            return

        # Step 2: Reset the local repository to the specified branch
        try:
            p = subprocess.run(
                ["git", "reset", "--hard", branch],
                text=True,
                capture_output=True,
                check=True,
            )
            output += p.stdout
        except subprocess.CalledProcessError as e:
            await interaction.response.send_message(
                f"⛔️ Unable to apply changes!\n**Error:**\n{e}"
            )
            return

        # Step 3: Prepare the embed with shell output
        embed = discord.Embed(
            title="GitHub Local Reset",
            description=f"Local files changed to match {branch}",
            color=discord.Color.brand_green(),
        )
        embed.add_field(name="Shell Output", value=f"```shell\n$ {output}\n```")

        # Step 4: Handle the mode of operation (-a for action, -c for cogs reload)
        if mode == "-a":
            embed.set_footer(text="Attempting to restart the bot...")
        elif mode == "-c":
            embed.set_footer(text="Attempting to reload cogs...")

        await interaction.response.send_message(embed=embed)

        # Step 5: Handle specific modes (unsupported bot restart or cogs reload)
        if mode == "-a":
            await interaction.followup.send("Bot restart is not supported on this server.")
            # This feature would depend on the host allowing restarts.
        elif mode == "-c":
            try:
                embed = discord.Embed(
                    title="Cogs - Reload",
                    description="Reloading all cogs...",
                    color=discord.Color.brand_green(),
                )
                for extension in get_extensions():
                    await self.bot.reload_extension(extension)
                await interaction.followup.send(embed=embed)
            except commands.ExtensionError:
                embed = discord.Embed(
                    title="Cogs - Reload",
                    description="Failed to reload cogs.",
                    color=discord.Color.brand_red(),
                )
                await interaction.followup.send(embed=embed)

        # Step 6: Optionally sync the bot commands
        if sync_commands:
            await self.bot.tree.sync()

# The get_extensions function must be defined elsewhere in your code
def get_extensions():
    return ["cogs.example", "cogs.another_cog"]

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
