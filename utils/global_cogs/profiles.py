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
background_image = Image.open('./core/images/profilebackground2.png').convert('RGBA')

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
        """
        longid = str(profile.id)
        avatar_url = profile.display_avatar.url

        # Query the profile from the database
        query = database.PortalbotProfile.select().where(
            database.PortalbotProfile.DiscordLongID == longid
        )
        
        if query.exists():
            profile_data = query.get()
            
            # Creating the embed with a custom color and footer
            embed = discord.Embed(
                title=f"{profile.display_name}'s Profile",
                description=f"**Profile for {profile.display_name}**",
                color=discord.Color.blurple()  # Fancy blurple color
            )
            embed.set_thumbnail(url=avatar_url)  # Set profile picture as thumbnail
            embed.set_footer(text="Generated with PortalBot")  # Add a custom footer

            # Use emojis to improve the field display
            embed.add_field(name="👤 Discord Name", value=profile_data.DiscordName, inline=True)
            embed.add_field(name="🆔 Long ID", value=profile_data.DiscordLongID, inline=True)

            # Add profile fields dynamically with icons/emojis
            if profile_data.Timezone != "None":
                embed.add_field(name="🕓 Timezone", value=profile_data.Timezone, inline=False)
            if profile_data.XBOX != "None":
                embed.add_field(name="🎮 XBOX Gamertag", value=profile_data.XBOX, inline=False)
            if profile_data.Playstation != "None":
                embed.add_field(name="🎮 Playstation ID", value=profile_data.Playstation, inline=False)
            if profile_data.Switch != "None":
                embed.add_field(name="🎮 Switch Friend Code", value=profile_data.Switch, inline=False)
            if profile_data.PokemonGo != "None":
                embed.add_field(name="🕹️ Pokemon Go ID", value=profile_data.PokemonGo, inline=False)
            if profile_data.Chessdotcom != "None":
                embed.add_field(name="♟️ Chess.com ID", value=profile_data.Chessdotcom, inline=False)
            
            return embed
        else:
            return None

    # Slash command to generate profile canvas as an image
    @app_commands.command(name="profile_canvas", description="Generates a profile image on a canvas.")
    async def canvas(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Slash command to generate a profile image on a canvas using Pillow.
        """
        if profile is None:
            profile = interaction.user

        avatar_url = profile.display_avatar.url
        profile_embed = await self.generate_profile_embed(profile)

        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(f"No profile found for {profile.mention}")

        # Generate profile card as an image
        await self.generate_profile_canvas(interaction, profile, avatar_url)

    async def generate_profile_canvas(self, interaction: discord.Interaction, profile, avatar_url):
        """
        Generates a profile canvas with the user's avatar and profile information.
        """
        AVATAR_SIZE = 128
        image = background_image.copy()
        draw = ImageDraw.Draw(image)

        # Download the user's avatar
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize((AVATAR_SIZE, AVATAR_SIZE))

        # Create a circle mask for the avatar
        avatar_circle = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
        avatar_draw = ImageDraw.Draw(avatar_circle)
        avatar_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

        # Paste the avatar onto the image with the circular mask
        image.paste(avatar_image, (50, 50), avatar_circle)

        # Fonts and Text Positions
        font = ImageFont.truetype("./fonts/OpenSansEmoji.ttf", 40)  # Custom font for the profile name
        small_font = ImageFont.truetype("./fonts/OpenSansEmoji.ttf", 20)

        # Profile Info Text (Username, ID, etc.)
        draw.text((200, 50), profile.display_name, font=font, fill=(255, 255, 255, 255))  # Username
        draw.text((200, 100), f"ID: {profile.id}", font=small_font, fill=(255, 255, 255, 255))  # ID

        # Add additional profile fields, like Timezone, XBOX, etc.
        profile_data = {
            "Timezone": "EST",
            "XBOX": "GamerTag123",
            "Playstation": "PSNUser456",
            "Switch": "SW-1234-5678-9101",
        }

        y_position = 150
        for key, value in profile_data.items():
            draw.text((200, y_position), f"{key}: {value}", font=small_font, fill=(255, 255, 255, 255))
            y_position += 40

        # Save the image to a buffer
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)

        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_canvas.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
