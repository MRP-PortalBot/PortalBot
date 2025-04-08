import discord
from discord.ext import commands
from discord import app_commands
import logging

_log = logging.getLogger(__name__)


class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    from .profile_visual import add_visual_commands
    from .profile_embed import add_embed_commands
    from .profile_edit import add_edit_commands

    # Create the top-level slash command group
    profile_group = app_commands.Group(
        name="profile", description="Commands for User Profiles"
    )

    # Inject subcommands into the group
    add_visual_commands(profile_group)
    add_embed_commands(profile_group)
    add_edit_commands(profile_group)

    # Register the group with the app command tree
    bot.tree.add_command(profile_group)

    # Add the cog
    await bot.add_cog(ProfileCMD(bot))
