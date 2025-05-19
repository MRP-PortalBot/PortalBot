# utils/banned_list/bl_main.py

from discord.ext import commands
from utils.helpers.logging_module import get_log

# Import internal structure
from . import __bl_commands, __bl_logic, __bl_views

_log = get_log(__name__)

async def setup(bot: commands.Bot):
    # Register the command group
    await bot.add_cog(__bl_commands.BannedListCommands(bot))

    # Register persistent views if needed (not used in current setup)
    # bot.add_view(__bl_views.BanishBlacklistForm(...))  # Example only if persistent views ever needed

    _log.info("✅ BannedListCommands system initialized (commands, views).")
