# utils/realm_profiles/rp_main.py

from discord.ext import commands
from utils.helpers.__logging_module import get_log

# Submodules
from . import __rp_commands, __rp_views

_log = get_log(__name__)


async def setup(bot: commands.Bot):
    # Register slash command groups
    await __rp_commands.setup(bot)

    # Register persistent views (selects/modals)
    await __rp_views.setup(bot)

    _log.info("✅ Realm Profile system initialized (commands, views)")
