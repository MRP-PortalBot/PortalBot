import discord
from discord import app_commands
from discord.ext import commands

from core import database
from core.checks import slash_owns_realm_channel

ConfigurableFields = {Platform: Bedrock Realm
Active Members: 35
Start date: June 1, 2017
Current season: 12
Current season start: June 16, 2023
Next reset: After 1.21 releases
Keep inventory: Off
Fire tick: Off
Achievements: Off
Explosions: Off, except TNT}

class RealmProfiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    RP = app_commands.Group(
        name="realm-profile",
        description="View/Configure your Realm Profile.",
    )

    @app_commands.command(description="View a Realm Profile")
    @slash_owns_realm_channel
    async def view(self, interaction: discord.Interaction):
        """View your Realm Profile."""
        await interaction.response.send_message("Viewing your Realm Profile.")

    @app_commands.command(description="Configure a Realm Profile")
    @slash_owns_realm_channel
    async def setup(
            self, interaction: discord.Interaction,
            realm_name: str,
            realm_emoji: str,
            pvp: bool,
            one_player_sleep: bool,
            world_age: str
    ):
        """Configure your Realm Profile."""


    

async def setup(bot):
    await bot.add_cog(RealmProfiles(bot))
