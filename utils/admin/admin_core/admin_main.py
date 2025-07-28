# utils/admin/admin_main.py

import discord
from discord.ext import commands

from . import __admin_commands, __admin_realm_management, __operator_commands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class AdminSystem(commands.GroupCog, name="admin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()  # Ensure GroupCog is properly initialized


async def setup(bot: commands.Bot):
    await __admin_commands.setup(bot)
    await __admin_realm_management.setup(bot)
    await __operator_commands.setup(bot)

    _log.info("✅ Admin system initialized: commands, realm management, operators")
