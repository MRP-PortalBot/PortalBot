import discord
from discord.ext import commands
import datetime
from datetime import datetime

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
        
def setup(bot):
  bot.add_cog(DailyCMD(bot))