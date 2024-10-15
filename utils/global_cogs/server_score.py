import discord
import random
import time
from discord.ext import commands
from datetime import datetime, timedelta
from peewee import fn  # For using database functions like increment
from core import database
from core.logging_module import get_log
from core.common import calculate_level

_log = get_log(__name__)
server_score_log = get_log("server_score", console=False)

# Create a dictionary to store the last message timestamp for each user
last_message_time = {}


class ScoreIncrement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function to get the cooldown and points from the BotData
    async def get_bot_data(self):
        return database.BotData.get_or_none(database.BotData.id == 1)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return  # Ignore bot messages or messages from DMs

        bot_data = await self.get_bot_data()
        if not bot_data:
            return  # Skip if bot data is not found

        cooldown_time = (
            bot_data.cooldown_time
        )  # Get the cooldown time from the database
        points_per_message = (
            bot_data.points_per_message
        )  # Get points per message from the database

        user_id = str(message.author.id)
        username = str(message.author.name)
        current_time = time.time()

        if user_id in last_message_time:
            last_time = last_message_time[user_id]
            time_diff = current_time - last_time

            if time_diff < cooldown_time:
                server_score_log.info(
                    f"User {username} is still on cooldown ({cooldown_time - time_diff:.2f} seconds left)."
                )
                return

        # Log that the user is eligible to gain score
        server_score_log.info(f"User {username} is eligible to gain score.")

        # If cooldown has passed, update the score
        score_increment = random.randint(points_per_message, points_per_message * 3)

        try:
            server_score_log.debug(
                f"Connecting to database to update score for {username}."
            )
            database.db.connect(reuse_if_open=True)

            server_score, created = database.ServerScores.get_or_create(
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                defaults={"Score": 0, "Level": 1, "Progress": 0},
            )

            previous_level = server_score.Level  # Store the previous level

            # Increment the score
            server_score.Score += score_increment
            server_score_log.info(
                f"{username} earned {score_increment} points. Total score is now {server_score.Score}."
            )

            # Calculate the new level and progress using the function
            new_level, progress, next_level_score = calculate_level(server_score.Score)

            # Update the database if the user leveled up or details changed
            if username != server_score.DiscordName:
                server_score.DiscordName = username
            server_score.Level = new_level
            server_score.Progress = next_level_score
            server_score.save()

            # Check if the user leveled up
            if new_level > previous_level:
                server_score_log.info(f"{username} leveled up to {new_level}.")

                # Fetch and assign the role for the new level
                role_name = await self.get_role_for_level(new_level, message.guild)
                if role_name:
                    new_role = discord.utils.get(message.guild.roles, name=role_name)
                    if new_role:
                        await message.author.add_roles(new_role)
                        server_score_log.info(
                            f"Assigned role '{role_name}' to {username} for reaching level {new_level}."
                        )

                await message.channel.send(
                    f"🎉 {message.author.mention} has leveled up to **Level {new_level}**! Congrats!"
                )

        except database.ServerScores.DoesNotExist:
            server_score_log.error(
                f"Score record not found for {username}. Creating new entry."
            )
            initial_score = score_increment
            new_level, progress, next_level_score = calculate_level(initial_score)

            database.ServerScores.create(
                DiscordName=username,
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                Score=initial_score,
                Level=new_level,
                Progress=next_level_score,
            )
            server_score_log.info(
                f"Created new score record for {username} with initial score {initial_score}."
            )

        except Exception as e:
            server_score_log.error(
                f"Error processing score increment for {username}: {e}"
            )

        finally:
            if not database.db.is_closed():
                database.db.close()
                server_score_log.debug("Database connection closed.")

        # Update the last_message_time dictionary with the current time
        last_message_time[user_id] = current_time

    async def get_role_for_level(self, level, guild):
        """
        Fetch the role name associated with the user's new level.
        """
        try:
            server_score_log.debug(
                f"Fetching role for level {level} in guild {guild.name}."
            )
            database.db.connect(reuse_if_open=True)
            leveled_role = database.LeveledRoles.get(
                database.LeveledRoles.Level == level
            )
            return leveled_role.RoleName if leveled_role else None

        except database.LeveledRoles.DoesNotExist:
            server_score_log.warning(
                f"No role found for level {level} in guild {guild.name}."
            )
            return None

        except Exception as e:
            server_score_log.error(f"Error fetching role for level {level}: {e}")
            return None

        finally:
            if not database.db.is_closed():
                database.db.close()
                server_score_log.debug(
                    "Database connection closed after fetching role."
                )


# Setup the cog
async def setup(bot):
    await bot.add_cog(ScoreIncrement(bot))
