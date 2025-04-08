# profile/profile_edit.py

import discord
import logging
from discord import app_commands
from core import database
from core.common import ensure_profile_exists

_log = logging.getLogger(__name__)


def add_edit_commands(group: app_commands.Group):
    @group.command(name="edit_profile", description="Edit your user profile.")
    async def edit_profile(interaction: discord.Interaction):
        user = interaction.user

        profile = ensure_profile_exists(user)
        if profile is None:
            await interaction.response.send_message(
                "An error occurred while preparing your profile.", ephemeral=True
            )
            return

        try:
            await interaction.response.send_modal(
                ProfileEditModal(interaction.client, user.id)
            )

        except Exception as e:
            _log.error(
                f"Unexpected error while opening profile modal for {user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "An error occurred while trying to edit your profile.", ephemeral=True
            )


class ProfileEditModal(discord.ui.Modal):
    def __init__(self, bot, user_id):
        super().__init__(title="Edit Your Profile")
        self.bot = bot
        self.user_id = user_id

        self.timezone_field = discord.ui.TextInput(
            label="Timezone",
            placeholder="e.g. UTC, CST, PST (or 'reset')",
            required=False,
        )
        self.xbox_field = discord.ui.TextInput(
            label="Xbox Gamertag",
            placeholder="Enter your Xbox Gamertag (or 'reset')",
            required=False,
        )
        self.psn_field = discord.ui.TextInput(
            label="PlayStation ID",
            placeholder="Enter your PlayStation ID (or 'reset')",
            required=False,
        )
        self.switch_field = discord.ui.TextInput(
            label="Switch Username",
            placeholder="Enter your Switch Username (or 'reset')",
            required=False,
        )
        self.nnid_field = discord.ui.TextInput(
            label="Nintendo Network ID",
            placeholder="SW-####-####-#### (or 'reset')",
            required=False,
        )

        self.add_item(self.timezone_field)
        self.add_item(self.xbox_field)
        self.add_item(self.psn_field)
        self.add_item(self.switch_field)
        self.add_item(self.nnid_field)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            profile = database.PortalbotProfile.get(
                database.PortalbotProfile.DiscordLongID == str(self.user_id)
            )

            def handle_input(field_value):
                return "None" if field_value.lower() == "reset" else field_value

            if self.timezone_field.value:
                profile.Timezone = handle_input(self.timezone_field.value)
            if self.xbox_field.value:
                profile.XBOX = handle_input(self.xbox_field.value)
            if self.psn_field.value:
                profile.Playstation = handle_input(self.psn_field.value)
            if self.switch_field.value:
                profile.Switch = handle_input(self.switch_field.value)
            if self.nnid_field.value:
                profile.SwitchNNID = handle_input(self.nnid_field.value)

            profile.save()

            await interaction.response.send_message(
                "Your profile has been updated successfully!", ephemeral=True
            )
            _log.info(f"User {self.user_id} updated their profile.")

        except database.PortalbotProfile.DoesNotExist:
            _log.error(f"Profile not found while submitting modal for {self.user_id}.")
            await interaction.response.send_message(
                "An error occurred: Profile not found.", ephemeral=True
            )

        except Exception as e:
            _log.error(f"Error updating profile for {self.user_id}: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while updating your profile.", ephemeral=True
            )
