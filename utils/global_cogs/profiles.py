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

_log = get_log(__name__)

# Load the background image for the profile card
background_image = Image.open('./core/images/profilebackground3.png').convert('RGBA')

# ------------------- Profile Command Cog -------------------
class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to view a profile with a fancy embed
    @app_commands.command(name="profile", description="Displays the profile of a user.")
    async def profile(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Slash command to display a profile in an enhanced embed format.
        If no user is specified, displays the author's profile.
        """
        if profile is None:
            profile = interaction.user

        profile_embed = await self.generate_profile_embed(profile, interaction.guild.id)  # Passing guild_id to fetch score
        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(f"No profile found for {profile.mention}")

    async def generate_profile_embed(self, profile: discord.Member, guild_id: int):
        """
        Helper function to generate a fancy profile embed for a user.
        This pulls data from the PortalbotProfile table in the database, along with the server score.
        """
        longid = str(profile.id)  # Get the user's Discord ID
        avatar_url = profile.display_avatar.url

        # Query the profile from the PortalbotProfile database using Peewee
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            return None

        ServerScores = database.ServerScores

        # Query the user's server score from ServerScores
        score_query = ServerScores.get_or_none(
            (ServerScores.DiscordLongID == longid) &
            (ServerScores.ServerID == str(guild_id))
        )
        
        # Calculate level and progress
        if isinstance(server_score, int):
            level, progress = calculate_level(server_score)
        else:
            level, progress = 0, 0

        # If the score entry exists, get the score, otherwise show "N/A"
        server_score = score_query.Score if score_query else "N/A"

        # If profile exists, create a fancy embed
        embed = discord.Embed(
            title=f"{profile.display_name}'s Profile",
            description=f"**Profile for {profile.display_name}**",
            color=discord.Color.blurple()  # Fancy blurple color
        )
        embed.set_thumbnail(url=avatar_url)  # Set profile picture as thumbnail
        embed.set_footer(text="Generated with PortalBot")  # Add a custom footer

        # Use emojis to improve the field display
        embed.add_field(name="👤 Discord Name", value=query.DiscordName, inline=True)
        embed.add_field(name="🆔 Long ID", value=query.DiscordLongID, inline=True)

        # Add server score
        embed.add_field(name="💬 Server Score", value=server_score, inline=False)
        embed.add_field(name="🎮 Level", value=f"Level {level}", inline=True)
        embed.add_field(name="📈 % to Next Level", value=f"{progress}%", inline=True)

        # Add profile fields dynamically with icons/emojis
        if query.Timezone != "None":
            embed.add_field(name="🕓 Timezone", value=query.Timezone, inline=False)
        if query.XBOX != "None":
            embed.add_field(name="🎮 XBOX Gamertag", value=query.XBOX, inline=False)
        if query.Playstation != "None":
            embed.add_field(name="🎮 Playstation ID", value=query.Playstation, inline=False)
        if query.Switch != "None":
            embed.add_field(name="🎮 Switch Friend Code", value=query.Switch, inline=False)
        
        # Add RealmsJoined and RealmsAdmin fields if they are not "None"
        if query.RealmsJoined != "None":  # Make sure it's not empty or default value
            embed.add_field(name="🏰 Member of Realms", value=query.RealmsJoined, inline=False)
        if query.RealmsAdmin != "None":  # Same check for RealmsAdmin
            embed.add_field(name="🛡️ Admin of Realms", value=query.RealmsAdmin, inline=False)

        return embed

    # Slash command to generate profile canvas as an image
    @app_commands.command(name="profile_canvas", description="Generates a profile image on a canvas.")
    async def generate_profile_canvas(self, interaction: discord.Interaction, profile: discord.Member):
        """
        Generates a profile canvas using the provided background image with improved text readability.
        """
        # Ensure interaction response before follow-up
        if not interaction.response.is_done():
            await interaction.response.defer()  # Defer the response to allow time for processing

        # Load the custom background image
        background_image_path = './core/images/profilebackground3.png'
        background_image = Image.open(background_image_path).convert('RGBA')

        # Define the canvas size (keeping it the same as the background image)
        WIDTH, HEIGHT = background_image.size
        AVATAR_SIZE = 128
        REP_SIZE = 64
        PADDING = 20

        # Create the base image using the custom background
        image = background_image.copy()
        draw = ImageDraw.Draw(image)

        # Load and paste avatar
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize((AVATAR_SIZE, AVATAR_SIZE))

        # Create a circular mask for the avatar
        mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        
        # Paste the avatar with the circular mask
        image.paste(avatar_image, (PADDING, PADDING), mask)

        # Fonts
        try:
            font = ImageFont.truetype("./core/fonts/OpenSansEmoji.ttf", 40)  # System font for username
            small_font = ImageFont.truetype("./core/fonts/OpenSansEmoji.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Fetch profile data from the database
        longid = str(profile.id)
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            await interaction.response.send_message("No profile found for this user.")
            return

        ServerScores = database.ServerScores

        # Fetch server score
        guild_id = str(interaction.guild_id)
        score_query = ServerScores.get_or_none(
            (ServerScores.DiscordLongID == longid) &
            (ServerScores.ServerID == guild_id)
        )
        server_score = score_query.Score if score_query else "N/A"

        # Calculate level and progress
        if isinstance(server_score, int):
            level, progress = calculate_level(server_score)
        else:
            level, progress = 0, 0

        # Username and other profile data
        username = query.DiscordName
        rep_text = "+7 rep"  # Example reputation, you can update this dynamically if needed
        score_text = f"Server Score: {server_score}"

        # Add text shadow for better readability (shifted black text behind the main white text)
        shadow_offset = 2
        shadow_color = (0, 0, 0, 200)  # Black with transparency
        text_color = (255, 255, 255, 255)  # White text

        # Adjust position for name, score, and progress bar
        double_padding = PADDING * 2
        text_x = double_padding + AVATAR_SIZE  # Position name further right
        score_x = text_x  # Align score under the name
        text_y = PADDING

        # Draw the username shadow
        draw.text((text_x + shadow_offset, text_y + shadow_offset), username, font=font, fill=shadow_color)
        draw.text((text_x, text_y), username, font=font, fill=text_color)

        # Server score
        score_y = text_y + 50
        draw.text((score_x + shadow_offset, score_y + shadow_offset), score_text, font=small_font, fill=shadow_color)
        draw.text((score_x, score_y), score_text, font=small_font, fill=text_color)

        # Progress bar (same x position as score)
        progress_bar_x = score_x
        progress_bar_y = score_y + 30

        # Progress bar properties
        bar_width = 400  # Total width of the progress bar
        bar_height = 20  # Height of the progress bar
        filled_width = int(bar_width * progress)  # Filled portion of the bar

        # Draw progress bar background (unfilled portion)
        draw.rounded_rectangle(
            [(progress_bar_x, progress_bar_y), (progress_bar_x + bar_width, progress_bar_y + bar_height)],
            fill=(50, 50, 50, 255)
        )
        # Draw filled portion of the progress bar
        draw.rounded_rectangle(
            [(progress_bar_x, progress_bar_y), (progress_bar_x + filled_width, progress_bar_y + bar_height)],
            fill=(0, 255, 0, 255)  # Green fill for progress
        )

        # Save the image to a buffer
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)

        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_card.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
