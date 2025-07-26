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

            # Cooldown check
            if hasattr(score, "LastMessageTimestamp") and score.LastMessageTimestamp:
                if current_time - score.LastMessageTimestamp < cooldown_time:
                    remaining = cooldown_time - (
                        current_time - score.LastMessageTimestamp
                    )
                    score_log.debug(
                        f"{username} is on cooldown ({remaining:.2f}s left)."
                    )
                    return

            # Score increment
            score_increment = random.randint(points_per_message, points_per_message * 3)
            previous_level = score.Level
            score.Score += score_increment

            # Recalculate level
            new_level, progress, next_level_score = calculate_level(score.Score)
            score.DiscordName = username
            score.Level = new_level
            score.Progress = next_level_score
            score.LastMessageTimestamp = current_time
            score.save()

            # If level-up occurred
            if new_level > previous_level:
                # Get all known level roles from DB for this guild
                all_roles = database.LeveledRoles.select().where(
                    database.LeveledRoles.ServerID == str(message.guild.id)
                )
                level_role_ids = {entry.RoleID for entry in all_roles}

                # Get current user roles that are level-based
                user_roles_to_remove = [
                    r for r in message.author.roles if r.id in level_role_ids
                ]

                # Remove old level roles
                if user_roles_to_remove:
                    await message.author.remove_roles(*user_roles_to_remove)

                # Add new role
                new_role = await get_role_for_level(new_level, message.guild)
                if new_role:
                    await message.author.add_roles(new_role)
                    score_log.info(
                        f"Updated {username}'s role to '{new_role.name}' for Level {new_level}"
                    )

        except Exception as e:
            _log.error(f"Error processing XP for {message.author}: {e}", exc_info=True)

        finally:
            if not database.db.is_closed():
                database.db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelSystemListener(bot))
    _log.info("📈 LevelSystemListener loaded.")
