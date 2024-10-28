import asyncio
import io
import logging
import re
import discord
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands
from discord import app_commands
from core import database
from core.logging_module import get_log
from core.common import calculate_level  # Import your helper function here
from core.common import get_user_rank
import emoji as em
from pilmoji import Pilmoji

_log = get_log(__name__)


# ------------------- Profile Modals -------------------
class ProfileEditModal(discord.ui.Modal, title="Edit Profile"):
    def __init__(self, bot, profile_id):
        super().__init__()
        self.bot = bot
        self.profile_id = profile_id

    # Text input fields for editing different profile properties
    xbox_field = discord.ui.TextInput(
        label="XBOX Gamertag",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Enter new XBOX Gamertag",
    )

    psn_field = discord.ui.TextInput(
        label="Playstation ID",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Enter new Playstation ID",
    )

    switch_field = discord.ui.TextInput(
        label="Switch Username",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Enter new Switch Username",
    )

    switch_nnid_field = discord.ui.TextInput(
        label="Switch NNID",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Enter new Switch Friend Code",
    )

    timezone_field = discord.ui.TextInput(
        label="Timezone",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Enter new timezone (e.g., UTC-5, CST, etc.)",
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Fetch the profile from the database
            profile = database.PortalbotProfile.get(
                database.PortalbotProfile.DiscordLongID == self.profile_id
            )

            # Validate user input before updating the profile
            if self.xbox_field.value and not re.match(
                r"^[a-zA-Z0-9 ]{1,15}$", self.xbox_field.value
            ):
                await interaction.response.send_message(
                    "Invalid XBOX Gamertag format.", ephemeral=True
                )
                _log.warning(
                    f"Invalid XBOX Gamertag format provided by user {self.profile_id}."
                )
                return
            if self.psn_field.value and not re.match(
                r"^[a-zA-Z0-9-_]{3,16}$", self.psn_field.value
            ):
                await interaction.response.send_message(
                    "Invalid Playstation ID format.", ephemeral=True
                )
                _log.warning(
                    f"Invalid Playstation ID format provided by user {self.profile_id}."
                )
                return
            if self.switch_field.value and not re.match(
                r"^[a-zA-Z0-9-_]{3,16}$", self.switch_field.value
            ):
                await interaction.response.send_message(
                    "Invalid Switch Friend Code format.", ephemeral=True
                )
                _log.warning(
                    f"Invalid Switch Username format provided by user {self.profile_id}."
                )
                return
            if self.switch_nnid_field.value and not re.match(
                r"^SW-\d{4}-\d{4}-\d{4}$", self.switch_nnid_field.value
            ):
                await interaction.response.send_message(
                    "Invalid Switch Friend Code format.", ephemeral=True
                )
                _log.warning(
                    f"Invalid Switch Friend Code format provided by user {self.profile_id}."
                )
                return
            if self.timezone_field.value and not re.match(
                r"^[a-zA-Z0-9\-+ ]+$", self.timezone_field.value
            ):
                await interaction.response.send_message(
                    "Invalid timezone format.", ephemeral=True
                )
                _log.warning(
                    f"Invalid timezone format provided by user {self.profile_id}."
                )
                return

            # Update profile fields based on user input
            if self.xbox_field.value:
                profile.XBOX = self.xbox_field.value
            if self.psn_field.value:
                profile.Playstation = self.psn_field.value
            if self.switch_field.value:
                profile.Switch = self.switch_field.value
            if self.switch_nnid_field.value:
                profile.SwitchNNID = self.switch_nnid_field.value
            if self.timezone_field.value:
                profile.Timezone = self.timezone_field.value

            # Save updated profile to the database
            profile.save()
            _log.info(f"Profile for user ID {self.profile_id} updated successfully.")

            # Notify the user that the profile was updated
            await interaction.response.send_message(
                "Your profile has been updated successfully!", ephemeral=True
            )

        except database.PortalbotProfile.DoesNotExist:
            await interaction.response.send_message(
                "Profile not found. Please create a profile first.", ephemeral=True
            )
            _log.error(
                f"Profile for user ID {self.profile_id} not found during update."
            )

        except Exception as e:
            _log.error(
                f"Error updating profile for user ID {self.profile_id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "An error occurred while updating your profile.", ephemeral=True
            )


# ------------------- Profile Command -------------------
class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    PF = app_commands.Group(name="profile", description="Commands for User Profiles")

    # Constants for easy updating
    AVATAR_SIZE = 145
    PADDING = 25
    TEXT_EXTRA_PADDING = PADDING * 2  # Double padding for text
    SMALL_PADDING = 10

    BAR_HEIGHT = 30  # Progress bar height
    RADIUS = 15  # Rounded corners radius for the progress bar
    FONT_PATH = "./core/fonts/Minecraft-Seven_v2-1.ttf"
    EMOJI_FONT_PATH = "./core/fonts/NotoColorEmoji-Regular.ttf"
    BACKGROUND_IMAGE_PATH = "./core/images/profilebackground4.png"
    TEXT_COLOR = (255, 255, 255, 255)
    SHADOW_COLOR = (0, 0, 0, 200)  # Black with transparency
    SHADOW_OFFSET = 2  # Shadow offset for text

    # Paths for console logo images
    PS_LOGO_PATH = "./core/images/ps-logo.png"
    XBOX_LOGO_PATH = "./core/images/xbox-logo.png"
    NS_LOGO_PATH = "./core/images/ns-logo.png"

    @PF.command(name="profile", description="Generates a profile card.")
    async def profile(
        self, interaction: discord.Interaction, profile: discord.Member = None
    ):
        if profile is None:
            profile = interaction.user

        # Ensure interaction response before follow-up
        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.InteractionResponded:
                _log.warning(
                    f"Interaction response already deferred for user {interaction.user.id}."
                )

        # Load background and create base image
        image = self.load_background_image()

        # Load and draw avatar
        try:
            avatar_image = await self.load_avatar_image(profile)
            self.draw_avatar(image, avatar_image)
        except Exception as e:
            _log.error(
                f"Error loading avatar for user {profile.id}: {e}", exc_info=True
            )
            await interaction.followup.send(
                "Failed to load the avatar image. Please try again later.",
                ephemeral=True,
            )
            return

        # Fetch profile data and score
        query, server_score, next_role_name = self.fetch_profile_data(
            profile, interaction.guild_id
        )
        if query is None:
            await interaction.response.send_message("No profile found for this user.")
            return

        # Calculate level and progress
        level, progress, next_level_score = self.calculate_progress(server_score)

        # **Fetch user rank**
        rank = get_user_rank(interaction.guild_id, profile.id)

        # Draw text and progress bar on the image
        self.draw_text_and_progress(
            image,
            profile.name,
            server_score,
            level,
            progress,
            rank,
            next_level_score,
            next_role_name,
        )

        # Draw game console usernames and NNID under the profile picture
        self.draw_console_usernames(image, query)

        # Draw realms information in the pink area below the score section
        self.draw_realms_info(image, query)

        # Send the final image
        await self.send_image(interaction, image)

    def draw_console_usernames(self, image, query):
        """Draws the console usernames and NNID under the profile picture with proper spacing and alignment."""
        draw = ImageDraw.Draw(image)
        font, small_font, smallest_font, emoji_font = self.load_fonts()

        # Starting position for drawing usernames
        x = self.SMALL_PADDING
        y = self.PADDING + self.AVATAR_SIZE  # Below the avatar image with some padding

        # Console info (name, image path, and username)
        consoles = [
            ("PlayStation", self.PS_LOGO_PATH, query.Playstation),
            ("Xbox", self.XBOX_LOGO_PATH, query.XBOX),
            ("Nintendo Switch", self.NS_LOGO_PATH, query.Switch),
        ]

        for console_name, logo_path, username in consoles:
            if username and username != "None":  # Ensure there is a valid username
                # Load and draw the console logo
                try:
                    logo = Image.open(logo_path).resize(
                        (24, 24)
                    )  # Resize the logo to fit nicely
                    image.paste(logo, (x, y), logo)
                except Exception as e:
                    _log.error(
                        f"Failed to load logo {logo_path} for {console_name}: {e}"
                    )

                # Draw the username below the logo
                text_x = x + 5
                text_y = y + 26  # Space below the logo to draw text
                self.draw_text_with_shadow(
                    draw, text_x, text_y, username, smallest_font
                )

                # Update y-coordinate for the next console, leaving enough space
                y += 50  # Adjust for the next entry to ensure consistent padding

        # Draw the NNID without the logo
        if query.SwitchNNID and query.SwitchNNID != "None":
            nnid_text = query.SwitchNNID
            self.draw_text_with_shadow(draw, x, y, nnid_text, smallest_font)

    def draw_realms_info(self, image, query):
        """Draws the realms information for OP and member realms in the pink area."""
        # Create a transparent layer to draw the rounded rectangle
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        draw = ImageDraw.Draw(image)
        _, small_font, _, _ = self.load_fonts()  # Load fonts

        # Define starting position for drawing the realms information
        x = int(self.PADDING + self.AVATAR_SIZE + self.TEXT_EXTRA_PADDING)
        y = int(image.height - 175)  # Position relative to the bottom of the image

        # Draw realms where the user is an OP
        if query.RealmsAdmin and query.RealmsAdmin != "None":
            # Draw the title first
            op_realms_text = "Realms as OP:"
            self.draw_text_with_shadow(draw, x, y, op_realms_text, small_font)

            # Update y-coordinate to add space below the title
            y += 25

            # Calculate the height of the OP realms text block
            op_realms_height = 30  # Initial height for the title
            current_x = x
            op_realms = query.RealmsAdmin.split(",")
            for index, realm in enumerate(op_realms):
                # Calculate width of each realm text and comma
                realm_text = realm.strip()
                text_width = small_font.getlength(realm_text)
                current_x += text_width
                if index < len(op_realms) - 1:
                    current_x += small_font.getlength(", ")
                op_realms_height += (
                    30 if index == 0 else 0
                )  # Add height for each realm text line

            # Draw a rounded transparent white square behind the OP realms section on the overlay
            rect_x0 = x - 10
            rect_y0 = y - 35
            rect_x1 = current_x + 10
            rect_y1 = y + op_realms_height - 10
            draw_overlay.rounded_rectangle(
                [rect_x0, rect_y0, rect_x1, rect_y1],
                radius=15,
                fill=(255, 255, 255, 100),  # Set the alpha value for transparency
            )

            # Draw OP realms in a single line, separated by commas
            current_x = x
            for index, realm in enumerate(op_realms):
                # Draw the realm name
                realm_text = realm.strip()
                self.draw_text_with_shadow(
                    draw, int(current_x), int(y), realm_text, small_font
                )
                current_x += small_font.getlength(realm_text)

                # Draw comma separator except after the last realm
                if index < len(op_realms) - 1:
                    draw.text(
                        (int(current_x), int(y)),
                        ", ",
                        font=small_font,
                        fill=self.TEXT_COLOR,
                    )
                    current_x += small_font.getlength(", ")

            y += 30  # Update y-coordinate after OP realms

        # Paste the overlay (with transparency) onto the original image
        image.alpha_composite(overlay)

        # Draw realms where the user is a member
        if query.RealmsJoined and query.RealmsJoined != "None":
            # Draw the title first
            member_realms_text = "Realms as Member:"
            self.draw_text_with_shadow(draw, x, y, member_realms_text, small_font)

            # Update y-coordinate to add space below the title
            y += 25

            # Draw member realms in a single line, separated by commas
            current_x = x
            member_realms = query.RealmsJoined.split(",")
            for index, realm in enumerate(member_realms):
                # Draw the realm name
                realm_text = realm.strip()
                self.draw_text_with_shadow(
                    draw, int(current_x), int(y), realm_text, small_font
                )
                current_x += small_font.getlength(realm_text)

                # Draw comma separator except after the last realm
                if index < len(member_realms) - 1:
                    draw.text(
                        (int(current_x), int(y)),
                        ", ",
                        font=small_font,
                        fill=self.TEXT_COLOR,
                    )
                    current_x += small_font.getlength(", ")

            y += 30  # Update y-coordinate after member realms

    def load_background_image(self):
        """Load and return the background image."""
        background_image = Image.open(self.BACKGROUND_IMAGE_PATH).convert("RGBA")
        return background_image.copy()

    async def load_avatar_image(self, profile):
        """Load and return the user's avatar image."""
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize(
            (self.AVATAR_SIZE, self.AVATAR_SIZE)
        )
        return avatar_image

    def draw_avatar(self, image, avatar_image):
        """Draws the avatar onto the canvas with a circular mask."""
        mask = Image.new("L", (self.AVATAR_SIZE, self.AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, self.AVATAR_SIZE - 1, self.AVATAR_SIZE - 1), fill=255)
        image.paste(avatar_image, (self.PADDING, self.PADDING - 10), mask)

    def fetch_profile_data(self, profile, guild_id):
        """Fetch profile data and score from the database."""
        longid = str(profile.id)
        try:
            query = database.PortalbotProfile.get(
                database.PortalbotProfile.DiscordLongID == longid
            )
        except database.PortalbotProfile.DoesNotExist:
            return None, None, None

        # Add console usernames and NNID to the query if not already present
        query.psn_username = getattr(query, "PSNUsername", None)
        query.xbox_username = getattr(query, "XboxUsername", None)
        query.switch_username = getattr(query, "SwitchUsername", None)
        query.SwitchNNID = getattr(query, "SwitchNNID", None)

        score_query = database.ServerScores.get_or_none(
            (database.ServerScores.DiscordLongID == longid)
            & (database.ServerScores.ServerID == str(guild_id))
        )
        server_score = score_query.Score if score_query else "N/A"
        current_level = score_query.Level if score_query else 0

        # Query the next role based on the current level
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

    def calculate_progress(self, server_score):
        """Calculate level and progress based on the server score."""
        if isinstance(server_score, int):
            return calculate_level(server_score)
        return 0, 0, 0

    def draw_text_and_progress(
        self,
        image,
        username,
        server_score,
        level,
        progress,
        rank,
        next_level_score,
        next_role_name,
    ):
        """Draws the username, server score, progress bar, and rank on the image."""
        draw = ImageDraw.Draw(image)
        font, small_font, smallest_font, emoji_font = self.load_fonts()

        # Define coordinates for text and progress bar
        text_x = self.PADDING + self.AVATAR_SIZE + self.TEXT_EXTRA_PADDING
        text_y = self.PADDING

        # Draw username and shadow
        self.draw_text_with_shadow(draw, text_x, text_y, username, font)

        # Draw the user's rank
        rank_text = f"#{rank}"
        rank_x = image.width - self.PADDING - font.getbbox(rank_text)[2]
        rank_y = text_y
        self.draw_text_with_shadow(draw, rank_x, rank_y, rank_text, font)

        # Shift the progress bar downward by adjusting the text_y + value
        progress_bar_y = text_y + 65  # Adjust this value for consistent padding

        # Draw progress bar
        bar_width = image.width - text_x - self.PADDING
        self.draw_progress_bar(
            draw,
            text_x,
            progress_bar_y,
            progress,
            bar_width,
            server_score,
            next_level_score,
        )

        # Draw text under the progress bar (server score and next level)
        text_below_y = (
            progress_bar_y + self.BAR_HEIGHT + 10
        )  # Adjust for padding below the bar
        score_text = f"Server Score ⤴"
        next_role_text = f"Next Role: {next_role_name}"  # Display the next role's name

        # Draw the text below the progress bar with shadow
        self.draw_text_below_progress_bar(
            draw,
            text_x,
            text_below_y,
            score_text,
            next_role_text,
            image.width,
            small_font,
        )

    def load_fonts(self):
        """Loads and returns the fonts for username and small text."""
        try:
            font = ImageFont.truetype(self.FONT_PATH, 40)
            small_font = ImageFont.truetype(self.FONT_PATH, 20)
            smallest_font = ImageFont.truetype(self.FONT_PATH, 17)
            emoji_font = ImageFont.truetype(self.EMOJI_FONT_PATH, 20)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            smallest_font = ImageFont.load_default()
            emoji_font = ImageFont.load_default()
        return font, small_font, smallest_font, emoji_font

    def draw_text_with_shadow(self, draw, x, y, text, font):
        """Draw text with a shadow for better readability."""
        draw.text(
            (x + self.SHADOW_OFFSET, y + self.SHADOW_OFFSET),
            text,
            font=font,
            fill=self.SHADOW_COLOR,
        )
        draw.text((x, y), text, font=font, fill=self.TEXT_COLOR)

    def draw_progress_bar(
        self, draw, x, y, progress, bar_width, current_score, next_level_score
    ):
        """Draw the progress bar showing the level progress with text in the middle."""

        # Draw the progress bar background (with rounded corners)
        draw.rounded_rectangle(
            [(x, y), (x + bar_width, y + self.BAR_HEIGHT)],
            radius=self.RADIUS,
            fill=(50, 50, 50, 255),
        )

        # Calculate the filled width based on the progress
        filled_width = int(bar_width * progress)

        # Draw the filled portion of the progress bar (with rounded corners)
        draw.rounded_rectangle(
            [(x, y), (x + filled_width, y + self.BAR_HEIGHT)],
            radius=self.RADIUS,
            fill=(0, 255, 0, 255),
        )

        # Load a smaller font for the text inside the progress bar
        small_font = ImageFont.truetype(self.FONT_PATH, 25)  # Adjust the size as needed

        # Text to display inside the progress bar
        progress_text = f"{current_score} / {next_level_score}"

        # Calculate text size using getbbox()
        text_bbox = small_font.getbbox(progress_text)
        text_width, text_height = (
            text_bbox[2] - text_bbox[0],
            text_bbox[3] - text_bbox[1],
        )

        # Calculate the position to center the text horizontally inside the progress bar
        text_x = x + (bar_width // 2) - (text_width // 2)

        # Calculate the Y position to center text vertically in the bar (compensating for baseline shift)
        ascent, descent = small_font.getmetrics()
        text_y = y + (self.BAR_HEIGHT // 2) - ((ascent + descent) // 2)

        # Draw the text in the center of the progress bar with shadow for readability
        self.draw_text_with_shadow(draw, text_x, text_y, progress_text, small_font)

    def draw_text_below_progress_bar(
        self, draw, x, y, score_text, next_role_text, image_width, font
    ):
        """Draw text (Server Score and Next Level) below the progress bar."""
        # Draw Server Score text with shadow
        self.draw_text_with_shadow(draw, x, y, score_text, font)

        # Draw Next Level text on the right, justified to the right of the image
        next_level_text_width = font.getbbox(next_role_text)[
            2
        ]  # Using getbbox for text size
        self.draw_text_with_shadow(
            draw,
            image_width - self.PADDING - next_level_text_width,
            y,
            next_role_text,
            font,
        )

    async def send_image(self, interaction, image):
        """Save the image to a buffer and send it in the interaction response."""
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)
        await interaction.followup.send(
            file=File(fp=buffer_output, filename="profile_card.png")
        )

    # ------------------- Profile Embed Command -------------------

    # Slash command to view a profile with a fancy embed
    @PF.command(name="embed", description="Displays the profile of a user as an embed.")
    async def profile_embed(
        self, interaction: discord.Interaction, profile: discord.Member = None
    ):
        """
        Slash command to display a profile in an enhanced embed format.
        If no user is specified, displays the author's profile.
        """
        if profile is None:
            profile = interaction.user

        # Automatically grab the guild ID from where the command is executed
        guild_id = interaction.guild.id

        profile_embed = await self.generate_profile_embed(
            profile, guild_id
        )  # Passing guild_id to fetch score
        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(
                f"No profile found for {profile.mention}"
            )

    async def generate_profile_embed(self, profile: discord.Member, guild_id: int):
        """
        Helper function to generate a fancy profile embed for a user.
        This pulls data from the PortalbotProfile table in the database, along with the server score.
        """
        longid = str(profile.id)  # Get the user's Discord ID
        avatar_url = profile.display_avatar.url

        # Query the profile from the PortalbotProfile database using Peewee
        try:
            query = database.PortalbotProfile.get(
                database.PortalbotProfile.DiscordLongID == longid
            )
        except database.PortalbotProfile.DoesNotExist:
            return None

        ServerScores = database.ServerScores

        # Query the user's server score from ServerScores
        score_query = ServerScores.get_or_none(
            (ServerScores.DiscordLongID == longid)
            & (ServerScores.ServerID == str(guild_id))
        )

        # If the score entry exists, get the score, otherwise show "N/A"
        server_score = score_query.Score if score_query else "N/A"

        # Calculate level and progress if server_score is valid
        if isinstance(server_score, int):
            level, progress, next_level_score = calculate_level(server_score)
        else:
            level, progress, next_level_score = 0, 0, 0

        # **Fetch user rank**
        rank = get_user_rank(guild_id, profile.id)

        # If profile exists, create a fancy embed
        embed = discord.Embed(
            title=f"{profile.display_name}'s Profile",
            description=f"**Profile for {profile.display_name}**",
            color=discord.Color.blurple(),  # Fancy blurple color
        )
        embed.set_thumbnail(url=avatar_url)  # Set profile picture as thumbnail
        embed.set_footer(text="Generated with PortalBot")  # Add a custom footer

        # Use emojis to improve the field display
        embed.add_field(name="👤 Discord Name", value=query.DiscordName, inline=True)
        embed.add_field(name="🆔 Long ID", value=query.DiscordLongID, inline=True)

        # Add server score
        embed.add_field(
            name="💬 Server Score",
            value=f"{server_score} / {next_level_score}",
            inline=False,
        )
        embed.add_field(name="🎮 Level", value=f"Level {level}", inline=True)
        embed.add_field(
            name="📈 % to Next Level", value=f"{round(progress * 100, 2)}%", inline=True
        )
        embed.add_field(name="🏆 Server Rank", value=rank, inline=False)

        # Add profile fields dynamically with icons/emojis
        if query.Timezone != "None":
            embed.add_field(name="🕓 Timezone", value=query.Timezone, inline=False)
        if query.XBOX != "None":
            embed.add_field(name="🎮 XBOX Gamertag", value=query.XBOX, inline=False)
        if query.Playstation != "None":
            embed.add_field(
                name="🎮 Playstation ID", value=query.Playstation, inline=False
            )
        if query.Switch != "None":
            embed.add_field(
                name="🎮 Switch Friend Code",
                value=f"{query.Switch} - {query.SwitchNNID}",
                inline=False,
            )

        # Add RealmsJoined and RealmsAdmin fields if they are not "None"
        if query.RealmsJoined != "None":  # Make sure it's not empty or default value
            embed.add_field(
                name="🏰 Member of Realms", value=query.RealmsJoined, inline=False
            )
        if query.RealmsAdmin != "None":  # Same check for RealmsAdmin
            embed.add_field(
                name="🛡️ Admin of Realms", value=query.RealmsAdmin, inline=False
            )

        return embed

    # ------------------- Profile Edit Command -------------------
    # Slash command to edit a user's profile
    @PF.command(name="edit_profile", description="Edit your user profile.")
    async def edit_profile(self, interaction: discord.Interaction):
        """
        Slash command to edit the user's profile.
        """
        profile = interaction.user

        # Ensure the user has a profile to edit
        try:
            # Try to get the user's profile from the database
            profile_query = database.PortalbotProfile.get(
                database.PortalbotProfile.DiscordLongID == str(profile.id)
            )

            # Show the profile edit modal if the profile exists
            await interaction.response.send_modal(
                ProfileEditModal(self.bot, profile.id)
            )

        except database.PortalbotProfile.DoesNotExist:
            # If the profile does not exist, send a message to the user
            await interaction.response.send_message(
                "You don't have a profile yet. Please create one first.", ephemeral=True
            )
            _log.warning(f"User {profile.id} attempted to edit a non-existent profile.")

        except Exception as e:
            _log.error(
                f"Error during profile edit command for user {profile.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "An error occurred while trying to edit your profile.", ephemeral=True
            )


# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
