from discord import app_commands
from discord.ext import commands
from discord import Interaction
from discord.app_commands.errors import CheckFailure

class RealmProfiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    RP = app_commands.Group(
        name="realm-profile",
        description="View/Configure your Realm Profile.",
    )

    @RP.command(description="Configure a Realm Profile")
    @slash_owns_realm_channel
    async def setup(
        self, interaction: Interaction,
        realm_name: str = None,
        realm_emoji: str,
        pvp: bool,
        one_player_sleep: bool,
        world_age: str,
        realm_style: str,
        gamemode: str
    ):
        """Configure your Realm Profile."""
        try:
            # Use the provided realm_name or default to the channel name
            realm_name = realm_name if realm_name else interaction.channel.name
            
            realm_profile, created = RealmProfile.get_or_create(
                realm_name=realm_name,
                defaults={
                    'realm_emoji': realm_emoji,
                    'pvp': pvp,
                    'one_player_sleep': one_player_sleep,
                    'world_age': world_age,
                    'realm_style': realm_style,
                    'gamemode': gamemode
                }
            )

            if not created:
                # Update the existing profile
                realm_profile.realm_emoji = realm_emoji
                realm_profile.pvp = pvp
                realm_profile.one_player_sleep = one_player_sleep
                realm_profile.world_age = world_age
                realm_profile.realm_style = realm_style
                realm_profile.gamemode = gamemode
                realm_profile.save()

            embed = discord.Embed(
                title="Realm Profile Configured",
                description=f"{realm_emoji} {realm_name} has been successfully configured.",
                color=discord.Color.green()
            )
            embed.add_field(name="PvP", value="Enabled" if pvp else "Disabled", inline=True)
            embed.add_field(name="One Player Sleep", value="Enabled" if one_player_sleep else "Disabled", inline=True)
            embed.add_field(name="World Age", value=world_age, inline=True)
            embed.add_field(name="Realm Style", value=realm_style, inline=True)
            embed.add_field(name="Game Mode", value=gamemode, inline=True)
            
            await interaction.response.send_message(embed=embed)
        
        except CheckFailure:
            if not interaction.response.is_done():
                await interaction.response.send_message("You do not own this realm channel or lack permissions.", ephemeral=True)

    # Error handling to avoid responding multiple times
    async def on_app_command_error(self, interaction: Interaction, error):
        if isinstance(error, CheckFailure):
            if not interaction.response.is_done():
                await interaction.response.send_message("Check failed: You don't have permission to run this command.", ephemeral=True)
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RealmProfiles(bot))
