import discord
import random
import time
from discord.ext import commands
from utils.database import __database
from utils.core_features.__common import calculate_level
from utils.helpers.__logging_module import get_log
from .__score_logic import get_role_for_level
from .__score_state import cooldowns


_log = get_log(__name__)
server_score_log = get_log("server_score", console=False)
last_message_time = {}


class ScoreIncrement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        bot_data = __database.BotData.get_or_none(__database.BotData.id == 1)
        if not bot_data:
            return

        blocked_channels = bot_data.get_blocked_channels()
        if message.channel.id in blocked_channels:
            server_score_log.info(
                f"Message from {message.author.name} ignored in blocked channel {message.channel.name}."
            )
            return

        cooldown_time = bot_data.cooldown_time
        points_per_message = bot_data.points_per_message
        user_id = str(message.author.id)
        username = str(message.author.name)
        current_time = time.time()

        score_increment = random.randint(points_per_message, points_per_message * 3)

        try:
            __database.db.connect(reuse_if_open=True)
            score, created = __database.ServerScores.get_or_create(
                DiscordLongID=user_id,
                ServerID=str(message.guild.id),
                defaults={"Score": 0, "Level": 1, "Progress": 0},
            )

            # Cooldown check:
            if current_time - score.LastMessageTimestamp < cooldown_time:
                remaining = cooldown_time - (current_time - score.LastMessageTimestamp)
                server_score_log.info(
                    f"{username} still on cooldown ({remaining:.2f}s left)."
                )
                return

            previous_level = score.Level
            score.Score += score_increment
            new_level, progress, next_level_score = calculate_level(score.Score)

            if score.DiscordName != username:
                score.DiscordName = username

            score.Level = new_level
            score.Progress = next_level_score
            score.save()

            if new_level > previous_level:
                role_name = await get_role_for_level(new_level, message.guild)
                if role_name:
                    role = discord.utils.get(message.guild.roles, name=role_name)
                    if role:
                        await message.author.add_roles(role)
                        server_score_log.info(
                            f"Assigned '{role_name}' to {username} (Level {new_level})."
                        )

                await message.channel.send(
                    f"🎉 {message.author.mention} has leveled up to **Level {new_level}**! Congrats!"
                )

        except Exception as e:
            server_score_log.error(
                f"Error processing score for {username}: {e}", exc_info=True
            )

        finally:
            if not __database.db.is_closed():
                __database.db.close()

        # After updating score and saving:
        score.LastMessageTimestamp = current_time
        score.save()


async def setup(bot: commands.Bot):
    await bot.add_cog(ScoreIncrement(bot))
    _log.info("✅ ScoreIncrement cog loaded.")
