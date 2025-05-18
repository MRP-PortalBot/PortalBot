import discord
from discord.ext import commands
from . import __bm_commands  # This triggers the setup() from __bm_commands.py


class BotManagement(commands.GroupCog, name="bot"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    cog = BotManagement(bot)
    await bot.add_cog(cog)

    # Register slash command groups defined in __bm_commands.py
    await __bm_commands.setup(bot)
