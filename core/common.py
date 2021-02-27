from pathlib import Path
from typing import Tuple
import asyncio
import discord
import json
import os
import requests
import random
from core import database
from datetime import datetime

def load_config() -> Tuple[dict, Path]:
    """Load data from the botconfig.json.\n
    Returns a tuple containing the data as a dict, and the file as a Path"""
    config_file = Path("botconfig.json")
    config_file.touch(exist_ok=True)
    if config_file.read_text() == "":
        config_file.write_text("{}")
    with config_file.open("r") as f:
        config = json.load(f)
    return config, config_file


def prompt_config(msg, key):
    """Ensure a value exists in the botconfig.json, if it doesn't prompt the bot owner to input via the console."""
    config, config_file = load_config()
    if key not in config:
        config[key] = input(msg)
        with config_file.open("w+") as f:
            json.dump(config, f, indent=4)


async def paginate_embed(bot: discord.Client, ctx, embed: discord.Embed, population_func, end: int, begin: int = 1, page=1):
    emotes = ["◀️", "▶️"]

    async def check_reaction(reaction, user):
         return await user == ctx.author and str(reaction.emoji) in emotes

    embed = await population_func(embed, page)
    if isinstance(embed, discord.Embed):
        message = await ctx.send(embed=embed)
    else:
        await ctx.send(str(type(embed)))
        return
    await message.add_reaction(emotes[0])
    await message.add_reaction(emotes[1])
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check_reaction)
            if user == bot.user:
                continue
            if str(reaction.emoji) == emotes[1] and page < end:
                page += 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
            elif str(reaction.emoji) == emotes[0] and page > begin:
                page -= 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

def query(authorname, ID, server, channel, suggestion, trellotype):
    url = "https://api.trello.com/1/cards"
    query = {
        'key': os.getenv("TRELLOKEY"),
        'token': os.getenv("TRELLOTOKEN"),
        'idList': '5fff8cd40de14a1cdc6fd79a',
        'pos': 'top',
        'name': f'[{trellotype}] by {authorname}',
        'desc': f'Author ID: {ID}\nGuild: {server}\nChannel: {channel}\n\nSuggestion/Bug: {suggestion}'
    }
    response = requests.request(
        "POST",
        url,
        params=query
    )
    return response.text

def solve(s):
    a = s.split(' ')
    for i in range(len(a)):
        a[i] = a[i].capitalize()
    return ' '.join(a)


config, _ = load_config()

async def mainTask2(client):
    while True:
        d = datetime.utcnow()
        if d.hour == 17 or d.hour == "17":
            guild = client.get_guild(config['ServerID'])
            channel = client.get_channel(config['GeneralChannel'])
            limit = int(database.Question.select().count())
            print(limit)
            Rnum = random.randint(1 , limit)
            try:
                database.db.connect(reuse_if_open=True)
                try:
                    q: database.Question = database.Question.select().where(database.Question.id == Rnum).get()
                    if q.usage == False or q.usage == "False" or q.usage == "FALSE":
                        embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓", description=f"**{q.question}**", color = 0xb10d9f)
                        await channel.send(embed=embed)
                        if config['BotType'] == "STABLE":
                            q.usage = "True"
                            q.save()
                    else:
                        return
        
                finally:
                    database.db.close()

            finally:
                database.db.close()
        await asyncio.sleep(3600)


async def missingArguments(ctx, example):
    em = discord.Embed(title = "Missing Required Arguments!", description = f"You have missed one or several arguments in this command\n**Example Usage:** `>{example}`", color = 0xf5160a)
    await ctx.send(embed = em)
    return