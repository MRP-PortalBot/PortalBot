#Example of SlashCog Usage
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashCommand
from discord_slash import SlashContext
from discord_slash.utils import manage_commands
import time
import logging
logger = logging.getLogger(__name__)

class Slash(commands.Cog):
    def __init__(self, bot):
        logger.info("SlashCMD: Cog Loaded!")
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

'''
    @cog_ext.cog_slash(name="say", description = "Iterates something as the bot!", guild_ids=[448488274562908170], options=[manage_commands.create_option(name = "phrase" , description = "Phrase to reiterate", option_type = 3, required = True)])
    async def say(self, ctx, phrase=None):
        await ctx.send(3, content = phrase)
'''
    



def setup(bot):
    bot.add_cog(Slash(bot))