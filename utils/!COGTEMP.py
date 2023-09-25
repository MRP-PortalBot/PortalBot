import discord
import logging
from discord.ext import commands
import json
import datetime
from datetime import timedelta, datetime


class SkeletonCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(SkeletonCMD(bot))
