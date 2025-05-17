# utils/daily_questions/dq_main.py

from discord.ext import commands
from core.logging_module import get_log

_log = get_log(__name__)

# Import all daily question components
from . import dq_commands, dq_tasks, dq_views


async def setup(bot: commands.Bot):
    # Load command group
    await dq_commands.setup(bot)

    # Load task that posts questions
    await dq_tasks.setup(bot)

    # Register persistent views
    bot.add_view(dq_views.QuestionSuggestionManager())
    bot.add_view(dq_views.SuggestQuestionFromDQ())

    _log.info("✅ Daily Question system initialized (commands, tasks, views).")
