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

discordcol = 1
longidcol = 2
tzonecol = 3
xboxcol = 4
playstationcol = 5
switchcol = 6
pokemongocol = 7
chesscol = 8

# -----------------------------------------------------

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#  Join Messages-----------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
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
        else:
            print(f"Unhandled Server: {member.display_name} | {member.guild.name}")

# profile events ---------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
        username = member
        longid = str(username.id)
        discordname = str(username.name + "#" + username.discriminator)
        
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
           


def setup(bot):
    bot.add_cog(Events(bot))