# utils/admin/admin_main.py

from discord.ext import commands
from core.logging_module import get_log
from . import __admin_commands

_log = get_log(__name__)


async def setup(bot: commands.Bot):
    # Register command group
    bot.tree.add_command(__admin_commands.AdminCommands(bot))
    _log.info("✅ Admin command group registered.")
