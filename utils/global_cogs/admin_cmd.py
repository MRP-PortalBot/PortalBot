import requests
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

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gitpull_dev")
    @slash_is_bot_admin_2
    async def gitpull_dev(
        self,
        interaction: discord.Interaction,
        mode: Literal["-a", "-c"] = "-a",  # Mode for action or cogs reload
        sync_commands: bool = False,       # Option to sync commands after pulling
    ) -> None:
        """
        Fetch and reset the bot's codebase from Git via API. Be careful: This can break things!
        """
        # Defer the interaction to prevent timeout
        await interaction.response.defer()

        api_url = "https://control.sparkedhost.us/api/client/servers/fd90ffb0-108d-4e24-996a-dc9678174d76/command"
        headers = {
            "Authorization": "Bearer ptlc_2jp6Kyd3f2pyPsTSDPNocqsmPXOGVTLP4l7z6mGUrjG",  # Replace with your actual API token
            "Content-Type": "application/json"
        }

        # Create the data payload for the API request
        data = {
            "command": "if [[ -d .git ]]; then git pull; fi"
        }

        # Step 1: Send API request to SparkedHost to pull changes
        try:
            response = requests.post(api_url, json=data, headers=headers)
            if response.status_code == 200:
                output = response.json().get("message", "No output from server.")
            else:
                output = f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            await interaction.followup.send(f"⛔️ Unable to send command to SparkedHost!\n**Error:** {e}")
            return

        # Step 2: Prepare the embed with the output
        embed = discord.Embed(
            title="GitHub Local Reset",
            description="Executed git pull on the server via API",
            color=discord.Color.brand_green(),
        )
        embed.add_field(name="API Response", value=f"```shell\n{output}\n```")

        # Step 3: Handle the mode of operation (-a for action, -c for cogs reload)
        if mode == "-a":
            embed.set_footer(text="Attempting to restart the bot...")
        elif mode == "-c":
            embed.set_footer(text="Attempting to reload cogs...")

        await interaction.followup.send(embed=embed)

        # Step 4: Handle specific modes (unsupported bot restart or cogs reload)
        if mode == "-a":
            await interaction.followup.send("Bot restart is not supported on this server.")
            # Add logic for bot restart here if SparkedHost allows
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

        # Step 5: Optionally sync the bot commands
        if sync_commands:
            await self.bot.tree.sync()

# The get_extensions function must be defined elsewhere in your code
def get_extensions():
    return ["cogs.example", "cogs.another_cog"]

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
