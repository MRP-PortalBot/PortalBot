# utils/level_system/ls_main.py

from discord.ext import commands
from utils.helpers.__logging_module import get_log

# Import command and listener modules
from . import __ls_commands, __ls_listeners

_log = get_log(__name__)


async def setup(bot: commands.Bot):
    # Load slash command group
    await __ls_commands.setup(bot)

    # Load XP/level event listener
    await __ls_listeners.setup(bot)

    _log.info("🏅 Level System fully initialized (commands + listeners).")
