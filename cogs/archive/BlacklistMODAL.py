import logging
import random
from datetime import datetime

import discord
import gspread
from discord.ext import commands
from discord.ui import InputText, Modal
from oauth2client.service_account import ServiceAccountCredentials

from core import database
from core.common import load_config

config, _ = load_config()

def printlen(*args):
    if not args:
        return 0
    value = sum(len(str(arg)) for arg in args) + len(args) - 1
    return value + 300

logger = logging.getLogger(__name__)
# --------------------------------------------------
# pip3 install gspread oauth2client


scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

sheet = client.open("MRP Bannedlist Data").sheet1
# 9 Values to fill

# Template on modfying spreadsheet
'''
row = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
sheet.insert_row(row, 3)
print("Done.")

cell = sheet.cell(3,1).value
print(cell)
'''

gtsheet = client.open("Gamertag Data").sheet1
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
    return discord.Colour.from_rgb(random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))

Q1 = "User's Discord"
Q2 = "User's Discord Long ID"
Q3 = "User's Gamertag"
Q4 = "What realm were they banned from?"
Q5 = "Known Alts"
Q6 = "Reason for Ban"
Q7 = "Date of Incident"
Q8 = "Is this a Temporary or Permanent ban?"
Q9 = "If the ban is temporary, the ban ends on:"

QQ1 = "What should I open for you? \n >  **Options:** `Gamertag` / `Discord` / `Combined`"
a_list = []

class BlacklistFormModal(Modal):
    def __init__(self, bot) -> None:
        super().__init__("Blacklist Form")
        self.bot = bot

        self.add_item(
            InputText(
                label=Q1,
                style=discord.InputTextStyle.short,
                max_length=75
            )
        )
        self.add_item(
            InputText(
                label=Q2,
                style=discord.InputTextStyle.short,
                max_length=20
            )
        )
        self.add_item(
            InputText(
                label=Q3,
                style=discord.InputTextStyle.short,
                max_length=100
            )
        )
        self.add_item(
            InputText(
                label=Q4,
                style=discord.InputTextStyle.short,
                max_length=200
            )
        )
        self.add_item(
            InputText(
                label=Q5,
                style=discord.InputTextStyle.long,
            )
        )
        self.add_item(
            InputText(
                label=Q6,
                style=discord.InputTextStyle.long,
                max_length=2000
            )
        )
        self.add_item(
            InputText(
                label=Q7,
                style=discord.InputTextStyle.short,
                max_length=100
            )
        )
        self.add_item(
            InputText(
                label=Q8,
                style=discord.InputTextStyle.short,
                max_length=75
            )
        )
        self.add_item(
            InputText(
                label=Q9,
                style=discord.InputTextStyle.short,
                max_length=75
            )
        )

    async def callback(self, interaction: discord.Interaction):
        schannel = await self.bot.fetch_channel(config['blacklistChannel'])
        entryid = (int(sheet.acell('A3').value)+1)
        row = [
            entryid,
            interaction.user.name,
            self.children[0].value, 
            self.children[1].value, 
            self.children[2].value, 
            self.children[3].value, 
            self.children[4].value, 
            self.children[5].value, 
            self.children[6].value, 
            self.children[7].value, 
            self.children[8].value
        ]
        sheet.insert_row(row, 3)

        database.db.connect(reuse_if_open=True)
        q: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.create(DiscUsername=self.children[0].value, DiscID = self.children[1].value, Gamertag = self.children[2].value, BannedFrom = self.children[3].value, KnownAlts = self.children[4].value, ReasonforBan = self.children[5].value, DateofIncident = self.children[6].value, TypeofBan = self.children[7].value, DatetheBanEnds = self.children[8].value, BanReason = interaction.user.name)
        q.save()
        database.db.close()
        blacklistembed = discord.Embed(
            title="Blacklist Report", description="Sent from: " + interaction.user.mention, color=0xb10d9f)

        blacklistembed.add_field(name = Q1, value = self.children[0].value + "\n", inline = False)
        blacklistembed.add_field(name = Q2, value = self.children[1].value + "\n", inline = False)
        blacklistembed.add_field(name = Q3, value = self.children[2].value + "\n", inline = False)
        blacklistembed.add_field(name = Q4, value = self.children[3].value + "\n", inline = False)
        blacklistembed.add_field(name = Q5, value = self.children[4].value + "\n", inline = False)
        blacklistembed.add_field(name = Q6, value = self.children[5].value + "\n", inline = False)
        blacklistembed.add_field(name = Q7, value = self.children[6].value + "\n", inline = False)
        blacklistembed.add_field(name = Q8, value = self.children[7].value + "\n", inline = False)
        blacklistembed.add_field(name = Q9, value = self.children[8].value + "\n", inline = False)

        timestamp = datetime.now()
        blacklistembed.set_footer(
            text=interaction.guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        await schannel.send(embed=blacklistembed)

        await interaction.response.send_message("I have sent in your blacklist report, thank you! \n**Response Record:** https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit#gid=0&range=D3 \n*Here is your cookie!* 🍪", ephemeral = True)

class BlacklistFormButton(discord.ui.View):
    def __init__(self, bot, author_id: int):
        super().__init__(timeout=None)
        self.value = None
        self.bot = bot
        self.author_id = author_id

    @discord.ui.button(
        label="Start Blacklist Process",
        style=discord.ButtonStyle.red,
        emoji="📝",
    )
    async def verify(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.author_id == interaction.user.id:
            await interaction.response.defer("You can't perform this action, do the command on your own if you intend to fill this out.")
        modal = BlacklistFormModal(self.bot)
        try:
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(f"Uh, something went wrong. Please try again.\n{e}")

class BlacklistMODAL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("BlacklistCMD: Cog Loaded!")

    # Starts the blacklist process.
    @commands.command()
    @commands.has_role("Realm OP")
    async def blacklist2(self, ctx: commands.Context):
        view = BlacklistFormButton(self.bot, ctx.author.id)
        await ctx.send(view=view)

    @blacklist2.error
    async def blacklist2_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")


def setup(bot):
    bot.add_cog(BlacklistMODAL(bot))

