import discord
import io
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands
from discord import app_commands
from core import database
from core.common import calculate_level  # Assuming this is moved to core.common

class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Constants for easy updating
    AVATAR_SIZE = 128
    REP_SIZE = 64
    PADDING = 20
    TEXT_EXTRA_PADDING = PADDING * 2  # Double padding for text

    BAR_WIDTH = 400  # Progress bar width
    BAR_HEIGHT = 20  # Progress bar height
    FONT_PATH = "./core/fonts/OpenSansEmoji.ttf"
    BACKGROUND_IMAGE_PATH = './core/images/profilebackground3.png'
    TEXT_COLOR = (255, 255, 255, 255)
    SHADOW_COLOR = (0, 0, 0, 200)  # Black with transparency
    SHADOW_OFFSET = 2  # Shadow offset for text

    @app_commands.command(name="profile", description="Generates a profile image.")
    async def generate_profile_canvas(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Generates a profile canvas using the provided background image with improved text readability.
        """
        if profile is None:
            profile = interaction.user

        # Ensure interaction response before follow-up
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Load background and create base image
        image = self.load_background_image()

        # Load and draw avatar
        avatar_image = await self.load_avatar_image(profile)
        self.draw_avatar(image, avatar_image)

        # Fetch profile data and score
        query, server_score = self.fetch_profile_data(profile, interaction.guild_id)
        if query is None:
            await interaction.response.send_message("No profile found for this user.")
            return

        # Calculate level and progress
        level, progress = self.calculate_progress(server_score)

        # Draw text and progress bar on the image
        self.draw_text_and_progress(image, profile.display_name, server_score, level, progress)

        # Send the final image
        await self.send_image(interaction, image)

    def load_background_image(self):
        """Load and return the background image."""
        background_image = Image.open(self.BACKGROUND_IMAGE_PATH).convert('RGBA')
        return background_image.copy()

    async def load_avatar_image(self, profile):
        """Load and return the user's avatar image."""
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize((self.AVATAR_SIZE, self.AVATAR_SIZE))
        return avatar_image

    def draw_avatar(self, image, avatar_image):
        """Draws the avatar onto the canvas with a circular mask."""
        mask = Image.new('L', (self.AVATAR_SIZE, self.AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, self.AVATAR_SIZE, self.AVATAR_SIZE), fill=255)
        image.paste(avatar_image, (self.PADDING, self.PADDING), mask)

    def fetch_profile_data(self, profile, guild_id):
        """Fetch profile data and score from the database."""
        longid = str(profile.id)
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            return None, None

        score_query = database.ServerScores.get_or_none(
            (database.ServerScores.DiscordLongID == longid) &
            (database.ServerScores.ServerID == str(guild_id))
        )
        server_score = score_query.Score if score_query else "N/A"
        return query, server_score

    def calculate_progress(self, server_score):
        """Calculate level and progress based on the server score."""
        if isinstance(server_score, int):
            return calculate_level(server_score)
        return 0, 0

    def draw_text_and_progress(self, image, username, server_score, level, progress):
        """Draws the username, server score, and progress bar on the image."""
        draw = ImageDraw.Draw(image)
        font, small_font = self.load_fonts()

        # Define coordinates for text and progress bar
        text_x = self.PADDING + self.AVATAR_SIZE + self.TEXT_EXTRA_PADDING
        text_y = self.PADDING

        # Draw username and shadow
        self.draw_text_with_shadow(draw, text_x, text_y, username, font)

        # Draw progress bar
        progress_bar_y = text_y + 50
        self.draw_progress_bar(draw, text_x, progress_bar_y, progress)

        # Define score and next level text
        score_text = f"Server Score: {server_score}"
        next_level_text = f"Next Level: {level + 1}"

        # Draw the score on the left and next level on the right below the progress bar
        text_below_y = progress_bar_y + 30  # Offset from the progress bar
        self.draw_text_below_progress_bar(draw, text_x, text_below_y, score_text, next_level_text, image.width, small_font)

    def load_fonts(self):
        """Loads and returns the fonts for username and small text."""
        try:
            font = ImageFont.truetype(self.FONT_PATH, 40)
            small_font = ImageFont.truetype(self.FONT_PATH, 20)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        return font, small_font

    def draw_text_with_shadow(self, draw, x, y, text, font):
        """Draw text with a shadow for better readability."""
        draw.text((x + self.SHADOW_OFFSET, y + self.SHADOW_OFFSET), text, font=font, fill=self.SHADOW_COLOR)
        draw.text((x, y), text, font=font, fill=self.TEXT_COLOR)

    def draw_progress_bar(self, draw, x, y, progress):
        """Draw the progress bar showing the level progress."""
        # Draw the progress bar background
        draw.rectangle([(x, y), (x + self.BAR_WIDTH, y + self.BAR_HEIGHT)], fill=(50, 50, 50, 255))

        # Draw the progress fill
        filled_width = int(self.BAR_WIDTH * progress)
        draw.rectangle([(x, y), (x + filled_width, y + self.BAR_HEIGHT)], fill=(0, 255, 0, 255))

    def draw_text_and_progress(self, image, username, server_score, level, progress):
        """Draws the username, server score, and progress bar on the image."""
        draw = ImageDraw.Draw(image)
        font, small_font = self.load_fonts()

        # Define coordinates for text and progress bar
        text_x = self.PADDING + self.AVATAR_SIZE + self.TEXT_EXTRA_PADDING
        text_y = self.PADDING

        # Draw username and shadow
        self.draw_text_with_shadow(draw, text_x, text_y, username, font)

        # Progress bar size calculation (fills available space between score and next level)
        bar_start_x = text_x
        bar_end_x = image.width - self.PADDING - 150  # Adjusting for padding and next level text space
        progress_bar_width = bar_end_x - bar_start_x  # Full width of the progress bar
        bar_y = text_y + 80

        # Draw the progress bar background
        draw.rectangle([(bar_start_x, bar_y), (bar_end_x, bar_y + self.BAR_HEIGHT)], fill=(50, 50, 50, 255))

        # Draw the progress fill
        filled_width = int(progress_bar_width * progress)
        draw.rectangle([(bar_start_x, bar_y), (bar_start_x + filled_width, bar_y + self.BAR_HEIGHT)], fill=(0, 255, 0, 255))

        # Draw text below the progress bar: server score on the left, next level on the right
        score_text = f"Server Score: {server_score}"
        next_level_text = f"Next Level: {level}"

        text_below_y = bar_y + 30  # Below the progress bar

        # Draw server score on the left and next level on the right
        self.draw_text_below_progress_bar(draw, bar_start_x, text_below_y, score_text, next_level_text, image.width, small_font)

    def draw_text_below_progress_bar(self, draw, bar_start_x, y, score_text, next_level_text, image_width, font):
        """Draws server score and next level text below the progress bar, justified left and right."""
        # Draw the score text on the left
        draw.text((bar_start_x, y), score_text, font=font, fill=self.TEXT_COLOR)

        # Calculate the width of the next level text (Pillow update: Use textbbox)
        next_level_text_width = draw.textbbox((0, 0), next_level_text, font=font)[2]  # Get width

        # Draw the next level text on the right
        draw.text((image_width - self.PADDING - next_level_text_width, y), next_level_text, font=font, fill=self.TEXT_COLOR)


# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
