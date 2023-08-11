import asyncio
import logging
import re
from typing import Literal

import discord
import xbox
from discord.ext import commands
from discord import app_commands

from core.logging_module import get_log

_log = get_log(__name__)
# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

try:
    gtsheet = client.open("Gamertag Data").sheet1
    sheet = client.open("MRP Bannedlist Data").sheet1
except Exception as e:
    _log.error(f"Error: {e}")
# 3 Values to fill

# Template on modfying spreadsheet
'''
gtrow = ["1", "2", "3"]
gtsheet.insert_row(row, 3)
print("Done.")

gtcell = sheet.cell(3,1).value
print(cell)
'''


# -----------------------------------------------------


class GamertagCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
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
