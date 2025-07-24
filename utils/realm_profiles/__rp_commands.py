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
        """View the details of a Realm Profile, as a card if possible, or fallback to embed."""
        realm_name = realm_name or interaction.channel.name
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)

        if not realm_profile:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )
            return

        try:
            # Defer the response while generating the image
            await interaction.response.defer()

            # Generate the image buffer from your existing generator function
            from utils.realm_profiles.__rp_logic import generate_realm_profile_card

            image_bytes = generate_realm_profile_card(interaction,realm_name)
            file = discord.File(image_bytes, filename="realm_profile_card.png")

            await interaction.followup.send(file=file, ephemeral=True)

        except Exception as e:
            _log.error(
                f"Error generating realm card for {realm_name}: {e}", exc_info=True
            )
            from utils.realm_profiles.__rp_logic import create_realm_embed

            embed = create_realm_embed(realm_profile)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="edit", description="Edit a Realm Profile")
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
