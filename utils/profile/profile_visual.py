# profile/profile_visual.py

import io
import logging
import discord
from discord import File
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from core import database
from core.common import calculate_level, get_user_rank
from core.common import ensure_profile_exists


_log = logging.getLogger(__name__)

# Paths and constants
AVATAR_SIZE = 145
PADDING = 25
TEXT_EXTRA_PADDING = PADDING * 2
SMALL_PADDING = 10
BAR_HEIGHT = 30
RADIUS = 15
FONT_PATH = "./core/fonts/Minecraft-Seven_v2-1.ttf"
EMOJI_FONT_PATH = "./core/fonts/NotoColorEmoji-Regular.ttf"
BACKGROUND_IMAGE_PATH = "./core/images/profilebackground4.png"
TEXT_COLOR = (255, 255, 255, 255)
SHADOW_COLOR = (0, 0, 0, 200)
SHADOW_OFFSET = 2
PS_LOGO_PATH = "./core/images/ps-logo.png"
XBOX_LOGO_PATH = "./core/images/xbox-logo.png"
NS_LOGO_PATH = "./core/images/ns-logo.png"


def add_visual_commands(group: app_commands.Group):
    @group.command(name="profile", description="Generates a profile card.")
    async def profile(interaction: discord.Interaction, profile: discord.Member = None):
        if ensure_profile_exists(profile) is None:
            await interaction.followup.send(
                "An error occurred while loading your profile.", ephemeral=True
            )
            return

        if profile is None:
            profile = interaction.user

        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.InteractionResponded:
                _log.warning(
                    f"Interaction already responded for user {interaction.user.id}"
                )

        # --- 🔄 Fallback: Ensure profile exists ---
        user_id = str(profile.id)
        discordname = f"{profile.name}#{profile.discriminator}"
        try:
            database.db.connect(reuse_if_open=True)
            profile_record, created = database.PortalbotProfile.get_or_create(
                DiscordLongID=user_id, defaults={"DiscordName": discordname}
            )
            if created:
                _log.info(f"Auto-created profile for {discordname} on demand")
        except Exception as e:
            _log.error(
                f"Failed to auto-create profile for {discordname}: {e}", exc_info=True
            )
            await interaction.followup.send(
                "An error occurred while loading your profile.", ephemeral=True
            )
            return
        finally:
            if not database.db.is_closed():
                database.db.close()

        # --- Image generation continues below ---
        image = load_background_image()
        try:
            avatar_image = await load_avatar_image(profile)
            draw_avatar(image, avatar_image)
        except Exception as e:
            _log.error(
                f"Error loading avatar for user {profile.id}: {e}", exc_info=True
            )
            await interaction.followup.send(
                "Failed to load avatar image. Try again later.", ephemeral=True
            )
            return

        query, server_score, next_role_name = fetch_profile_data(
            profile, interaction.guild_id
        )
        if query is None:
            await interaction.followup.send(
                "No profile found for this user.", ephemeral=True
            )
            return

        level, progress, next_level_score = calculate_progress(server_score)
        rank = get_user_rank(interaction.guild_id, profile.id)

        draw_text_and_progress(
            image,
            profile.name,
            server_score,
            level,
            progress,
            rank,
            next_level_score,
            next_role_name,
        )
        draw_console_usernames(image, query)
        draw_realms_info(image, query)
        image = add_rounded_corners(image, radius=30)

        await send_image(interaction, image)

        def load_background_image():
            return Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA").copy()

        async def load_avatar_image(profile):
            avatar_asset = await profile.display_avatar.read()
            return Image.open(io.BytesIO(avatar_asset)).resize(
                (AVATAR_SIZE, AVATAR_SIZE)
            )

        def draw_avatar(image, avatar_image):
            mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, AVATAR_SIZE - 1, AVATAR_SIZE - 1), fill=255)
            image.paste(avatar_image, (PADDING, PADDING - 10), mask)

        def fetch_profile_data(profile, guild_id):
            longid = str(profile.id)
            try:
                query = database.PortalbotProfile.get(
                    database.PortalbotProfile.DiscordLongID == longid
                )
            except database.PortalbotProfile.DoesNotExist:
                return None, None, None

            score_query = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == longid)
                & (database.ServerScores.ServerID == str(guild_id))
            )
            server_score = score_query.Score if score_query else "N/A"
            current_level = score_query.Level if score_query else 0

            next_role_query = (
                database.LeveledRoles.select()
                .where(
                    (database.LeveledRoles.ServerID == str(guild_id))
                    & (database.LeveledRoles.LevelThreshold > current_level)
                )
                .order_by(database.LeveledRoles.LevelThreshold.asc())
                .first()
            )
            next_role_name = next_role_query.RoleName if next_role_query else "None"
            return query, server_score, next_role_name

        def calculate_progress(server_score):
            return (
                calculate_level(server_score)
                if isinstance(server_score, int)
                else (0, 0, 0)
            )

        def draw_text_and_progress(
            image, username, score, level, progress, rank, next_score, next_role
        ):
            draw = ImageDraw.Draw(image)
            font, small_font, _, _ = load_fonts()

            x = PADDING + AVATAR_SIZE + TEXT_EXTRA_PADDING
            y = PADDING
            draw_text_with_shadow(draw, x, y, username, font)

            rank_text = f"#{rank}"
            rank_x = image.width - 10 - PADDING - font.getbbox(rank_text)[2]
            draw_text_with_shadow(draw, rank_x, y, rank_text, font)

            progress_y = y + 65
            bar_width = image.width - x - PADDING - 10
            draw_progress_bar(
                draw, x, progress_y, progress, bar_width, score, next_score
            )

            y_below = progress_y + BAR_HEIGHT + 10
            draw_text_with_shadow(draw, x, y_below, "Server Score ⤴", small_font)
            role_text = f"Next Role: {next_role}"
            role_text_width = small_font.getbbox(role_text)[2]
            draw_text_with_shadow(
                draw,
                image.width - 10 - PADDING - role_text_width,
                y_below,
                role_text,
                small_font,
            )

        def draw_console_usernames(image, query):
            draw = ImageDraw.Draw(image)
            _, _, smallest_font, _ = load_fonts()
            x = SMALL_PADDING
            y = PADDING + AVATAR_SIZE

            consoles = [
                ("Xbox", XBOX_LOGO_PATH, query.XBOX),
                ("PlayStation", PS_LOGO_PATH, query.Playstation),
                ("Nintendo Switch", NS_LOGO_PATH, query.Switch),
            ]
            for name, path, username in consoles:
                if username and username != "None":
                    try:
                        logo = Image.open(path).resize((24, 24))
                        image.paste(logo, (x, y), logo)
                    except Exception as e:
                        _log.error(f"Failed to load logo {path} for {name}: {e}")
                    draw_text_with_shadow(draw, x + 5, y + 26, username, smallest_font)
                    y += 50

            if query.SwitchNNID and query.SwitchNNID != "None":
                draw_text_with_shadow(draw, x + 10, y, query.SwitchNNID, smallest_font)

        def draw_realms_info(image, query):
            draw = ImageDraw.Draw(image)
            _, small_font, _, _ = load_fonts()
            overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            x = PADDING + AVATAR_SIZE + TEXT_EXTRA_PADDING
            y = image.height - 175
            max_width = image.width - PADDING - x - 10

            def draw_wrapped(draw, text, font, x, y, max_width):
                words, line = text.split(), ""
                for word in words:
                    test = f"{line} {word}".strip()
                    if font.getlength(test) <= max_width:
                        line = test
                    else:
                        draw.text((x, y), line, font=font, fill=TEXT_COLOR)
                        y += 20
                        line = word
                if line:
                    draw.text((x, y), line, font=font, fill=TEXT_COLOR)
                return y + 20

            def draw_section(title, realms):
                nonlocal y
                if realms and realms != "None":
                    draw_text_with_shadow(draw, x, y, title, small_font)
                    y += 25
                    box_y0 = y - 32
                    box_y1 = box_y0 + 30
                    overlay_draw.rounded_rectangle(
                        [x - 7, box_y0, image.width - PADDING - 10, box_y1],
                        radius=15,
                        fill=(0, 0, 0, 50),
                    )
                    text = ", ".join(realm.strip() for realm in realms.split(","))
                    y = draw_wrapped(draw, text, small_font, x, y, max_width)

            draw_section("Realms as OP:", query.RealmsAdmin)
            y += 15
            draw_section("Realms as Member:", query.RealmsJoined)
            image.alpha_composite(overlay)

        def draw_progress_bar(draw, x, y, progress, width, current, max_score):
            draw.rounded_rectangle(
                [(x, y), (x + width, y + BAR_HEIGHT)],
                radius=RADIUS,
                fill=(50, 50, 50, 255),
            )
            fill_width = int(width * progress)
            draw.rounded_rectangle(
                [(x, y), (x + fill_width, y + BAR_HEIGHT)],
                radius=RADIUS,
                fill=(29, 188, 101, 255),
            )

            font = ImageFont.truetype(FONT_PATH, 25)
            text = f"{current} / {max_score}"
            text_bbox = font.getbbox(text)
            text_x = x + (width // 2) - ((text_bbox[2] - text_bbox[0]) // 2)
            ascent, descent = font.getmetrics()
            text_y = y + (BAR_HEIGHT // 2) - ((ascent + descent) // 2)
            draw_text_with_shadow(draw, text_x, text_y, text, font)

        def draw_text_with_shadow(draw, x, y, text, font):
            draw.text(
                (x + SHADOW_OFFSET, y + SHADOW_OFFSET),
                text,
                font=font,
                fill=SHADOW_COLOR,
            )
            draw.text((x, y), text, font=font, fill=TEXT_COLOR)

        def load_fonts():
            try:
                return (
                    ImageFont.truetype(FONT_PATH, 40),
                    ImageFont.truetype(FONT_PATH, 20),
                    ImageFont.truetype(FONT_PATH, 17),
                    ImageFont.truetype(EMOJI_FONT_PATH, 20),
                )
            except IOError:
                return (ImageFont.load_default(),) * 4

        async def send_image(interaction, image):
            buffer_output = io.BytesIO()
            image.save(buffer_output, format="PNG")
            buffer_output.seek(0)
            await interaction.followup.send(
                file=File(fp=buffer_output, filename="profile_card.png")
            )

        def add_rounded_corners(image, radius):
            """Adds rounded corners to an image."""
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0) + image.size, radius=radius, fill=255)

            rounded_image = Image.new("RGBA", image.size)
            rounded_image.paste(image, (0, 0), mask=mask)

            return rounded_image
