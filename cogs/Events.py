import discord
from discord.ext import commands
from datetime import datetime
import time
import re
import asyncio
from discord import Embed
import requests

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 587495640502763521:
            guild = self.bot.get_guild(587495640502763521)
            channel = guild.get_channel(588813558486269956)
            count = int(member.guild.member_count) + 1
            embed = discord.Embed(title = f"Welcome to the {member.guild.name}", description = f"**{str(member.display_name)}** is the **{str(count)}**th member!", color = 0xb10d9f)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text = "Got any questions? Feel free to ask a Moderator!",icon_url = member.guild.icon_url)
            await channel.send(embed=embed)
        else:
            print(f"Unhandled Server: {member.display_name} | {member.guild.name}")


def setup(bot):
    bot.add_cog(Events(bot))