# utils/core_features/cf_main.py

import discord
from discord.ext import commands

from . import __help_commands, __rules_commands, __utility_commands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class CoreFeatures(commands.GroupCog, name="core"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    bot.tree.add_command(__help_commands.HelpCommands())
    bot.tree.add_command(__rules_commands.RulesCommands())
    bot.tree.add_command(__utility_commands.UtilityCommands(bot))  # ⬅️ bot passed here

    _log.info("✅ CoreFeatures groups registered: help, rules, utility.")
