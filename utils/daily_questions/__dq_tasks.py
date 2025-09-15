# utils/daily_questions/dq_task.py

import pytz
from datetime import datetime
from discord.ext import tasks, commands

from utils.admin.bot_management.__bm_logic import get_bot_data_for_server
from utils.helpers.__logging_module import get_log
from .__dq_logic import (
    get_or_create_todays_question_id,
    send_daily_question_to_guilds,
    send_daily_question_repost_to_guild,
)

_log = get_log(__name__)


class DailyQuestionPoster(commands.Cog):
    """
    Runs every minute, but posts at exactly 10:00 and reposts at 18:00 America/Chicago.
    Uses a central DailyQuestionLog so only one question is chosen for the day.
    """

    def __init__(self, bot):
        self.bot = bot
        self.post_question.start()
        _log.info("✅ DailyQuestionPoster task started.")

    @tasks.loop(minutes=1)
    async def post_question(self):
        try:
            now_cst = datetime.now(pytz.timezone("America/Chicago"))
            hour = now_cst.hour
            minute = now_cst.minute

            # 10:00 AM — pick or reuse the one global question for the day and post per guild
            if hour == 11 and minute >= 0:
                _log.info(
                    "⏰ 10:00 AM tick — choosing today's question and posting to guilds."
                )
                question_display_order = get_or_create_todays_question_id()
                await send_daily_question_to_guilds(
                    self.bot, question_display_order, now_cst
                )

            # 6:00 PM — repost the same day's question per guild
            if hour == 18 and minute >= 0:
                _log.info("⏰ 6:00 PM tick — reposting today's question to guilds.")
                # We do not need to re-choose; use today's logged question
                question_display_order = get_or_create_todays_question_id()
                for guild in self.bot.guilds:
                    bot_data = get_bot_data_for_server(str(guild.id))
                    if not bot_data:
                        _log.warning(
                            f"No BotData for guild {guild.id} — is it configured?"
                        )
                        continue
                    # Only repost if we posted this question to this guild earlier today
                    if bot_data.last_question_posted == str(question_display_order):
                        await send_daily_question_repost_to_guild(
                            self.bot, guild.id, question_display_order
                        )
                    else:
                        _log.debug(
                            f"⏭️ Skipping repost for {guild.name} ({guild.id}); "
                            f"last_question_posted={bot_data.last_question_posted}, "
                            f"today={question_display_order}"
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
