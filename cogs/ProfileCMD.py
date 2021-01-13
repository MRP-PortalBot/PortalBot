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

profilesheet = client.open("PortalbotProfile").sheet1
sheet = client.open("MRP Blacklist Data").sheet1
# 3 Values to fill

# Template on modfying spreadsheet
'''
gtrow = ["1", "2", "3"]
profilesheet.insert_row(row, 3)
print("Done.")

gtcell = sheet.cell(3,1).value
print(cell)
'''
# -----------------------------------------------------

discordcol = 1
longidcol = 2
xboxcol = 3
psnidcol = 4
nnidcol = 5
pokemongocol = 6
chesscol = 7

# -----------------------------------------------------

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
        if username.nick == None:
            anick = str(username.name)
        else:
            anick = str(username.nick)

        longid = str(username.id)        
        pfp = username.avatar_url
        profileembed = discord.Embed(
            title=anick + "'s Profile", description="=======================", color=0x18c927)
        username_re = re.compile(r'(?i)' + '(?:' + aname + ')')

        try:
            usercell = profilesheet.find(username_re, in_column=1)
        except:
            print("User Not Found")
            noprofileembed = discord.Embed(
            title="Sorry", description=author.mention + "\n" + "No user by that name has been found.", color=0x18c927)
            await ctx.send(embed=noprofileembed) 
        else:
            print("User Found!")

            userrow = usercell.row
            discordname = profilesheet.cell(userrow, discordcol).value
            longid = profilesheet.cell(userrow, longidcol).value
            xbox = profilesheet.cell(userrow, xboxcol).value
            psnid = profilesheet.cell(userrow, psnidcol).value
            nnid = profilesheet.cell(userrow, nnidcol).value
            pokemongo = profilesheet.cell(userrow, pokemongocol).value
            chessdotcom = profilesheet.cell(userrow, chesscol).value
            
            profileembed.set_thumbnail(url=pfp)
            profileembed.add_field(name="Discord", value=discordname, inline=True)
            profileembed.add_field(name="LongID", value=longid, inline=True)
            if xbox != "":
                profileembed.add_field(name="XBOX Gamertag", value=xbox, inline=False)
            if psnid != "":
                profileembed.add_field(name="Playstation ID", value=psnid, inline=False) 
            if nnid != "":
                profileembed.add_field(name="Nintendo Network ID", value=nnid, inline=False) 
            if pokemongo != "":
                profileembed.add_field(name="Pokemon Go ID", value=pokemongo, inline=False) 
            if chessdotcom != "":
                profileembed.add_field(name="Chess.com ID", value=chessdotcom, inline=False)      
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
    async def add(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        discordname = str(username.name)
        longid = str(username.id)
        xbox = str("")
        psnid = str("")
        nnid = str("")
        pokemongo = str("")
        chessdotcom = str("")        

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        
        await channel.send("What would you like to add?")
        
        message = await channel.send("1️⃣ - XBOX\n2️⃣ - Playstation ID\n3️⃣ - Nintendo Network ID\n4️⃣ - Pokemon GO ID\n5️⃣ - Chess.com ID\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '1️⃣' or str(reaction.emoji) == '2️⃣' or str(reaction.emoji) == '3️⃣' or str(reaction.emoji) == '4️⃣' or str(reaction.emoji) == '5️⃣' or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
            if str(reaction.emoji) == "❌":
                await channel.send("Okay, nothing will be removed!")
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                return
            elif str(reaction.emoji) == "1️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your XBOX Gamertag?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    xbox = addedid

                    row = [discordname, longid, xbox, psnid, nnid, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
                else:
                    userrow = usercell.row
                    xbox = addedid
                    profilesheet.update_cell(userrow, xboxcol, str(xbox))
                    print("User Found!")
                    await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
            elif str(reaction.emoji) == "2️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your PSN ID?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    psnid = addedid

                    row = [discordname, longid, xbox, psnid, nnid, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await channel.send("Success!, You have added your PSN ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
                else:
                    userrow = usercell.row
                    psnid = addedid
                    profilesheet.update_cell(userrow, psnidcol, str(psnid))
                    print("User Found!")
                    await channel.send("Success!, You have added your PSN ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
            elif str(reaction.emoji) == "3️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your Nintendo Network ID?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    nnid = addedid

                    row = [discordname, longid, xbox, psnid, nnid, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await channel.send("Success!, You have added your Nintendo Network ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
                else:
                    userrow = usercell.row
                    nnid = addedid
                    profilesheet.update_cell(userrow, nnidcol, str(nnid))
                    print("User Found!")
                    await channel.send("Success!, You have added your Nintendo Network ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
            elif str(reaction.emoji) == "4️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your Pokemon GO ID?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    pokemongo = addedid

                    row = [discordname, longid, xbox, psnid, nnid, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await channel.send("Success!, You have added your Pokemon Go ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
                else:
                    userrow = usercell.row
                    pokemongo = addedid
                    profilesheet.update_cell(userrow, pokemongocol, str(pokemongo))
                    print("User Found!")
                    await channel.send("Success!, You have added your Pokemon Go ID? to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
            elif str(reaction.emoji) == "5️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your Chess.com ID?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    chessdotcom = addedid

                    row = [discordname, longid, xbox, psnid, nnid, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await channel.send("Success!, You have added your Chess.com ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return
                else:
                    userrow = usercell.row
                    chessdotcom = addedid
                    profilesheet.update_cell(userrow, chesscol, str(chessdotcom))
                    print("User Found!")
                    await channel.send("Success!, You have added your Chess.com ID to to your profile!")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    return            

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")

    @profile.command()
    async def remove(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        aname = str(username.name)
        longid = str(username.id)
        cellclear = str("")        

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        
        await channel.send("What would you like to remove")
        
        message = await channel.send("1️⃣ - XBOX\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['1️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
            if str(reaction.emoji) == "❌":
                await channel.send("Okay, nothing will be removed!")
                for emoji in reactions:
                    await message.clear_reaction(emoji)
                return
            else:
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    await ctx.send("User has no profile")
                else:
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
                    userrow = usercell.row
                    xbox = cellclear
                    profilesheet.update_cell(userrow, xboxcol, str(xbox))
                    print("User Found!")
                    await channel.send("Success!, You have removed XBOX Gamertag from your profile!")

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")




    @commands.command()
    async def getprofile(self, ctx, user: discord.User = None):

        if user is None:
            user = ctx.author
        accounts = discord.user.Profile.connected_accounts
        print(accounts)
        await ctx.send(accounts)

def setup(bot):
    bot.add_cog(ProfileCMD(bot))
