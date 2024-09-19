import discord
import random
import time
from discord.ext import commands
from datetime import datetime, timedelta
from peewee import fn  # For using database functions like increment
from core import database  # Your database module
from core.logging_module import get_log
from core.common import calculate_level  # Assuming you've moved it to core.common

_log = get_log(__name__)

# Create a dictionary to store the last message timestamp for each user
last_message_time = {}

class ScoreIncrement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listener that increments score for each message sent by a user
        with a random point increment (10 to 30 points) and a cooldown of 1 to 3 minutes.
        """
        if message.author.bot or message.guild is None:
            return  # Ignore messages from bots or DMs

        user_id = str(message.author.id)
        username = str(message.author.name)
        current_time = time.time()

        # Get the cooldown (in seconds) as a random value between 60 and 180 seconds
        cooldown = random.randint(60, 180)

        # Check if the user is in the last_message_time dictionary
        if user_id in last_message_time:
            last_time = last_message_time[user_id]

            # If the cooldown hasn't passed, return early
            if current_time - last_time < cooldown:
                return

        # If cooldown has passed or it's the user's first message, update the score
        score_increment = random.randint(10, 30)

        # Try to fetch the current score from the database
        try:
            server_score = database.ServerScores.get(
                database.ServerScores.DiscordLongID == user_id,
                database.ServerScores.ServerID == str(message.guild.id)
            )
            server_score.Score += score_increment  # Increment the score

            # **Calculate the new level and progress using your function**
            new_level, progress = calculate_level(server_score.Score)

            # Update the score, level, and progress
            server_score.Level = new_level
            server_score.Progress = progress
            server_score.save()

        except database.ServerScores.DoesNotExist:
            # If the user doesn't have a score record yet, create one
            initial_score = score_increment
            new_level, progress = calculate_level(initial_score)  # Calculate initial level and progress

            database.ServerScores.create(
                DiscordName=username,
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                Score=initial_score,
                Level=new_level,
                Progress=progress
            )

        # Update the last_message_time dictionary with the current time
        last_message_time[user_id] = current_time

        # Optional: send a message or log the score increment
        await message.channel.send(f"{message.author.mention} earned {score_increment} points!")

# Setup the cog
async def setup(bot):
    await bot.add_cog(ScoreIncrement(bot))
