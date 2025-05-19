# utils/admin/admin_main.py

from discord.ext import commands
from utils.helpers.logging_module import get_log
from . import __admin_commands, __admin_realm_management

_log = get_log(__name__)

# Import admin components
from . import (
    __operator_commands,
)


async def setup(bot: commands.Bot):
    # Load grouped command cogs
    await __admin_commands.setup(bot)
    await __admin_realm_management.setup(bot)
    await __operator_commands.setup(bot)

    _log.info("✅ Admin system initialized: commands, realm management, operators")
