from typing import Literal

import discord
import xbox
from discord import app_commands
from discord.ext import commands

from core.logging_module import get_log

_log = get_log(__name__)


class GamertagCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Search for an xbox profile by gamertag or XUID.")
    @app_commands.describe(
        search_type="What would you like to search by?",
        query="Search Term"
    )
    @app_commands.checks.has_role("Realm OP")
    async def get_xbox(self, interaction: discord.Interaction, search_type: Literal["Gamertag", "XUID"], query: str):
        if search_type == "Gamertag":
            try:
                profile = xbox.GamerProfile.from_gamertag(query)
                gamertag_value = profile.gamertag
                GT = gamertag_value.replace(" ", "-")
            except xbox.exceptions.GamertagNotFound:
                embed = discord.Embed(title="Xbox Information",
                                      description=f"Requested by Operator: {interaction.user.mention}",
                                      color=0x18c927)
                embed.add_field(name="Information", value="No results found!")
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Xbox Information",
                                      description=f"Requested by Operator: {interaction.user.mention}",
                                      color=0x18c927)
                embed.add_field(name="Information:",
                                value=f"**Gamertag:** {profile.gamertag}\n**Gamerscore:** {profile.gamerscore} \n**XUID:** {profile.xuid}")
                embed.add_field(name="Profile Links",
                                value=f"**XBOX Lookup:** https://xboxgamertag.com/search/{GT} \n**XBOX Profile:** https://account.xbox.com/en-us/profile?gamertag={GT}")
                embed.set_thumbnail(url=profile.gamerpic)
                await interaction.response.send_message(embed=embed)
        else:
            try:
                messageopt1c = int(query)
            except:
                messageopt1c = int(query, 16)
            else:
                messageopt1c = query

            try:
                profile = xbox.GamerProfile.from_xuid(messageopt1c)
                gamertag_value = profile.gamertag
                GT = gamertag_value.replace(" ", "-")
            except xbox.exceptions.GamertagNotFound:
                embed = discord.Embed(title="Xbox Information",
                                      description=f"Requested by Operator: {interaction.user.mention}", color=0x18c927)
                embed.add_field(name="Information", value="No results found!")
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Xbox Information",
                                      description=f"Requested by Operator: {interaction.user.mention}", color=0x18c927)
                embed.add_field(name="Information:",
                                value=f"**Gamertag:** {profile.gamertag}\n**Gamerscore:** {profile.gamerscore} \n**XUID:** {profile.xuid}")
                embed.add_field(name="Profile Links",
                                value=f"**XBOX Lookup:** https://xboxgamertag.com/search/{GT} \n**XBOX Profile:** https://account.xbox.com/en-us/profile?gamertag={GT}")
                embed.set_thumbnail(url=profile.gamerpic)
                return await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(GamertagCMD(bot))
