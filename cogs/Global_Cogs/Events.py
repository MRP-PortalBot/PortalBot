import discord
from discord.ext import commands
from datetime import datetime, timezone
import time
import re
import asyncio
from discord import Embed
import requests
from core.common import load_config
config, _ = load_config()
import logging
from core import database, common

logger = logging.getLogger(__name__)
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

discordcol = 1
longidcol = 2
tzonecol = 3
xboxcol = 4
psnidcol = 5
nnidcol = 6
pokemongocol = 7
chesscol = 8

IPlinks = ["turtletest.com","grabify.link", "lovebird.gutu", "dateing.club", 'otherhalf.life','shrekis.life','headshot.monster','gaming-at-my.best','progaming.monster','yourmy.monster','screenshare.host','imageshare.best','screenshot.best','gamingfun.me','catsnthing.com','mypic.icu','catsnthings.fun','curiouscat.club','joinmy.site','fortnitechat.site','fortnight.space','freegiftcards.co','stopify.co','leancoding.co','bit.ly','shorte.st','adf.lv','bc.vc','bit.do','soo.gd','7.ly','5.gp','tiny.cc','ouo.io','zzb.bz','adfoc.us','my.su','goo.gl']
# -----------------------------------------------------

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Events: Cog Loaded!")

#  Join Messages-----------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
    #    username = member
    #    longid = str(username.id)
    #    discordname = str(username.name + "#" + username.discriminator)

    #    database.db.connect(reuse_if_open=True)
    #    q: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.create(DiscUsername=answer1.content, DiscID = answer2.content, Gamertag = answer3.content, BannedFrom = answer4.content, KnownAlts = answer5.content , ReasonforBan = answer6.content, DateofIncident = answer7.content, TypeofBan = answer8.content, DatetheBanEnds = answer9.content, BanReason = author.name)
     #   q.save()
     #   database.db.close()
        guild = member.guild
        channel = discord.utils.get(guild.channels, name="member-log")
        username = member
        longid = str(username.id)
        discordname = str(username.name + "#" + username.discriminator)     
        
        #----Database------------------------------------------------

        try:
            database.db.connect(reuse_if_open=True)
            profile: database.PortalbotProfile = database.PortalbotProfile.select().where(
                database.PortalbotProfile.DiscordLongID == longid).get()
            profile.DiscordName = discordname
            profile.save()
            await channel.send(f"{profile.DiscordName}'s Profile has been modified successfully.")
        except database.DoesNotExist:
            try:
                database.db.connect(reuse_if_open=True)
                profile: database.PortalbotProfile = database.PortalbotProfile.create(
                    DiscordName=discordname, DiscordLongID=longid)
                profile.save()
                await channel.send(f"{profile.DiscordName}'s Profile has been created successfully.")
            except database.IntegrityError:
                await channel.send("That profile name is already taken!")
        finally:
            database.db.close()
        
        #----GSheets------------------------------------------------
       
        try:
            usercell = gtsheet.find(longid, in_column=2)
        except:
            row = [discordname, longid]
            print(row)
            gtsheet.insert_row(row, 3)
        else:
            userrow = usercell.row
            gtsheet.update_cell(userrow, discordcol, str(discordname))
            gtsheet.update_cell(userrow, longidcol, str(longid))

        #------Welcome Message:---------
        if member.guild.id == 587495640502763521:
            guild = self.bot.get_guild(587495640502763521)
            channel = guild.get_channel(588813558486269956)
            count = int(member.guild.member_count) + 1
            embed = discord.Embed(title = f"Welcome to the {member.guild.name}!", description = f"**{str(member.display_name)}** is the **{str(count)}**th member!", color = 0xb10d9f)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text = "Got any questions? Feel free to ask a Moderator!",icon_url = member.guild.icon_url)
            await channel.send(embed=embed)
        elif member.guild.id == 192052103017922567:
            guild = self.bot.get_guild(192052103017922567)
            channel = guild.get_channel(796115065622626326)
            count = int(member.guild.member_count) + 1
            embed = discord.Embed(title = f"Welcome to the {member.guild.name}!", description = f"**{str(member.display_name)}** is the **{str(count)}**th member!", color = 0xFFCE41)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text = "Got any questions? Feel free to ask a Moderator!",icon_url = member.guild.icon_url)
            await channel.send(embed=embed)    
        elif member.guild.id == 448488274562908170:
            print("here!")
        else:
            print(f"Unhandled Server: {member.display_name} | {member.guild.name}")



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot or message.guild.id == 192052103017922567 or message.guild == None:
            return
        msg = message.content
        message_content = message.content.strip().lower()
        for link in IPlinks:
            link = link.lower()
            if link in message_content:
                await message.delete()
                embed = discord.Embed(title = "⚠️ Warning!", description = "Suspicious Link Detected!", color = 0xf05c07)
                embed.add_field(name = f"WARNING:", value = f"{message.author.mention}: \nPlease DO NOT Send IP Grabbers!")
                await message.channel.send(embed = embed)
                channel = self.bot.get_channel(config["ModReport"])
                embed2 = discord.Embed(title = "Suspicious Link Detected", description = f"Information:\nAuthor: {message.author.mention}\nChannel: {message.channel.mention}\nLink: {msg}" ,color =0xf05c07)
                await channel.send(embed =embed2)


        #await self.bot.process_commands(message)



def setup(bot):
    bot.add_cog(Events(bot))