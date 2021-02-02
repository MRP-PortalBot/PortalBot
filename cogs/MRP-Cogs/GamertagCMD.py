import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
import requests
import xbox
import logging


logger = logging.getLogger(__name__)
# --------------------------------------------------
# pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

gtsheet = client.open("Gamertag Data").sheet1
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


class GamertagCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("GamertagCMD: Cog Loaded!")

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



'''
  #searches gamertags
  @commands.command()
  @commands.has_role("Realm OP")
  async def gsearch(self, ctx):
    author = ctx.message.author
    channel = ctx.message.channel
    guild = ctx.message.guild
     logfile = open("commandlog.txt", "a")
     logfile.write(str(author.name) + " used GSEARCH \n")
     logfile.close()
     searchfile = open("Gamertags.txt", "r")
     SearchResults = discord.Embed(title = "Search Results", description = "Requested by: " + author.mention, color = 0xb10d9f)
    def check(m):
       return m.content is not None and m.channel == channel and m.author is not self.bot.user

     await ctx.send("Specify a User or a Gamertag!")
     message1 = await self.bot.wait_for('message', check=check)

     message1c = message1.content

     if message1c.isdigit():   #DISCORD ID
       for line in searchfile:
         if message1c in line:
          #searchphrase being ID
           Gamertag , ID = line.split(" ")
           newI = Gamertag.replace("\n", "")
           SearchResults.add_field(name = "Gamertag Results", value = "**Xbox Gamertag:** " + "**" + newI + "**" + "\n**Xbox Profile:** https://account.xbox.com/en-us/profile?gamertag=" + newI + "\n**Xbox Lookup:** https://xboxgamertag.com/search/" + newI)
           SearchResults.set_thumbnail(url = guild.icon_url)
           timestamp = datetime.now()
           SearchResults.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
           await ctx.send(embed = SearchResults)
           time.sleep(2)
           return
        else:
          print()

     else:
       for line in searchfile:   #GAMERTAG
         if message1c in line:
           #searchphrase being ID
           Gamertag , ID = line.split(" ")
           newI = ID.replace("\n", "")
           GamertagI = Gamertag.replace("\n" , "")
           SearchResults.add_field(name = "User Results", value = "Username: <@" + newI + "> \nThis user matched up with: **" + GamertagI + "**")
           SearchResults.set_thumbnail(url = guild.icon_url)
           timestamp = datetime.now()
           SearchResults.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
           await ctx.send(embed = SearchResults)
           time.sleep(2)
           return

         else:
           await ctx.send(message1c + " was not found in the database!")
           time.sleep(1)
           newI = message1c
           SearchResults.add_field(name = "Gamertag Search Failed", value = "**Xbox Gamertag:** " + "**" + newI + "**" + "\n**Xbox Profile:** https://account.xbox.com/en-us/profile?gamertag=" + newI + "\n**Xbox Lookup:** https://xboxgamertag.com/search/" + newI)
           SearchResults.set_thumbnail(url = guild.icon_url)
           timestamp = datetime.now()
           SearchResults.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
           await ctx.send(embed = SearchResults)
           time.sleep(2)
           return

  @gtsearch.error
  async def gtsearc_error(self,ctx,error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, you can't run this! You aren't a Realm OP!")
'''
'''
#Starts the blacklist process.
  @commands.command()
  @commands.has_role("Realm OP")
  async def blacklist(self, ctx):
    a_list = []
    author = ctx.message.author
    guild = ctx.message.guild
    channel = await ctx.author.create_dm()
    #schannel = self.bot.get_channel(778453455848996876)

    schannel = self.bot.get_channel(590226302171349003)
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

    #Spreadsheet Data
    row = [answer1.content, answer2.content, answer3.content, answer4.content, answer5.content, answer6.content, answer7.content, answer8.content, answer9.content]
    sheet.insert_row(row, 3)

    submit_wait = True
    while submit_wait:
      await channel.send('End of questions, send "**submit**". If you want to cancel, send "**break**".  \nPlease note that the bot is **CASE SENSITIVE**!')
      msg = await self.bot.wait_for('message', check=check)
      if "submit" in msg.content:
        submit_wait = False
        blacklistembed = discord.Embed(title = "Blacklist Report", description = "Sent from: " + author.mention, color = 0xb10d9f)
        blacklistembed.add_field(name = "Questions", value = f'**{Q1}** \n {answer1.content} \n\n'
        f'**{Q2}** \n {answer2.content} \n\n'
        f'**{Q3}** \n {answer3.content} \n\n'
        f'**{Q4}** \n {answer4.content} \n\n'
        f'**{Q5}** \n {answer5.content} \n\n'
        f'**{Q6}** \n {answer6.content} \n\n'
        f'**{Q7}** \n {answer7.content} \n\n'
        f'**{Q8}** \n {answer8.content} \n\n'
        f'**{Q9}** \n {answer9.content} \n\n')
        timestamp = datetime.now()
        blacklistembed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        await schannel.send(embed = blacklistembed)
        await channel.send("I have sent in your blacklist report, thank you! \n**Response Record:** https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit#gid=0&range=D3 \n*Here is your cookie!* 🍪")
      elif "break" in msg.content:
        schannel.send("Canceled Request...")
        submit_wait = False


  @blacklist.error
  async def blacklist_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
'''


def setup(bot):
    bot.add_cog(GamertagCMD(bot))
