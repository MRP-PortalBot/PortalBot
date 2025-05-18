# utils/profile/__profile_main.py

from discord.ext import commands
from core.logging_module import get_log

# Import internal modules
from . import __profile_commands, __profile_views

_log = get_log(__name__)


async def setup(bot: commands.Bot):
    # Load the commands as a cog
    await __profile_commands.setup(bot)

    # Register persistent views (if needed in the future)

    _log.info("✅ Profile system initialized (commands, tasks, views).")
