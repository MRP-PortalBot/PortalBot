# utils/realm_profiles/__rp_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from utils.database.__database import RealmProfile
from utils.realm_profiles.__rp_logic import (
    realm_name_autocomplete,
    has_realm_operator_role,
)
from utils.realm_profiles.__rp_views import RealmManagerPanel
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class RealmProfileCommands(app_commands.Group, name="realm-profile"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="view", description="View a Realm Profile")
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def view(self, interaction: discord.Interaction, realm_name: str = None):
        realm_name = realm_name or interaction.channel.name
        profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)

        if profile:
            embed = discord.Embed(
                title=f"{profile.emoji} {profile.realm_name} - Realm Profile",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Realm Name", value=profile.realm_name, inline=False)
            embed.add_field(name="Description", value=profile.long_desc, inline=False)
            embed.add_field(
                name="PvP", value="Enabled" if profile.pvp else "Disabled", inline=True
            )
            embed.add_field(
                name="One Player Sleep",
                value="Enabled" if profile.percent_player_sleep else "Disabled",
                inline=True,
            )
            embed.add_field(name="World Age", value=profile.world_age, inline=True)
            embed.add_field(name="Realm Style", value=profile.play_style, inline=True)
            embed.add_field(name="Game Mode", value=profile.gamemode, inline=True)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )

    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def open_realm_panel(self, interaction: discord.Interaction, realm_name: str):
        if not has_realm_operator_role(interaction.user, realm_name):
            await interaction.response.send_message(
                f"🚫 You must have the `{realm_name} OP` role to manage this realm.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🔧 Opening management panel for `{realm_name}`.",
            view=RealmManagerPanel(interaction.user, realm_name),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    group = RealmProfileCommands(bot)
    bot.tree.add_command(group)
    _log.info("🧭 RealmProfileCommands slash group registered")
