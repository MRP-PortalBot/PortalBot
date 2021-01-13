import discord
import logging
from discord.ext import commands
import json
import datetime
from datetime import timedelta, datetime
from github import Github #(pip install PyGithub)
import os
import asyncio

#Bot Suggestions! (Using GitHub Issues!)

#GitHub Auth 
g = Github(os.getenv("GITHUB"))
repo = g.get_repo("MRP-PortalBot/PortalBot")

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def suggest(self, ctx, *, suggestion = None):
        author = ctx.message.author
        authorname = ctx.message.author.display_name
        ID = ctx.message.author.id
        server = ctx.message.guild.name
        channel = ctx.message.channel
        label = repo.get_label("enchancement")
        label2 = repo.get_label("Awaiting Review")
        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user and m.author == author
        if suggestion == None:
            await channel.send("Suggestion/Feedback")
            answer = await self.bot.wait_for('message', check=check)

            message = await channel.send("**That's it!**\n\nReady to submit?\n✅ - SUBMIT\n❌ - CANCEL\n*You have 100 seconds to react, otherwise the application will cancel.* ")
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check2(reaction, user):
                return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=100.0, check=check2)
                if str(reaction.emoji) == "❌":
                    await channel.send("Ended Task")
                    await message.delete()
                    return
                else:
                    await message.delete()
                    Issue = repo.create_issue(title=f"[SUGGESTION] by {authorname}", body = answer.content, labels = [label, label2])
                    embed = discord.Embed(title = "I have sent in your suggestion!", value = f"You can view your suggestion's progress here! [GitHub URL](https://github.com/MRP-PortalBot/PortalBot/issues/{Issue.number})")
                    await ctx.send(embed = embed)

            except asyncio.TimeoutError:
                await channel.send("Looks like you didn't react in time, please try again later!")
        else:
            message = await channel.send("**Are you sure you want to submit?** \n✅ - SUBMIT\n❌ - CANCEL\n*You have 100 seconds to react, otherwise the application will cancel.* ")
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check2(reaction, user):
                return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=100.0, check=check2)
                if str(reaction.emoji) == "❌":
                    await channel.send("Ended Task")
                    await message.delete()
                    return
                else:
                    await message.delete()
                    Issue = repo.create_issue(title=f"[SUGGESTION] by {authorname}", body = suggestion, labels = [label, label2])
                    embed = discord.Embed(title = "I have sent in your suggestion!", value = f"You can view your suggestion's progress here! [GitHub URL](https://github.com/MRP-PortalBot/PortalBot/issues/{Issue.number})")
                    await ctx.send(embed = embed)

            except asyncio.TimeoutError:
                await channel.send("Looks like you didn't react in time, please try again later!")

            


    

def setup(bot):
    bot.add_cog(Suggestions(bot))
