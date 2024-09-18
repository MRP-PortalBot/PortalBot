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

        profile_embed = await self.generate_profile_embed(profile)
        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(f"No profile found for {profile.mention}")

    async def generate_profile_embed(self, profile: discord.Member):
        """
        Helper function to generate a fancy profile embed for a user.
        This pulls data from the PortalbotProfile table in the database.
        """
        longid = str(profile.id)  # Get the user's Discord ID
        avatar_url = profile.display_avatar.url

        # Query the profile from the PortalbotProfile database using Peewee
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            return None
        
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

        # Add profile fields dynamically with icons/emojis
        if query.Timezone != "None":
            embed.add_field(name="🕓 Timezone", value=query.Timezone, inline=False)
        if query.XBOX != "None":
            embed.add_field(name="🎮 XBOX Gamertag", value=query.XBOX, inline=False)
        if query.Playstation != "None":
            embed.add_field(name="🎮 Playstation ID", value=query.Playstation, inline=False)
        if query.Switch != "None":
            embed.add_field(name="🎮 Switch Friend Code", value=query.Switch, inline=False)
        if query.PokemonGo != "None":
            embed.add_field(name="🕹️ Pokemon Go ID", value=query.PokemonGo, inline=False)
        if query.Chessdotcom != "None":
            embed.add_field(name="♟️ Chess.com ID", value=query.Chessdotcom, inline=False)

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

        # Username and other profile data
        username = query.DiscordName
        rep_text = "+7 rep"  # Example reputation, you can update this dynamically if needed
        score_text = f"Server Score: {query.ServerScore}" if hasattr(query, 'ServerScore') else "Server Score: N/A"

        # Add text shadow for better readability (shifted black text behind the main white text)
        shadow_offset = 2
        shadow_color = (0, 0, 0, 200)  # Black with transparency
        text_color = (255, 255, 255, 255)  # White text

        # Username text alignment (aligned with the avatar)
        text_x = PADDING + AVATAR_SIZE + 20
        text_y = PADDING

        # Draw the username shadow
        draw.text((text_x + shadow_offset, text_y + shadow_offset), username, font=font, fill=shadow_color)
        draw.text((text_x, text_y), username, font=font, fill=text_color)

        # Reputation section (e.g. "+7 rep")
        rep_bg_color = (150, 150, 255, 255)  # Light blue for reputation background
        rep_box_x, rep_box_y = PADDING, PADDING + AVATAR_SIZE + 10
        draw.rounded_rectangle(
            [(rep_box_x, rep_box_y), (rep_box_x + REP_SIZE * 2, rep_box_y + REP_SIZE)],
            radius=10,
            fill=rep_bg_color
        )
        draw.text((rep_box_x + 10 + shadow_offset, rep_box_y + 10 + shadow_offset), rep_text, font=small_font, fill=shadow_color)
        draw.text((rep_box_x + 10, rep_box_y + 10), rep_text, font=small_font, fill=text_color)

        # Server score text
        score_x = text_x
        score_y = text_y + 50
        draw.text((score_x + shadow_offset, score_y + shadow_offset), score_text, font=small_font, fill=shadow_color)
        draw.text((score_x, score_y), score_text, font=small_font, fill=text_color)

        # Level text (e.g., "#4")
        level_text = "#4"  # Example level
        level_font = ImageFont.truetype("./core/fonts/OpenSansEmoji.ttf", 60)
        level_x = WIDTH - PADDING - 80
        draw.text((level_x + shadow_offset, PADDING + shadow_offset), level_text, font=level_font, fill=shadow_color)
        draw.text((level_x, PADDING), level_text, font=level_font, fill=text_color)

        # Draw a text box with "All roles earned"
        all_roles_text = query.Role if hasattr(query, 'Role') else "All roles earned!"
        all_roles_x = score_x
        all_roles_y = score_y + 40
        draw.text((all_roles_x + shadow_offset, all_roles_y + shadow_offset), all_roles_text, font=small_font, fill=shadow_color)
        draw.text((all_roles_x, all_roles_y), all_roles_text, font=small_font, fill=text_color)

        # Save the image to a buffer
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)

        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_card.png"))



# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
