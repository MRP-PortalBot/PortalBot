import discord
from discord.ext import commands
from .__help_commands import HelpCommands
from .__rules_commands import RulesCommands
from .__utility_commands import UtilityCommands
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class CoreFeatures(commands.GroupCog, name="core_features"):
    """Container cog for core feature slash command groups."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    cog = CoreFeatures(bot)
    await bot.add_cog(cog)

    # Register slash command groups
    bot.tree.add_command(HelpCommands())
    bot.tree.add_command(RulesCommands())
    bot.tree.add_command(UtilityCommands(bot))  # ✅ Pass bot here

    _log.info("✅ CoreFeatures groups registered: help, rules, utility.")
