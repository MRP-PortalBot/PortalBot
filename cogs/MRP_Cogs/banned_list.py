import asyncio
import re
from datetime import datetime
from typing import List, Literal

import discord
import gspread
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from discord import app_commands
from core.common import load_config, paginate_embed, return_banishblacklistform_modal
from core.logging_module import get_log

config, _ = load_config()
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

    @app_commands.command(
        name="banish_user",
        description="Add a person to the banned list")
    @app_commands.describe(
        discord_id="The Discord ID of the user to banish",
        gamertag="The gamertag of the user to banish",
        originating_realm="The realm the user is being banned from",
        ban_type="The type of ban that was applied"
    )
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

    @commands.command()
    @commands.has_role("Realm OP")
    async def oldsearch(self, ctx, *, username):
        checkcheck = "FALSE"
        author = ctx.message.author
        em = discord.Embed(title="Google Sheets Search",
                           description="Requested by Operator " +
                           author.mention,
                           color=0x18c927)
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
                em.add_field(
                    name="Results: \n",
                    value="```autohotkey\n" + "Discord Username: " + str(A1) +
                    "\nDiscord ID: " + str(A2) + "\nGamertag: " + str(A3) +
                    "\nBanned From: " + str(A4) + "\nKnown Alts: " + str(A5) +
                    "\nBan Reason: " + str(A6) + "\nDate of Ban: " + str(A7) +
                    "\nType of Ban: " + str(A8) + "\nDate the Ban Ends: " +
                    str(A9) + "\n```",
                    inline=False)
            await ctx.send(embed=em)
        else:
            em.add_field(
                name="No Results",
                value=
                "I'm sorry, but it looks like the [spreadsheet](https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit?usp=sharing) doesn't have any results for the query you have sent! \n\n**Tips:**\n- Don't include the user's tag number! (Ex: #1879)\n- Try other ways of spelling out the username such as putting everything as lowercase! \n- Try checking the orginal spreadsheet for the value and try searching any term in the row here!"
            )
            await ctx.send(embed=em)

    @oldsearch.error
    async def oldsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send(
                "Uh oh, looks like you don't have the Realm OP role!")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                "Your search returned to many results. Please narrow your search, or try a different search term."
            )

    @commands.command(aliases=['blogsnew'])
    @commands.has_role("Realm OP")
    async def blogs(self, ctx, page: int = 3):
        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed for the 'blogs' command."""
            embed.clear_fields()
            values = sheet.row_values(page)
            embed.add_field(name=f"Row: {page}",
                            value=f"```\n {' '.join(values)}```",
                            inline=False)
            embed.add_field(name="Discord Username",
                            value=values[0],
                            inline=False)
            embed.add_field(name="Discord ID", value=values[1], inline=False)
            embed.add_field(name="Gamertag", value=values[2], inline=False)
            embed.add_field(name="Banned From", value=values[3], inline=False)
            embed.add_field(name="Known Alts", value=values[4], inline=False)
            embed.add_field(name="Reason for ban",
                            value=values[5],
                            inline=False)
            embed.add_field(name="Date of Incident",
                            value=values[6],
                            inline=False)
            embed.add_field(name="Type of Ban", value=values[7], inline=False)
            embed.add_field(name="Date the Ban ends",
                            value=values[8],
                            inline=False)
            return embed

        author = ctx.message.author
        embed = discord.Embed(
            title="MRP Bannedlist Data",
            description=f"Requested by Operator {author.mention}")
        await paginate_embed(self.bot,
                             ctx,
                             embed,
                             populate_embed,
                             sheet.row_count,
                             page=page,
                             begin=3)

    @blogs.error
    async def blogs_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send(
                "Uh oh, looks like you don't have the Realm OP role!")

    @app_commands.command(description="Search the banned list")
    @app_commands.describe(
        search_term="The term to search for in the banned list")
    @commands.has_role("Realm OP")
    async def blacklist_search(self, interaction: discord.Interaction, *, query: str):
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
                data.contains(query)))
            if query.exists():
                for p in query:
                    e = discord.Embed(
                        title="Bannedlist Search",
                        description=
                        f"Requested by {ctx.message.author.mention}",
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
                value=f"`{query}`'s query did not bring back any results!")
            await interaction.response.send_message(embed=e)

    @commands.command()
    async def Bmodify(self, ctx, entryID: int):
        channel = ctx.message.channel
        username = ctx.message.author
        try:
            database.db.connect(reuse_if_open=True)
        except:
            await ctx.send("ERROR: Code 1")
            return

        embed = discord.Embed(
            title="Record Manager",
            description=
            "Options:\n1️⃣ - **BanReporter**\n2️⃣ - **Discord Username**\n3️⃣ - **Discord ID**\n4️⃣ - **Gamertag**\n5️⃣ - **Realm Banned from**\n6️⃣ - **Known Alts**\n7️⃣ - **Ban Reason**\n8️⃣ - **Date of Incident**\n9️⃣ - **Type of Ban**\n🔟 - **Date the Ban Ends**",
            color=0x34ebbd)
        reactions = [
            '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
        ]
        msg = await ctx.send(embed=embed)
        for emoji in reactions:
            await msg.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) in reactions)

        def check3(m):
            return m.content is not None and m.channel == channel and m.author == username

        try:
            reaction, user = await self.bot.wait_for('reaction_add',
                                                     timeout=150.0,
                                                     check=check2)
            if str(reaction.emoji) == "1️⃣":

                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Ban Reporter`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.BanReporter
                    b.BanReporter = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, banreportcol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "2️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Discord Username`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DiscUsername
                    b.DiscUsername = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, discusercol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "3️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Discord ID`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DiscID
                    b.DiscID = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, longIDcol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "4️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Gamertag`")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.Gamertag
                    b.Gamertag = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, gamertagcol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "5️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Banned From (Realm)`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.BannedFrom
                    b.BannedFrom = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, bannedfromcol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "6️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Known Alts`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.KnownAlts
                    b.KnownAlts = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, knownaltscol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "7️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Ban Reason`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.ReasonforBan
                    b.ReasonforBan = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, reasoncol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "8️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Date of Incident`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DateofIncident
                    b.DateofIncident = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, dateofbancol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "9️⃣":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Type of Ban`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.TypeofBan
                    b.TypeofBan = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, bantypecol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            elif str(reaction.emoji) == "🔟":
                await ctx.send(
                    "New content to modify:\n*Currently modifying* `Date the Ban Ends`"
                )
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                newData = messagecontent.content

                try:
                    b: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.select(
                    ).where(
                        database.MRP_Blacklist_Data.entryid == entryID).get()
                    oldData = b.DatetheBanEnds
                    b.DatetheBanEnds = newData
                    b.save()
                    usercell = sheet.find(str(entryID), in_column=entryidcol)
                    userrow = usercell.row
                    sheet.update_cell(userrow, banenddatecol, str(newData))
                    await ctx.send(
                        f"Entry {b.entryid} has been modified successfully.\n**Updated:** {oldData} -> {newData}"
                    )
                except database.DoesNotExist:
                    await ctx.send(
                        "ERROR: This entry you provided **DOES NOT EXIST**\nPlease make sure you provided an **ENTRY ID**, you can find this by searching for your entry using `>Bsearch` and looking at the footer for its ID!"
                    )
            else:
                await ctx.send("Wha, what emoji did you react with?")
        except asyncio.TimeoutError:
            await ctx.send("You didn't react to anything! (Timed out)")

    @commands.command()
    async def DBget5(self, ctx, *, req: str):
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
            database.MRP_Blacklist_Data.entryid
        ]
        for data in databaseData:
            query = (database.MRP_Blacklist_Data.select().where(
                data.contains(req)))
            try:
                query.exists()
            except:
                await ctx.send("No results")
            else:
                for p in query:
                    e = discord.Embed(
                        title="Bannedlist Search",
                        description=f"Requested by {ctx.message.author.mention}"
                    )
                    e.add_field(
                        name="Results: \n",
                        value=
                        f"```autohotkey\nDiscord Username: {p.DiscUsername}\nDiscord ID: {p.DiscID}\nGamertag: {p.Gamertag} \nBanned From: {p.BannedFrom}\nKnown Alts: {p.KnownAlts}\nBan Reason: {p.ReasonforBan}\nDate of Ban: {p.DateofIncident}\nType of Ban: {p.TypeofBan}\nDate the Ban Ends: {p.DatetheBanEnds}\n```",
                        inline=False)
                    await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(BannedlistCMD(bot))
