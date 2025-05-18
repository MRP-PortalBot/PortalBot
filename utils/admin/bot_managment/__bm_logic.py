from core import database
from core.logging_module import get_log

_log = get_log(__name__)

async def fetch_admins_by_level(bot, level: int):
    try:
        _log.debug(f"Fetching administrators with permit level {level}")
        database.db.connect(reuse_if_open=True)
        query = database.Administrators.select().where(
            database.Administrators.TierLevel == level
        )

        admin_list = []
        for admin in query:
            try:
                user = bot.get_user(int(admin.discordID)) or await bot.fetch_user(int(admin.discordID))
                admin_list.append(f"`{user.name}` -> `{user.id}`")
            except Exception as e:
                _log.error(f"Error fetching user with ID {admin.discordID}: {e}")
                continue

        return admin_list or ["None"]
    finally:
        if not database.db.is_closed():
            database.db.close()
