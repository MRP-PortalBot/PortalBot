from oauth2client.service_account import ServiceAccountCredentials
import gspread
import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
from core.common import load_config, paginate_embed
config, _ = load_config()
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


class BlacklistCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Starts the blacklist process.
    @commands.command()
    @commands.has_role("Realm OP")
    async def blacklist(self, ctx):
        author = ctx.message.author
        guild = ctx.message.guild
        channel = await ctx.author.create_dm()
        #schannel = self.bot.get_channel(778453455848996876)

        schannel = self.bot.get_channel(config['blacklistChannel'])
        await ctx.send("Please take a look at your DM's!")

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user

        await channel.send("Please answer the questions with as much detail as you can. \nWant to cancel the command? Answer everything and at the end then you have the option to either break or submit the responses, there you could say 'break'!\nIf you are having trouble with the command, please contact Space! \n\n*Starting Questions Now...*")
        time.sleep(2)
        await channel.send(Q1)
        answer1 = await self.bot.wait_for('message', check=check)

        await channel.send(Q2)
        answer2 = await self.bot.wait_for('message', check=check)

        await channel.send(Q3)
        answer3 = await self.bot.wait_for('message', check=check)

        await channel.send(Q4)
        answer4 = await self.bot.wait_for('message', check=check)

        await channel.send(Q5)
        answer5 = await self.bot.wait_for('message', check=check)

        await channel.send(Q6)
        answer6 = await self.bot.wait_for('message', check=check)

        await channel.send(Q7)
        answer7 = await self.bot.wait_for('message', check=check)

        await channel.send(Q8)
        answer8 = await self.bot.wait_for('message', check=check)

        await channel.send(Q9)
        answer9 = await self.bot.wait_for('message', check=check)

        time.sleep(0.5)

        # Spreadsheet Data
        row = [answer1.content, answer2.content, answer3.content, answer4.content,
               answer5.content, answer6.content, answer7.content, answer8.content, answer9.content]
        sheet.insert_row(row, 3)

        message = await channel.send("**That's it!**\n\nReady to submit?\n✅ - SUBMIT\n❌ - CANCEL\n*You have 300 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check2)
            if str(reaction.emoji) == "❌":
                await channel.send("Ended Form...")
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                return
            else:
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                await channel.send("Sending your responses!")
                blacklistembed = discord.Embed(
                    title="Blacklist Report", description="Sent from: " + author.mention, color=0xb10d9f)
                blacklistembed.add_field(name="Questions", value=f'**{Q1}** \n {answer1.content} \n\n'
                                         f'**{Q2}** \n {answer2.content} \n\n'
                                         f'**{Q3}** \n {answer3.content} \n\n'
                                         f'**{Q4}** \n {answer4.content} \n\n'
                                         f'**{Q5}** \n {answer5.content} \n\n'
                                         f'**{Q6}** \n {answer6.content} \n\n'
                                         f'**{Q7}** \n {answer7.content} \n\n'
                                         f'**{Q8}** \n {answer8.content} \n\n'
                                         f'**{Q9}** \n {answer9.content} \n\n')
                timestamp = datetime.now()
                blacklistembed.set_footer(
                    text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
                await schannel.send(embed=blacklistembed)
                await channel.send("I have sent in your blacklist report, thank you! \n**Response Record:** https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit#gid=0&range=D3 \n*Here is your cookie!* 🍪")

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")

    @blacklist.error
    async def blacklist_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    @commands.command()
    @commands.has_role("Realm OP")
    async def bsearch(self, ctx, *, username):
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

    @bsearch.error
    async def bsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("Your search returned to many results. Please narrow your search, or try a different search term.")

    async def populate_embed(self, embed: discord.Embed, page):
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

    @commands.command(aliases=['blogsnew'])
    async def blogs(self, ctx, page: int = 3):
        author = ctx.message.author
        embed = discord.Embed(title="MRP Blacklist Data", description=
            f"Requested by Operator {author.mention}")
        await paginate_embed(self.bot, ctx, embed, self.populate_embed, sheet.row_count, page=page, begin=3)


def setup(bot):
    bot.add_cog(BlacklistCMD(bot))
