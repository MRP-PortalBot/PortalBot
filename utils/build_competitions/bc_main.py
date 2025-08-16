# utils/build_competitions/bc_main.py
from discord.ext import commands
from utils.helpers.__logging_module import get_log

# Import internal modules
from . import __bc_commands, __bc_tasks

_log = get_log(__name__)


async def setup(bot: commands.Bot):
    # Register commands and tasks just like your profile system
    await __bc_commands.setup(bot)
    await __bc_tasks.setup(bot)

    _log.info("✅ Build competition initialized (commands + tasks).")
