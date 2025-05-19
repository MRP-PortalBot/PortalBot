from utils.database import __database
from utils.helpers.__logging_module import get_log

_log = get_log("server_score_logic")


async def get_role_for_level(level: int, guild) -> str | None:
    """
    Fetch the role name associated with a given level.
    """
    try:
        _log.debug(f"Fetching role for level {level} in guild {guild.name}.")
        __database.db.connect(reuse_if_open=True)
        leveled_role = __database.LeveledRoles.get_or_none(
            __database.LeveledRoles.Level == level
        )
        return leveled_role.RoleName if leveled_role else None
    except Exception as e:
        _log.error(f"Error fetching role for level {level}: {e}")
        return None
    finally:
        if not __database.db.is_closed():
            __database.db.close()
