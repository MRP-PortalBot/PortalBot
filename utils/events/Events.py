import discord
from discord.ext import commands

from core.common import load_config
from core.logging_module import get_log

config, _ = load_config()
import logging
from core import database

_log = get_log(__name__)
# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

try:
    gtsheet = client.open("PortalbotProfile").sheet1
    sheet = client.open("MRP Bannedlist Data").sheet1
except Exception as e:
    _log.error(f"Error: {e}")
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

entryidcol = 1
discordcol = 2
longidcol = 3
tzonecol = 4
xboxcol = 5
psnidcol = 6
nnidcol = 7
pokemongocol = 8
chesscol = 9

IPlinks = [
    "turtletest.com", "grabify.link", "lovebird.gutu", "dateing.club",
    'otherhalf.life', 'shrekis.life', 'headshot.monster', 'gaming-at-my.best',
    'progaming.monster', 'yourmy.monster', 'screenshare.host',
    'imageshare.best', 'screenshot.best', 'gamingfun.me', 'catsnthing.com',
    'mypic.icu', 'catsnthings.fun', 'curiouscat.club', 'joinmy.site',
    'fortnitechat.site', 'fortnight.space', 'freegiftcards.co', 'stopify.co',
    'leancoding.co', 'bit.ly', 'shorte.st', 'adf.lv', 'bc.vc', 'bit.do',
    'soo.gd', '7.ly', '5.gp', 'tiny.cc', 'ouo.io', 'zzb.bz', 'adfoc.us',
    'my.su', 'goo.gl'
]
discordLink = ['discord.gg']


# -----------------------------------------------------


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #  Join Messages-----------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(ctx, self, member):
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
        longid = str(member.id)
        discordname = str(username.name + "#" + username.discriminator)

        # ----Database------------------------------------------------

        try:
            database.db.connect(reuse_if_open=True)
            profile: database.PortalbotProfile = database.PortalbotProfile.select(
            ).where(database.PortalbotProfile.DiscordLongID == longid).get()
            profile.DiscordName = discordname
            profile.save()
            await channel.send(
                f"{profile.DiscordName}'s Profile has been modified successfully."
            )
        except database.DoesNotExist:
            try:
                database.db.connect(reuse_if_open=True)
                profile: database.PortalbotProfile = database.PortalbotProfile.create(
                    DiscordName=discordname, DiscordLongID=longid)
                profile.save()
                await channel.send(
                    f"{profile.DiscordName}'s Profile has been created successfully."
                )
            except database.IntegrityError:
                await channel.send("That profile name is already taken!")
        finally:
            database.db.close()

        # ----GSheets------------------------------------------------

        try:
            usercell = gtsheet.find(longid, in_column=3)
        except:
            entryid = (int(gtsheet.acell('A2').value) + 1)
            row = [entryid, discordname, longid]
            print(row)
            gtsheet.insert_row(row, 2)
        else:
            userrow = usercell.row
            gtsheet.update_cell(userrow, discordcol, str(discordname))
            gtsheet.update_cell(userrow, longidcol, str(longid))

        # ------Welcome Message:---------
        if member.guild.id == 587495640502763521:
            guild = self.bot.get_guild(587495640502763521)
            channel = guild.get_channel(588813558486269956)
            count = int(member.guild.member_count) + 1
            embed = discord.Embed(
                title=f"Welcome to the {member.guild.name}!",
                description=
                f"**{str(member.display_name)}** is the **{str(count)}**th member!",
                color=0xb10d9f)
            embed.add_field(
                name="Looking for a Realm?",
                value="Check out the Realm list in <#588070315117117440>!",
                inline=False)
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text="Join the MRP Community Realm!!!",
                             icon_url=member.guild.icon.url)
            await channel.send(embed=embed)
        elif member.guild.id == 192052103017922567:
            guild = self.bot.get_guild(192052103017922567)
            channel = guild.get_channel(796115065622626326)
            count = int(member.guild.member_count) + 1
            embed = discord.Embed(
                title=f"Welcome to the {member.guild.name}!",
                description=f"**{str(member.display_name)}** is ready to game!",
                color=0xFFCE41)
            embed.add_field(
                name="Want to see more channels?",
                value=
                "Check out the Game list in <#796114173514743928>, and react to a game to join the channel!",
                inline=False)
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(
                text="Got any questions? Feel free to ask in the Gaming Hub!",
                icon_url=member.guild.icon.url)
            await channel.send(embed=embed)
        elif member.guild.id == 448488274562908170:
            print("here!")
        else:
            print(
                f"Unhandled Server: {member.display_name} | {member.guild.name}"
            )

    """@commands.Cog.listener()
    async def on_message(self, message):
        msg = message.content
        message_content = message.content.strip().lower()
        for link in IPlinks:
            link = link.lower()
            if link in message_content:
                await message.delete()
                embed = discord.Embed(title="⚠️ Warning!",
                                      description="Suspicious Link Detected!",
                                      color=0xf05c07)
                embed.add_field(
                    name=f"WARNING:",
                    value=
                    f"{message.author.mention}: \nPlease DO NOT Send IP Grabbers!"
                )
                await message.channel.send(embed=embed)
                channel = self.bot.get_channel(config["ModReport"])
                embed2 = discord.Embed(
                    title="Suspicious Link Detected",
                    description=
                    f"**Information:**\n\n**Author:** {message.author.mention}\**Channel:** {message.channel.mention}\n**Link:** {msg}",
                    color=0xf05c07)
                await channel.send(embed=embed2)

        if message.content.lower() == 'discord.gg':
            RealmOP = discord.utils.get(message.guild.roles, name='Realm OP')
            Bots = discord.utils.get(message.guild.roles, name='Bots')
            Moderator = discord.utils.get(message.guild.roles,
                                          name='Moderator')
            Admin = discord.utils.get(message.guild.roles, name='Admin')

            if RealmOP in message.author.roles or Bots in message.author.roles or Moderator in message.author.roles or Admin in message.author.roles:
                print("Ignored Server Invite")
                return
            else:
                await message.delete()
                embed = discord.Embed(
                    title="⚠️ Warning!",
                    description="Advertisement Is Not Allowed!",
                    color=0xf05c07)
                embed.add_field(
                    name=f"WARNING:",
                    value=
                    f"{message.author.mention}: \n**Please DO NOT send server links here!** \n*If you would like to advertise your realm, please apply for one using the >applyrealm command!*"
                )
                embed.set_footer(
                    text=
                    "Reading the rules again will help you avoid any warnings!"
                )
                await message.channel.send(embed=embed)

                channel = self.bot.get_channel(config["ModReport"])
                embed2 = discord.Embed(
                    title="Discord Server Link Detected",
                    description=
                    f"**Information:**\n\n**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Link:** {msg}",
                    color=0xf05c07)
                await channel.send(embed=embed2)

        #await self.bot.process_commands(message)"""


async def setup(bot):
    await bot.add_cog(Events(bot))
