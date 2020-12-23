import discord
from discord.ext import commands
import datetime
from discord import CategoryChannel


def solve(s):
  a = s.split(' ')
  for i in range(len(a)):
    a[i]= a[i].capitalize()
  return ' '.join(a)

class OperatorCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=['addop', 'addOP', 'Addop', 'AddOP'])
  @commands.has_role("Realm OP")
  async def _addOP(self, ctx, user: discord.Member ,*,role: discord.Role):
    guild = ctx.message.guild
    channel = ctx.message.channel
    author = ctx.message.author
    check_role = discord.utils.get(ctx.guild.roles, name=role.name)
    print(check_role)
    print(str(role) + author.name)
    if role not in author.roles:
      await ctx.send(f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!")
      return
    else:
      await user.add_roles(role)
    embed = discord.Embed(title = "Realm Operator Command", description = user.mention + " now has " + role.mention + "!\nPlease remember you require Spider Sniper or above in order to get the Realm OP role!", color = 0x4287f5)
    await ctx.send(embed = embed)

    await user.send("Hello, you have been given OP privileges for " + str(role) + " in the Minecraft Realm Portal. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules.")

    '''
    channel = self.bot.get_channel(778453455848996876)
    #778453455848996876
    #587858951522091018
    embed = discord.Embed(title = "Operator Command Used!" ,description = author.name + " used addOP on " + user.name, color = 0xb10d9f)
    embed.add_field(name = "Usage Details", value = "**Result:**\n" + user.name + " was given the " + role.mention + " role. \n **Channel:**\nThe action took place in <#" + str(channel.id) + ">")
    timestamp = datetime.now()
    embed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
    await channel.send(embed=embed)
    '''

  
  @_addOP.error
  async def addOP_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    elif isinstance(error, commands.RoleNotFound):
      await ctx.send("Uh oh, I couldn't find that role!")

    elif isinstance(error, commands.BadArgument):
      await ctx.send("Hmmm, are you sure you ran the command right? Check the help command for 'addOP'! ")

  
    

  @commands.command(aliases=['removeop', 'removeOP', 'Removeop' , 'RemoveOP'])
  @commands.has_role("Realm OP")
  async def _removeOP(self, ctx, user: discord.Member ,*,role: discord.Role):
    guild = ctx.message.guild
    channel = ctx.message.channel
    author = ctx.message.author
    check_role = discord.utils.get(ctx.guild.roles, name=role.name)
    print(check_role)
    if role not in author.roles:
      await ctx.send(f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!")
    else:
      await user.remove_roles(role)
      embed = discord.Embed(title = "Realm Operator Command", description = "**Operator** " + author.mention + " removed " + role.mention + " from " + user.name, color =0x4287f5)
      await ctx.send(embed = embed)

      '''
      modlog = self.bot.get_channel(778453455848996876)
      em = discord.Embed(title = "Operator Command Used!" ,description = author.name + " used removeOP on " + user.name, color = 0xb10d9f)
      em.add_field(name = "Usage Details", value = "**Result:**\n" + user.name + " had the " + role.mention + " removed. \n **Channel:**\nThe action took place in <#" + str(channel.id) + ">")
      timestamp = datetime.now()
      em.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
      await modlog.send(embed=em)
      '''

  @_removeOP.error
  async def removeOP_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    elif isinstance(error, commands.RoleNotFound):
      await ctx.send("Uh oh, I couldn't find that role!")

    elif isinstance(error, commands.BadArgument):
      await ctx.send("Hmmm, are you sure you ran the command right? Check the help command for 'addOP'! ")


  @commands.command()
  async def comm(self, ctx, *, category: CategoryChannel):
    for channel in category.text_channels:
      await ctx.send(channel.name)
      await ctx.send(channel.topic)
  
 
  
  
  @commands.command()
  @commands.has_role("Realm OP")
  async def block(self, ctx, user: discord.User):
    DMchannel = await ctx.author.create_dm()
    channel = ctx.message.channel
    achannel = ctx.message.channel
    author = ctx.message.author
    guild = ctx.message.guild
    mentions = [role.mention for role in ctx.message.author.roles if role.mentionable]
    channel2 = str(channel.name)
    channel = channel2.split('-')
    if len(channel2) == 2: # #real-emoji
      realm, emoji = channel
    else: # #realm-name-emoji  
      realm, emoji = channel[0], channel[-1]
      realmName = realm.replace("-" , " ")
      realmName1 = realmName.lower()
    rolelist = []
    print(realmName1)
    a = solve(realmName1)
    print(a)
    realmName2 = str(a) + " OP"
    print(realmName2)
    check_role = discord.utils.get(ctx.guild.roles, name= realmName2)
    if check_role not in ctx.author.roles:
      return await ctx.send('You do not own this channel')

    else:
      await ctx.send("You own this channel!")
      def check(m):
        return m.channel == DMchannel and m.author != self.bot.user
        
      await DMchannel.send("Please fill out the questions in order to block the user!")

      await DMchannel.send("User's Gamertag: (If you don't know, try using the >search command to see if they have any previous records!) ")
      blocka1 = await self.bot.wait_for('message', check=check)

      await DMchannel.send("Reason for block:")
      blocka2 = await self.bot.wait_for('message', check=check)


      submit_wait = True
      while submit_wait:
        await DMchannel.send('End of questions, send "**submit**". If you want to cancel, send "**break**".  ')
        msg = await self.bot.wait_for('message', check=check)
        if "submit" in msg.content.lower():
          submit_wait = False
          embed = discord.Embed(title = "New Player Block", description = str(user.name) + " was removed by " + author.name, color = 0xb10d9f)   
          embed.add_field(name = "**Channel: **" + str(achannel) , value = "**User Blocked: **" + str(user.name) + "\n**User ID:** " + str(user.id) + "\n**Gamertag Given: **" + str(blocka1.content) + "\n**Reason: **" + str(blocka2.content))
          embed.add_field(name = "Developer Stuff", value = "**Channel Split:** " + str(channel) + "\n**String Split Stages:**" + "\nStage 1: " + realmName + "\nStage 2: " + a + "\nStage 3: " + realmName2)
          timestamp = datetime.now()
          embed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
          perms = achannel.overwrites_for(user)
          perms.read_messages = False
          perms.send_messages = False
          await achannel.set_permissions(user, overwrite=perms, reason="Block was requested by " + author.name)

          modlog = self.bot.get_channel(783141636543610960)
          # Test Realm: 783141636543610960
          #Savage Test server: 778616690741084174
          #My Test Server: 778453455848996876
          #MRP: 587858951522091018
          await modlog.send(embed = embed)
          BlockA = open(realmName1 + "_blocks.txt", "a")
          BlockA.write(str(user.id) + " - " + blocka2.content + "\n")
          BlockA.close()
        elif "break" in msg.content.lower():
          submit_wait = False
          await DMchannel.send("Canceled Operation on " + user.name)
    
  @commands.command()
  @commands.has_role("Realm OP")
  async def unblock(self, ctx, user: discord.User):
    DMchannel = await ctx.author.create_dm()
    channel = ctx.message.channel
    achannel = ctx.message.channel
    author = ctx.message.author
    guild = ctx.message.guild
    mentions = [role.mention for role in ctx.message.author.roles if role.mentionable]
    channel2 = str(channel.name)
    channel = channel2.split('-')
    if len(channel2) == 2: # #real-emoji
      realm, emoji = channel
    else: # #realm-name-emoji  
      realm, emoji = channel[0], channel[-1]
      realmName = realm.replace("-" , " ")
      realmName1 = realmName.lower()
    rolelist = []
    print(realmName1)
    a = solve(realmName1)
    print(a)
    realmName2 = str(a) + " OP"
    print(realmName2)
    check_role = discord.utils.get(ctx.guild.roles, name= realmName2)
    if check_role not in ctx.author.roles:
      return await ctx.send('You do not own this channel')

    else:
      #await ctx.send("You own this channel!")
      embed = discord.Embed(title = "New Player Unblock", description = str(user.name) + " was removed by " + author.name, color = 0xb10d9f)   
      embed.add_field(name = "**Channel: **" + str(achannel) , value = "**User Unblocked: **" + str(user.name) + "\n**User ID:** " + str(user.id))
      embed.add_field(name = "Developer Stuff", value = "**Channel Split:** " + str(channel) + "\n**String Split Stages:**" + "\nStage 1: " + realmName + "\nStage 2: " + a + "\nStage 3: " + realmName2)
      timestamp = datetime.now()
      embed.set_footer(text=guild.name + " | Date: " + str(timestamp.strftime(r"%x")))
      perms = achannel.overwrites_for(user)
      perms.read_messages = True
      perms.send_messages = True
      await achannel.set_permissions(user, overwrite=perms, reason="Unblock was requested by " + author.name)
      modlog = self.bot.get_channel(778453455848996876)
      
      with open(realmName1 + "_blocks.txt", "r") as f:
        lines = f.readlines()
      with open(realmName1 + "_blocks.txt", "w") as f: 
        for line in lines:
          ID, reason = line.split(" - ")
          if ID == str(user.id):
            f.write("\n")
          else:
            f.write(line)
          #Savage Test server: 778616690741084174
          #My Test Server: 778453455848996876
          #MRP: 587858951522091018
      await modlog.send(embed = embed)

  @commands.command()
  @commands.has_role("Realm OP")
  async def blocks(self, ctx):
    channel = ctx.message.channel
    achannel = ctx.message.channel
    author = ctx.message.author
    guild = ctx.message.guild
    mentions = [role.mention for role in ctx.message.author.roles if role.mentionable]
    channel2 = str(channel.name)
    channel = channel2.split('-')
    if len(channel2) == 2: # #real-emoji
      realm, emoji = channel
    else: # #realm-name-emoji  
      realm, emoji = channel[0], channel[-1]
      realmName = realm.replace("-" , " ")
      realmName1 = realmName.lower()
    rolelist = []
    print(realmName1)
    a = solve(realmName1)
    print(a)
    realmName2 = str(a) + " OP"
    print(realmName2)
    embed = discord.Embed(title = "Channel Blocks", description = "Requested by: " + author.mention)
    try: 
      x = open(realmName1 + "_blocks.txt", "r")
      lines = x.readlines()
      with open(realmName1 + "_blocks.txt", "w") as f: 
        for line in lines:
          ID, reason = line.split(" - ")
          embed.add_field(name = "Results: ", value = "**Username:** <@" + ID + "> **Reason:** " + reason)
      await ctx.send(embed = embed)

    except IOError:
      await ctx.send("Looks like I can't find your channel's database, it may be due to the fact that the `block` command hasn't been used in your channel!")
      

  

def setup(bot):
  bot.add_cog(OperatorCMD(bot))
