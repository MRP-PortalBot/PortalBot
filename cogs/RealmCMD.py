import discord
from discord.ext import commands
import time

i = 1
time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

def convert(time):
    try:
        return int(time[:-1]) * time_convert[time[-1]]
    except:
        return time





class RealmCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  
   
  @commands.command()
  @commands.has_permissions(manage_roles = True)
  async def newrealm(self, ctx, realm, emoji,  user: discord.Member, *, message=None):
    #Status set to null
    RoleCreate = "FALSE"
    ChannelCreate = "FALSE"
    RoleGiven = "FALSE"
    ChannelPermissions = "FALSE"
    DMStatus = "FALSE"
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used NEWREALM \n")
    logfile.close()
    guild = ctx.message.guild
    channel = ctx.message.channel
    color = discord.Colour(0x3498DB)
    role = await guild.create_role(name= realm + " OP", color = color, mentionable = True)
    RoleCreate = "DONE"
    #category = discord.utils.get(guild.categories, name = "Realm Channels List Test")
    category = discord.utils.get(guild.categories, name = "🎮 Realms & Servers")
    channel = await category.create_text_channel(realm + "-" + emoji)
    await channel.send(role.mention + " **Welcome to the MRP!** \n Your channel has been created and you should have gotten a DM regarding some stuff about your channel! \n If you have any questions, feel free to DM an Admin or a Moderator! ")
    await channel.edit(topic="The newest Realm on the Minecraft Realm Portal, Check it out and chat with the owners for more Realm information. \n \n ]]Realm: Survival Multiplayer[[")
    ChannelCreate = "DONE"
    await user.add_roles(role)
    RoleGiven = "DONE"
    perms = channel.overwrites_for(role)
    perms.manage_channels = True
    perms.manage_webhooks = True
    perms.manage_messages = True
    await channel.set_permissions(role, overwrite=perms, reason="Created New Realm!")
    channelrr = guild.get_channel(683454087206928435) 
    await channelrr.send(role.mention + "\n **Please agree to the rules to gain access to the Realm Owner Chats!**")
    perms12 = channelrr.overwrites_for(role)
    perms12.read_messages = True
    #Muted = guild.get_role(778267159138402324)
    #MRP below
    Muted = guild.get_role(630770012524642314)
    permsM = channel.overwrites_for(Muted)
    permsM.read_messages = False
    permsM.send_messages = False
    ChannelPermissions = "DONE"
    await channel.set_permissions(Muted, overwrite=permsM)
    await user.send(user.mention)
    try:
      await user.send("Enjoy your new channel. Use this channel to advertise your realm, and engage the community. The more active a channel the more likely people will be to stop by and check you out. You have moderation privileges in your channel. You can change the description, pin messages, and delete messages. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules. If you would like to add an OP to your team, in your channel type: ")
      await user.send("```>addOP @newOP @reamlrole```")
      await user.send("In order to have your Realm listed in #realm-channels-info, please do not remove the ]]Realm: Survival Multiplayer[[ portion of your channel description. Feel free to edit this in the following way ]]Anything You Want To Show Up After Your Realm Name: Short Description Of Your Realm[[. ")
      await user.send("Thanks for joining the Portal, and if you have any questions contact an Admin.")
    except:
      await ctx.send("Uh oh, something went wrong while trying to DM the Realm Owner. \n`Error: Discord Forbidden (User's Privacy Settings Prevented the DM Message)`")
      await ctx.send("DM Status: **FAILED**")
      DMStatus = "FAILED"
    else:
      await ctx.send("DM Status: **SENT**")
      DMStatus = "DONE"
    finally:
      await ctx.send("**The command has finished all of its tasks.**\n> *If there was an error with anything, you should see the status for that specific argument.*")
      time.sleep(2)
      #Variables:
      '''
      RoleCreate = "FALSE"
      ChannelCreate = "FALSE"
      RoleGiven = "FALSE"
      ChannelPermissions = "FALSE"
      DMStatus = "FALSE"
      '''
      await ctx.send("**Console Logs** \n```\nRole Created: " + RoleCreate + "\nChannel Created: " + ChannelCreate + "\nRole Given: " + RoleGiven + "\nChannel Permissions: " + ChannelPermissions + "\nDMStatus: " +DMStatus + "\n```")


  @newrealm.error
  async def newrealm_error(self, ctx,error):
    if isinstance(error, commands.MissingPermissions):
      await ctx.send("Uh oh, looks like I can't execute this command because you don't have permissions!")

    if isinstance(error, commands.TooManyArguments):
      await ctx.send("You sent too many arguments! Did you use quotes for realm names over 2 words?")
    
  


  

def setup(bot):
  bot.add_cog(RealmCMD(bot))
