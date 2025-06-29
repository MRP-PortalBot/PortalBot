# utils/leveled_roles/__lr_listeners.py

import discord
import random
import time
from discord.ext import commands

from utils.database import __database
from utils.helpers.__logging_module import get_log
from utils.leveled_roles.__lr_logic import calculate_level, get_role_for_level

_log = get_log("leveled_roles")
score_log = get_log("score_loop", console=False)


class LevelRoleListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        bot_data = __database.BotData.get_or_none(__database.BotData.server_id == str(message.guild.id))
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

        try:
            __database.db.connect(reuse_if_open=True)

            score, created = __database.ServerScores.get_or_create(
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                defaults={"Score": 0, "Level": 1, "Progress": 0},
            )

            # Cooldown logic
            if hasattr(score, "LastMessageTimestamp") and score.LastMessageTimestamp:
                if current_time - score.LastMessageTimestamp < cooldown_time:
                    return

            score_increment = random.randint(points_per_message, points_per_message * 3)

            previous_level = score.Level
            score.Score += score_increment
            new_level, progress, next_level_score = calculate_level(score.Score)

            score.DiscordName = username
            score.Level = new_level
            score.Progress = next_level_score
            score.LastMessageTimestamp = current_time
            score.save()

            if new_level > previous_level:
                role_name = await get_role_for_level(new_level, message.guild)
                if role_name:
                    role = discord.utils.get(message.guild.roles, name=role_name)
                    if role:
                        await message.author.add_roles(role)
                        score_log.info(f"Assigned role '{role.name}' to {username} (Level {new_level})")

                        await message.channel.send(
                            f"🎉 {message.author.mention} has leveled up to **Level {new_level}**!"
                        )

        except Exception as e:
            _log.error(f"Error processing message from {username}: {e}", exc_info=True)
        finally:
            if not __database.db.is_closed():
                __database.db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelRoleListener(bot))
    _log.info("✅ LevelRoleListener cog loaded.")
