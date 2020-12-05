import discord
from discord.ext import commands
from datetime import datetime

class OperatorCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.command(aliases=['addop'])
  @commands.has_role("Realm OP")
  async def addOP(self, ctx, user: discord.Member ,*,role: discord.Role):
    guild = ctx.message.guild
    RealmOP = guild.get_role(630770012524642314)
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used ADDOP \n")
    logfile.close()
    check_role = discord.utils.get(ctx.guild.roles, name=role)
    print(check_role)
    print(str(role) + author.name)
    if role not in author.roles:
      await ctx.send(f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!")
    else:
      await user.add_roles(role)
      await ctx.send(f"The role '{str(role)}' has been given to {user.mention}.")
      await user.send("Hello, you have been given OP privileges for " + str(role) + " in the Minecraft Realm Portal. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules.")
  
  @addOP.error
  async def addOP_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    elif isinstance(error, commands.RoleNotFound):
      await ctx.send("Uh oh, I couldn't find that role!")

    elif isinstance(error, commands.BadArgument):
      await ctx.send("Hmmm, are you sure you ran the command right? Check the help command for 'addOP'! ")

  
    

  @commands.command(aliases=['removeop'])
  @commands.has_role("Realm OP")
  async def removeOP(self, ctx, user: discord.Member ,*,role: discord.Role):
    guild = ctx.message.guild
    RealmOP = guild.get_role(630770012524642314)
    author = ctx.message.author
    logfile = open("commandlog.txt", "a")
    logfile.write(str(author.name) + " used REMOVEOP \n")
    logfile.close()
    check_role = discord.utils.get(ctx.guild.roles, name=role)
    print(check_role)
    if role not in author.roles:
      await ctx.send(f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!")
    else:
      await user.remove_roles(role)
      check_role = discord.utils.get(ctx.guild.roles, name=role)
      if role not in user.roles:
        await user.remove_roles(role)
      else:
        await user.remove_roles(role)
        await user.remove_roles(RealmOP)
      await ctx.send(f"The role '{str(role)}' has been removed from {user.mention}.")

  @removeOP.error
  async def removeOP_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Realm OP role!")

    elif isinstance(error, commands.RoleNotFound):
      await ctx.send("Uh oh, I couldn't find that role!")

    elif isinstance(error, commands.BadArgument):
      await ctx.send("Hmmm, are you sure you ran the command right? Check the help command for 'addOP'! ")

  

  

def setup(bot):
  bot.add_cog(OperatorCMD(bot))