import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import discord
import psutil
from discord import app_commands
from discord.ext import commands

# Custom logger setup
logger = logging.getLogger(__name__)


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpCMD: Cog Loaded!")

    # Helper function to count lines in a file
    @staticmethod
    def count_lines_in_file(file_path):
        try:
            with open(file_path, encoding="utf8") as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return 0

    # Help Command
    @app_commands.command(description="Reference to documentation")
    async def help(self, interaction: discord.Interaction):
        logger.info(f"Help command called by {interaction.user}")

        line_count = 0
        for file in Path("utils").glob("**/*.py"):
            if "!" in file.name or "DEV" in file.name:
                continue
            line_count += self.count_lines_in_file(file)

        line_count += self.count_lines_in_file("./main.py")
        formatted_line_count = f"{line_count:,}"

        embed = discord.Embed(
            color=discord.Color.purple(),
            title="Hey, I'm PortalBot, MRP’s very own mascot! 👋",
            description=f"\n`Coded in {formatted_line_count} lines`\n\n"
            f"Read the documentation here: [PortalBot Docs](https://brave-bongo-a8b.notion.site/PortalBot-Help-Commands-9f482fe2d19545aa9d497bb1f3c18b84)",
        )
        embed.set_footer(
            text=f"Requested by {interaction.user}",
            icon_url=interaction.user.avatar.url,
        )

        await interaction.response.send_message(embed=embed)

    # Ping Command
    @app_commands.command(description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        logger.info(f"Ping command called by {interaction.user}")

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

        # Adding system resource usage with more details
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


# Setup function to load the cog
async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
