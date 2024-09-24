import discord
import io
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands
from discord import app_commands
from core import database
from core.common import calculate_level
from core.common import get_user_rank

class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Constants for easy updating
    AVATAR_SIZE = 128
    PADDING = 20
    TEXT_EXTRA_PADDING = PADDING * 2  # Double padding for text

    BAR_HEIGHT = 30  # Progress bar height
    RADIUS = 15  # Rounded corners radius for the progress bar
    FONT_PATH = "./core/fonts/Minecraft-Seven_v2-1.ttf"
    BACKGROUND_IMAGE_PATH = './core/images/profilebackground4.png'
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
        query, server_score, next_role_name = self.fetch_profile_data(profile, interaction.guild_id)
        if query is None:
            await interaction.response.send_message("No profile found for this user.")
            return

        # Calculate level and progress
        level, progress = self.calculate_progress(server_score)

        # **Fetch user rank**
        rank = get_user_rank(interaction.guild_id, profile.id)

        # Draw text and progress bar on the image
        self.draw_text_and_progress(image, profile.name, server_score, level, progress, rank, next_role_name)

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
        current_level = score_query.Level if score_query else 0

        # Query the next role based on the current level
        next_role_query = database.LeveledRoles.select().where(
            (database.LeveledRoles.ServerID == str(guild_id)) &
            (database.LeveledRoles.LevelThreshold > current_level)
        ).order_by(database.LeveledRoles.LevelThreshold.asc()).first()

        next_role_name = next_role_query.RoleName if next_role_query else "None"

        return query, server_score, next_role_name

    def calculate_progress(self, server_score):
        """Calculate level and progress based on the server score."""
        if isinstance(server_score, int):
            return calculate_level(server_score)
        return 0, 0

    def draw_text_and_progress(self, image, username, server_score, level, progress, rank):
        """Draws the username, server score, progress bar, and rank on the image."""
        draw = ImageDraw.Draw(image)
        font, small_font = self.load_fonts()

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
        next_level_score = (level + 1) ** 2 * 100  # Example for calculating next level score
        self.draw_progress_bar(draw, text_x, progress_bar_y, progress, bar_width, server_score, next_level_score)

        # Draw text under the progress bar (server score and next level)
        text_below_y = progress_bar_y + self.BAR_HEIGHT + 10  # Adjust for padding below the bar
        score_text = f"Server Score \u2934"
        next_role_text = f"Next Role: {next_role_name}"  # Display the next role's name
        
        # Draw the text below the progress bar with shadow
        self.draw_text_below_progress_bar(draw, text_x, text_below_y, score_text, next_role_text, image.width, small_font)


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

    def draw_progress_bar(self, draw, x, y, progress, bar_width, current_score, next_level_score):
        """Draw the progress bar showing the level progress with text in the middle."""

        # Draw the progress bar background (with rounded corners)
        draw.rounded_rectangle([(x, y), (x + bar_width, y + self.BAR_HEIGHT)], radius=self.RADIUS, fill=(50, 50, 50, 255))

        # Calculate the filled width based on the progress
        filled_width = int(bar_width * progress)

        # Draw the filled portion of the progress bar (with rounded corners)
        draw.rounded_rectangle([(x, y), (x + filled_width, y + self.BAR_HEIGHT)], radius=self.RADIUS, fill=(0, 255, 0, 255))

        # Load a smaller font for the text inside the progress bar
        small_font = ImageFont.truetype(self.FONT_PATH, 25)  # Adjust the size as needed

        # Text to display inside the progress bar
        progress_text = f"{current_score} / {next_level_score}"

        # Calculate text size using getbbox()
        text_bbox = small_font.getbbox(progress_text)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        # Calculate the position to center the text horizontally inside the progress bar
        text_x = x + (bar_width // 2) - (text_width // 2)
        
        # Calculate the Y position to center text vertically in the bar (compensating for baseline shift)
        ascent, descent = small_font.getmetrics()
        text_y = y + (self.BAR_HEIGHT // 2) - ((ascent + descent) // 2)

        # Draw the text in the center of the progress bar with shadow for readability
        self.draw_text_with_shadow(draw, text_x, text_y, progress_text, small_font)

        total_score_needed = sum((n ** 2) * 100 for n in range(1, 51))
        print(total_score_needed)

    def draw_text_below_progress_bar(self, draw, x, y, score_text, next_role_text, image_width, font):
        """Draw text (Server Score and Next Level) below the progress bar."""
        # Draw Server Score text with shadow
        self.draw_text_with_shadow(draw, x, y, score_text, font)

        # Draw Next Level text on the right, justified to the right of the image
        next_level_text_width = font.getbbox(next_role_text)[2]  # Using getbbox for text size
        self.draw_text_with_shadow(draw, image_width - self.PADDING - next_level_text_width, y, next_role_text, font)

    async def send_image(self, interaction, image):
        """Save the image to a buffer and send it in the interaction response."""
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)
        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_card.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))