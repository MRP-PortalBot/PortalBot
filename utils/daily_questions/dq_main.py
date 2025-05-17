# utils/daily_questions/dq_main.py

from discord.ext import commands
from core.logging_module import get_log

_log = get_log(__name__)

# Import all daily question components
from . import __dq_commands, __dq_tasks, __dq_views


async def setup(bot: commands.Bot):
    # Load command group
    await __dq_commands.setup(bot)

    # Load task that posts questions
    await __dq_tasks.setup(bot)

    # Register persistent views
    bot.add_view(__dq_views.QuestionSuggestionManager(bot))
    bot.add_view(__dq_views.SuggestQuestionFromDQ(bot))

    _log.info("✅ Daily Question system initialized (commands, tasks, views).")
