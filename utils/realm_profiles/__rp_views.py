# utils/realm_profiles/__rp_views.py

import discord
from discord.ui import View, Button, Modal, TextInput
from utils.helpers.__logging_module import get_log
from utils.database.__database import RealmProfile
from utils.realm_profiles.__rp_logic import (
    generate_realm_profile_card,
    save_image_from_url,
)

_log = get_log(__name__)


def _get_profile(realm_name: str) -> RealmProfile | None:
    return RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)


def _field_default(profile: RealmProfile, field_name: str) -> str | None:
    value = getattr(profile, field_name, None)
    if value is None:
        return None
    return str(value)


def _safe_member_count(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class RealmManagerPanel(View):
    def __init__(self, user: discord.User, realm_name: str):
        super().__init__(timeout=300)
        self.user = user
        self.realm_name = realm_name

        self.add_item(ViewProfileButton(label="📜 View Profile"))
        self.add_item(EditProfileSectionButton("Identity", "🪪 Identity"))
        self.add_item(EditProfileSectionButton("Descriptions", "📝 Descriptions"))
        self.add_item(EditProfileSectionButton("CurrentRealm", "⚙️ Current Realm"))
        self.add_item(EditProfileSectionButton("Addons", "🧩 Addons"))
        self.add_item(EditProfileSectionButton("Community", "👥 Community"))
        self.add_item(EditProfileSectionButton("Apply", "📨 How to Apply"))
        self.add_item(EditProfileSectionButton("Admin", "🛡 Admin/Members"))
        self.add_item(UploadLogoModalButton(label="🖼 Logo URL"))
        self.add_item(UploadBannerModalButton(label="🎏 Banner URL"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        expected_role_name = f"{self.realm_name} OP"
        user_roles = [role.name for role in getattr(interaction.user, "roles", [])]

        if interaction.user.id != self.user.id or expected_role_name not in user_roles:
            await interaction.response.send_message(
                f"🚫 You must have the `{expected_role_name}` role to manage this realm.",
                ephemeral=True,
            )
            return False
        return True


# ---------- Buttons ----------


class ViewProfileButton(Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            _log.debug(
                f"Calling generate_realm_profile_card with user={interaction.user}, realm={self.view.realm_name}"
            )
            image_bytes, error = await generate_realm_profile_card(
                interaction, self.view.realm_name
            )

            if error:
                await interaction.followup.send(error, ephemeral=True)
                return

            file = discord.File(image_bytes, filename="realm_card.png")
            await interaction.followup.send(file=file, ephemeral=True)

        except Exception as e:
            _log.error(f"Error viewing profile: {e}", exc_info=True)
            await interaction.followup.send("Failed to load profile.", ephemeral=True)


class UploadLogoModalButton(Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            UploadImageModal("logo", self.view.realm_name)
        )


class UploadBannerModalButton(Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            UploadImageModal("banner", self.view.realm_name)
        )


class EditProfileSectionButton(Button):
    def __init__(self, section: str, label: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.section = section

    async def callback(self, interaction: discord.Interaction):
        profile = _get_profile(self.view.realm_name)
        if not profile:
            await interaction.response.send_message(
                f"⚠️ Realm profile `{self.view.realm_name}` was not found.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            RealmProfileEditModal(self.section, self.view.realm_name, profile)
        )


# ---------- Modal ----------


class RealmProfileEditModal(Modal):
    SECTIONS = {
        "Identity": {
            "title": "Edit Realm Identity",
            "fields": [
                ("realm_name", "Realm Name", discord.TextStyle.short, True),
                ("emoji", "Emoji", discord.TextStyle.short, True),
            ],
        },
        "Descriptions": {
            "title": "Edit Descriptions",
            "fields": [
                ("short_desc", "Short Description", discord.TextStyle.long, True),
                ("long_desc", "Long Description", discord.TextStyle.long, True),
            ],
        },
        "CurrentRealm": {
            "title": "Edit Current Realm Facts",
            "fields": [
                ("gamemode", "Game Mode", discord.TextStyle.short, True),
                ("pvp", "PvP", discord.TextStyle.short, True),
                ("percent_player_sleep", "One Player Sleep", discord.TextStyle.short, True),
                ("world_age", "World Age", discord.TextStyle.short, True),
                ("play_style", "Play Style", discord.TextStyle.short, True),
            ],
        },
        "Community": {
            "title": "Edit Community Facts",
            "fields": [
                ("member_count", "Member Count", discord.TextStyle.short, True),
                ("community_age", "Community Age", discord.TextStyle.short, True),
                ("reset_schedule", "How Often Do Resets Occur?", discord.TextStyle.short, True),
                ("foreseeable_future", "Foreseeable Future", discord.TextStyle.long, True),
            ],
        },
        "Addons": {
            "title": "Edit Realm Addons",
            "fields": [
                ("realm_addons", "Realm Addons", discord.TextStyle.long, True),
            ],
        },
        "Apply": {
            "title": "Edit How to Apply",
            "fields": [
                ("application_process", "How to Apply", discord.TextStyle.long, True),
                ("portal_invite", "Portal Invite", discord.TextStyle.short, False),
            ],
        },
        "Admin": {
            "title": "Edit Admin/Members",
            "fields": [
                ("admin_team", "Admin Team", discord.TextStyle.long, True),
                ("members", "Members", discord.TextStyle.long, False),
            ],
        },
    }

    def __init__(self, section: str, realm_name: str, profile: RealmProfile):
        section_config = self.SECTIONS[section]
        super().__init__(title=section_config["title"])
        self.section = section
        self.realm_name = realm_name
        self.inputs: dict[str, TextInput] = {}

        for field_name, label, style, required in section_config["fields"]:
            text_input = TextInput(
                label=label,
                style=style,
                required=required,
                default=_field_default(profile, field_name),
                max_length=4000 if style == discord.TextStyle.long else 250,
            )
            self.inputs[field_name] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        profile = _get_profile(self.realm_name)
        if not profile:
            await interaction.response.send_message(
                f"⚠️ Realm profile `{self.realm_name}` was not found.",
                ephemeral=True,
            )
            return

        updates: dict[str, object] = {}
        for field_name, text_input in self.inputs.items():
            value = str(text_input.value).strip()
            if field_name == "member_count":
                member_count = _safe_member_count(value)
                if member_count is None:
                    await interaction.response.send_message(
                        "Member Count must be a whole number.",
                        ephemeral=True,
                    )
                    return
                updates[field_name] = member_count
            else:
                updates[field_name] = value

        old_realm_name = profile.realm_name
        for field_name, value in updates.items():
            setattr(profile, field_name, value)
        profile.save()

        if "realm_name" in updates:
            self.realm_name = str(updates["realm_name"])

        message = f"✅ Updated **{old_realm_name}**."
        if old_realm_name != self.realm_name:
            message = f"✅ Updated **{old_realm_name}** and renamed it to **{self.realm_name}**."

        await interaction.response.send_message(
            message,
            view=RealmManagerPanel(interaction.user, self.realm_name),
            ephemeral=True,
        )


class UploadImageModal(Modal):
    def __init__(self, image_type: str, realm_name: str):
        title = f"Upload {image_type.capitalize()} URL"
        super().__init__(title=title)
        self.image_type = image_type
        self.realm_name = realm_name

        self.url = TextInput(
            label=f"{image_type.capitalize()} Image URL",
            placeholder="Paste a valid image URL...",
            required=True,
        )
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        image_url = self.url.value.strip()
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            # Validate and save the image
            save_path = f"./data/images/realms/{self.image_type}s/{self.realm_name}_{self.image_type}.png"
            if not save_image_from_url(image_url, save_path):
                await interaction.followup.send(
                    "❌ Failed to upload the image. Make sure the URL points to a valid image.",
                    ephemeral=True,
                )
                return

            profile = RealmProfile.get_or_none(RealmProfile.realm_name == self.realm_name)
            if not profile:
                await interaction.followup.send(
                    f"⚠️ Realm profile `{self.realm_name}` was not found.",
                    ephemeral=True,
                )
                return

            if self.image_type == "logo":
                profile.logo_url = save_path
            else:
                profile.banner_url = save_path
            profile.save()

            await interaction.followup.send(
                f"✅ {self.image_type.capitalize()} image updated for **{self.realm_name}**.",
                ephemeral=True,
            )
        except Exception as e:
            _log.error(f"Image upload failed for {self.realm_name}: {e}")
            await interaction.followup.send(
                "❌ Failed to upload the image. Make sure the URL points to a valid image.",
                ephemeral=True,
            )


def setup(bot):
    pass  # no persistent views needed right now
