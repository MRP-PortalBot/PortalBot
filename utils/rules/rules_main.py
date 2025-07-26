from discord.ext import commands
from utils.helpers.__logging_module import get_log
from . import __rules_commands

_log = get_log(__name__)


class RulesMain(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(RulesMain(bot))
    await __rules_commands.setup(bot)
    _log.info("📜 Rules module initialized (commands + logic loaded).")
