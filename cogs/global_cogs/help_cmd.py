import logging
from datetime import datetime
from pathlib import Path

import discord
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



# nick clear DM newrealm

def setup(bot):
    bot.add_cog(HelpCMD(bot))
