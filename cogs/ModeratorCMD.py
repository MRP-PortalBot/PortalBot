import discord
import flask
import keep_alive
import logging
from discord.ext import commands
import json 
import datetime
from datetime import timedelta, datetime
from discord import Webhook, AsyncWebhookAdapter
import aiohttp

class DailyCMD(commands.Cog):
  def __init__(self,bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_message(self,message):
    with open('EVAL_Lock.txt', 'r') as myfile:
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
  

  @commands.command()
  @commands.is_owner()
  async def locklisten(self, ctx):
    #evallock = True
    evallock = open("Message_Lock.txt", "w")
    evallock.write("True")
    evallock.close
    await ctx.send("Locked Eval Command ✅")

  @commands.command()
  @commands.is_owner()
  async def unlocklisten(self, ctx):
    #evallock = False
    evalunlock = open("Message_Lock.txt", "w")
    evalunlock.write("False")
    evalunlock.close
    await ctx.send("Unlocked Eval Command ✅")


def setup(bot):
  bot.add_cog(DailyCMD(bot))

'''
logfile = open("commandlog.txt", "a")
logfile.write(author + " used C \n")
logfile.close()
'''