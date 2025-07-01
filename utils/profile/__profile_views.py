# utils/profile/__profile_views.py

import discord
from discord.ui import View, Button, Modal, TextInput
from utils.helpers.__logging_module import get_log
from utils.database import __database as database
from utils.core_features.__common import get_profile_record

_log = get_log(__name__)


# ---------- Game Usernames Modal ----------
class GameUsernamesModal(Modal, title="Game Usernames"):
    def __init__(self):
        super().__init__(timeout=None)
        self.xbox = TextInput(label="Xbox Username", required=False, max_length=100)
        self.playstation = TextInput(
            label="PlayStation Username", required=False, max_length=100
        )
        self.switch = TextInput(label="Switch Username", required=False, max_length=100)
        self.nnid = TextInput(
            label="Nintendo Network ID", required=False, max_length=100
        )

        self.add_item(self.xbox)
        self.add_item(self.playstation)
        self.add_item(self.switch)
        self.add_item(self.nnid)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            profile = database.PortalbotProfile.get_or_none(
                database.PortalbotProfile.DiscordLongID == str(interaction.user.id)
            )
            if not profile:
                await interaction.response.send_message(
                    "❌ Profile not found.", ephemeral=True
                )
                return

            profile.XBOX = self.xbox.value.strip() or "None"
            profile.Playstation = self.playstation.value.strip() or "None"
            profile.Switch = self.switch.value.strip() or "None"
            profile.SwitchNNID = self.nnid.value.strip() or "None"
            profile.save()

            _log.info(f"Updated game usernames for {interaction.user.name}")
            await interaction.response.send_message(
                "✅ Game usernames updated successfully!", ephemeral=True
            )

        except Exception as e:
            _log.error(f"Error updating game usernames: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to update game usernames.", ephemeral=True
            )


# ---------- Realm Info Modal ----------
class RealmInfoModal(Modal, title="Realm Information"):
    def __init__(self):
        super().__init__(timeout=None)
        self.joined = TextInput(
            label="Realms You Are In",
            required=False,
            placeholder="Comma-separated list",
            max_length=250,
        )
        self.admin = TextInput(
            label="Realms You Admin",
            required=False,
            placeholder="Comma-separated list",
            max_length=250,
        )

        self.add_item(self.joined)
        self.add_item(self.admin)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            profile = database.PortalbotProfile.get_or_none(
                database.PortalbotProfile.DiscordLongID == str(interaction.user.id)
            )
            if not profile:
                await interaction.response.send_message(
                    "❌ Profile not found.", ephemeral=True
                )
                return

            profile.RealmsJoined = self.clean_field(self.joined.value)
            profile.RealmsAdmin = self.clean_field(self.admin.value)
            profile.save()

            _log.info(f"Updated realm info for {interaction.user.name}")
            await interaction.response.send_message(
                "✅ Realm information updated successfully!", ephemeral=True
            )

        except Exception as e:
            _log.error(f"Error updating realm info: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to update realm information.", ephemeral=True
            )

    def clean_field(self, raw_input: str) -> str:
        """Clean and normalize comma-separated field input."""
        if not raw_input.strip():
            return "None"
        items = [item.strip() for item in raw_input.split(",") if item.strip()]
        return ", ".join(items) if items else "None"


# ---------- Profile Edit Launcher View ----------
class ProfileEditLauncherView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.add_item(GameUsernamesButton())
        self.add_item(RealmInfoButton())


class GameUsernamesButton(Button):
    def __init__(self):
        super().__init__(label="Game Usernames", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GameUsernamesModal())


class RealmInfoButton(Button):
    def __init__(self):
        super().__init__(label="Realm Info", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RealmInfoModal())


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
