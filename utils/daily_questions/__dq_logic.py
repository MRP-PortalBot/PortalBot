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

# ----- Helpers -----


def _today_cst_date() -> date:
    return datetime.now(pytz.timezone("America/Chicago")).date()


def _now_cst_naive() -> datetime:
    # MariaDB DATETIME expects naive "YYYY-MM-DD HH:MM:SS"
    return datetime.now(pytz.timezone("America/Chicago")).replace(tzinfo=None)


def _ensure_db():
    database.ensure_database_connection()


# Raw SQL helpers (robust against ORM mapping issues)
# Adjust column/table names here if your schema differs.
_DQL_TABLE = "daily_question_log"
_DQL_DATE_COL = (
    "log_date"  # << if your column is actually named `date`, change this to "date"
)


def _delete_zero_date_rows():
    # Remove any bad rows that might have been inserted earlier by non-strict mode.
    sql = f"DELETE FROM `{_DQL_TABLE}` WHERE `{_DQL_DATE_COL}` = '0000-00-00'"
    database.db.execute_sql(sql)


def _select_today_question_id(today: date):
    sql = f"SELECT question_id FROM `{_DQL_TABLE}` WHERE `{_DQL_DATE_COL}`=%s LIMIT 1"
    cur = database.db.execute_sql(sql, (today.strftime("%Y-%m-%d"),))
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None


def _upsert_daily_log(today: date, question_id: int, posted_at: datetime):
    sql = f"""
        INSERT INTO `{_DQL_TABLE}` (`{_DQL_DATE_COL}`, `question_id`, `posted_at`)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `question_id` = VALUES(`question_id`),
            `posted_at`   = VALUES(`posted_at`)
    """
    params = (
        today.strftime("%Y-%m-%d"),
        int(question_id),
        posted_at.strftime("%Y-%m-%d %H:%M:%S"),
    )
    database.db.execute_sql(sql, params)


# ----- Central “question of the day” -----


def get_or_create_todays_question_id() -> int:
    _ensure_db()
    today = _today_cst_date()

    with database.db.atomic():
        # Defensive cleanup
        _delete_zero_date_rows()

        # Already chosen today?
        qid = _select_today_question_id(today)
        if qid is not None:
            q = database.Question.get_by_id(qid)
            return q.display_order

        # Pick an unused question (usage is "True"/"False" text in your schema)
        unused = database.Question.select().where(database.Question.usage == "False")
        if not unused.exists():
            database.Question.update(usage="False").execute()

        question = (
            database.Question.select()
            .where(database.Question.usage == "False")
            .order_by(fn.Rand())
            .limit(1)
            .get()
        )
        question.usage = "True"
        question.save()

        # Upsert today's log row (robust against double-runs)
        _upsert_daily_log(today, question.id, _now_cst_naive())

        return question.display_order


# ----- Posting flows -----


async def post_question_to_guild(
    bot,
    guild,
    question_id,
    embed,
    posted_at: datetime,
    *,
    record_to_botdata: bool = True,
):
    """
    Posts the question to a single guild if enabled.
    When record_to_botdata=False, does NOT touch BotData.last_question_posted(_time).
    """
    try:
        bot_data = get_bot_data_for_server(str(guild.id))
        if not bot_data:
            _log.warning(
                f"No BotData for guild {guild.id} — configure the server first."
            )
            return
        if not bot_data.daily_question_enabled:
            _log.debug(f"Daily Question disabled for {guild.name} ({guild.id}).")
            return
        if not bot_data.daily_question_channel:
            _log.warning(
                f"No daily_question_channel set for {guild.name} ({guild.id})."
            )
            return

        # Normalize to naive for DB comparisons/saves
        posted_at_naive = (
            posted_at.replace(tzinfo=None) if posted_at.tzinfo else posted_at
        )

        # Only do the "already posted today" guard for the normal daily posts
        if record_to_botdata:
            if (
                bot_data.last_question_posted_time
                and bot_data.last_question_posted_time.date() == posted_at_naive.date()
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
            bot_data.last_question_posted_time = posted_at_naive
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

        # Normalize to naive before we pass into post_question_to_guild
        when_naive = when_cst.replace(tzinfo=None) if when_cst.tzinfo else when_cst

        for guild in bot.guilds:
            await post_question_to_guild(
                bot, guild, question.display_order, embed, when_naive
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
            now_cst = _now_cst_naive()
            await post_question_to_guild(
                bot, guild, question.display_order, embed, now_cst
            )

    except Exception as e:
        _log.error(f"❌ Error reposting daily question: {e}", exc_info=True)


# ----- Maintenance -----


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


# ----- Manual post (no usage / no daily log) -----


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

        now_cst = _now_cst_naive()
        await post_question_to_guild(
            bot,
            guild,
            question.display_order,
            embed,
            now_cst,
            record_to_botdata=False,  # do NOT touch BotData
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
