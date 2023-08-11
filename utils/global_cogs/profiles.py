import asyncio
import io
import logging
import re

import discord
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands

from core import database
from core.logging_module import get_log

_log = get_log(__name__)

#---------------------------------------------------

background_image = Image.open('./core/images/profilebackground2.png')
background_image = background_image.convert('RGBA')
#fontfile = './fonts/gameria.ttf'

# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

try:
    profilesheet = client.open("PortalbotProfile").sheet1
    sheet = client.open("MRP Bannedlist Data").sheet1
except Exception as e:
    _log.error(f"Error: {e}")
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

entryidcol = 1
discordcol = 2
longidcol = 3
tzonecol = 4
xboxcol = 5
psnidcol = 6
switchcol = 7
pokemongocol = 8
chesscol = 9

# -----------------------------------------------------


class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, profile: discord.Member = None):
        print(profile)
        databaseData = [
            database.PortalbotProfile.DiscordName,
            database.PortalbotProfile.DiscordLongID,
            database.PortalbotProfile.Timezone, database.PortalbotProfile.XBOX,
            database.PortalbotProfile.Playstation,
            database.PortalbotProfile.Switch,
            database.PortalbotProfile.PokemonGo,
            database.PortalbotProfile.Chessdotcom,
            database.PortalbotProfile.entryid
        ]
        blacklistdata = [database.MRP_Blacklist_Data.DiscID]
        ResultsGiven = False
        author = ctx.message.author
        role = discord.utils.get(ctx.guild.roles, name="Realm OP")
        channel = ctx.message.channel
        adminchannel = ctx.guild.get_channel(778710730580557847)

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
        print(longid)
        pfp = username.avatar.url
        profileembed = discord.Embed(title=anick + "'s Profile",
                                     description="=======================",
                                     color=0x18c927)
        username_re = re.compile(r'(?i)' + '(?:' + aname + ')')

        query = (database.PortalbotProfile.select().where(
            database.PortalbotProfile.DiscordLongID.contains(longid)))
        if query.exists():
            for p in query:
                discordname = p.DiscordName
                longid = p.DiscordLongID
                tzone = p.Timezone
                xbox = p.XBOX
                psnid = p.Playstation
                switch = p.Switch
                pokemongo = p.PokemonGo
                chessdotcom = p.Chessdotcom

                profileembed.set_thumbnail(url=pfp)
                profileembed.add_field(name="Discord",
                                       value=discordname,
                                       inline=True)
                profileembed.add_field(name="LongID",
                                       value=longid,
                                       inline=True)
                if tzone != "None":
                    profileembed.add_field(name="Timezone",
                                           value=tzone,
                                           inline=True)
                if xbox != "None":
                    profileembed.add_field(name="XBOX Gamertag",
                                           value=xbox,
                                           inline=False)
                if psnid != "None":
                    profileembed.add_field(name="Playstation ID",
                                           value=psnid,
                                           inline=False)
                if switch != "None":
                    profileembed.add_field(name="Switch Friend Code",
                                           value=switch,
                                           inline=False)
                if pokemongo != "None":
                    profileembed.add_field(name="Pokemon Go ID",
                                           value=pokemongo,
                                           inline=False)
                if chessdotcom != "None":
                    profileembed.add_field(name="Chess.com ID",
                                           value=chessdotcom,
                                           inline=False)
                if username == ctx.message.author:
                    profileembed.set_footer(
                        text=
                        "If you want to edit your profile, use the command >profile edit"
                    )
                else:
                    profileembed.set_footer(text="Requested by " + author.name)
                #if role in author.roles and adminchannel == channel:
                #   qID = (database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.DiscID.contains(longid)))
                #  qNAME = (database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.DiscUsername.contains(discordname)))
                # qNAME2 = (database.MRP_Blacklist_Data.select().where(database.MRP_Blacklist_Data.DiscUsername.contains(aname)))
                # if qID.exists() or qNAME.exists() or qNAME2.exists():
                #    profileembed.add_field(name="BANNED PLAYER", value="Player is on the banned players list", inline=False)
                #   await ctx.send(embed=profileembed)
                #  else:
                #     await ctx.send(embed=profileembed)
                #else:
                await ctx.send(embed=profileembed)
        else:
            noprofileembed = discord.Embed(
                title="Sorry",
                description=author.mention + "\n" +
                "No user by that name has been found.",
                color=0x18c927)
            await ctx.send(embed=noprofileembed)

    @profile.error
    async def profile_error(self, ctx, error):
        author = ctx.message.author
        if isinstance(error, commands.UserNotFound):
            noprofileembed = discord.Embed(
                title="Sorry",
                description=author.mention + "\n" +
                "No user by that name has been found.",
                color=0x18c927)
            await ctx.send(embed=noprofileembed)

        else:
            raise error

    @profile.command()
    async def edit(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        discordname = str(username.name + "#" + username.discriminator)
        longid = str(username.id)

        def purgecheck(m):
            return m.author == username or m.author == self.bot.user

        await channel.send("What would you like to edit?")

        message = await channel.send(
            "1️⃣ - Timezone\n2️⃣ - XBOX\n3️⃣ - Playstation ID\n4️⃣ - Switch Friend Code\n5️⃣ - Pokemon GO ID\n6️⃣ - Chess.com ID\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* "
        )
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (
                str(reaction.emoji) == '1️⃣' or str(reaction.emoji) == '2️⃣'
                or str(reaction.emoji) == '3️⃣' or str(reaction.emoji) == '4️⃣'
                or str(reaction.emoji) == '5️⃣' or str(reaction.emoji) == '6️⃣'
                or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add',
                                                     timeout=60.0,
                                                     check=check2)
            if str(reaction.emoji) == "❌":
                await ctx.channel.purge(limit=2, check=purgecheck)
                await channel.send("Okay, nothing will be edited!")
            elif str(reaction.emoji) == "1️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your Timezone?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Timezone = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your Timezone to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            timezone=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Timezone to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "2️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your XBOX Gamertag?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.XBOX = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your XBOX Gamertag to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            XBOX=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your XBOX Gamertag to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "3️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your PSN ID?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Playstation = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your Playstation ID to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            Playstation=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Playstation ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "4️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your Nintendo Network ID?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Switch = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your NNID to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            Switch=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your NNID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "5️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your Pokemon GO ID?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.PokemonGo = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your Pokemon Go ID to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            PokemonGo=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Pokemon Go ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "6️⃣":

                def check3(m):
                    return m.content is not None and m.channel == channel and m.author == username

                await ctx.send("What is your Chess.com ID?")
                messagecontent = await self.bot.wait_for('message',
                                                         check=check3)
                addedid = messagecontent.content

                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Chessdotcom = addedid
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have added your Chess.com ID to to your profile!"
                    )
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname,
                            DiscordLongID=longid,
                            Chessdotcom=addedid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

        except asyncio.TimeoutError:
            await channel.send(
                "Looks like you didn't react in time, please try again later!")

    @profile.command()
    async def remove(self, ctx):
        channel = ctx.message.channel
        username = ctx.message.author
        discordname = str(username.name + "#" + username.discriminator)
        longid = str(username.id)
        cellclear = str("")

        def purgecheck(m):
            return m.author == username or m.author == self.bot.user

        await channel.send("What would you like to remove?")

        message = await channel.send(
            "1️⃣ - Timezone\n2️⃣ - XBOX\n3️⃣ - Playstation ID\n4️⃣ - Switch Friend Code\n5️⃣ - Pokemon GO ID\n6️⃣ - Chess.com ID\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* "
        )
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (
                str(reaction.emoji) == '1️⃣' or str(reaction.emoji) == '2️⃣'
                or str(reaction.emoji) == '3️⃣' or str(reaction.emoji) == '4️⃣'
                or str(reaction.emoji) == '5️⃣' or str(reaction.emoji) == '6️⃣'
                or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add',
                                                     timeout=60.0,
                                                     check=check2)
            if str(reaction.emoji) == "❌":
                await ctx.channel.purge(limit=2)
                await channel.send("Okay, nothing will be removed!")
            elif str(reaction.emoji) == "1️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Timezone = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "2️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.XBOX = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "3️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Playstation = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "4️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Switch = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "5️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.PokemonGo = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

            elif str(reaction.emoji) == "6️⃣":
                try:
                    database.db.connect(reuse_if_open=True)
                    profile: database.PortalbotProfile = database.PortalbotProfile.select(
                    ).where(database.PortalbotProfile.DiscordLongID ==
                            longid).get()
                    profile.DiscordName = discordname
                    profile.Chessdotcom = cellclear
                    profile.save()
                    await ctx.channel.purge(limit=4, check=purgecheck)
                    await channel.send(
                        "Success!, You have edited your profile!")
                except database.DoesNotExist:
                    try:
                        database.db.connect(reuse_if_open=True)
                        profile: database.PortalbotProfile = database.PortalbotProfile.create(
                            DiscordName=discordname, DiscordLongID=longid)
                        profile.save()
                        await ctx.channel.purge(limit=4, check=purgecheck)
                        await channel.send(
                            "Success!, You have added your Chess.com ID to to your profile!"
                        )
                    except database.IntegrityError:
                        await channel.send(
                            "That profile name is already taken!")
                finally:
                    database.db.close()

        except asyncio.TimeoutError:
            await channel.send(
                "Looks like you didn't react in time, please try again later!")

    @profile.command()
    async def canvas(self, ctx, *, profile: discord.Member = None):
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
        pfp = username.avatar.url
        profileembed = discord.Embed(title=anick + "'s Profile",
                                     description="=======================",
                                     color=0x18c927)
        username_re = re.compile(r'(?i)' + '(?:' + aname + ')')

        try:
            usercell = profilesheet.find(username_re, in_column=1)
        except:
            print("User Not Found")
            noprofileembed = discord.Embed(
                title="Sorry",
                description=author.mention + "\n" +
                "No user by that name has been found.",
                color=0x18c927)
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

            AVATAR_SIZE = 128

            # --- duplicate image ----

            image = background_image.copy()

            image_width, image_height = image.size

            # --- draw on image ---

            # create object for drawing

            #draw = ImageDraw.Draw(image)

            # draw red rectangle with alpha channel on new image (with the same size as original image)

            rect_x0 = 20  # left marign
            rect_y0 = 20  # top marign

            rect_x1 = image_width - 20  # right margin
            #rect_y1 = 20 + AVATAR_SIZE - 1  # top margin + size of avatar
            rect_y1 = image_height - 20

            rect_width = rect_x1 - rect_x0
            rect_height = rect_y1 - rect_y0

            rectangle_image = Image.new('RGBA', (image_width, image_height))
            rectangle_draw = ImageDraw.Draw(rectangle_image)

            rectangle_draw.rectangle((rect_x0, rect_y0, rect_x1, rect_y1),
                                     fill=(0, 0, 0, 80))

            # put rectangle on original image

            image = Image.alpha_composite(image, rectangle_image)

            # create object for drawing

            draw = ImageDraw.Draw(
                image
            )  # create new object for drawing after changing original `image`

            # ------PROFILE HEADING-------

            nicktext = anick

            nickfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 40)
            text_width, text_height = draw.textsize(nicktext, font=nickfont)

            if text_width > (rect_width - AVATAR_SIZE):
                nickfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 30)
                text_width, text_height = draw.textsize(nicktext,
                                                        font=nickfont)

            if text_width > (rect_width - AVATAR_SIZE):
                nickfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 20)
                text_width, text_height = draw.textsize(nicktext,
                                                        font=nickfont)

            x = (rect_width - text_width -
                 (AVATAR_SIZE - 28)) // 2  # skip avatar when center text
            y = (AVATAR_SIZE - text_height) // 2

            x += rect_x0 + (AVATAR_SIZE - 28)  # skip avatar when center text
            #y += rect_y0

            draw.text((x, y),
                      nicktext,
                      font=nickfont,
                      fill=(255, 255, 255, 255),
                      stroke_width=1,
                      stroke_fill=(0, 0, 0, 255))

            # --- avatar ---

            # get URL to avatar
            # sometimes `size=` doesn't gives me image in expected size so later I use `resize()`
            avatar_asset = author.avatar.url_as(format='jpg', size=AVATAR_SIZE)

            # read JPG from server to buffer (file-like object)
            buffer_avatar = io.BytesIO(await avatar_asset.read())

            #    buffer_avatar = io.BytesIO()
            #    await avatar_asset.save(buffer_avatar)
            #    buffer_avatar.seek(0)

            # read JPG from buffer to Image
            avatar_image = Image.open(buffer_avatar)

            # resize it
            AVATAR_SIZE_NEW = AVATAR_SIZE - 28
            avatar_image = avatar_image.resize(
                (AVATAR_SIZE_NEW, AVATAR_SIZE_NEW))  #

            circle_image = Image.new('L', (AVATAR_SIZE_NEW, AVATAR_SIZE_NEW))
            circle_draw = ImageDraw.Draw(circle_image)
            circle_draw.ellipse((0, 0, AVATAR_SIZE_NEW, AVATAR_SIZE_NEW),
                                fill=255)
            #avatar_image.putalpha(circle_image)
            #avatar_image.show()

            image.paste(avatar_image, (rect_x0, rect_y0), circle_image)

            # ------PROFILE Components-------

            discordtext = discordname

            discordfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 20)
            text_width, text_height = draw.textsize(discordtext,
                                                    font=discordfont)

            #if text_width > rect_width//2:
            #    discordfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 20)
            #    text_width, text_height = draw.textsize(discordtext, font=discordfont)

            #if text_width > rect_width//2:
            #    discordfont = ImageFont.truetype('./fonts/OpenSansEmoji.ttf', 15)
            #    text_width, text_height = draw.textsize(discordtext, font=discordfont)

            x = rect_x0  # skip avatar when center text
            y = rect_y0 + AVATAR_SIZE

            #x += rect_x0 + AVATAR_SIZE     # skip avatar when center text
            #y += rect_y0

            draw.text((x, y),
                      "Discord Info\n" + discordtext + "\n" + longid,
                      font=discordfont,
                      fill=(255, 255, 255, 255),
                      stroke_width=1,
                      stroke_fill=(0, 0, 0, 255))

            # --- sending image ---

            # create buffer
            buffer_output = io.BytesIO()

            # save PNG in buffer
            image.save(buffer_output, format='PNG')

            # move to beginning of buffer so `send()` it will read from beginning
            buffer_output.seek(0)

            # send image
            await ctx.send(file=File(buffer_output, 'myimage.png'))


async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
