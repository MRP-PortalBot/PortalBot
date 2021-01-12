import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
import requests

# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

gtsheet = client.open("PortalbotProfile").sheet1
sheet = client.open("MRP Blacklist Data").sheet1
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

xboxcol = 3

# -----------------------------------------------------

'''
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

    # Add's a gamertag to the database.
    @commands.command()
    async def gtadd(self, ctx, *, gamertag):
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

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        await channel.send("Success! \nWould you like to change your nickname to your gamertag? (If so, you may have to add your emojis to your nickname again!)")
        

        message = await channel.send("✅ - CHANGE NICKNAME\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
            if str(reaction.emoji) == "❌":
                await channel.send("Okay, won't change your nickname!")
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                return
            else:
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                await author.edit(nick=gamertag)
                await ctx.send("Success!")

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")


            

    @gtadd.error
    async def gtadd_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Uh oh, you didn't include all the arguments! ")

'''
class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, profile: discord.Member = None):
        print(profile)
        author = ctx.message.author
        role = discord.utils.get(ctx.guild.roles, name="Realm OP")
        channel = ctx.message.channel

        if profile == None:
            username = ctx.message.author
            print(username)
        else:
            username = profile
            print(username)  

        aname = str(username.name)
        anick = str(username.nick)
        alid = str(username.id)        
        pfp = username.avatar_url
        profileembed = discord.Embed(
            title=anick + "'s Profile", description="=======================", color=0x18c927)
        username_re = re.compile(r'(?i)' + '(?:' + aname + ')')

        try:
            usercell = gtsheet.find(username_re, in_column=1)
        except:
            print("User Not Found")
            noprofileembed = discord.Embed(
            title="Sorry", description=author.mention + "\n" + "No user by that name has been found.", color=0x18c927)
            await ctx.send(embed=noprofileembed) 
        else:
            print("User Found!")

            userrow = usercell.row
            discordname = gtsheet.cell(userrow, 1).value
            longid = gtsheet.cell(userrow, 2).value
            xbox = gtsheet.cell(userrow, xboxcol).value
            
            if xbox == "":
                xbox = "N/A"
            
            profileembed.set_thumbnail(url=pfp)
            profileembed.add_field(name="Discord", value=discordname, inline=True)
            profileembed.add_field(name="LongID", value=longid, inline=True)
            profileembed.add_field(name="XBOX Gamertag", value=xbox, inline=False)     
            profileembed.set_footer(text="Requested by " + author.name)
            if role in author.roles: 
                try:
                    longid = sheet.find(longid, in_column=2)
                except:
                    try:
                        discordname = sheet.find(username_re, in_column=1)
                    except:
                        await ctx.send(embed=profileembed)
                    else:
                        profileembed.add_field(name="BANNED PLAYER", value="Player is on the banned players list", inline=False)
                        await ctx.send(embed=profileembed)
                else:
                    profileembed.add_field(name="BANNED PLAYER", value="Player is on the banned players list", inline=False)
                    await ctx.send(embed=profileembed)
            else:
                await ctx.send(embed=profileembed)


    @profile.error
    async def profile_error(self, ctx, error):
        author = ctx.message.author
        if isinstance(error, commands.UserNotFound):
            noprofileembed = discord.Embed(
            title="Sorry", description=author.mention + "\n" + "No user by that name has been found.", color=0x18c927)
            await ctx.send(embed=noprofileembed)

        else:
            raise error          

    @profile.command()
    async def xbox(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        aname = str(username.name)
        alid = str(username.id)        

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user

        await ctx.send("What is your Gamertag")
        messagecontent = await self.bot.wait_for('message', check=check)
        xboxid = messagecontent.content

        try:
            usercell = gtsheet.find(alid, in_column=2)
        except:
            discordname = str(username.name + "#" + username.discriminator)
            longid = alid
            xbox = xboxid

            row = [discordname, longid, xbox]
            print(row)
            gtsheet.insert_row(row, 3)

            await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")
        else:
            userrow = usercell.row
            xbox = xboxid
            gtsheet.update_cell(userrow, xboxcol, str(xbox))
            print("User Found!")
            await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")




    @commands.command()
    async def getprofile(self, ctx, user: discord.User = None):

        if user is None:
            user = ctx.author
        accounts = discord.user.Profile.connected_accounts
        print(accounts)
        await ctx.send(accounts)

def setup(bot):
    bot.add_cog(ProfileCMD(bot))
