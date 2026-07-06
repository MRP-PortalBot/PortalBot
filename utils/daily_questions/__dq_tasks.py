# utils/daily_questions/dq_task.py

import asyncio
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
        self._daily_posted_date = None
        self._daily_reposted_date = None
        self.post_question.start()
        _log.info("✅ DailyQuestionPoster task started.")

    @tasks.loop(minutes=1)
    async def post_question(self):
        try:
            now_cst = datetime.now(pytz.timezone("America/Chicago"))
            hour = now_cst.hour
            today = now_cst.date()

            # 10 AM — try once per minute until a daily question posts, then stop for the day.
            if hour == 10 and self._daily_posted_date != today:
                posted = await self._post_daily_question_until_success(today)
                if posted:
                    self._daily_posted_date = today

            # 6 PM — try once per minute until the daily question reposts, then stop for the day.
            if hour == 18 and self._daily_reposted_date != today:
                reposted = await self._repost_daily_question_until_success(today)
                if reposted:
                    self._daily_reposted_date = today

        except Exception as e:
            _log.error(f"Error in post_question task: {e}", exc_info=True)

    async def _post_daily_question_until_success(self, today) -> bool:
        while datetime.now(pytz.timezone("America/Chicago")).hour == 10:
            now_cst = datetime.now(pytz.timezone("America/Chicago"))
            _log.info(
                "⏰ 10 AM retry — choosing today's question and posting to guilds."
            )
            question_display_order = get_or_create_todays_question_id()
            posted = await send_daily_question_to_guilds(
                self.bot, question_display_order, now_cst
            )

            if posted:
                _log.info("✅ Daily question posted; stopping 10 AM retries.")
                return True

            _log.warning(
                "Daily question did not post; trying again in 60 seconds."
            )
            await asyncio.sleep(60)

        _log.warning(f"Daily question did not post during the 10 AM window for {today}.")
        return False

    async def _repost_daily_question_until_success(self, today) -> bool:
        while datetime.now(pytz.timezone("America/Chicago")).hour == 18:
            _log.info("⏰ 6 PM retry — reposting today's question to guilds.")
            question_display_order = get_or_create_todays_question_id()
            reposted = False

            for guild in self.bot.guilds:
                bot_data = get_bot_data_for_server(str(guild.id))
                if not bot_data:
                    _log.warning(
                        f"No BotData for guild {guild.id} — is it configured?"
                    )
                    continue

                # Only repost if we posted this question to this guild earlier today.
                if bot_data.last_question_posted == str(question_display_order):
                    reposted_to_guild = await send_daily_question_repost_to_guild(
                        self.bot, guild.id, question_display_order
                    )
                    reposted = reposted or reposted_to_guild
                else:
                    _log.debug(
                        f"⏭️ Skipping repost for {guild.name} ({guild.id}); "
                        f"last_question_posted={bot_data.last_question_posted}, "
                        f"today={question_display_order}"
                    )

            if reposted:
                _log.info("✅ Daily question reposted; stopping 6 PM retries.")
                return True

            _log.warning(
                "Daily question repost did not send; trying again in 60 seconds."
            )
            await asyncio.sleep(60)

        _log.warning(
            f"Daily question did not repost during the 6 PM window for {today}."
        )
        return False

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        _log.info("✅ Bot is ready. Starting post_question loop.")


async def setup(bot):
    await bot.add_cog(DailyQuestionPoster(bot))
    _log.info("✅ DailyQuestionPoster cog loaded.")
