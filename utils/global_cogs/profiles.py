import discord
import io
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands
from discord import app_commands
from core import database
from core.common import calculate_level  # Assuming this is in core.common

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
    FLAG_SIZE = 32  # Size of the flag image

    FONT_PATH = "./core/fonts/OpenSansEmoji.ttf"
    BACKGROUND_IMAGE_PATH = './core/images/profilebackground3.png'
    TEXT_COLOR = (255, 255, 255, 255)
    SHADOW_COLOR = (0, 0, 0, 200)  # Black with transparency
    SHADOW_OFFSET = 2  # Shadow offset for text
    FLAG_PATH = "./core/flags/"  # Folder containing country flags

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
        self.draw_text_and_progress(image, profile.display_name, server_score, level, progress, query.RealmsAdmin)

        # Load and draw region flag
        self.draw_region_flag(image, query.Region)

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

    def draw_text_and_progress(self, image, username, server_score, level, progress, realms_admin):
        """Draws the username, server score, and progress bar on the image."""
        draw = ImageDraw.Draw(image)
        font, small_font = self.load_fonts()

        # Define coordinates for text and progress bar
        text_x = self.PADDING + self.AVATAR_SIZE + self.TEXT_EXTRA_PADDING
        text_y = self.PADDING

        # Draw username and shadow
        self.draw_text_with_shadow(draw, text_x, text_y, username, font)

        # Draw server score below the username
        score_text = f"Server Score: {server_score}"
        score_y = text_y + 50  # Offset from the username
        self.draw_text_with_shadow(draw, text_x, score_y, score_text, small_font)

        # Now draw the progress bar below the server score
        progress_bar_y = score_y + 30  # Offset from the server score text
        self.draw_progress_bar(draw, text_x, progress_bar_y, progress)

        # Draw the next role field
        next_role_text = f"Next Role: {realms_admin or 'Slime Divider'}"  # Example of next role
        self.draw_text_with_shadow(draw, text_x, text_y + 110, next_role_text, small_font)

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
        # Define the colors for the background and the progress bar fill
        background_color = (50, 50, 50, 255)  # Dark gray background
        fill_color = (0, 255, 0, 255)         # Green for the filled part
        bar_height = 20  # Adjust height if needed
        bar_width = self.BAR_WIDTH  # Full width of the bar

        # Draw the background rectangle for the progress bar
        draw.rectangle([(x, y), (x + bar_width, y + bar_height)], fill=background_color)

        # Calculate the width of the filled portion based on progress
        filled_width = int(bar_width * progress)
        
        # Draw the filled portion of the progress bar
        if filled_width > 0:
            draw.rectangle([(x, y), (x + filled_width, y + bar_height)], fill=fill_color)

        # Optionally: Add a border or shadow effect to make the bar more visually distinct
        border_color = (200, 200, 200, 255)  # Light gray for the border
        draw.rectangle([(x, y), (x + bar_width, y + bar_height)], outline=border_color, width=2)


    #def draw_region_flag(self, image, region_code):
    #    """Draw the region flag on the image based on the user's region."""
     #   if not region_code:
    #        return  # No region provided
#
 #       flag_path = f"{self.FLAG_PATH}{region_code.lower()}.svg"
  #      try:
   #         flag_image = Image.open(flag_path).resize((self.FLAG_SIZE, self.FLAG_SIZE))
    #   except FileNotFoundError:
     #       print(f"Flag image for region '{region_code}' not found.")

    async def send_image(self, interaction, image):
        """Save the image to a buffer and send it in the interaction response."""
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)
        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_card.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
