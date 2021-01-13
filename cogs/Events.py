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

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        else:
            print(f"Unhandled Server: {member.display_name} | {member.guild.name}")

# profile events ---------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
        username = member
        alid = str(username.id)
        alidsheet = gtsheet.find(alid, in_column=2)

        if alid == alidsheet:
            print("User already exists in sheet!")
        else:
            discordname = str(username.name + "#" + username.discriminator)
            longid = alid

            row = [discordname, longid]
            print(row)
            gtsheet.insert_row(row, 3)


'''
        try:
            usercell = gtsheet.find(alid, in_column=2)
        except:
            print("User already exists in sheet!")
        else:
            discordname = str(username.name + "#" + username.discriminator)
            longid = alid

            row = [discordname, longid]
            print(row)
            gtsheet.insert_row(row, 3)
'''           


def setup(bot):
    bot.add_cog(Events(bot))