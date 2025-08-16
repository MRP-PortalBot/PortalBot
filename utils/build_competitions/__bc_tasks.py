# utils/build_competitions/__bc_tasks.py
from discord.ext import commands, tasks
from utils.helpers.__logging_module import get_log
from .__bc_logic import process_scheduled_events

_log = get_log("build_comp.tasks")

class _BCScheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._tick.start()

    def cog_unload(self):
        self._tick.cancel()

    @tasks.loop(seconds=60)
    async def _tick(self):
        try:
            await process_scheduled_events(self.bot)
        except Exception as e:
            _log.exception(f"Scheduler error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(_BCScheduler(bot))
    _log.info("⏱️ Build competition scheduler started.")
