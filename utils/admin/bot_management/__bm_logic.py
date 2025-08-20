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


# --- DB bootstrap and repair helpers ---

def initialize_db(bot):
    try:
        _log.info("Initializing database...")
        database.db.connect(reuse_if_open=True)
        with database.db.atomic():
            for guild in list(bot.guilds):
                _ensure_botdata_for_guild(bot, guild)

            if database.Administrators.select().count() == 0:
                _create_administrators(bot.owner_ids)
    except Exception:
        _log.exception("Error during database initialization")
    finally:
        if not database.db.is_closed():
            database.db.close()

def _ensure_botdata_for_guild(bot, guild):
    gid = str(guild.id)
    row = database.BotData.get_or_none(database.BotData.server_id == gid)

    desired = {
        "server_name": guild.name,
        "server_id": gid,
        "bot_id": str(bot.user.id),
        "prefix": ">",
        "pb_test_server_id": "448488274562908170",
    }

    desired_welcome = str(guild.system_channel.id) if guild.system_channel else "0"

    if row is None:
        _create_bot_data(
            server_name=desired["server_name"],
            server_id=desired["server_id"],
            bot_id=desired["bot_id"],
            prefix=desired["prefix"],
            pb_test_server_id=desired["pb_test_server_id"],
            welcome_channel=desired_welcome,
        )
        _log.info(f"Created BotData for {guild.name} ({gid})")
        return

    changed = False
    if (not row.server_name) or row.server_name != desired["server_name"]:
        row.server_name = desired["server_name"]; changed = True
    if (not row.server_id) or row.server_id != desired["server_id"]:
        row.server_id = desired["server_id"]; changed = True
    if (not row.bot_id) or row.bot_id in ("0", ""):
        row.bot_id = desired["bot_id"]; changed = True
    if not getattr(row, "prefix", None):
        row.prefix = desired["prefix"]; changed = True
    if (not getattr(row, "welcome_channel", None)) or row.welcome_channel in ("0", ""):
        if desired_welcome != "0":
            row.welcome_channel = desired_welcome; changed = True
    if getattr(row, "pb_test_server_id", None) != desired["pb_test_server_id"]:
        row.pb_test_server_id = desired["pb_test_server_id"]; changed = True

    if changed:
        row.save()
        _log.info(f"Repaired BotData for {guild.name} ({gid})")

def _create_bot_data(*, server_name: str, server_id: str, bot_id: str,
                     prefix: str = ">", pb_test_server_id: str = "448488274562908170",
                     welcome_channel: str = "0"):
    database.BotData.create(
        server_name=server_name,
        server_desc="",
        server_invite="0",
        server_id=server_id,
        bot_id=bot_id,
        bot_type="Stable",
        pb_test_server_id=pb_test_server_id,
        prefix=prefix,
        admin_role="0",
        persistent_views=False,
        welcome_channel=welcome_channel,
    )

def _create_administrators(owner_ids):
    for owner_id in owner_ids:
        database.Administrators.create(discordID=str(owner_id), TierLevel=4)
    database.Administrators.create(discordID="306070011028439041", TierLevel=4)
