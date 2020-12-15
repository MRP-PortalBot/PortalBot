import discord
from discord.ext import commands
import datetime

class DailyCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

@commands.command()
async def info(self, ctx, user: discord.Member):
    mentions = [role.mention for role in ctx.message.author.roles if role.mentionable]
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used INFO \n")
    logfile.close()
    guild = ctx.message.guild
    channel = ctx.message.channel
    searchfile = open("MRPFull.txt", "r")
    count = 0
    rolelist = []
    for role in user.roles:
      rolelist.append(role.mention)
    roles = '\n'.join(rolelist)
    for line in searchfile:
      if str(user.id) in list:
        count = count + 1
    accountcreate = user.created_at
    mem_join = user.joined_at
    guild_create = guild.created_at
 
    
    for line in searchfile:
      if str(user.id) in line: 
        REDEmbed = discord.Embed(title = "Details about: " + user.name, description = "ID: " + str(user.id), color = 0xe02648)
        REDEmbed.set_thumbnail(url=user.avatar_url)
        REDEmbed.add_field(name = "Roles:", value = roles)
        REDEmbed.add_field(name = "Joined Server On:", value = mem_join)
        REDEmbed.add_field(name = "Created Account On:", value = accountcreate)
        REDEmbed.set_thumbnail(url = guild.icon_url)
        timestamp = datetime.now()
        REDEmbed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        await ctx.send(embed = REDEmbed)
        searchfile.close()
        return 
      elif str(user.id) != line:
        REDEmbed = discord.Embed(title = "Details about: " + user.name, description = "ID: " + str(user.id), color = 0x44e813)
        REDEmbed.set_thumbnail(url=user.avatar_url)
        REDEmbed.add_field(name = "Roles:", value = roles)
        REDEmbed.add_field(name = "Joined Server On:", value = mem_join)
        REDEmbed.add_field(name = "Created Account On:", value = accountcreate)
        REDEmbed.set_thumbnail(url = guild.icon_url)
        timestamp = datetime.now()
        REDEmbed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
        await ctx.send(embed = REDEmbed)
        searchfile.close()
        return 
#---
'''
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
#------------------------------------------
#Lists all blacklist data.
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
  
  #searches blacklist data for a specific query
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

#------------------------------------------
    elif A2 == "REMOVE":
      await channel.send("What would you like to remove?: (Use the line number please, you can find it by using the >listq command!) ")
      REMOVE = await self.bot.wait_for('message', check=check)
      reason = REMOVE.content
      toWrite = "";
      with open("DailyQuestions.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
          Num, A = line.split(" - ")
        if Num != reason: #something to place here
            toWrite += line
      with open("DailyQuestions.txt", "w") as w:
        w.write(toWrite)
  

  @commands.Cog.listener()
  async def on_message(self,message):
    with open('Message_Lock.txt', 'r') as myfile:
      data = myfile.read()
      sentences = data
      if sentences == "True":
        return
      else:
        if not message.author.bot:
          msg = message
          guild = message.guild
          content = message.content
          if message.channel.name == ("portal-bot-discussion"): #listen to this channel
            async with aiohttp.ClientSession() as session:
              url = "https://discord.com/api/webhooks/783141451416338453/W_2n6GTTsbvE_aqyWMAG6jAYplvubYqzFpo0V_jgbw4MKPxxTTPtLUY-mf_OwYNdq2aO"
              #URL to send messages
              webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session)) #something here to cycle through url's
              author = message.author
              await webhook.send(message.content ,username= message.author.name + " - " + guild.name, avatar_url = author.avatar_url)
  '''
        
def setup(bot):
  bot.add_cog(DailyCMD(bot))
