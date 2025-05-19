# utils/profile/__profile_views.py

import discord
from discord import ui
from utils.helpers.__logging_module import get_log
from utils.database import database
from utils.core_features.common import get_profile_record

_log = get_log(__name__)


class ProfileEditModal(discord.ui.Modal, title="Edit Your Profile"):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    xbox = ui.TextInput(
        label="Xbox Username (Optional)", required=False, max_length=100
    )
    playstation = ui.TextInput(
        label="PlayStation Username (Optional)", required=False, max_length=100
    )
    switch = ui.TextInput(
        label="Nintendo Switch Username (Optional)", required=False, max_length=100
    )
    nnid = ui.TextInput(
        label="Nintendo Network ID (Optional)", required=False, max_length=100
    )
    realms_joined = ui.TextInput(
        label="Realms You Are In (Optional)",
        required=False,
        placeholder="Comma-separated list",
        max_length=250,
    )
    realms_admin = ui.TextInput(
        label="Realms You Admin (Optional)",
        required=False,
        placeholder="Comma-separated list",
        max_length=250,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            profile = database.PortalbotProfile.get_or_none(
                database.PortalbotProfile.DiscordLongID == str(self.user_id)
            )

            if not profile:
                await interaction.response.send_message(
                    "❌ Your profile could not be found.", ephemeral=True
                )
                return

            profile.XBOX = self.xbox.value or "None"
            profile.Playstation = self.playstation.value or "None"
            profile.Switch = self.switch.value or "None"
            profile.SwitchNNID = self.nnid.value or "None"
            profile.RealmsJoined = self.realms_joined.value or "None"
            profile.RealmsAdmin = self.realms_admin.value or "None"
            profile.save()

            await interaction.response.send_message(
                "✅ Your profile has been updated!", ephemeral=True
            )
            _log.info(f"Profile updated for user {interaction.user.display_name}")
        except Exception as e:
            _log.error(f"Error updating profile: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while updating your profile.", ephemeral=True
            )


class RealmSelection(discord.ui.Select):
    def __init__(self, bot, user_id: int, field: str, label: str, placeholder: str):
        self.bot = bot
        self.user_id = user_id
        self.field = field  # Either 'RealmsJoined' or 'RealmsAdmin'

        # Fetch active realms
        active_realms = (
            database.RealmProfile.select()
            .where(database.RealmProfile.archived == False)
            .order_by(database.RealmProfile.realm_name)
        )
        active_names = [realm.realm_name for realm in active_realms]

        # Fetch user profile
        profile = get_profile_record(self.bot, str(user_id))
        existing = []
        if profile:
            current_value = getattr(profile, self.field, "None")
            if current_value and current_value != "None":
                existing = [r.strip() for r in current_value.split(",")]

        # Build options
        options = [
            discord.SelectOption(
                label=name,
                value=name,
                default=name in existing,
            )
            for name in active_names
        ]

        super().__init__(
            placeholder=placeholder,
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id=f"profile_set_realms_{field.lower()}",
            row=0 if field == "RealmsJoined" else 1,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            profile = get_profile_record(self.bot, str(self.user_id))
            if not profile:
                await interaction.response.send_message(
                    "Profile not found.", ephemeral=True
                )
                return

            setattr(
                profile, self.field, ", ".join(self.values) if self.values else "None"
            )
            profile.save()

            _log.info(
                f"{self.field} updated for {interaction.user.display_name}: {getattr(profile, self.field)}"
            )
            await interaction.response.send_message(
                f"✅ Your {self.field} realms have been updated!", ephemeral=True
            )
        except Exception as e:
            _log.error("Error in realm selection callback", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while updating realms.", ephemeral=True
            )


class RealmSelectionView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=None)
        self.add_item(
            RealmSelection(
                bot,
                user_id,
                field="RealmsAdmin",
                label="OP Realms",
                placeholder="Select realms you are an OP in...",
            )
        )
        self.add_item(
            RealmSelection(
                bot,
                user_id,
                field="RealmsJoined",
                label="Member Realms",
                placeholder="Select realms you are a member of...",
            )
        )



class RealmDropdown(discord.ui.Select):
    def __init__(
        self, label: str, realm_type: str, options: list[discord.SelectOption]
    ):
        super().__init__(
            placeholder=f"Select your {label}",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id=f"realm_select_{realm_type}",
        )
        self.realm_type = realm_type

    async def callback(self, interaction: discord.Interaction):
        profile = database.PortalbotProfile.get(
            database.PortalbotProfile.DiscordLongID == str(interaction.user.id)
        )

        selected_realms = ", ".join(self.values) if self.values else "None"
        if self.realm_type == "joined":
            profile.RealmsJoined = selected_realms
        elif self.realm_type == "admin":
            profile.RealmsAdmin = selected_realms

        profile.save()
        await interaction.response.send_message(
            f"✅ Updated your {self.placeholder.lower()} to: {selected_realms}",
            ephemeral=True,
        )
