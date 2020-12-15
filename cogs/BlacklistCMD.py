import discord
from discord.ext import commands
from datetime import datetime
import time

#--------------------------------------------------
#pip3 install gspread oauth2client

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

sheet = client.open("MRP Blacklist Data").sheet1
#9 Values to fill

#Template on modfying spreadsheet
'''
row = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
sheet.insert_row(row, 3)  
print("Done.")

cell = sheet.cell(3,1).value
print(cell)
'''
#-----------------------------------------------------


Q1 = "User's Discord: "
Q2 = "User's Discord Long ID: "
Q3 = "User's Gamertag: "
Q4 = "Banned from (realm): "
Q5 = "Known Alts: "
Q6 = "Reason for Ban: "
Q7 = "Date of Incident"
Q8 = "The User has faced a (Temporary/Permanent) ban: "
Q9 = "If the ban is Temporary, the ban ends on: "

QQ1 = "What should I open for you? \n >  **Options:** `Gamertag` / `Discord` / `Combined`"
a_list = []


class BlacklistCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  #Starts the blacklist process.
  @commands.command()
  @commands.has_role("Realm OP")
  async def blacklist(self, ctx):
    a_list = []
    author = ctx.message.author
    guild = ctx.message.guild
    channel = await ctx.author.create_dm()
    #schannel = self.bot.get_channel(778453455848996876)
    
    schannel = self.bot.get_channel(778453455848996876)
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
        await channel.send("I have sent in your blacklist report, thank you! \n*Here is your cookie!* 🍪")
      elif "break" in msg.content:
        schannel.send("Canceled Request...")
        submit_wait = False
          
  
  @blacklist.error
  async def blacklist_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
  
  @commands.command()
  async def blogs(self, ctx):
    author = ctx.message.author
    em = discord.Embed(title = "Google Sheets Link", description = "")

  

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

  @gsearch.error
  async def gsearc_error(self,ctx,error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, you can't run this! You aren't a Realm OP!")

      



def setup(bot):
  bot.add_cog(BlacklistCMD(bot))
