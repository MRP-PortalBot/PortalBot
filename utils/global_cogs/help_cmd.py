import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import discord
import psutil
from discord import app_commands
from discord.ext import commands

import core.common

logger = logging.getLogger(__name__)

class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpCMD: Cog Loaded!")

    # Help Command
    @app_commands.command(description="Reference to documentation")
    async def help(self, interaction: discord.Interaction):
        line_count = 0

        for file in Path("utils").glob("**/*.py"):
            if "!" in file.name or "DEV" in file.name:
                continue
            num_lines_cogs = sum(1 for line in open(f"{file}", encoding="utf8"))
            line_count += num_lines_cogs

        num_lines_main = sum(1 for line in open(f"./main.py", encoding="utf8"))
        line_count += num_lines_main
        line_count = f"{line_count:,}"

        embed = discord.Embed(color=discord.Color.purple(), title="Hey, I'm PortalBot, MRP’s very own mascot! 👋",
                              description=f"\n`Coded in {line_count} lines`"
                                          f"\n\nRead the documentation here: https://brave-bongo-a8b.notion.site/PortalBot-Help-Commands-9f482fe2d19545aa9d497bb1f3c18b84")
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        current_time = float(time.time())
        difference = int(round(current_time - float(self.bot.start_time)))
        text = str(timedelta(seconds=difference))

        pingembed = discord.Embed(
            title="Pong! ⌛",
            color=discord.Colour.purple(),
            description="Current Discord API Latency",
        )
        pingembed.set_author(
            name="PortalBot"
        )
        pingembed.add_field(
            name="Ping & Uptime:",
            value=f"```diff\n+ Ping: {round(self.bot.latency * 1000)}ms\n+ Uptime: {text}\n```",
        )

        pingembed.add_field(
            name="System Resource Usage",
            value=f"```diff\n- CPU Usage: {psutil.cpu_percent()}%\n- Memory Usage: {psutil.virtual_memory().percent}%\n```",
            inline=False,
        )
        pingembed.set_footer(
            text=f"PortalBot Version: {self.bot.version}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=pingembed)


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
