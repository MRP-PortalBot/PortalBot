# utils/realm_profiles/__rp_logic.py

import os
import io
from io import BytesIO
import discord
from PIL import Image
from utils.database.__database import RealmProfile
from utils.helpers.__logging_module import get_log

import requests

_log = get_log(__name__)


def fetch_realm_autocomplete(interaction: discord.Interaction, current: str):
    """
    Return autocomplete choices for realm names based on current input.
    """
    names = [r.realm_name for r in RealmProfile.select()]
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in names
        if current.lower() in name.lower()
    ]


async def generate_realm_profile_card(
    interaction: discord.Interaction, realm_name: str
):
    """
    Builds and sends the realm profile card with banner/logo and overlaid text.
    """
    await interaction.response.defer()

    profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
    if not profile:
        await interaction.followup.send("Invalid realm name provided.", ephemeral=True)
        return

    try:
        background_path = "./core/images/realm_background4.png"
        fallback_banner = "./core/images/realm_backround_banner.png"
        fallback_logo = Image.new("RGBA", (200, 200), (255, 0, 0, 255))

        base = Image.open(background_path).convert("RGBA")
        banner = (
            Image.open(profile.banner_url).convert("RGBA")
            if os.path.exists(profile.banner_url)
            else Image.open(fallback_banner).convert("RGBA")
        )
        logo = (
            Image.open(profile.logo_url).convert("RGBA").resize((200, 200))
            if os.path.exists(profile.logo_url)
            else fallback_logo
        )

        card = Image.new("RGBA", base.size, (0, 0, 0, 0))
        card.paste(banner, (5, 5), banner)
        card.paste(base, (0, 0), base)
        card.paste(logo, (50, 194), logo)

        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)

        await interaction.followup.send(
            file=discord.File(buffer, "realm_profile_card.png")
        )
        _log.info(f"Realm profile card generated for {realm_name}")
    except Exception as e:
        _log.error(f"Failed to generate card: {e}", exc_info=True)
        await interaction.followup.send(
            "Error generating profile card.", ephemeral=True
        )


async def update_realm_logo_attachment(
    interaction: discord.Interaction, realm_name: str, attachment: discord.Attachment
):
    try:
        if not attachment.content_type or not attachment.content_type.startswith(
            "image"
        ):
            await interaction.response.send_message(
                "Only image files are supported.", ephemeral=True
            )
            return

        os.makedirs("./core/images/realms/logos/", exist_ok=True)
        path = f"./core/images/realms/logos/{realm_name}_logo.png"
        await attachment.save(path)

        profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
        if profile:
            profile.logo_url = path
            profile.save()
            await interaction.response.send_message(
                "✅ Realm logo uploaded successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⚠️ Realm not found.", ephemeral=True
            )
    except Exception as e:
        _log.error(f"Failed to upload logo: {e}", exc_info=True)
        await interaction.response.send_message("Error uploading logo.", ephemeral=True)


async def update_realm_banner_attachment(
    interaction: discord.Interaction, realm_name: str, attachment: discord.Attachment
):
    try:
        if not attachment.content_type or not attachment.content_type.startswith(
            "image"
        ):
            await interaction.response.send_message(
                "Only image files are supported.", ephemeral=True
            )
            return

        os.makedirs("./core/images/realms/banners/", exist_ok=True)
        path = f"./core/images/realms/banners/{realm_name}_banner.png"
        await attachment.save(path)

        profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
        if profile:
            profile.banner_url = path
            profile.save()
            await interaction.response.send_message(
                "✅ Realm banner uploaded successfully.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⚠️ Realm not found.", ephemeral=True
            )
    except Exception as e:
        _log.error(f"Failed to upload banner: {e}", exc_info=True)
        await interaction.response.send_message(
            "Error uploading banner.", ephemeral=True
        )


def ensure_realm_profile_exists(realm_name: str) -> RealmProfile:
    profile, created = RealmProfile.get_or_create(
        realm_name=realm_name,
        defaults={
            "emoji": "🌐",
            "pvp": False,
            "percent_player_sleep": False,
            "world_age": "Unknown",
            "play_style": "Unknown",
            "gamemode": "Survival",
            "logo_url": "./core/images/default_logo.png",
            "banner_url": "./core/images/default_banner.png",
        },
    )
    return profile


def has_realm_operator_role(member: discord.Member, realm_name: str) -> bool:
    expected_role = f"{realm_name} OP"
    return any(role.name == expected_role for role in member.roles)


def save_image_from_url(url: str, save_path: str) -> bool:
    """
    Validates and saves an image from a URL to the given path.
    Returns True if successful, False otherwise.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        # Load the image with PIL to validate it's a real image
        image = Image.open(BytesIO(response.content))
        image.verify()  # Verify that it is an image

        # Save it
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)

        return True

    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Failed to save image from {url}: {e}")
        return False
