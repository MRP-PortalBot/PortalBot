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

# Load the background image
background_image = Image.open('./core/images/profilebackground2.png').convert('RGBA')

# ------------------- Profile Command Cog -------------------
class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to view a profile
    @app_commands.command(name="profile", description="Displays the profile of a user.")
    async def profile(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Slash command to display a profile.
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
        Helper function to generate a profile embed for a user.
        """
        longid = str(profile.id)
        avatar_url = profile.display_avatar.url

        # Query the profile from the database
        query = database.PortalbotProfile.select().where(
            database.PortalbotProfile.DiscordLongID == longid
        )
        
        if query.exists():
            profile_data = query.get()
            embed = discord.Embed(
                title=f"{profile.display_name}'s Profile",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Discord", value=profile_data.DiscordName, inline=True)
            embed.add_field(name="LongID", value=profile_data.DiscordLongID, inline=True)

            # Add profile fields dynamically
            if profile_data.Timezone != "None":
                embed.add_field(name="Timezone", value=profile_data.Timezone, inline=True)
            if profile_data.XBOX != "None":
                embed.add_field(name="XBOX Gamertag", value=profile_data.XBOX, inline=False)
            if profile_data.Playstation != "None":
                embed.add_field(name="Playstation ID", value=profile_data.Playstation, inline=False)
            if profile_data.Switch != "None":
                embed.add_field(name="Switch Friend Code", value=profile_data.Switch, inline=False)
            if profile_data.PokemonGo != "None":
                embed.add_field(name="Pokemon Go ID", value=profile_data.PokemonGo, inline=False)
            if profile_data.Chessdotcom != "None":
                embed.add_field(name="Chess.com ID", value=profile_data.Chessdotcom, inline=False)
            
            return embed
        else:
            return None

    # Slash command to edit a profile (placeholder)
    @app_commands.command(name="profile_edit", description="Allows the user to edit their profile.")
    async def edit(self, interaction: discord.Interaction):
        """
        Slash command placeholder for editing profile information.
        """
        await interaction.response.send_message("Editing your profile... (placeholder for the edit command)")

    # Slash command to generate profile canvas
    @app_commands.command(name="profile_canvas", description="Generates a profile image on a canvas.")
    async def canvas(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Slash command to generate a profile image on a canvas.
        """
        if profile is None:
            profile = interaction.user

        avatar_url = profile.display_avatar.url
        profile_embed = await self.generate_profile_embed(profile)

        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(f"No profile found for {profile.mention}")

        # Avatar and Canvas Logic (using PIL)...
        await self.generate_profile_canvas(interaction, profile, avatar_url)

    async def generate_profile_canvas(self, interaction: discord.Interaction, profile, avatar_url):
        """
        Generates a profile canvas with the user's avatar.
        """
        AVATAR_SIZE = 128
        image = background_image.copy()

        # Avatar handling
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize((AVATAR_SIZE, AVATAR_SIZE))
        
        # Draw avatar on the canvas
        avatar_circle = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
        avatar_draw = ImageDraw.Draw(avatar_circle)
        avatar_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

        image.paste(avatar_image, (20, 20), avatar_circle)

        # Save the image to a buffer
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)

        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_canvas.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
