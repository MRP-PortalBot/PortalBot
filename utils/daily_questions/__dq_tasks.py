# utils/daily_questions/dq_task.py

import pytz
from datetime import datetime
from discord.ext import tasks, commands
from utils.admin.bot_management.__bm_logic import get_cached_bot_data

from utils.helpers.__logging_module import get_log
from admin.bot_management.__bm_commands import update_bot_data
from .__dq_logic import send_daily_question

_log = get_log(__name__)


class DailyQuestionPoster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_question.start()
        _log.info("✅ DailyQuestionPoster task started.")

    @tasks.loop(hours=1)
    async def post_question(self):
        _log.info("🕒 post_question loop ticked.")

        try:
            now = datetime.now(pytz.timezone("America/Chicago"))
            hour = now.hour
            minute = now.minute

            if 10 == hour and 0 <= minute <= 10:
                _log.info("⏰ Attempting 10:00 AM post.")
                question_id = await send_daily_question(self.bot)

                for guild in self.bot.guilds:
                    bot_data = get_cached_bot_data(guild.id)
                    if bot_data:
                        bot_data.last_question_posted = question_id
                        bot_data.last_question_posted_time = now
                        bot_data.save()
                        _log.info(f"✅ Saved last_question_posted for {guild.name}.")

            elif 18 == hour and 0 <= minute <= 10:
                _log.info("⏰ Attempting 6:00 PM repost.")
                for guild in self.bot.guilds:
                    bot_data = get_cached_bot_data(guild.id)
                    if bot_data and bot_data.last_question_posted:
                        await send_daily_question(
                            self.bot, bot_data.last_question_posted
                        )
                    else:
                        _log.warning(
                            f"⚠️ No question to repost for {guild.name} ({guild.id})."
                        )

        except Exception as e:
            _log.error(f"Error in post_question task: {e}", exc_info=True)

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        _log.info("✅ Bot is ready. Starting post_question loop.")


async def setup(bot):
    await bot.add_cog(DailyQuestionPoster(bot))
    _log.info("✅ DailyQuestionPoster cog loaded.")
