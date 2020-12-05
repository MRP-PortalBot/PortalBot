import discord
from discord.ext import commands
import datetime
from datetime import datetime
import time
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

  @commands.command()
  @commands.has_role("Realm OP")
  async def blacklist(self, ctx):
    a_list = []
    author = ctx.message.author
    guild = ctx.message.guild
    channel = await ctx.author.create_dm()
    schannel = self.bot.get_channel(778453455848996876)
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used BLACKLIST \n")
    logfile.close()
   

    def check(m):
        return m.content is not None and m.channel == channel and m.author is not self.bot.user

    
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

  

    MRPShort = open("MRPDiscord.txt", "a")
    MRPShort.write("`" + str(answer1.content) + "` - `" + str(answer2.content) + "`" + "\n")
    MRPShort.close()
    MRPLong = open("MRPGamertags.txt", "a")
    MRPLong.write("`" + str(answer3.content) + "` \n")
    MRPLong.close()

    MRPLong = open("MRPCombine.txt", "a")
    MRPLong.write("`" + str(answer1.content) + "` - `" + str(answer2.content) + "` - `" + str(answer3.content) + "` - `" + str(answer6.content) + "`" + "\n")
    MRPLong.close()

    MRPLong = open("MRPFull.txt", "a")
    MRPLong.write("`" + str(answer1.content) + "` - `" + str(answer2.content) + "` - `" + str(answer3.content) + "` - `" + str(answer4.content) + "` - `" + str(answer5.content) + "` - `" + str(answer6.content) + "` - `" + str(answer7.content) + "` - `" + str(answer8.content) + "` - `" + str(answer9.content) + "` \n")
    MRPLong.close()
    submit_wait = True
    while submit_wait:
      await channel.send('End of questions, send "**submit**". If you want to cancel, send "**break**".  ')
      print("1")
      msg = await self.bot.wait_for('message', check=check)
      print("22")
      if "submit" in msg.content.lower():
        print("2")
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
        print("3")
        timestamp = datetime.now()
        blacklistembed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        print("4")
        await schannel.send(embed = blacklistembed)
        print("5")
      elif "break" in msg.content.lower():
        schannel.send("Canceled Request...")
        submit_wait = False
          
  
  @blacklist.error
  async def blacklist_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
  


  @commands.command()
  @commands.has_role("Realm OP")
  async def blogs(self, ctx):
    author = ctx.message.author
    guild = ctx.message.guild
    channel = ctx.message.channel
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used BLOGS \n")
    logfile.close()
    if ctx.channel.name == ("banned-players"):

      def check(m):
        return m.content is not None and m.channel == channel and m.author is not self.bot.user


      await channel.send(QQ1)
      checklogsA = await self.bot.wait_for('message', check=check)

      if checklogsA.content == "Gamertag":
        MRPShort = open("MRPGamertags.txt", "r")
        file_contents = MRPShort.read()
        blacklistdata = discord.Embed(title = "Recorded Gamertag Blacklists", description = "Data requested by: " + author.mention, color = 0xb10d9f)
        blacklistdata.add_field(name = "Logs:", value = file_contents)
        blacklistdata.set_thumbnail(url = guild.icon_url)
        timestamp = datetime.now()
        blacklistdata.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        MRPShort.close()
        await ctx.send(embed = blacklistdata)

      elif checklogsA.content == "Discord":
        MRPShort = open("MRPDiscord.txt", "r")
        file_contents = MRPShort.read()
        blacklistdata = discord.Embed(title = "Recorded Discord Blacklists", description = "Data requested by: " + author.mention, color = 0xb10d9f)
        blacklistdata.add_field(name = "Logs:", value = file_contents)
        blacklistdata.set_thumbnail(url = guild.icon_url)
        timestamp = datetime.now()
        blacklistdata.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        MRPShort.close()
        await ctx.send(embed = blacklistdata)

      elif checklogsA.content == "Combined":
        MRPShort = open("MRPCombine.txt", "r")
        file_contents = MRPShort.read()
        blacklistdata = discord.Embed(title = "Recorded  Blacklists", description = "Data requested by: " + author.mention, color = 0xb10d9f)
        blacklistdata.add_field(name = "Logs:", value ="Discord Username - Discord ID - Gamertag - Reason for ban:\n" + file_contents)
        blacklistdata.set_thumbnail(url = guild.icon_url)
        timestamp = datetime.now()
        blacklistdata.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        MRPShort.close()
        await ctx.send(embed = blacklistdata) 


      else:
        await ctx.send("I'm sorry, I didn't understand what you said. ")
        return 
    else:
      await ctx.send("You sure you in the right channel bud? 👀")



  @blogs.error
  async def blogs_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")
  
  @commands.command()
  @commands.has_role("Realm OP")
  async def bsearch(self, ctx):
    channel = ctx.message.channel
    author = ctx.message.author
    guild = ctx.message.guild
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used BSEARCH \n")
    logfile.close()
    blacklistdata = discord.Embed(title = "Blacklist Search Results", description = "Data requested by: " + author.mention, color = 0xb10d9f)
  
    def check(m):
      return m.content is not None and m.channel == channel and m.author is not self.bot.user

    await channel.send("Enter search phrase: ")
    searchphrase = await self.bot.wait_for('message', check=check)
    
    searchfile = open("MRPFull.txt", "r")
    for line in searchfile:
      if searchphrase.content in line: 
        #Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, = line.split(" - ")
        #blacklistdata.add_field(name = "Results:" , value = "Discord Username: " + str(Q1) + "\n" + "Discord ID: " + str(Q2) + "\n" + "Gamertag: " + str(Q3) + "\n" + "Realm they were Banned from: " + str(Q4) + "\n" + "Known Alts: " + str(Q5) + "\n" + "Reason for the Ban: " + str(Q6) + "\n" + "Date of Incident: " + str(Q7) + "\n" + "Type of Ban Faced: " + str(Q8) + "\n" + "End Date of Ban: " + str(Q9), inline = False)
        blacklistdata.add_field(name = "Results:", value = line, inline = False)
        
    blacklistdata.set_thumbnail(url = guild.icon_url)
    timestamp = datetime.now()
    blacklistdata.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
    await ctx.send(embed = blacklistdata)
    await ctx.send("**Format:** \n >>> Discord Username - Discord ID - Gamertag - Realm they were banned from - Known Alts - Reason for ban - Date of Incident - Type of ban faced - End date for ban:\n")
    searchfile.close()
    return
  
  @bsearch.error
  async def bsearch_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")


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