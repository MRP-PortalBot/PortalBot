# utils/realm_profiles/__rp_logic.py

import os
import io
from io import BytesIO
import discord
from PIL import Image, ImageDraw, ImageFont
from utils.database.__database import RealmProfile
from utils.helpers.__logging_module import get_log

import requests

_log = get_log(__name__)

FONT_PATH = "./data/fonts/Minecraft-Seven_v2-1.ttf"
TEXT_COLOR = (255, 255, 255, 255)
TEXT_SHADOW_COLOR = (0, 0, 0, 180)
REALM_NAME_BOX = (276, 236, 732, 408)
PANEL_FILL = (12, 5, 18, 175)
PANEL_OUTLINE = (255, 120, 255, 80)
LABEL_COLOR = (210, 190, 225, 255)
PINK_SECTION_TOP = 409
BOTTOM_BORDER_TOP = 888
PINK_SECTION_EXTRA_HEIGHT = 220
PANEL_MARGIN = 28
PANEL_GAP = 18
PANEL_PADDING = 18


async def realm_name_autocomplete(interaction: discord.Interaction, current: str):
    """
    Return autocomplete choices for realm names based on current input.
    """
    names = [r.realm_name for r in RealmProfile.select()]
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in names
        if current.lower() in name.lower()
    ]


def create_realm_embed(realm_profile: RealmProfile) -> discord.Embed:
    """Builds a fallback embed for a Realm Profile."""
    embed = discord.Embed(
        title=f"{realm_profile.emoji} {realm_profile.realm_name} - Realm Profile",
        color=discord.Color.blue(),
    )

    embed.add_field(name="Realm Name", value=realm_profile.realm_name, inline=False)
    embed.add_field(name="Description", value=realm_profile.long_desc, inline=False)
    embed.add_field(
        name="PvP", value="Enabled" if realm_profile.pvp else "Disabled", inline=True
    )
    embed.add_field(
        name="One Player Sleep",
        value="Enabled" if realm_profile.percent_player_sleep else "Disabled",
        inline=True,
    )
    embed.add_field(name="World Age", value=realm_profile.world_age, inline=True)
    embed.add_field(name="Realm Style", value=realm_profile.play_style, inline=True)
    embed.add_field(name="Game Mode", value=realm_profile.gamemode, inline=True)

    return embed


def _load_realm_name_font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _realm_name_lines(realm_name: str) -> list[str]:
    words = realm_name.split()
    if not words:
        return [realm_name]
    if len(words) <= 2:
        return [" ".join(words)]
    return [" ".join(words[:2]), " ".join(words[2:])]


def _draw_realm_name(card: Image.Image, realm_name: str) -> None:
    draw = ImageDraw.Draw(card)
    box_x, box_y, box_x2, box_y2 = REALM_NAME_BOX
    box_width = box_x2 - box_x
    box_height = box_y2 - box_y
    lines = _realm_name_lines(realm_name)

    font_size = 60
    font = _load_realm_name_font(font_size)
    while font_size > 10:
        line_sizes = [_text_size(draw, line, font) for line in lines]
        total_height = sum(height for _, height in line_sizes) + 5 * (len(lines) - 1)
        widest_line = max(width for width, _ in line_sizes)
        if widest_line <= box_width - 50 and total_height <= box_height - 20:
            break
        font_size -= 2
        font = _load_realm_name_font(font_size)

    line_sizes = [_text_size(draw, line, font) for line in lines]
    total_height = sum(height for _, height in line_sizes) + 5 * (len(lines) - 1)
    text_y = box_y + (box_height - total_height) // 2

    for line, (text_width, text_height) in zip(lines, line_sizes):
        text_x = box_x + (box_width - text_width) // 2
        draw.text((text_x + 2, text_y + 2), line, font=font, fill=TEXT_SHADOW_COLOR)
        draw.text((text_x, text_y), line, font=font, fill=TEXT_COLOR)
        text_y += text_height + 5


def _clean_value(value, default: str = "Not set") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() == "none":
        return default
    return text


