import discord
from discord import app_commands
from discord.ext import commands

from core.checks import slash_owns_realm_channel
from core.database import RealmProfile

class RealmProfiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    RP = app_commands.Group(
        name="realm-profile",
        description="View/Configure your Realm Profile.",
    )

    @RP.command(description="View a Realm Profile")
    async def view(self, interaction: discord.Interaction, realm_name: str = None):
        """View your Realm Profile."""
        # Check if realm_name is provided, else default to the channel name
        realm_name = realm_name if realm_name else interaction.channel.name
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)

        if realm_profile:
            embed = discord.Embed(
                title=f"{realm_profile.realm_emoji} {realm_profile.realm_name} - Realm Profile",
                color=discord.Color.blue()
            )
            embed.add_field(name="Realm Name", value=realm_profile.realm_name, inline=False)
            embed.add_field(name="Realm Description", value=realm_profile.realm_long_desc, inline=False)
            embed.add_field(name="PvP", value="Enabled" if realm_profile.pvp else "Disabled", inline=True)
            embed.add_field(name="One Player Sleep", value="Enabled" if realm_profile.one_player_sleep else "Disabled", inline=True)
            embed.add_field(name="World Age", value=realm_profile.world_age, inline=True)
            embed.add_field(name="Realm Style", value=realm_profile.realm_style, inline=True)
            embed.add_field(name="Game Mode", value=realm_profile.gamemode, inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Realm profile not found for {realm_name}.")

    @RP.command(description="Configure a Realm Profile")
    @slash_owns_realm_channel
    async def setup(
        self, 
        interaction: discord.Interaction,
        realm_name: str,  # Realm name is now optional
        realm_emoji: str,
        pvp: bool,
        one_player_sleep: bool,
        world_age: str,
        realm_style: str,
        gamemode: str
    ):
        """Configure your Realm Profile."""
        
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

async def setup(bot):
    await bot.add_cog(RealmProfiles(bot))
