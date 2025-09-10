# utils/daily_questions/dq_logic.py

import pytz
import discord
from datetime import datetime, date
from peewee import fn

from utils.database import __database as database
from utils.admin.bot_management.__bm_logic import get_bot_data_for_server

from utils.helpers.__logging_module import get_log
from .__dq_views import QuestionVoteView, create_question_embed

_log = get_log(__name__)


# ---------- Helpers: schema accessors ----------


def _today_cst_date():
    return datetime.now(pytz.timezone("America/Chicago")).date()

def _now_cst_naive():
    # MariaDB DATETIME expects naive "YYYY-MM-DD HH:MM:SS"
    return datetime.now(pytz.timezone("America/Chicago")).replace(tzinfo=None)


def _ensure_db():
    database.ensure_database_connection()


# ---------- New: central “question of the day” log ----------


def get_or_create_todays_question_id() -> int:
    database.ensure_database_connection()
    today = _today_cst_date()

    with database.db.atomic():
        existing = (database.Daily_Question_Log
                    .select()
                    .where(database.Daily_Question_Log.log_date == today)
                    .first())
        if existing:
            q = database.Question.get_by_id(existing.question_id)
            return q.display_order

        # pick an unused question (usage is 'True'/'False' text in your schema)
        unused = database.Question.select().where(database.Question.usage == "False")
        if not unused.exists():
            database.Question.update(usage="False").execute()

        question = (database.Question
                    .select()
                    .where(database.Question.usage == "False")
                    .order_by(fn.Rand())
                    .limit(1)
                    .get())

        question.usage = "True"
        question.save()

        database.Daily_Question_Log.create(
            date=today,                      # <-- a date object, not a string
            question=question,               # <-- FK instance or id both fine
            posted_at=_now_cst_naive(),      # <-- naive datetime, not ISO w/ tz
        )
        return question.display_order

# ---------- Posting flows ----------
async def post_question_to_guild(
    bot,
    guild,
    question_id,
    embed,
    posted_at: datetime,
    *,
    record_to_botdata: bool = True,  # <— NEW
):
    """
    Posts the question to a single guild if enabled.
    When record_to_botdata=False, does NOT touch BotData.last_question_posted(_time).
    """
    try:
        bot_data = get_bot_data_for_server(str(guild.id))  # <-- was guild.id
        if not bot_data or not bot_data.daily_question_enabled:
            _log.debug(f"⏭️ Skipping guild {guild.id} (not enabled or missing data).")
            return
        
        # Only do the "already posted today" guard for the normal daily posts
        if record_to_botdata:
            if (
                bot_data.last_question_posted_time
                and bot_data.last_question_posted_time.date() == posted_at.date()
            ):
                if str(bot_data.last_question_posted) == str(question_id):
                    _log.debug(
                        f"⏭️ Already posted today's question to {guild.name}; skipping."
                    )
                    return

        send_channel = bot.get_channel(int(bot_data.daily_question_channel))
        if not send_channel:
            _log.error(
                f"❌ Channel ID {bot_data.daily_question_channel} not found in {guild.name}."
            )
            return

        view = QuestionVoteView(bot, question_id)
        await send_channel.send(embed=embed, view=view)
        _log.info(
            f"📤 Posted question #{question_id} to {send_channel.name} in {guild.name} (record={record_to_botdata})."
        )

        if record_to_botdata:
            bot_data.last_question_posted = str(question_id)
            bot_data.last_question_posted_time = posted_at
            bot_data.save()

    except Exception as e:
        _log.error(f"❌ Failed to send question to {guild.name}: {e}", exc_info=True)


async def send_daily_question_to_guilds(
    bot, question_display_order: int, when_cst: datetime
):
    """
    Build embed once and post to every enabled guild, using the already-chosen
    question_display_order for today.
    """
    try:
        _ensure_db()
        question = database.Question.get(
            database.Question.display_order == question_display_order
        )
        embed = create_question_embed(question)

        for guild in bot.guilds:
            await post_question_to_guild(
                bot, guild, question.display_order, embed, when_cst
            )

    except Exception as e:
        _log.error(f"❌ Error posting daily question to guilds: {e}", exc_info=True)


async def send_daily_question_repost_to_guild(
    bot, guild_id, question_display_order: int
) -> None:
    """
    Reposts today's question to a single guild.
    """
    try:
        _ensure_db()
        question = database.Question.get(
            database.Question.display_order == question_display_order
        )
        embed = create_question_embed(question)

        guild = bot.get_guild(guild_id)
        if guild:
            now_cst = datetime.now(pytz.timezone("America/Chicago"))
            await post_question_to_guild(
                bot, guild, question.display_order, embed, now_cst
            )

    except Exception as e:
        _log.error(f"❌ Error reposting daily question: {e}", exc_info=True)


# ---------- Maintenance ----------


def renumber_display_order():
    """Reassign sequential display_order to all questions based on creation order."""
    try:
        _ensure_db()
        questions = database.Question.select().order_by(database.Question.id)
        for new_order, question in enumerate(questions, start=1):
            question.display_order = new_order
            question.save()
        _log.info("✅ Renumbered display_order for all questions.")
    except Exception as e:
        _log.error(f"❌ Failed to renumber display_order: {e}", exc_info=True)


def reset_question_usage() -> int:
    """
    Resets all questions' usage status to "False".
    """
    try:
        _ensure_db()
        updated = database.Question.update(usage="False").execute()
        _log.info(f"🔄 Reset usage for {updated} questions.")
        return updated
    except Exception as e:
        _log.error(f"❌ Failed to reset question usage: {e}", exc_info=True)
        return 0


# ---------- Post Question without updating database ----------


async def send_specific_question_to_guild_no_usage(
    bot, guild_id: int, question_display_order: int
) -> None:
    """
    Post a specific question to ONE guild without changing usage or today's log,
    and without recording BotData.last_question_posted(_time).
    """
    try:
        _ensure_db()
        question = database.Question.get(
            database.Question.display_order == question_display_order
        )
        embed = create_question_embed(question)

        guild = bot.get_guild(int(guild_id))
        if not guild:
            _log.error(f"❌ Guild {guild_id} not found.")
            return

        now_cst = datetime.now(pytz.timezone("America/Chicago"))
        await post_question_to_guild(
            bot,
            guild,
            question.display_order,
            embed,
            now_cst,
            record_to_botdata=False,  # <— do NOT touch BotData
        )

    except database.Question.DoesNotExist:
        _log.error(
            f"❌ Question with display_order={question_display_order} not found."
        )
        raise
    except Exception as e:
        _log.error(
            f"❌ Error posting specific question (no-usage) to guild {guild_id}: {e}",
            exc_info=True,
        )
        raise
