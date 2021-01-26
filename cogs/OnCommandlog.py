from discord.ext import commands
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class CommandLogger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        logger.info("OnCommandlog: Cog Loaded!")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        author = ctx.message.author
        authorname = author.name
        timestamp = datetime.now()
        with open("commandlog.txt", "a") as file:
            file.write(str(authorname) + " used " + str(ctx.command) + " | Executed on: (Date | Time) " + str(timestamp.strftime("%m/%d/%y")) + " : " + str(timestamp.strftime("%H:%M:%S")) + "\n")


def setup(bot):
    bot.add_cog(CommandLogger(bot))