def _format_bool_value(value) -> str:
    text = _clean_value(value, "No").lower()
    if text in {"true", "yes", "enabled", "on", "1"}:
        return "Enabled"
    if text in {"false", "no", "disabled", "off", "0"}:
        return "Disabled"
    return _clean_value(value)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if _text_size(draw, test_line, font)[0] <= max_width:
                line = test_line
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font, fill=TEXT_COLOR
) -> None:
    draw.text((x + 2, y + 2), text, font=font, fill=TEXT_SHADOW_COLOR)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    x: int,
    y: int,
    max_width: int,
    max_height: int,
    line_gap: int = 5,
) -> None:
    line_height = _text_size(draw, "Ag", font)[1] + line_gap
    max_lines = max(1, max_height // line_height)
    lines = _wrap_text(draw, text, font, max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = f"{lines[-1].rstrip('. ')}..."

    for line in lines:
        _draw_text_with_shadow(draw, x, y, line, font)
        y += line_height


def _draw_panel(
    overlay_draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]
) -> None:
    overlay_draw.rounded_rectangle(box, radius=8, fill=PANEL_FILL, outline=PANEL_OUTLINE)


def _expand_pink_section(base: Image.Image) -> Image.Image:
    if PINK_SECTION_EXTRA_HEIGHT <= 0:
        return base

    width, height = base.size
    top = base.crop((0, 0, width, PINK_SECTION_TOP))
    pink_section = base.crop((0, PINK_SECTION_TOP, width, BOTTOM_BORDER_TOP))
    bottom = base.crop((0, BOTTOM_BORDER_TOP, width, height))
    expanded_pink = pink_section.resize(
        (width, pink_section.height + PINK_SECTION_EXTRA_HEIGHT),
        Image.NEAREST,
    )

    expanded = Image.new(
        "RGBA", (width, height + PINK_SECTION_EXTRA_HEIGHT), (0, 0, 0, 0)
    )
    expanded.paste(top, (0, 0), top)
    expanded.paste(expanded_pink, (0, PINK_SECTION_TOP), expanded_pink)
    expanded.paste(bottom, (0, BOTTOM_BORDER_TOP + PINK_SECTION_EXTRA_HEIGHT), bottom)
    return expanded


def _draw_detail_row(
    draw: ImageDraw.ImageDraw,
    label: str,
    value: str,
    x: int,
    y: int,
    label_font,
    value_font,
) -> None:
    _draw_text_with_shadow(draw, x, y, label.upper(), label_font, fill=LABEL_COLOR)
    _draw_text_with_shadow(draw, x, y + 19, value, value_font)


def _draw_fact_row(
    draw: ImageDraw.ImageDraw,
    label: str,
    value: str,
    x: int,
    y: int,
    max_width: int,
    label_font,
    value_font,
) -> int:
    _draw_text_with_shadow(draw, x, y, label.upper(), label_font, fill=LABEL_COLOR)
    value_lines = _wrap_text(draw, value, value_font, max_width)
    value_lines = value_lines[:2] if value_lines else ["Not set"]
    if len(_wrap_text(draw, value, value_font, max_width)) > 2:
        value_lines[-1] = f"{value_lines[-1].rstrip('. ')}..."

    value_y = y + 18
    for line_index, line in enumerate(value_lines):
        _draw_text_with_shadow(draw, x, value_y + (line_index * 21), line, value_font)
    return value_y + (len(value_lines) * 21) + 6


def _draw_realm_details(card: Image.Image, profile: RealmProfile) -> None:
    overlay = Image.new("RGBA", card.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    top_y = REALM_NAME_BOX[3] + PANEL_GAP
    footer_bottom = card.height - PANEL_MARGIN
    upper_height = 350
    footer_top = top_y + upper_height + PANEL_GAP
    left_box_right = 448
    right_box_left = left_box_right + PANEL_GAP
    description_box = (PANEL_MARGIN, top_y, left_box_right, top_y + upper_height)
    facts_box = (right_box_left, top_y, card.width - PANEL_MARGIN, top_y + upper_height)
    footer_box = (PANEL_MARGIN, footer_top, card.width - PANEL_MARGIN, footer_bottom)

    for box in (description_box, facts_box, footer_box):
        _draw_panel(overlay_draw, box)
    card.alpha_composite(overlay)

    draw = ImageDraw.Draw(card)
    title_font = _load_realm_name_font(24)
    body_font = _load_realm_name_font(19)
    label_font = _load_realm_name_font(14)
    value_font = _load_realm_name_font(18)

    description_x = description_box[0] + PANEL_PADDING
    description_y = description_box[1] + PANEL_PADDING
    description_width = description_box[2] - description_box[0] - (PANEL_PADDING * 2)
    description_text_y = description_y + 38
    description_height = description_box[3] - description_text_y - PANEL_PADDING
    _draw_text_with_shadow(draw, description_x, description_y, "Description", title_font)
    description = _clean_value(profile.long_desc, _clean_value(profile.short_desc))
    _draw_wrapped_text(
        draw,
        description,
        body_font,
        description_x,
        description_text_y,
        description_width,
        description_height,
        line_gap=8,
    )

    facts_x = facts_box[0] + PANEL_PADDING
    facts_y = facts_box[1] + PANEL_PADDING
    facts_width = facts_box[2] - facts_box[0] - (PANEL_PADDING * 2)
    _draw_text_with_shadow(draw, facts_x, facts_y, "Quick Facts", title_font)
    facts = [
        ("Game Mode", _clean_value(profile.gamemode)),
        ("PvP", _format_bool_value(profile.pvp)),
        ("Sleep", _format_bool_value(profile.percent_player_sleep)),
        ("World Age", _clean_value(profile.world_age)),
        ("Style", _clean_value(profile.play_style)),
    ]
    y = facts_y + 42
    for label, value in facts:
        y = _draw_fact_row(
            draw, label, value, facts_x, y, facts_width, label_font, value_font
        )

    footer_x = footer_box[0] + PANEL_PADDING
    footer_y = footer_box[1] + PANEL_PADDING
    _draw_text_with_shadow(draw, footer_x, footer_y, "Realm Info", title_font)
    footer_details = [
        ("Members", _clean_value(getattr(profile, "member_count", None))),
        ("Community", _clean_value(profile.community_age)),
        ("Apply", _clean_value(profile.application_process)),
        ("Reset", _clean_value(profile.reset_schedule)),
        ("Addons", _clean_value(profile.realm_addons)),
        ("Future", _clean_value(profile.foreseeable_future)),
    ]

    left_x = footer_x
    right_x = footer_box[0] + ((footer_box[2] - footer_box[0]) // 2) + 12
    footer_content_top = footer_y + 38
    footer_row_height = 76
    footer_row_gap = max(
        54, (footer_bottom - footer_content_top - footer_row_height) // 2
    )
    y_positions = [
        footer_content_top,
        footer_content_top + footer_row_gap,
        footer_content_top + (footer_row_gap * 2),
    ]
    for index, (label, value) in enumerate(footer_details):
        x = left_x if index % 2 == 0 else right_x
        y = y_positions[index // 2]
        value_lines = _wrap_text(draw, value, value_font, 295)
        value_lines = value_lines[:3] if value_lines else ["Not set"]
        if len(_wrap_text(draw, value, value_font, 295)) > 3:
            value_lines[-1] = f"{value_lines[-1].rstrip('. ')}..."
        _draw_text_with_shadow(draw, x, y, label.upper(), label_font, fill=LABEL_COLOR)
        for line_index, line in enumerate(value_lines):
            _draw_text_with_shadow(
                draw, x, y + 19 + (line_index * 19), line, value_font
            )


async def generate_realm_profile_card(
    interaction: discord.Interaction, realm_name: str
):
    """
    Builds and returns the realm profile card with banner/logo and overlaid text.
    """
    profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
    if not profile:
        return None, "Invalid realm name provided."

    try:
        background_path = "./data/images/realm_background4.png"
        fallback_banner = "./data/images/realm_backround_banner.png"
        fallback_logo = Image.new("RGBA", (200, 200), (255, 0, 0, 255))

        base = _expand_pink_section(Image.open(background_path).convert("RGBA"))
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
        card.paste(logo, (45, 194), logo)
        _draw_realm_name(card, profile.realm_name)
        _draw_realm_details(card, profile)

        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)

        _log.info(f"Realm profile card generated for {realm_name}")
        return buffer, None

    except Exception as e:
        _log.error(f"Failed to generate card: {e}", exc_info=True)
        return None, "Error generating profile card."


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

        os.makedirs("./data/images/realms/logos/", exist_ok=True)
        path = f"./data/images/realms/logos/{realm_name}_logo.png"
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

        os.makedirs("./data/images/realms/banners/", exist_ok=True)
        path = f"./data/images/realms/banners/{realm_name}_banner.png"
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
            "logo_url": "./data/images/default_logo.png",
            "banner_url": "./data/images/default_banner.png",
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
