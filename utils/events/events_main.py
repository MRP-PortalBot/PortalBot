from discord.ext import commands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)

# Import listener modules with setup functions
from . import __events_listeners


async def setup(bot: commands.Bot):
    # Load listener cog(s)
    await __events_listeners.setup(bot)

    _log.info("✅ Events system initialized (listeners).")
