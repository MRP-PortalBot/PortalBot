import asyncio
import json
from pathlib import Path
from typing import Union

from utils.database import __database as database
from utils.helpers.__logging_module import get_log

# utils/admin/bot_management/__bm_logic.py

from utils.core_features.__common import refresh_bot_data_cache

_log = get_log(__name__)

# ========== Admin Helpers ==========


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
                user = bot.get_user(int(admin.discordID)) or await bot.fetch_user(
                    int(admin.discordID)
                )
                admin_list.append(f"`{user.name}` -> `{user.id}`")
            except Exception as e:
                _log.error(f"Error fetching user with ID {admin.discordID}: {e}")
                continue

        return admin_list or ["None"]
    finally:
        if not database.db.is_closed():
            database.db.close()


# ========== BotData Cache ==========

cache_lock = asyncio.Lock()
bot_data_cache = {}


async def get_bot_data_for_server(server_id: Union[int, str]):
    """
    Fetch and cache BotData for a given server.
    Uses string-based ID comparison to support TextField storage.
    """
    async with cache_lock:
        if str(server_id) in bot_data_cache:
            _log.info(f"Returning cached bot data for server {server_id}")
            return bot_data_cache[str(server_id)]

    try:
        bot_info = (
            database.BotData.select()
            .where(database.BotData.server_id == str(server_id))
            .get()
        )
        async with cache_lock:
            bot_data_cache[str(server_id)] = bot_info
        _log.info(
            f"Bot data fetched and cached for guild {server_id}: "
            f"Prefix: {bot_info.prefix}, Server ID: {bot_info.server_id}"
        )
        return bot_info
    except database.DoesNotExist:
        _log.error(f"No BotData found for server ID: {server_id}")
        return None
    except Exception as e:
        _log.error(
            f"Error fetching bot data for server ID {server_id}: {e}", exc_info=True
        )
        return None


def get_cached_bot_data(server_id: Union[int, str]):
    """
    Return cached BotData for the given server ID if it exists.
    """
    bot_data = bot_data_cache.get(str(server_id))
    if bot_data:
        _log.info(
            f"Cached bot data fetched for guild {server_id}: "
            f"Prefix: {bot_data.prefix}, Server ID: {bot_data.server_id}"
        )
    else:
        _log.warning(f"No cached bot data found for guild {server_id}")
    return bot_data


def refresh_bot_data_cache(guild_id: int):
    """Refresh the bot_data_cache entry for a specific guild from the DB."""
    bot_data = database.BotData.get_or_none(database.BotData.server_id == str(guild_id))
    if bot_data:
        bot_data_cache[str(guild_id)] = bot_data


async def update_bot_data_cache_for_guild(guild_id: int):
    try:
        refresh_bot_data_cache(str(guild_id))
        _log.info(f"Bot data cache updated for guild: {guild_id}")
        return True
    except Exception as e:
        _log.error(f"Error updating bot data cache: {e}", exc_info=True)
        return False


# ========== Config Loader ==========


def load_config():
    """
    Load config from botconfig.json.

    Returns:
        Tuple[dict, Path]: The config dictionary and the Path object.
    """
    config_file = Path("botconfig.json")
    try:
        config_file.touch(exist_ok=True)
        if config_file.read_text() == "":
            config_file.write_text("{}")
        with config_file.open("r") as f:
            config = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        _log.error(f"Failed to load configuration: {e}")
        raise e
    return config, config_file


# Global load on import
config, config_file = load_config()
