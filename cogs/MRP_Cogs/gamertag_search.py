import asyncio
import logging
import re

import discord
import xbox
from discord.ext import commands
from discord import app_commands

from core.logging_module import get_log

_log = get_log(__name__)
_log.info("Starting PortalBot...")
# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

gtsheet = client.open("Gamertag Data").sheet1
sheet = client.open("MRP Bannedlist Data").sheet1
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

    # new gamertags command
    @commands.command()
    @commands.has_role("Realm OP")
    async def gtsearch(self, ctx):
        checkcheck = "FALSE"
        author = ctx.message.author
        channel = ctx.message.channel
        guild = ctx.message.guild
        SearchResults = discord.Embed(
            title="Gamertag Search", description="Requested by Operator " + author.mention, color=0x18c927)

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user

        await ctx.send("How do you want to search?\n**Discord**\n**LongID**\n**Gamertag**")
        message1 = await self.bot.wait_for('message', check=check)

        message1c = message1.content
        if 'Discord' in message1c:
            await ctx.send("Please enter the Discord Username")
            messageopt1 = await self.bot.wait_for('message', check=check)
            messageopt1c = messageopt1.content
            gtvalues_re = re.compile(r'(?i)' + '(?:' + messageopt1c + ')')
            print(gtvalues_re)
            gtvalues = gtsheet.findall(gtvalues_re, in_column=1)
            print(gtvalues)
            gtselect = 'False'
        elif 'LongID' in message1c:
            await ctx.send("Please enter the Discord LongID")
            messageopt1 = await self.bot.wait_for('message', check=check)
            messageopt1c = messageopt1.content
            gtvalues_re = re.compile(r'(?i)' + '(?:' + messageopt1c + ')')
            print(gtvalues_re)
            gtvalues = gtsheet.findall(gtvalues_re, in_column=2)
            print(gtvalues)
            gtselect = 'False'
        elif 'Gamertag' in message1c:
            await ctx.send("Please enter the Gamertag")
            messageopt1 = await self.bot.wait_for('message', check=check)
            messageopt1c = messageopt1.content
            gtvalues_re = re.compile(r'(?i)' + '(?:' + messageopt1c + ')')
            print(gtvalues_re)
            gtvalues = gtsheet.findall(gtvalues_re, in_column=3)
            print(gtvalues)
            gtselect = "True"
        else:
            gtvalues = "specialerror"
        try:
            checkempty = ', '.join(gtsheet.row_values(
                gtsheet.find(gtvalues_re).row))
            print(checkempty)
        except:
            checkcheck = "TRUE"
        print(checkcheck)
        if checkcheck == "FALSE":
            for r in gtvalues:
                output = ', '.join(gtsheet.row_values(r.row))
                print(output)
                A1, A2, A3 = output.split(", ")
                SearchResults.add_field(name="Results: \n", value="```autohotkey\n" + "Discord Username: " + str(
                    A1) + "\nDiscord ID: " + str(A2) + "\nGamertag: " + str(A3) + "\n```", inline=False)
                newI = A3
                SearchResults.add_field(name="Gamertag Search links", value="**Xbox Gamertag:** " + "**" + newI + "**" +
                                        "\n**Xbox Profile:** https://account.xbox.com/en-us/profile?gamertag=" + newI + "\n**Xbox Lookup:** https://xboxgamertag.com/search/" + newI)
            await ctx.channel.purge(limit=5)
            await ctx.send(embed=SearchResults)
        elif gtvalues == "specialerror":
            await ctx.channel.purge(limit=5)
            await ctx.send("Please try again using a valid search type.")
        elif gtselect == "True":
            SearchResults.add_field(
                name="No Results", value="I'm sorry, but it looks like the [spreadsheet](https://docs.google.com/spreadsheets/d/10IwbwXo_ifPXYngSrO2lHVr6N2fXOKadZNR6MWqihzc/edit?usp=sharing) doesn't have any results for the query you have sent! \n\n**Tips:**\n- Don't include the user's tag number! (Ex: #1879)\n- Try other ways of spelling out the username such as putting everything as lowercase! \n- Try checking the orginal spreadsheet for the value and try searching any term in the row here!")
            newI = messageopt1c
            SearchResults.add_field(name="Gamertag Search links", value="**Xbox Gamertag:** " + "**" + newI + "**" +
                                    "\n**Xbox Profile:** https://account.xbox.com/en-us/profile?gamertag=" + newI + "\n**Xbox Lookup:** https://xboxgamertag.com/search/" + newI)
            await ctx.channel.purge(limit=5)
            await ctx.send(embed=SearchResults)
        else:
            SearchResults.add_field(
                name="No Results", value="I'm sorry, but it looks like the [spreadsheet](https://docs.google.com/spreadsheets/d/10IwbwXo_ifPXYngSrO2lHVr6N2fXOKadZNR6MWqihzc/edit?usp=sharing) doesn't have any results for the query you have sent! \n\n**Tips:**\n- Don't include the user's tag number! (Ex: #1879)\n- Try other ways of spelling out the username such as putting everything as lowercase! \n- Try checking the orginal spreadsheet for the value and try searching any term in the row here!")
            await ctx.channel.purge(limit=5)
            await ctx.send(embed=SearchResults)

    @gtsearch.error
    async def gtsearch_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("Uh oh, looks like you don't have the Realm OP role!")


    @app_commands.command()
    @app_commands.describe(
        gamertag="Enter your gamer-tag here",
        replace_nick="Do you want to use your gamer-tag as your nickname?"
    )
    async def gamertag(self, interaction: discord.Interaction, gamertag: str, replace_nick: bool = False):
        author = ctx.message.author
        channel = ctx.message.channel
        alid = str(author.id)
        aname = str(author.name + '#' + author.discriminator)

        # Spreadsheet Data
        row = [aname, alid, gamertag]
        print(row)
        gtsheet.insert_row(row, 3)
        #GamerTag = open("Gamertags.txt", "a")
        #GamerTag.write(gamertag + " " + str(author.id) + "\n")

        if replace_nick is True:
            await author.edit(nick=gamertag)
            await interaction.response.send_message("Updated your gamertag and nickname!", ephemeral=True)
        else:
            await interaction.response.send_message("Updated your gamertag!", ephemeral=True)


    @commands.command()
    async def getxbox(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.author
        msg = await ctx.send("How do you want to search?\n**GAMERTAG** - 📇\n**XUID** - 🆔")
        reactions = ['📇', '🆔']
        for emoji in reactions:
            await msg.add_reaction(emoji)

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user and m.author == author

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '📇' or str(reaction.emoji) == '🆔')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=100.0, check=check2)
            if str(reaction.emoji) == "📇":
                for emoji in reactions:
                    await msg.clear_reaction(emoji)
                await ctx.send("Please enter the Gamertag")
                messageopt1 = await self.bot.wait_for('message', check=check)
                messageopt1c = messageopt1.content
                try:
                    profile = xbox.GamerProfile.from_gamertag(messageopt1c)
                    gamertagvalue = profile.gamertag
                    GT = gamertagvalue.replace(" ", "-")
                except xbox.exceptions.GamertagNotFound:
                    embed = discord.Embed(title = "Xbox Information", description = f"Requested by Operator: {author.mention}", color =0x18c927)
                    embed.add_field(name = "Information", value = "No results found!")
                    await ctx.send(embed = embed)
                else:
                    embed = discord.Embed(title = "Xbox Information", description = f"Requested by Operator: {author.mention}", color =0x18c927)
                    embed.add_field(name = "Information:", value = f"**Gamertag:** {profile.gamertag}\n**Gamerscore:** {profile.gamerscore} \n**XUID:** {profile.xuid}")
                    embed.add_field(name = "Profile Links", value = f"**XBOX Lookup:** https://xboxgamertag.com/search/{GT} \n**XBOX Profile:** https://account.xbox.com/en-us/profile?gamertag={GT}")
                    embed.set_thumbnail(url = profile.gamerpic)
                    await ctx.send(embed =embed)
                return
            else:
                for emoji in reactions:
                    await msg.clear_reaction(emoji)
                await ctx.send("Please enter the XUID")
                messageopt2 = await self.bot.wait_for('message', check=check)
                messageopt1c = messageopt2.content
                
                try:
                    messageopt1c = int(messageopt1c)
                except:
                    messageopt1c = int(messageopt1c, 16)
                else:
                    messageopt1c = messageopt2.content

                try:
                    profile = xbox.GamerProfile.from_xuid(messageopt1c)
                    gamertagvalue = profile.gamertag
                    GT = gamertagvalue.replace(" ", "-")
                except xbox.exceptions.GamertagNotFound:
                    embed = discord.Embed(title = "Xbox Information", description = f"Requested by Operator: {author.mention}", color =0x18c927)
                    embed.add_field(name = "Information", value = "No results found!")
                    await ctx.send(embed = embed)
                else:
                    embed = discord.Embed(title = "Xbox Information", description = f"Requested by Operator: {author.mention}", color =0x18c927)
                    embed.add_field(name = "Information:", value = f"**Gamertag:** {profile.gamertag}\n**Gamerscore:** {profile.gamerscore} \n**XUID:** {profile.xuid}")
                    embed.add_field(name = "Profile Links", value = f"**XBOX Lookup:** https://xboxgamertag.com/search/{GT} \n**XBOX Profile:** https://account.xbox.com/en-us/profile?gamertag={GT}")
                    embed.set_thumbnail(url = profile.gamerpic)
                    await ctx.send(embed =embed)
                return


        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")


def setup(bot):
    bot.add_cog(GamertagCMD(bot))
