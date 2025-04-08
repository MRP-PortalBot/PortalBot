# profile/profile_main.py

import discord
from discord.ext import commands
from discord import app_commands
import logging

_log = logging.getLogger(__name__)


class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.profile_group = app_commands.Group(
            name="profile", description="Commands for User Profiles"
        )


async def setup(bot):
    from .profile_visual import add_visual_commands
    from .profile_embed import add_embed_commands
    from .profile_edit import add_edit_commands

    # Inject subcommands into the command group
    add_visual_commands(bot.profile_group)
    add_embed_commands(bot.profile_group)
    add_edit_commands(bot.profile_group)

    # Register the group with the tree
    bot.tree.add_command(bot.profile_group)

    # Add the cog
    await bot.add_cog(ProfileCMD(bot))
