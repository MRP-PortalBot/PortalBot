# utils/realm_profiles/__rp_views.py

import discord
from discord.ui import View, Button, Modal, TextInput
from utils.helpers.__logging_module import get_log
from utils.database.__database import RealmProfile
from utils.realm_profiles.__rp_logic import (
    create_realm_channel_link_view,
    generate_realm_profile_card,
    save_image_from_url,
    _parse_world_start_date,
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


def _channel_topic(description: object) -> str:
    text = str(description or "").strip()
    if not text:
        text = "The newest Realm on the Minecraft Realm Portal."
    return text[:1024]


def _user_can_manage_realm(user: discord.Member, realm_name: str) -> bool:
    profile = _get_profile(realm_name)
    user_roles = getattr(user, "roles", [])

    if profile and getattr(profile, "op_role_id", None):
        role_id = str(profile.op_role_id)
        if role_id != "0":
            return any(str(role.id) == role_id for role in user_roles)

    expected_role_name = f"{realm_name} OP"
    return any(role.name == expected_role_name for role in user_roles)


async def _sync_realm_channel_topic(
    interaction: discord.Interaction, profile: RealmProfile
) -> bool:
    channel_id = getattr(profile, "channel_id", None)
    if not channel_id or str(channel_id) == "0" or not interaction.guild:
        return False

    try:
        channel = interaction.guild.get_channel(int(channel_id))
    except (TypeError, ValueError):
        return False

    if channel is None:
        try:
            channel = await interaction.guild.fetch_channel(int(channel_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException, ValueError):
            return False

    if not isinstance(channel, discord.TextChannel):
        return False

    await channel.edit(topic=_channel_topic(profile.short_desc))
    return True


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

        if interaction.user.id != self.user.id or not _user_can_manage_realm(
            interaction.user, self.realm_name
        ):
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

            profile = _get_profile(self.view.realm_name)
            file = discord.File(image_bytes, filename="realm_card.png")
            await interaction.followup.send(
                file=file,
                view=(
                    create_realm_channel_link_view(profile, interaction.guild_id)
                    if profile
                    else None
                ),
                ephemeral=True,
            )

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
                ("short_desc", "Short Desc (also updates channel)", discord.TextStyle.long, True),
                ("long_desc", "Long Description", discord.TextStyle.long, True),
            ],
        },
        "CurrentRealm": {
            "title": "Edit Current Realm Facts",
            "fields": [
                ("gamemode", "Game Mode", discord.TextStyle.short, True),
                ("pvp", "PvP", discord.TextStyle.short, True),
                ("percent_player_sleep", "One Player Sleep", discord.TextStyle.short, True),
                ("world_start_date", "World Start Date (YYYY-MM-DD)", discord.TextStyle.short, True),
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
                placeholder=(
                    "Changing this also updates the realm channel description."
                    if field_name == "short_desc"
                    else None
                ),
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
            elif field_name == "world_start_date":
                world_start_date = _parse_world_start_date(value)
                if world_start_date is None:
                    await interaction.response.send_message(
                        "World Start Date must be a date, preferably `YYYY-MM-DD`.",
                        ephemeral=True,
                    )
                    return
                updates[field_name] = world_start_date
            else:
                updates[field_name] = value

        old_realm_name = profile.realm_name
        for field_name, value in updates.items():
            setattr(profile, field_name, value)
        profile.save()

        channel_synced = False
        if "short_desc" in updates:
            channel_synced = await _sync_realm_channel_topic(interaction, profile)

        if "realm_name" in updates:
            self.realm_name = str(updates["realm_name"])

        message = f"✅ Updated **{old_realm_name}**."
        if old_realm_name != self.realm_name:
            message = f"✅ Updated **{old_realm_name}** and renamed it to **{self.realm_name}**."
        if "short_desc" in updates:
            if channel_synced:
                message += "\n✅ Realm channel description updated."
            else:
                message += "\n⚠️ Profile saved, but I could not update the realm channel description."

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
