import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashCommand
from discord_slash import SlashContext


class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)


    @cog_ext.cog_slash(name="Say_Command", description = "Iterates something as the bot!", guild_ids=[448488274562908170])
    @commands.has_permissions(manage_channels=True)
    async def say(self, ctx, *, reason):
        await ctx.channel.purge(limit=1)
        await ctx.send(reason)

    



def setup(bot):
    bot.add_cog(Slash(bot))