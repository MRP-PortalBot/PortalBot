# utils/banned_list/bl_main.py

import discord
from discord.ext import commands

from . import __bl_commands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class BannedList(commands.GroupCog, name="banned-list"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    cog = BannedList(bot)
    await bot.add_cog(cog)

    await __bl_commands.setup(bot)

    _log.info("✅ Banned list system initialized.")
