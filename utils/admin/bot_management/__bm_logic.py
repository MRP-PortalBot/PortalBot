# utils/admin/bot_management/__bm_logic.py

import asyncio
import json
from pathlib import Path
from typing import Union

from utils.database import __database as database
from utils.helpers.__logging_module import get_log

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


# ========== BotData ==========


def get_bot_data_for_server(guild_id: Union[int, str]):
    """Fetch BotData directly from the database for the specified guild."""
    try:
        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(guild_id)
        )
        if bot_data:
            _log.info(
                f"BotData loaded from DB: Prefix: {bot_data.prefix}, Server ID: {bot_data.server_id}"
            )
        else:
            _log.warning(f"No BotData found for guild {guild_id}")
        return bot_data
    except Exception as e:
        _log.error(f"Error fetching BotData for guild {guild_id}: {e}", exc_info=True)
        return None


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
