from discord.ext import commands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)

# Import all leveled roles components
from . import __lr_commands, __lr_sync, __lr_listeners

async def setup(bot: commands.Bot):
    # Load slash command groups
    await __lr_commands.setup(bot)
    await __lr_sync.setup(bot)

    # Load event listeners
    await __lr_listeners.setup(bot)

    _log.info("🏆 Leveled Roles system initialized (commands + listeners).")
