import discord
from discord.ext import commands

# Subcommand groups (each has a setup(bot) or is a Group subclass)
from . import __bm_commands


class BotManagement(commands.GroupCog, name="bot"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    cog = BotManagement(bot)
    await bot.add_cog(cog)
    await __bm_commands.setup(bot)

    # Optional: log success
    from utils.helpers.__logging_module import get_log

    get_log(__name__).info("✅ BotManagement initialized.")
