# utils/daily_questions/dq_logic.py

import pytz
import discord
from datetime import datetime
from peewee import fn

from utils.database import __database as database
from utils.admin.bot_management.__bm_logic import get_bot_data_for_server

from utils.helpers.__logging_module import get_log
from .__dq_views import QuestionVoteView, create_question_embed

_log = get_log(__name__)


def renumber_display_order():
    """Reassign sequential display_order to all questions based on creation order."""
    try:
        database.ensure_database_connection()
        questions = database.Question.select().order_by(database.Question.id)
        for new_order, question in enumerate(questions, start=1):
            question.display_order = new_order
            question.save()
        _log.info("✅ Renumbered display_order for all questions.")
    except Exception as e:
        _log.error(f"❌ Failed to renumber display_order: {e}", exc_info=True)

async def post_question_to_guild(bot, guild, question_id, embed):
    try:
        bot_data = get_bot_data_for_server(guild.id)
        if not bot_data or not bot_data.daily_question_enabled:
            _log.debug(f"⏭️ Skipping guild {guild.id} (not enabled or missing data).")
            return

        send_channel = bot.get_channel(int(bot_data.daily_question_channel))
        if not send_channel:
            _log.error(f"❌ Channel ID {bot_data.daily_question_channel} not found in {guild.name}.")
            return

        view = QuestionVoteView(bot, question_id)
        await send_channel.send(embed=embed, view=view)
        _log.info(f"📤 Posted question #{question_id} to {send_channel.name} in {guild.name}.")

    except Exception as e:
        _log.error(f"❌ Failed to send question to {guild.name}: {e}", exc_info=True)

async def send_daily_question(bot, question_id: str = None) -> str | None:
    try:
        database.ensure_database_connection()

        # Pick unused or specific question
        if question_id is None:
            unused = database.Question.select().where(database.Question.usage == "False")
            if not unused.exists():
                database.Question.update(usage="False").execute()
                _log.info("🔄 All questions used — resetting usage flags.")

            question = (
                database.Question.select()
                .where(database.Question.usage == "False")
                .order_by(fn.Rand())
                .limit(1)
                .get()
            )
            question.usage = "True"
            question.save()
        else:
            question = database.Question.get(database.Question.display_order == question_id)

        embed = create_question_embed(question)

        for guild in bot.guilds:
            await post_question_to_guild(bot, guild, question.display_order, embed)

        return question.display_order

    except Exception as e:
        _log.error(f"❌ Error posting daily question: {e}", exc_info=True)

async def send_daily_question_repost(bot, guild_id, question_id: str) -> None:
    try:
        database.ensure_database_connection()

        question = database.Question.get(database.Question.display_order == question_id)
        embed = create_question_embed(question)

        guild = bot.get_guild(guild_id)
        if guild:
            await post_question_to_guild(bot, guild, question.display_order, embed)

    except Exception as e:
        _log.error(f"❌ Error reposting daily question: {e}", exc_info=True)
        

def reset_question_usage() -> int:
    """
    Resets all questions' usage status to "False".

    Returns:
        int: Number of questions updated.
    """
    try:
        database.ensure_database_connection()
        updated = database.Question.update(usage="False").execute()
        _log.info(f"🔄 Reset usage for {updated} questions.")
        return updated
    except Exception as e:
        _log.error(f"❌ Failed to reset question usage: {e}", exc_info=True)
        return 0
