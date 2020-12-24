import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
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

gtsheet = client.open("Gamertag Data").sheet1
#3 Values to fill

#Template on modfying spreadsheet
'''
gtrow = ["1", "2", "3"]
gtsheet.insert_row(row, 3)  
print("Done.")

gtcell = sheet.cell(3,1).value
print(cell)
'''
#-----------------------------------------------------


Q1 = "User's Discord: "
#Savaged, changed the question so it doesn't say not to include the tag number here
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
        await channel.send("Canceled Request...")
        await ctx.send("Canceled Request...")
        submit_wait = False
          
  
  @blacklist.error
  async def blacklist_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
  
  @commands.command()
  @commands.has_role("Realm OP")
  async def bsearch(self, ctx, * , username):
    checkcheck = "FALSE"
    author = ctx.message.author
    em = discord.Embed(title = "Google Sheets Search", description = "Requested by Operator " + author.mention, color = 0x18c927)
    #values_re = re.compile(r'(?i)' + username)
    #print(values_re)
    #'re.Pattern' object is not iterable
    #values = sheet.findall(username)
    values_re = re.compile(r'(?i)' + '(?:' + username + ')')
    print(values_re)
    values = sheet.findall(values_re)
    print(values)
    try:
      checkempty = ', '.join(sheet.row_values(sheet.find(values_re).row))
      print(checkempty)
    except:
      checkcheck = "TRUE"
    print(checkcheck)
    if checkcheck == "FALSE":
      for r in values:
        output = ', '.join(sheet.row_values(r.row))
        print(output)
        A1, A2, A3, A4, A5, A6, A7, A8 ,A9 = output.split(", ")
        em.add_field(name = "Results: \n",value = "```autohotkey\n" + "Discord Username: " + str(A1) + "\nDiscord ID: " + str(A2) + "\nGamertag: " + str(A3) +"\nBanned From: " + str(A4) + "\nKnown Alts: " + str(A5) + "\nBan Reason: " + str(A6) + "\nDate of Ban: " + str(A7) + "\nType of Ban: " + str(A8) + "\nDate the Ban Ends: " + str(A9) + "\n```",inline = False) 
      await ctx.send(embed = em)
    else:
      em.add_field(name = "No Results", value = "I'm sorry, but it looks like the [spreadsheet](https://docs.google.com/spreadsheets/d/1WKplLqk2Tbmy_PeDDtFV7sPs1xhIrySpX8inY7Z1wzY/edit?usp=sharing) doesn't have any results for the query you have sent! \n\n**Tips:**\n- Don't include the user's tag number! (Ex: #1879)\n- Try other ways of spelling out the username such as putting everything as lowercase! \n- Try checking the orginal spreadsheet for the value and try searching any term in the row here!")
      await ctx.send(embed = em)
   
  @bsearch.error
  async def bsearch_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")   
    elif isinstance(error, commands.CommandInvokeError):
      await ctx.send("Your search returned to many results. Please narrow your search, or try a different search term.") 

  async def populate_embed(self, embed, starting_point):
    """Used to populate the embed for the 'blogs' command."""
    i = 0
    index = starting_point
    for field in embed.fields:  # cleans embed before rebuilding
      embed.fields.remove(field)
    while i < 3:
      values = sheet.row_values(index)
      embed.add_field(name=f"Row: {index-1}", value=f"```\n {' '.join(values)}")
      index += 1
      i += 1
    return embed, index+1

  @commands.command()
  async def blogsnew(self, ctx):
    """View all data in the blacklist spreadsheet"""
    async def check_reaction(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
    
    author = ctx.message.author
    embed = discord.Embed(title = "MRP Blacklist Data", description = f"Requested by Operator {author.mention}")
    embed, index = await self.populate_embed(embed, 2)
    message = await ctx.send(embed=embed)
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")
    while True:
      try:
        reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check_reaction)
        if str(reaction.emoji) == "▶️":
          embed, index = await self.populate_embed(embed, index)
          await message.edit(embed=embed)
        elif str(reaction.emoji) == "◀️":
          embed, index = await self.populate_embed(embed, index-3)
          await message.edit(embed=embed)
      except asyncio.TimeoutError:  # ends loop after timeout.
          await message.remove_reaction(reaction, user)
          break

  @commands.command()
  async def blogs(self, ctx):
    author = ctx.message.author
    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
    values = sheet.get_all_values()
    #-----------
    current_index = 2
    results = values[current_index:current_index+1]
    results =  ', '.join([str(elem) for elem in results])
    print(results)
    A1, A2, A3, A4, A5, A6, A7, A8 ,A9 = results.split(", ")
    current_index+=1
    results = values[current_index:current_index+1]
    results =  ', '.join([str(elem) for elem in results])
    B1, B2, B3, B4, B5, B6, B7, B8 ,B9 = results.split(", ")
    current_index+=1
    results = values[current_index:current_index+1]
    results =  ', '.join([str(elem) for elem in results])
    C1, C2, C3, C4, C5, C6, C7, C8 ,C9 = results.split(", ")
    current_index+=1
    #-----------
    embed = discord.Embed(title = "MRP Blacklist Data", description = "Requested by Operator " + author.mention)
    embed.add_field(name = "Spreadsheet", value = "```\n" + A1 + A2 + A3 + A4 + A5 + A6 + A7 + A8 + A9 + "\n" + B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9 + "\n" + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8 + C9 + "\n```")
    #Replace these 2 lines
    #message = await ctx.send(values[current_index:current_index+3])
    message = await ctx.send(embed = embed)
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")
    
    while True:
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            # waiting for a reaction to be added - times out after x seconds, 60 in this
            # example

            if str(reaction.emoji) == "▶️":
                results = values[current_index:current_index+1]
                results =  ', '.join([str(elem) for elem in results])
                A1, A2, A3, A4, A5, A6, A7, A8 ,A9 = results.split(", ")
                current_index+=1
                results = values[current_index:current_index+1]
                results =  ', '.join([str(elem) for elem in results])
                B1, B2, B3, B4, B5, B6, B7, B8 ,B9 = results.split(", ")
                current_index+=1
                results = values[current_index:current_index+1]
                results =  ', '.join([str(elem) for elem in results])
                C1, C2, C3, C4, C5, C6, C7, C8 ,C9 = results.split(", ")
                current_index+=1
                #embed.add_field(name = "Spreadsheet", value = "```\n" + A1 + A2 + A3 + A4 + A5 + A6 + A7 + A8 + A9 + "\n" + B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9 + "\n" + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8 + C9 + "\n```")
                newembed = discord.Embed(title = "MRP Blacklist Data", description = "Requested by Operator " + author.mention)
                newembed.add_field(name = "Spreadsheet", value = "```\n" + A1 + A2 + A3 + A4 + A5 + A6 + A7 + A8 + A9 + "\n" + B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9 + "\n" + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8 + C9 + "\n```")
                await message.edit(embed = newembed)
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == "◀️":
                results = values[current_index:current_index-1]
                results =  ', '.join([str(elem) for elem in results])
                print(results)
                A1, A2, A3, A4, A5, A6, A7, A8 ,A9 = results.split(", ")
                current_index-=1
                results = values[current_index:current_index-1]
                results =  ', '.join([str(elem) for elem in results])
                B1, B2, B3, B4, B5, B6, B7, B8 ,B9 = results.split(", ")
                current_index-=1
                results = values[current_index:current_index-1]
                results =  ', '.join([str(elem) for elem in results])
                C1, C2, C3, C4, C5, C6, C7, C8 ,C9 = results.split(", ")
                current_index-=1
                #embed.add_field(name = "Spreadsheet", value = "```\n" + A1 + A2 + A3 + A4 + A5 + A6 + A7 + A8 + A9 + "\n" + B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9 + "\n" + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8 + C9 + "\n```")
                newembed = discord.Embed(title = "MRP Blacklist Data", description = "Requested by Operator " + author.mention)
                newembed.add_field(name = "Spreadsheet", value = "```\n" + A1 + A2 + A3 + A4 + A5 + A6 + A7 + A8 + A9 + "\n" + B1 + B2 + B3 + B4 + B5 + B6 + B7 + B8 + B9 + "\n" + C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8 + C9 + "\n```")
                await message.edit(embed = newembed)
                await message.remove_reaction(reaction, user)
                                                         
            else:
                await message.remove_reaction(reaction, user)
                # removes reactions if the user tries to go forward on the last page or
                # backwards on the first page
        except asyncio.TimeoutError:
            await message.remove_reaction(reaction, user)
            break
            # ending the loop if user doesn't react after x seconds

  
def setup(bot):
  bot.add_cog(BlacklistCMD(bot))
