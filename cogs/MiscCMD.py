import discord
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import random

rules = [":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!", ":two: **No spamming** in chat or direct messages!", ":three: **No religious or political topics**, those don’t usually end well!", ":four: **Keep pinging to a minimum**, it is annoying!", ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!", ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**", ":seven: **No realm or server is better than another!** It is **not** a competition.", ":eight: **Have fun** and happy crafting!", ":nine: **Discord Terms of Service apply!** You must be at least **13** years old."]


class MiscCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  #DM Command
  @commands.command()
  @commands.has_role("Moderator")
  async def DM(self, ctx, user: discord.User, *, message=None):
    message = message or "This Message is sent via DM"
    author = ctx.message.author
    await user.send(message)
    await user.send("Sent by: " + author.name)
  
  @DM.error
  async def DM_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Moderator role!")

  #Ping Command
  @commands.command()
  async def ping(self, ctx):
    author = ctx.message.author
    #await ctx.send(f'**__Latency is__ ** {round(client.latency * 1000)}ms')
    pingembed = discord.Embed(title = "Pong! ⌛", color = 0xb10d9f, description="Current Discord API Latency")
    pingembed.add_field(name = "Current Ping:" , value = f'{round(self.bot.latency * 1000)}ms')
    await ctx.send(embed = pingembed)

  #Uptime Command
  @commands.command()
  async def uptime(self,ctx):
    author = ctx.message.author
    await ctx.send("Really long time, lost track. ")

  #Purge Command
  @commands.command()
  @commands.has_permissions(manage_messages = True)
  async def clear(self, ctx,amount=2):
    author = ctx.message.author
    await ctx.channel.purge(limit = amount)

  #Say Command
  @commands.command()
  @commands.has_permissions(manage_channels = True)
  async def say(self, ctx,*,reason):
    author = ctx.message.author
    await ctx.channel.purge(limit = 1)
    await ctx.send(reason) 

  #Embed Command
  @commands.command()
  @commands.has_permissions(manage_channels = True)
  async def embed(self, ctx, channel : discord.TextChannel, color : discord.Color , *, body):
    author = ctx.message.author
    title , bottom = body.split(" | ")
    embed = discord.Embed(title = title, description = bottom, color = color)
    await channel.send(embed = embed)
    
  #Nick Commamd
  @commands.command()
  @commands.has_role("Moderator")
  async def nick(self, ctx, user :discord.Member, channel : discord.TextChannel):
    author = ctx.message.author
    name = user.display_name
    channel = channel.name.split('-')
    if len(channel) == 2: # #real-emoji
      realm, emoji = channel
    else: # #realm-name-emoji  
      realm, emoji = channel[0], channel[-1]
    await user.edit(nick=str(name) + " " + str(emoji))
    await ctx.send("Changed nickname!")

  @nick.error
  async def nick_error(self,ctx, error):
    if isinstance(error, commands.MissingRole):
      await ctx.send("Uh oh, looks like you don't have the Moderator role!")

  #Removes your nickname. 
  @commands.command()
  async def rememoji(self, ctx):
    author = ctx.message.author
    name = author.name
    await author.edit(nick = str(author.name))
    await ctx.send("Removed your nickname!")

  #Add's an emoji to your nickname.
  @commands.command()
  async def addemoji(self, ctx, channel : discord.TextChannel):
    author = ctx.message.author
    name = author.display_name
    channel = channel.name.split('-')
    if len(channel) == 2: # #real-emoji
      realm, emoji = channel
    else: # #realm-name-emoji  
      realm, emoji = channel[0], channel[-1]
    await author.edit(nick=str(name) + str(emoji))
    await ctx.send("Changed your nickname!")
  
  @addemoji.error
  async def addemoji_error(self,ctx, error):
    if isinstance(error, commands.BadArgument):
      await ctx.send("Hmm, you didn't give me all the arguments.")

  #Rule Command [INT]
  @commands.command()
  async def rule(self, ctx,*,number):
    author = ctx.message.author
    await ctx.send(rules[int(number)-1])


  #Add's a gamertag to the database. 
  @commands.command()
  async def gamertag(self, ctx, gamertag):
    author = ctx.message.author
    channel = ctx.message.channel
    GamerTag = open("Gamertags.txt", "a")
    GamerTag.write(gamertag + " " + str(author.id) + "\n")
    def check(m):
      return m.content is not None and m.channel == channel and m.author is not self.bot.user
    await channel.send("Success! \nWould you like to change your nickname to your gamertag? (If so, you may have to add your emojis to your nickname again!)\n> *Reply with:* **YES** or **NO**")
    answer7 = await self.bot.wait_for('message', check=check)

    if answer7.content == "YES":
      await author.edit(nick = gamertag)
      await ctx.send("Success!")

    elif answer7.content == "NO":
      await ctx.send("Okay, canceled it...")

  @gamertag.error
  async def gamertag_error(self, ctx, error):
    if isinstance(error, commands.BadArgument):
      await ctx.send("Uh oh, you didn't include all the arguments! ")


  #Tag command, extra commands basically. 
  @commands.command()
  async def tag(self, ctx, tagnum):
    if tagnum == "1":
      text_channel = self.bot.get_channel("587502693246042112")
      text_channel2 = self.bot.get_channel("587632638819434507")
      contentc = discord.Embed(title = "Content Creators", description = f"Minecraft Related Content may go in the <#587632638819434507> channel while other content can go in <#587502693246042112>! \n**Make content?** Feel free to ask a Moderator to give you the Content Creator role!", color = 0xfc0303)
      await ctx.send(embed = contentc)
    elif tagnum == "2":
      text_channel2 = self.bot.get_channel("587850399759990794")
      realm = discord.Embed(title = "Realm Applications", description = f"Welcome! I see you've asked about joining a realm! The Realm Portal has a ton of realms you can choose from. Each having their own application process, if you would like to join one check out the Realms and Server tab! You can view details about each realm by checking its pins and channel description! Please remember that there is no 'better' realm! \n**Community Realm** Don't know what to join? Consider joining the MRP Community Realm! \n**Apply for a Realm Channel!** Have a realm you would like to advertise? Once you reach Zombie Slayer, you should be able to fill out the application in <#587850399759990794>!", color = 0xeb07cc)
      await ctx.send(embed = realm)
    elif tagnum == "3":
      realm = discord.Embed(title = "Realm Applications", description = "Hello! It looks like you wanted to join a realm! Please not that all realms that are shown in the Realm Portal are **BEDROCK**! If you would like to join a realm, please take a moment and read the channel's description **and** the pins! You can find things like their application, realm details, etc in there. \n**NOTE:** Please do not contact Moderators or Admins if you have a question regarding a realm. It's best to contact the realm owners/operators as we are not a representative for that specific realm! ")
    
    elif tagnum == "help":
      await ctx.send("**Tag Numbers:** \n1: Content Related \n2: Realm Applications")

    else:
      await ctx.send("That number isn't a valid response!")

  #OfO command. 
  @commands.command()
  async def webhook(self, ctx, *, reason):
    return
    async with aiohttp.ClientSession() as session:
      url = 'https://discord.com/api/webhooks/783135151155970049/nTOU4H3ch2Q3Z3lLEDUGj8jq-tNZ-cZFRvBPdjphl5aMYtM5j3Urv7p1KtTMxXfrwZmo'
      webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session)) #something here to cycle through url's
      author = ctx.message.author
      await webhook.send(reason ,username=author.name, avatar_url = author.avatar_url)

  @commands.command(description="Rock Paper Scissors")
  async def rps(self, msg: str):
        """Rock paper scissors. Example : /rps Rock if you want to use the rock."""
        # Les options possibles
        t = ["rock", "paper", "scissors"]
        # random choix pour le bot
        computer = t[random.randint(0, 2)]
        player = msg.lower()
        print(msg)
        if player == computer:
            await self.bot.say("Tie!")
        elif player == "rock":
            if computer == "paper":
                await self.bot.say("You lose! {0} covers {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} smashes {1}".format(player, computer))
        elif player == "paper":
            if computer == "scissors":
                await self.bot.say("You lose! {0} cut {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} covers {1}".format(player, computer))
        elif player == "scissors":
            if computer == "rock":
                await self.bot.say("You lose! {0} smashes {1}".format(computer, player))
            else:
                await self.bot.say("You win! {0} cut {1}".format(player, computer))
        else:
            await self.bot.say("That's not a valid play. Check your spelling!")


def setup(bot):
  bot.add_cog(MiscCMD(bot))
