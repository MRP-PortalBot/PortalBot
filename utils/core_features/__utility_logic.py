import discord
from datetime import datetime
from utils.database import database
from utils.helpers.__logging_module import get_log

_log = get_log("reminder_logic")


async def run_reminder_loop(bot: discord.Client):
    """
    Check and send reminders. Intended to be called by a scheduled task every minute.
    """
    try:
        now = datetime.now()
        due = database.Reminder.select().where(database.Reminder.remind_at <= now)

        for reminder in due:
            user = bot.get_user(int(reminder.user_id))
            if user:
                try:
                    await user.send(
                        f"🔔 Hey {user.mention}, here's your reminder:\n{reminder.message_link}"
                    )
                    _log.info(f"Reminder sent to {user.id}")
                except Exception as e:
                    _log.warning(f"Failed to DM reminder to {user.id}: {e}")
            reminder.delete_instance()

    except Exception as e:
        _log.error(f"Reminder loop error: {e}", exc_info=True)
