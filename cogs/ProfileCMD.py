import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
import requests
from discord import File

from PIL import Image, ImageDraw, ImageFont
import io

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
tzonecol = 3
xboxcol = 4
psnidcol = 5
switchcol = 6
pokemongocol = 7
chesscol = 8

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
            tzone = profilesheet.cell(userrow, tzonecol).value
            xbox = profilesheet.cell(userrow, xboxcol).value
            psnid = profilesheet.cell(userrow, psnidcol).value
            switch = profilesheet.cell(userrow, switchcol).value
            pokemongo = profilesheet.cell(userrow, pokemongocol).value
            chessdotcom = profilesheet.cell(userrow, chesscol).value
            
            profileembed.set_thumbnail(url=pfp)
            profileembed.add_field(name="Discord", value=discordname, inline=True)
            profileembed.add_field(name="LongID", value=longid, inline=True)
            if tzone != "":
                profileembed.add_field(name="Timezone", value=tzone, inline=True)
            if xbox != "":
                profileembed.add_field(name="XBOX Gamertag", value=xbox, inline=False)
            if psnid != "":
                profileembed.add_field(name="Playstation ID", value=psnid, inline=False) 
            if switch != "":
                profileembed.add_field(name="Switch Friend Code", value=switch, inline=False) 
            if pokemongo != "":
                profileembed.add_field(name="Pokemon Go ID", value=pokemongo, inline=False) 
            if chessdotcom != "":
                profileembed.add_field(name="Chess.com ID", value=chessdotcom, inline=False)      
            if username == ctx.message.author:
                profileembed.set_footer(text="If you want to edit your profile, use the command >profile edit")
            else:
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
    async def edit(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        discordname = str(username.name + "#" + username.discriminator)
        longid = str(username.id)
        tzone = str("")
        xbox = str("")
        psnid = str("")
        switch = str("")
        pokemongo = str("")
        chessdotcom = str("")        

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        
        await channel.send("What would you like to edit?")
        
        message = await channel.send("1️⃣ - Timezone\n2️⃣ - XBOX\n3️⃣ - Playstation ID\n4️⃣ - Switch Friend Code\n5️⃣ - Pokemon GO ID\n6️⃣ - Chess.com ID\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '1️⃣' or str(reaction.emoji) == '2️⃣' or str(reaction.emoji) == '3️⃣' or str(reaction.emoji) == '4️⃣' or str(reaction.emoji) == '5️⃣' or str(reaction.emoji) == '6️⃣' or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
            if str(reaction.emoji) == "❌":
                await ctx.channel.purge(limit=2)
                await channel.send("Okay, nothing will be edited!")
            elif str(reaction.emoji) == "1️⃣":
                def check3(m):
                    return m.content is not None and m.channel == channel and m.author is not self.bot.user

                await ctx.send("What is your Timezone?")
                messagecontent = await self.bot.wait_for('message', check=check3)
                addedid = messagecontent.content

                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    discordname = str(username.name + "#" + username.discriminator)
                    longid = longid
                    tzone = addedid

                    row = [discordname, longid, tzone, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Timezone to to your profile!")
                else:
                    userrow = usercell.row
                    tzone = addedid
                    profilesheet.update_cell(userrow, tzonecol, str(tzone))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Timezone to to your profile!")
            elif str(reaction.emoji) == "2️⃣":
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

                    row = [discordname, longid, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")
                else:
                    userrow = usercell.row
                    xbox = addedid
                    profilesheet.update_cell(userrow, xboxcol, str(xbox))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your XBOX Gamertag to to your profile!")
            elif str(reaction.emoji) == "3️⃣":
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

                    row = [discordname, longid, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your PSN ID to to your profile!")
                else:
                    userrow = usercell.row
                    psnid = addedid
                    profilesheet.update_cell(userrow, psnidcol, str(psnid))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)                    
                    await channel.send("Success!, You have added your PSN ID to to your profile!")
            elif str(reaction.emoji) == "4️⃣":
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
                    switch = addedid

                    row = [discordname, longid, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Switch Friend Code to to your profile!")
                else:
                    userrow = usercell.row
                    switch = addedid
                    profilesheet.update_cell(userrow, switchcol, str(switch))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Switch Friend Code to to your profile!")
            elif str(reaction.emoji) == "5️⃣":
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

                    row = [discordname, longid, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Pokemon Go ID to to your profile!")
                else:
                    userrow = usercell.row
                    pokemongo = addedid
                    profilesheet.update_cell(userrow, pokemongocol, str(pokemongo))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Pokemon Go ID? to to your profile!")
            elif str(reaction.emoji) == "6️⃣":
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

                    row = [discordname, longid, xbox, psnid, switch, pokemongo, chessdotcom]
                    print(row)
                    profilesheet.insert_row(row, 3)

                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Chess.com ID to to your profile!")
                else:
                    userrow = usercell.row
                    chessdotcom = addedid
                    profilesheet.update_cell(userrow, chesscol, str(chessdotcom))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=4)
                    await channel.send("Success!, You have added your Chess.com ID to to your profile!")

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")

    @profile.command()
    async def remove(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        discordname = str(username.name + "#" + username.discriminator)
        longid = str(username.id)
        cellclear = str("")         

        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        
        await channel.send("What would you like to remove?")
        
        message = await channel.send("1️⃣ - Timezone\n2️⃣ - XBOX\n3️⃣ - Playstation ID\n4️⃣ - Switch Friend Code\n5️⃣ - Pokemon GO ID\n6️⃣ - Chess.com ID\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
        reactions = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '1️⃣' or str(reaction.emoji) == '2️⃣' or str(reaction.emoji) == '3️⃣' or str(reaction.emoji) == '4️⃣' or str(reaction.emoji) == '5️⃣' or str(reaction.emoji) == '6️⃣' or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
            if str(reaction.emoji) == "❌":
                await ctx.channel.purge(limit=2)
                await channel.send("Okay, nothing will be removed!")
            elif str(reaction.emoji) == "1️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, tzonecol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed your Timezone from your profile!")
            elif str(reaction.emoji) == "2️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, xboxcol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed your XBOX Gamertag from your profile!")
            elif str(reaction.emoji) == "3️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, psnidcol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed your Playstation ID from your profile!")
            elif str(reaction.emoji) == "4️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, switchcol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed your Switch Friend Code from your profile!")
            elif str(reaction.emoji) == "5️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, pokemongocol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed your Pokemon GO ID from your profile!")
            elif str(reaction.emoji) == "6️⃣":
                try:
                    usercell = profilesheet.find(longid, in_column=2)
                except:
                    await ctx.channel.purge(limit=2)
                    await ctx.send("User has no profile")
                else:
                    userrow = usercell.row
                    profilesheet.update_cell(userrow, chesscol, str(cellclear))
                    profilesheet.update_cell(userrow, discordcol, str(discordname))
                    print("User Found!")
                    await ctx.channel.purge(limit=2)
                    await channel.send("Success!, You have removed Chess.com ID from your profile!")

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")


    @profile.command()
    async def canvas(self, ctx):
        author = ctx.message.author
        #print('\n'.join(dir(ctx)))
        #print('\n'.join(dir(ctx.author)))

        # --- create empty image ---

        #IMAGE_WIDTH = 600
        #IMAGE_HEIGHT = 300

        # create empty image 600x300 
        #image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT)) # RGB, RGBA (with alpha), L (grayscale), 1 (black & white)

        # --- load image from local file ---

        # or load existing image
        image = Image.open('/home/runner/PortalBot-Beta/images/profilebackground2.png')

        # --- load image from url ---

        #import urllib.request    

        #url = 'https://media.discordapp.net/attachments/788873229136560140/801180249748406272/Portal_Design.png?download'

        #response = urllib.request.urlopen(url)
        #image = Image.open(response)  # it doesn't need `io.Bytes` because it `response` has method `read()`
        #print('size:', image.size)

        IMAGE_WIDTH, IMAGE_HEIGHT = image.size
        IMAGE_WIDTH = image.size[0] 

        # --- draw on image ---

        # create object for drawing
        draw = ImageDraw.Draw(image)

        # draw red rectangle with green outline from point (50,50) to point (550,250) #(600-50, 300-50)
        #draw.rectangle([0, 0, IMAGE_WIDTH-50, 50], fill=(255,0,0, 128), outline=(0,255,0))

        # draw text in center
        text = f'Hello {author.name}'

        font = ImageFont.load_default()

        text_width, text_height = draw.textsize(text, font=font)
        x = (IMAGE_WIDTH - text_width)//2
        y = (IMAGE_HEIGHT - text_height)//2

        draw.text( (x, 10), text, fill=(0,0,255), font=font)

        # --- avatar ---

        #print('avatar:', ctx.author.avatar_url)
        #print('avatar:', ctx.author.avatar_url_as(format='jpg'))
        #print('avatar:', ctx.author.avatar_url_as(format='png'))

        AVATAR_SIZE = 128

        # get URL to avatar
        # sometimes `size=` doesn't gives me image in expected size so later I use `resize()`
        avatar_asset = author.avatar_url_as(format='jpg', size=AVATAR_SIZE)

        # read JPG from server to buffer (file-like object)
        buffer_avatar = io.BytesIO()
        await avatar_asset.save(buffer_avatar)
        buffer_avatar.seek(0)

        # read JPG from buffer to Image 
        avatar_image = Image.open(buffer_avatar)

        # resize it 
        avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE)) # 

        x = 0
        y = 0
        image.paste(avatar_image, (x, y))

        # --- sending image ---

        # create buffer
        buffer_output = io.BytesIO()

        # save PNG in buffer
        image.save(buffer_output, format='PNG')    

        # move to beginning of buffer so `send()` it will read from beginning
        buffer_output.seek(0) 

        # send image
        await ctx.send(file=File(buffer_output, 'myimage.png'))


def setup(bot):
    bot.add_cog(ProfileCMD(bot))
