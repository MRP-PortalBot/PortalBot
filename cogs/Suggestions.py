import discord
import logging
from discord.ext import commands
import json
import datetime
from datetime import timedelta, datetime
import os
import asyncio

import requests

url = "https://api.trello.com/1/cards"

def query(authorname, ID, server, channel, suggestion):
    query = {
        'key': os.getenv("TRELLOKEY"),
        'token': os.getenv("TRELLOTOKEN"),
        'idList': '5fff8cd40de14a1cdc6fd79a',
        'pos': 'top',
        'name': f'[Suggestion] by {authorname}',
        'desc': f'Author ID: {ID}\nGuild: {server}\nChannel: {channel}\n\nSuggestion: {suggestion}'
    }
    response = requests.request(
        "POST",
        url,
        params=query
    )
    return response.text



#Bot Suggestions! (Using Trello !)


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
            suggestion = await self.bot.wait_for('message', check=check)

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
                    query(authorname, ID, server, channel.name, suggestion.content)
                    embed = discord.Embed(title = "I have sent in your suggestion!", description = f"You can view your suggestion's progress here! [Trello URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)")
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
                    query(authorname, ID, server, channel.name, suggestion)
                    embed = discord.Embed(title = "I have sent in your suggestion!", value = f"You can view your suggestion's progress here! [Trellp URL](https://trello.com/b/kSjptEEb/portalbot-dev-trello)")
                    await ctx.send(embed = embed)

            except asyncio.TimeoutError:
                await channel.send("Looks like you didn't react in time, please try again later!")

            


    

def setup(bot):
    bot.add_cog(Suggestions(bot))
