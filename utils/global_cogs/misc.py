import ast
import json
import random
import logging
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands
from core.checks import slash_is_bot_admin_1

from core import database

# List of server rules
rules = [
    ":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!",
    ":two: **No spamming** in chat or direct messages!",
    ":three: **No religious or political topics**, those don’t usually end well!",
    ":four: **Keep pinging to a minimum**, it is annoying!",
    ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!",
    ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**",
    ":seven: **No realm or server is better than another!** It is **not** a competition.",
    ":eight: **Have fun** and happy crafting!",
    ":nine: **Discord Terms of Service apply!** You must be at least **13** years old.",
]

# Logger setup
logger = logging.getLogger(__name__)


class MiscCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("MiscCMD Cog Loaded")

    ##======================================================Slash Commands===========================================================

    # Nick Command
    @app_commands.command(
        name="nick",
        description="Change a user's nickname based on the channel name emoji.",
    )
    @app_commands.describe(
        user="The user whose nickname you want to change",
        channel="The channel with the emoji in the name",
    )
    @slash_is_bot_admin_1
    async def nick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        channel: discord.TextChannel,
    ):
        """Slash command to change a user's nickname based on the channel's emoji."""
        try:
            logger.info(
                f"{interaction.user} initiated nickname change for {user.display_name} using channel {channel.name}"
            )
            name = user.display_name
            channel_parts = channel.name.split("-")

            # Determine the emoji and realm format based on the channel name
            if len(channel_parts) == 2:  # realm-emoji format
                realm, emoji = channel_parts
            else:  # realm-name-emoji format
                realm, emoji = channel_parts[0], channel_parts[-1]

            # Update user's nickname with the emoji
            await user.edit(nick=f"{name} {emoji}")
            await interaction.response.send_message(
                f"Changed {user.mention}'s nickname!"
            )
            logger.info(
                f"Successfully changed {user.display_name}'s nickname to {name} {emoji}"
            )

        except Exception as e:
            logger.error(f"Error in changing nickname for {user.display_name}: {e}")
            await interaction.response.send_message(
                "An error occurred while changing the nickname.", ephemeral=True
            )

    # Rule Command [INT]
    @app_commands.command(name="rule", description="Sends out MRP Server Rules")
    async def rule(self, interaction: discord.Interaction, number: int = None):
        """Send the requested server rule."""
        try:
            if 1 <= number <= len(rules):
                await interaction.response.send_message(rules[number - 1])
                logger.info(f"Rule {number} sent by {interaction.user}")
            else:
                await interaction.response.send_message(
                    f"Please choose a valid rule number between 1 and {len(rules)}."
                )
                logger.warning(
                    f"Invalid rule number {number} requested by {interaction.user}"
                )
        except Exception as e:
            logger.error(f"Error in rule command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the rule.", ephemeral=True
            )

    # Ping Command
    @app_commands.command(description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        """Display the bot's ping and system resource usage."""
        try:
            logger.info(f"Ping command initiated by {interaction.user}")
            uptime = timedelta(seconds=int(time.time() - self.bot.start_time))
            ping_latency = round(self.bot.latency * 1000)

            pingembed = discord.Embed(
                title="Pong! ⌛",
                color=discord.Color.purple(),
                description="Current Discord API Latency",
            )
            pingembed.set_author(name="PortalBot")
            pingembed.add_field(
                name="Ping & Uptime:",
                value=f"```diff\n+ Ping: {ping_latency}ms\n+ Uptime: {str(uptime)}\n```",
            )

            # Adding system resource usage details
            memory = psutil.virtual_memory()
            pingembed.add_field(
                name="System Resource Usage",
                value=f"```diff\n- CPU Usage: {psutil.cpu_percent()}%\n- Memory Usage: {memory.percent}%\n"
                f"- Total Memory: {memory.total / (1024**3):.2f} GB\n- Available Memory: {memory.available / (1024**3):.2f} GB\n```",
                inline=False,
            )

            pingembed.set_footer(
                text=f"PortalBot Version: {self.bot.version}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.response.send_message(embed=pingembed)
            logger.info(
                f"Ping and system resource information sent to {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the ping information.", ephemeral=True
            )


# Set up the cog
async def setup(bot):
    await bot.add_cog(MiscCMD(bot))
    logger.info("MiscCMD Cog setup completed")
