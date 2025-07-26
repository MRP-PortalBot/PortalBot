# utils/level_system/__ls_listeners.py

import discord
import random
import time
from discord.ext import commands

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from .__ls_logic import calculate_level, get_role_for_level

_log = get_log("level_system")
score_log = get_log("level_system.score")


class LevelSystemListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        try:
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(message.guild.id)
            )
            if not bot_data:
                return

            blocked_channels = bot_data.get_blocked_channels()
            if message.channel.id in blocked_channels:
                return

            cooldown_time = bot_data.cooldown_time
            points_per_message = bot_data.points_per_message
            user_id = str(message.author.id)
            username = str(message.author.name)
            current_time = time.time()

            database.db.connect(reuse_if_open=True)

            score, created = database.ServerScores.get_or_create(
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                defaults={"Score": 0, "Level": 1, "Progress": 0},
            )

            # Fix future timestamp issues
            if score.LastMessageTimestamp and score.LastMessageTimestamp > current_time:
                score_log.warning(
                    f"{username}'s timestamp was in the future. Resetting."
                )
                score.LastMessageTimestamp = current_time

            # Cooldown check
            if (
                score.LastMessageTimestamp
                and current_time - score.LastMessageTimestamp < cooldown_time
            ):
                remaining = cooldown_time - (current_time - score.LastMessageTimestamp)
                score_log.debug(f"{username} is on cooldown ({remaining:.2f}s left).")
                return

            # Add XP and calculate level
            score_increment = random.randint(points_per_message, points_per_message * 3)
            previous_level = score.Level
            score.Score += score_increment
            new_level, progress, next_level_score = calculate_level(score.Score)

            score_log.debug(
                f"{username} gained {score_increment} XP → Score: {score.Score}, "
                f"Level: {previous_level} → {new_level}, Next: {next_level_score}"
            )

            score.DiscordName = username
            score.Level = new_level
            score.Progress = next_level_score
            score.LastMessageTimestamp = current_time
            score.save()

            # Level-up logic
            if new_level > previous_level:
                score_log.info(f"{username} leveled up from {previous_level} → {new_level}")

                # Get all level role IDs for this server
                all_roles = (
                    database.LeveledRoles
                    .select()
                    .where(database.LeveledRoles.ServerID == str(message.guild.id))
                )
                level_role_ids = {int(entry.RoleID) for entry in all_roles if entry.RoleID}

                # Remove existing level roles
                old_roles = [r for r in message.author.roles if r.id in level_role_ids]
                if old_roles:
                    await message.author.remove_roles(*old_roles)
                    score_log.debug(f"Removed old level roles from {username}: {[r.name for r in old_roles]}")

                # Assign new level role
                new_role = await get_role_for_level(new_level, message.guild)
                if new_role:
                    await message.author.add_roles(new_role)
                    score_log.info(f"Assigned role '{new_role.name}' to {username}")
                else:
                    score_log.warning(f"No role found for Level {new_level} in {message.guild.name}")

                # Announce level-up
                await message.channel.send(
                    f"🎉 {message.author.mention} has leveled up to **Level {new_level}**! Congrats!"
                )

        except Exception as e:
            _log.error(f"Error processing XP for {message.author}: {e}", exc_info=True)

        finally:
            if not database.db.is_closed():
                database.db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelSystemListener(bot))
    _log.info("📈 LevelSystemListener loaded.")
