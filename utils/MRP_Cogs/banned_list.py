import asyncio
import re
from datetime import datetime
from typing import List, Literal

import discord
import gspread
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from discord import app_commands
from core.common import paginate_embed, return_banishblacklistform_modal
from core.logging_module import get_log

from core import database
import random


def printlen(*args):
    if not args:
        return 0
    value = sum(len(str(arg)) for arg in args) + len(args) - 1
    return value + 300


_log = get_log(__name__)
# --------------------------------------------------
# pip3 install gspread oauth2client

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

try:
    sheet = client.open("MRP Bannedlist Data").sheet1
except Exception as e:
    _log.error(f"Error: {e}")
# 9 Values to fill

# Template on modfying spreadsheet
'''
row = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
sheet.insert_row(row, 3)
print("Done.")

cell = sheet.cell(3,1).value
print(cell)
'''
entryidcol = 1
banreportcol = 2
discusercol = 3
longIDcol = 4
gamertagcol = 5
bannedfromcol = 6
knownaltscol = 7
reasoncol = 8
dateofbancol = 9
bantypecol = 10
banenddatecol = 11

try:
    gtsheet = client.open("Gamertag Data").sheet1
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


def solve(s):
    a = s.split(' ')
    for i in range(len(a)):
        a[i] = a[i].capitalize()
    return ' '.join(a)


def random_rgb(seed=None):
    if seed is not None:
        random.seed(seed)
    return discord.Colour.from_rgb(random.randrange(0, 255),
                                   random.randrange(0, 255),
                                   random.randrange(0, 255))


Q1 = "User's Discord: "
Q2 = "User's Discord Long ID: "
Q3 = "User's Gamertag: "
Q4 = "Banned from (realm): "
Q5 = "Known Alts: "
Q6 = "Reason for Ban: "
Q7 = "Date of Incident"
Q8 = "The User has faced a (Temporary/Permanent) ban: "
Q9 = "If the ban is Temporary, the ban ends on: "

QQ1 = "What should I open for you? \n >  **Options:** `Gamertag` / `Discord` / `Combined`"
a_list = []


class BannedlistCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    BL = app_commands.Group(
        name="blacklist",
        description="Manage the posted blacklist.",
    )

    @BL.command(
        name="post",
        description="Add a person to the banned list")
    @app_commands.describe(
        discord_id="The Discord ID of the user to banish",
        gamertag="The gamertag of the user to banish",
        originating_realm="The realm the user is being banned from",
        ban_type="The type of ban that was applied"
    )
    @app_commands.checks.has_role("Realm OP")
    async def banish_user(
            self,
            interaction: discord.Interaction,
            discord_id: str,
            gamertag: str,
            originating_realm: str,
            ban_type: Literal["Temporary", "Permanent"]
    ):
        """Add a person to the banned list"""
        # check if the discord_id is valid
        try:
            found_user = await self.bot.fetch_user(int(discord_id))
        except discord.NotFound:
            await interaction.response.send_message(
                "The Discord ID you provided is invalid!",
                ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(
                "An unknown error occured while checking the Discord ID!",
                ephemeral=True)
            _log.exception(e)
            return
        view = return_banishblacklistform_modal(self.bot, sheet, found_user, gamertag, originating_realm,
                                                ban_type)
        await interaction.response.send_modal(view)

    @BL.command(description="Search the banned list")
    @app_commands.describe(
        search_term="The term to search for in the banned list")
    @app_commands.checks.has_role("Realm OP")
    async def _search(self, interaction: discord.Interaction, *, search_term: str):
        databaseData = [
            database.MRP_Blacklist_Data.DiscUsername,
            database.MRP_Blacklist_Data.DiscID,
            database.MRP_Blacklist_Data.Gamertag,
            database.MRP_Blacklist_Data.BannedFrom,
            database.MRP_Blacklist_Data.KnownAlts,
            database.MRP_Blacklist_Data.ReasonforBan,
            database.MRP_Blacklist_Data.DateofIncident,
            database.MRP_Blacklist_Data.TypeofBan,
            database.MRP_Blacklist_Data.DatetheBanEnds,
            database.MRP_Blacklist_Data.entryid,
            database.MRP_Blacklist_Data.BanReporter
        ]
        ResultsGiven = False

        for data in databaseData:
            query = (database.MRP_Blacklist_Data.select().where(
                data.contains(search_term)))
            if query.exists():
                for p in query:
                    e = discord.Embed(
                        title="Bannedlist Search",
                        description=
                        f"Requested by {interaction.user.mention}",
                        color=0x18c927)
                    e.add_field(
                        name="Results: \n",
                        value=
                        f"```autohotkey\nDiscord Username: {p.DiscUsername}\nDiscord ID: {p.DiscID}\nGamertag: {p.Gamertag} \nBanned From: {p.BannedFrom}\nKnown Alts: {p.KnownAlts}\nBan Reason: {p.ReasonforBan}\nDate of Ban: {p.DateofIncident}\nType of Ban: {p.TypeofBan}\nDate the Ban Ends: {p.DatetheBanEnds}\nReported by: {p.BanReporter}\n```",
                        inline=False)
                    e.set_footer(
                        text=
                        f"Querying from MRP_Bannedlist_Data | Entry ID: {p.entryid}"
                    )
                    if ResultsGiven is True:
                        await interaction.followup.send(
                            embed=e)
                    else:
                        await interaction.response.send_message(embed=e)
                        ResultsGiven = True

        if ResultsGiven == False:
            e = discord.Embed(
                title="Bannedlist Search",
                description=f"Requested by {interaction.user.mention}",
                color=0x18c927)
            e.add_field(
                name="No Results!",
                value=f"`{search_term}`'s query did not bring back any results!")
            await interaction.response.send_message(embed=e)

    @BL.command(name="edit")
    @app_commands.checks.has_role("Realm OP")
    async def _edit(self, interaction: discord.Interaction, entry_id: int, modify: Literal[
        "Ban Reporter", "Discord Username", "Discord ID", "Gamertag", "Realm Banned from", "Known Alts", "Ban Reason", "Date of Incident", "Type of Ban", "Ban End Date"],
                    new_value: str):
        q: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(
            database.MRP_Blacklist_Data.id == entry_id)
        if not q.exists():
            await interaction.response.send_message("Invalid Entry ID", ephermal=True)
        else:
            string_to_field = {"Ban Reporter": q.BanReporter, "Discord Username": q.DiscUsername,
                               "Discord ID": q.DiscID, "Gamertag": q.Gamertag, "Realm Banned from": q.BannedFrom,
                               "Known Alts": q.KnownAlts, "Ban Reason": q.ReasonforBan,
                               "Date of Incident": q.DateofIncident, "Type of Ban": q.TypeofBan,
                               "Ban End Date": q.DatetheBanEnds, modify: new_value}
            q.save()
            await interaction.response.send_message(f"Modified Field {modify} to {new_value}.")


async def setup(bot):
    await bot.add_cog(BannedlistCMD(bot))
