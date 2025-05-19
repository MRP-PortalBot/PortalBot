# utils/daily_questions/dq_logic.py

import pytz
import discord
from datetime import datetime
from peewee import fn

from utils.database import __database
from admin.bot_management.__bm_logic import get_cached_bot_data

from utils.helpers.__logging_module import get_log
from .__dq_views import QuestionVoteView

_log = get_log(__name__)


def renumber_display_order():
    """Reassign sequential display_order to all questions based on creation order."""
    try:
        __database.ensure_database_connection()
        questions = __database.Question.select().order_by(__database.Question.id)
        for new_order, question in enumerate(questions, start=1):
            question.display_order = new_order
            question.save()
        _log.info("✅ Renumbered display_order for all questions.")
    except Exception as e:
        _log.error(f"❌ Failed to renumber display_order: {e}", exc_info=True)


async def send_daily_question(bot, question_id: str = None) -> str | None:
    """Selects and sends a daily question embed to configured channels in all guilds."""
    try:
        __database.ensure_database_connection()

        # Pick unused or specific question
        if question_id is None:
            unused = __database.Question.select().where(
                __database.Question.usage == "False"
            )
            if not unused.exists():
                __database.Question.update(usage="False").execute()
                _log.info("🔄 All questions used — resetting usage flags.")

            question = (
                __database.Question.select()
                .where(__database.Question.usage == "False")
                .order_by(fn.Rand())
                .limit(1)
                .get()
            )
            question.usage = "True"
            question.save()
        else:
            question = __database.Question.get(
                __database.Question.display_order == question_id
            )

        # Create embed
        embed = discord.Embed(
            title="🌟❓Question of the Day❓🌟",
            description=f"## **{question.question}**",
            color=discord.Color.from_rgb(177, 13, 159),
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/788873229136560140/1298745739048124457/MC-QOD.png"
        )
        embed.add_field(
            name="🗣️ Discuss",
            value="We'd love to hear your thoughts! Share your response below and get to know the community better!",
            inline=False,
        )
        embed.add_field(
            name="💡 Tip",
            value="Remember, thoughtful answers help everyone learn something new!",
            inline=False,
        )
        embed.set_footer(
            text=f"Thank you for participating! • Question #{question.display_order}",
            icon_url="https://cdn.discordapp.com/attachments/788873229136560140/801180249748406272/Portal_Design.png",
        )
        embed.timestamp = datetime.now()

        # Send to all enabled guilds
        for guild in bot.guilds:
            bot_data = get_cached_bot_data(guild.id)
            if not bot_data or not bot_data.daily_question_enabled:
                _log.debug(
                    f"⏭️ Skipping guild {guild.id} (not enabled or missing data)."
                )
                continue

            send_channel = bot.get_channel(int(bot_data.daily_question_channel))
            if not send_channel:
                _log.error(
                    f"❌ Channel ID {bot_data.daily_question_channel} not found in {guild.name}."
                )
                continue

            view = QuestionVoteView(bot, question.display_order)
            await send_channel.send(embed=embed, view=view)
            _log.info(
                f"📤 Posted question #{question.display_order} to {send_channel.name} in {guild.name}."
            )

        return question.display_order

    except __database.Question.DoesNotExist:
        _log.error("❗ Question not found.")
    except Exception as e:
        _log.error(f"❌ Error posting daily question: {e}", exc_info=True)


def reset_question_usage() -> int:
    """
    Resets all questions' usage status to "False".

    Returns:
        int: Number of questions updated.
    """
    try:
        __database.ensure_database_connection()
        updated = __database.Question.update(usage="False").execute()
        _log.info(f"🔄 Reset usage for {updated} questions.")
        return updated
    except Exception as e:
        _log.error(f"❌ Failed to reset question usage: {e}", exc_info=True)
        return 0
