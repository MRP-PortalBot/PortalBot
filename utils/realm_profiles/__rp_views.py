# utils/realm_profiles/__rp_views.py

import discord
from discord.ui import View, Button, Modal, TextInput
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_logic import (
    generate_realm_profile_card,
    save_image_from_url,
    ensure_realm_profile_exists,
)

_log = get_log(__name__)


class RealmManagerPanel(View):
    def __init__(self, user: discord.User, realm_name: str):
        super().__init__(timeout=300)
        self.user = user
        self.realm_name = realm_name

        self.add_item(ViewProfileButton(label="📜 View Profile"))
        self.add_item(UploadLogoModalButton(label="🖼 Upload Logo URL"))
        self.add_item(UploadBannerModalButton(label="🎏 Upload Banner URL"))
        self.add_item(UploadConfirmButton(label="✅ Confirm Changes"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        expected_role_name = f"{self.realm_name} OP"
        user_roles = [role.name for role in interaction.user.roles]

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
            await interaction.response.defer()
            image_bytes = generate_realm_profile_card(interaction.user, self.view.realm_name)
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


class UploadConfirmButton(Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.success, label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Your updates to **{self.view.realm_name}** have been saved.",
            ephemeral=True,
        )


# ---------- Modal ----------


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

        try:
            # Validate and save the image
            save_image_from_url(self.image_type, self.realm_name, image_url)

            await interaction.response.send_message(
                f"✅ {self.image_type.capitalize()} image updated for **{self.realm_name}**.",
                ephemeral=True,
            )
        except Exception as e:
            _log.error(f"Image upload failed for {self.realm_name}: {e}")
            await interaction.response.send_message(
                "❌ Failed to upload the image. Make sure the URL points to a valid image.",
                ephemeral=True,
            )


def setup(bot):
    pass  # no persistent views needed right now
