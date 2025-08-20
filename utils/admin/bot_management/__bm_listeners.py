import discord
from discord.ext import commands

from utils.helpers.__logging_module import get_log
from utils.database import __database as database
# Use the normalized creator/repair function we added earlier
from utils.admin.bot_management.__bm_logic import _ensure_botdata_for_guild

_log = get_log(__name__)


def _first_welcome_channel_id(guild: discord.Guild) -> str:
    """Prefer system channel; otherwise first text channel; else '0'."""
    if guild.system_channel:
        return str(guild.system_channel.id)
    return str(guild.text_channels[0].id) if guild.text_channels else "0"


class BotManagementListeners(commands.Cog):
    """Event listeners for bot-management lifecycle tasks."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Ensure BotData exists for newly joined guilds."""
        _log.info(f"Joined guild {guild.name} ({guild.id}); ensuring BotData.")
        # If your _ensure_botdata_for_guild relies on DB connection, wrap it:
        with database.db.connection_context():
            # _ensure_botdata_for_guild handles create/repair idempotently
            _ensure_botdata_for_guild(self.bot, guild)
        # If you also want to set a default welcome channel immediately:
        row = database.BotData.get_or_none(database.BotData.server_id == str(guild.id))
        if row and (not getattr(row, "welcome_channel", None) or row.welcome_channel in ("", "0")):
            row.welcome_channel = _first_welcome_channel_id(guild)
            row.save()

    # Optional: log leaves or clean up if you store per-guild caches
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        _log.info(f"Removed from guild {guild.name} ({guild.id}).")
        # Usually you DO NOT delete DB rows automatically. If you want to, do it here.


async def setup(bot: commands.Bot):
    await bot.add_cog(BotManagementListeners(bot))
