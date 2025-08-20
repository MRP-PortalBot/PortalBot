import os
import asyncio
from datetime import datetime
import discord
from discord.ext import commands

from utils.helpers.__logging_module import get_log
from utils.database import __database as database
from utils.core_features.__constants import ConsoleColors
from utils.admin.bot_management.__bm_logic import initialize_db
from utils.admin.bot_management.__bm_listeners import (
    _first_welcome_channel_id,
)  # reuse helper
from utils.admin.bot_management.__bm_logic import (
    get_bot_data_for_server,
)  # if you have this; else query BotData directly

_log = get_log(__name__)


class BotManagementBootstrap(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ran_ready_once = False

    @commands.Cog.listener()
    async def on_ready(self):
        # prevent running twice on reconnects
        if self._ran_ready_once:
            return
        self._ran_ready_once = True

        now = datetime.now()
        _log.info(f"Bot ready at {now}. Running bootstrap...")

        # Ensure DB rows for all guilds
        with database.db.connection_context():
            initialize_db(self.bot)

        # Initialize persistent views once per guild
        await self._init_persistent_views()

        # Git version banner (best-effort)
        git_version = await self._git_version()
        self._print_banner(now, git_version)

        # Post to github-log in your PB test server
        await self._notify_github_log()

        _log.info("Bootstrap complete.")

    async def _init_persistent_views(self):
        from utils.daily_questions.__dq_views import QuestionSuggestionManager
        from utils.database import __database as database

        with database.db.connection_context():
            for guild in self.bot.guilds:
                row = database.BotData.get_or_none(
                    database.BotData.server_id == str(guild.id)
                )
                if not row:
                    _log.warning(
                        f"BotData missing during persistent view init for {guild.id}"
                    )
                    continue
                if not row.persistent_views:
                    self.bot.add_view(QuestionSuggestionManager())
                    row.persistent_views = True
                    row.save()
                    _log.info(
                        f"Persistent views initialized for {guild.name} ({guild.id})"
                    )

    async def _git_version(self) -> str:
        try:
            proc = await asyncio.create_subprocess_shell(
                "git describe --always",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip() if proc.returncode == 0 else "ERROR"
        except Exception as e:
            _log.error(f"Error fetching Git version: {e}", exc_info=True)
            return "ERROR"

    def _print_banner(self, now: datetime, git_version: str):
        db_src = "External" if not os.getenv("USEREAL") else "localhost"
        db_color = ConsoleColors.OKGREEN if db_src == "External" else ConsoleColors.FAIL
        db_warning = (
            f"{ConsoleColors.WARNING}WARNING: Not recommended to use SQLite.{ConsoleColors.ENDC}"
            if db_src == "localhost"
            else ""
        )
        database_message = (
            f"{db_color}Selected Database: {db_src}{ConsoleColors.ENDC}\n{db_warning}"
        )

        print(
            f"""
      _____           _        _ ____        _   
     |  __ \\         | |      | |  _ \\      | |  
     | |__) |__  _ __| |_ __ _| | |_) | ___ | |_ 
     |  ___/ _ \\| '__| __/ _  | |  _ < / _ \\| __|
     | |  | (_) | |  | || (_| | | |_) | (_) | |_ 
     |_|   \\___/|_|   \\__\\__,_|_|____/ \\___/ \\__|

    Bot Account: {self.bot.user.name} | {self.bot.user.id}
    {ConsoleColors.OKCYAN}Discord API Version: {discord.__version__}{ConsoleColors.ENDC}
    {ConsoleColors.WARNING}PortalBot Version: {git_version}{ConsoleColors.ENDC}
    {database_message}

    {ConsoleColors.OKCYAN}Current Time: {now}{ConsoleColors.ENDC}
    {ConsoleColors.OKGREEN}Initialization complete: Cogs, libraries, and views have successfully been loaded.{ConsoleColors.ENDC}
    ==================================================
    {ConsoleColors.WARNING}Statistics{ConsoleColors.ENDC}
    Guilds: {len(self.bot.guilds)}
    Members: {len(self.bot.users)}
    """
        )

    async def _notify_github_log(self):
        # If you store pb_test_server_id in BotData for a known guild, you can read from that row.
        bot_data = get_bot_data_for_server(
            448488274562908170
        )  # or query BotData directly
        if not bot_data or not getattr(bot_data, "pb_test_server_id", None):
            _log.error("pb_test_server_id not found in BotData.")
            return

        pb_guild = self.bot.get_guild(int(bot_data.pb_test_server_id))
        if not pb_guild:
            _log.error(f"Guild with ID {bot_data.pb_test_server_id} not found.")
            return

        github_channel = discord.utils.get(pb_guild.channels, name="github-log")
        if github_channel:
            await github_channel.send("Github Synced, and bot is restarted")
            _log.info("Sync message sent to 'github-log'.")
        else:
            _log.error("'github-log' channel not found in PB guild.")


async def setup(bot: commands.Bot):
    await bot.add_cog(BotManagementBootstrap(bot))
