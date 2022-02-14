import asyncio
import logging
import random
import re
import time
from datetime import datetime

import discord
import gspread
from core import database
from core.common import load_config, paginate_embed
from discord.ext import commands
from discord.ui import InputText, Modal
from oauth2client.service_account import ServiceAccountCredentials

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

sheet = client.open("MRP Blacklist Data").sheet1
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

class BlacklistCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("BlacklistCMD: Cog Loaded!")

    # Starts the blacklist process.
    @commands.command()
    @commands.has_role("Realm OP")
    async def blacklist(self, ctx: commands.Context):
        view = BlacklistFormButton(self.bot, ctx.author.id)
        await ctx.send(view=view)

    @blacklist.error
    async def blacklist_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    @commands.command()
    @commands.has_role("Realm OP")
    async def oldsearch(self, ctx, *, username):
        checkcheck = "FALSE"
        author = ctx.message.author
        em = discord.Embed(title="Google Sheets Search",
                           description="Requested by Operator " + author.mention, color=0x18c927)
        #values_re = re.compile(r'(?i)' + username)
        # print(values_re)
        # 're.Pattern' object is not iterable
        #values = sheet.findall(username)
        values_re = re.compile(r'(?i)' + '(?:' + username + ')')
        print(values_re)
        values = sheet.findall(values_re)
        print(values)
        try:
            checkempty = ', '.join(sheet.row_values(sheet.find(values_re).row))
            print(checkempty)
        except:
            checkcheck = "TRUE"
        print(checkcheck)
        if checkcheck == "FALSE":
            for r in values:
                output = ', '.join(sheet.row_values(r.row))
                print(output)
                A1, A2, A3, A4, A5, A6, A7, A8, A9 = output.split(", ")
                em.add_field(name="Results: \n", value="```autohotkey\n" + "Discord Username: " + str(A1) + "\nDiscord ID: " + str(A2) + "\nGamertag: " + str(A3) + "\nBanned From: " + str(
                    A4) + "\nKnown Alts: " + str(A5) + "\nBan Reason: " + str(A6) + "\nDate of Ban: " + str(A7) + "\nType of Ban: " + str(A8) + "\nDate the Ban Ends: " + str(A9) + "\n```", inline=False)
            await ctx.send(embed=em)
        else:
            em.add_field(name="No Results", value="I'm sorry, but it looks like the [spreadsheet](https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit?usp=sharing) doesn't have any results for the query you have sent! \n\n**Tips:**\n- Don't include the user's tag number! (Ex: #1879)\n- Try other ways of spelling out the username such as putting everything as lowercase! \n- Try checking the orginal spreadsheet for the value and try searching any term in the row here!")
            await ctx.send(embed=em)

    @oldsearch.error
    async def oldsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("Your search returned to many results. Please narrow your search, or try a different search term.")

    @commands.command(aliases=['blogsnew'])
    @commands.has_role("Realm OP")
    async def blogs(self, ctx, page: int = 3):
        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed for the 'blogs' command."""
            embed.clear_fields()
            values = sheet.row_values(page)
            embed.add_field(
                name=f"Row: {page}", value=f"```\n {' '.join(values)}```", inline=False)
            embed.add_field(name="Discord Username", value=values[0], inline=False)
            embed.add_field(name="Discord ID", value=values[1], inline=False)
            embed.add_field(name="Gamertag", value=values[2], inline=False)
            embed.add_field(name="Banned From", value=values[3], inline=False)
            embed.add_field(name="Known Alts", value=values[4], inline=False)
            embed.add_field(name="Reason for ban", value=values[5], inline=False)
            embed.add_field(name="Date of Incident", value=values[6], inline=False)
            embed.add_field(name="Type of Ban", value=values[7], inline=False)
            embed.add_field(name="Date the Ban ends",
                            value=values[8], inline=False)
            return embed
    

        author = ctx.message.author
        embed = discord.Embed(title="MRP Blacklist Data", description=
            f"Requested by Operator {author.mention}")
        await paginate_embed(self.bot, ctx, embed, populate_embed, sheet.row_count, page=page, begin=3)

    @blogs.error
    async def blogs_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
 

    @commands.command()
    @commands.has_role("Realm OP")
    async def Bsearch(self, ctx, *, req : str):
        databaseData = [database.MRP_Blacklist_Data.DiscUsername, database.MRP_Blacklist_Data.DiscID, database.MRP_Blacklist_Data.Gamertag, database.MRP_Blacklist_Data.BannedFrom, database.MRP_Blacklist_Data.KnownAlts, database.MRP_Blacklist_Data.ReasonforBan, database.MRP_Blacklist_Data.DateofIncident, database.MRP_Blacklist_Data.TypeofBan, database.MRP_Blacklist_Data.DatetheBanEnds, database.MRP_Blacklist_Data.entryid,
        database.MRP_Blacklist_Data.BanReporter]
        ResultsGiven = False

        for data in databaseData:
            query = (database.MRP_Blacklist_Data.select().where(data.contains(req)))
            if query.exists():
                for p in query:
                    e = discord.Embed(title = "Blacklist Search", description = f"Requested by {ctx.message.author.mention}", color = 0x18c927)
                    e.add_field(name="Results: \n", value=f"```autohotkey\nDiscord Username: {p.DiscUsername}\nDiscord ID: {p.DiscID}\nGamertag: {p.Gamertag} \nBanned From: {p.BannedFrom}\nKnown Alts: {p.KnownAlts}\nBan Reason: {p.ReasonforBan}\nDate of Ban: {p.DateofIncident}\nType of Ban: {p.TypeofBan}\nDate the Ban Ends: {p.DatetheBanEnds}\nReported by: {p.BanReporter}\n```", inline=False)
                    e.set_footer(text = f"Querying from MRP_Blacklist_Data | Entry ID: {p.entryid}")
                    await ctx.send(embed = e)
                    ResultsGiven = True
            
        if ResultsGiven == False:
            e = discord.Embed(title = "Blacklist Search", description = f"Requested by {ctx.message.author.mention}", color = 0x18c927)
            e.add_field(name = "No Results!", value = f"`{req}`'s query did not bring back any results!")
            await ctx.send(embed = e)
                
    


    @commands.command()
    async def Bmodify(self, ctx, entryID: str):
        channel = ctx.message.channel
        username = ctx.message.author
        try:
            database.db.connect(reuse_if_open=True)
        except:
            await ctx.send("ERROR: Code 1")
            return
        

        embed = discord.Embed(title = "Record Manager", description = "Options:\n1️⃣ - **BanReporter**\n2️⃣ - **Discord Username**\n3️⃣ - **Discord ID**\n4️⃣ - **Gamertag**\n5️⃣ - **Realm Banned from**\n6️⃣ - **Known Alts**\n7️⃣ - **Ban Reason**\n8️⃣ - **Date of Incident**\n9️⃣ - **Type of Ban**\n🔟 - **Date the Ban Ends**", color = 0x34ebbd)
        reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
        msg = await ctx.send(embed = embed)
        for emoji in reactions:
            await msg.add_reaction(emoji)
        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) in reactions)
        def check3(m):
            return m.content is not None and m.channel == channel and m.author == username

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=150.0, check=check2)
            if str(reaction.emoji) == "1️⃣":

                await ctx.send("New content to modify:\n*Currently modifying* `Ban Reporter`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.BanReporter
                    b.BanReporter = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "2️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Discord Username`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DiscUsername
                    b.DiscUsername = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "3️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Discord ID`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DiscID
                    b.DiscID = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "4️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Gamertag`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.Gamertag
                    b.Gamertag = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "5️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Banned From (Realm)`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.BannedFrom
                    b.BannedFrom = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "6️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Known Alts`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.KnownAlts
                    b.KnownAlts = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "7️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Ban Reason`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.ReasonforBan
                    b.ReasonforBan = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "8️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Date of Incident`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DateofIncident
                    b.DateofIncident = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "9️⃣":
                await ctx.send("New content to modify:\n*Currently modifying* `Type of Ban`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.TypeofBan
                    b.TypeofBan = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            elif str(reaction.emoji) == "🔟":
                await ctx.send("New content to modify:\n*Currently modifying* `Date the Ban Ends`")
                messagecontent = await self.bot.wait_for('message', check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DatetheBanEnds
                    b.DatetheBanEnds = newData
                    b.save()
                    await ctx.send(f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}")
                except database.DoesNotExist:
                    await ctx.send("ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!")
            else:
                await ctx.send("Wha, what emoji did you react with?")
        except asyncio.TimeoutError:
            await ctx.send("You didn't react to anything! (Timed out)")
        
            

    @commands.command()
    async def DBget5(self, ctx, *, req:str):
        databaseData = [database.MRP_Blacklist_Data.DiscUsername, database.MRP_Blacklist_Data.DiscID, database.MRP_Blacklist_Data.Gamertag, database.MRP_Blacklist_Data.BannedFrom, database.MRP_Blacklist_Data.KnownAlts, database.MRP_Blacklist_Data.ReasonforBan, database.MRP_Blacklist_Data.DateofIncident, database.MRP_Blacklist_Data.TypeofBan, database.MRP_Blacklist_Data.DatetheBanEnds, database.MRP_Blacklist_Data.entryid]
        for data in databaseData:
            query = (database.MRP_Blacklist_Data.select().where(data.contains(req)))
            try:
                query.exists()
            except:
                await ctx.send("No results")
            else:
                for p in query:
                    e = discord.Embed(title = "Blacklist Search", description = f"Requested by {ctx.message.author.mention}")
                    e.add_field(name="Results: \n", value=f"```autohotkey\nDiscord Username: {p.DiscUsername}\nDiscord ID: {p.DiscID}\nGamertag: {p.Gamertag} \nBanned From: {p.BannedFrom}\nKnown Alts: {p.KnownAlts}\nBan Reason: {p.ReasonforBan}\nDate of Ban: {p.DateofIncident}\nType of Ban: {p.TypeofBan}\nDate the Ban Ends: {p.DatetheBanEnds}\n```", inline=False)
                    await ctx.send(embed = e)
        
               

                


            
                



            

def setup(bot):
    bot.add_cog(BlacklistCMD(bot))

