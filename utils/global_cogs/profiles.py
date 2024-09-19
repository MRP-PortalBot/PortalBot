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
from core.common import calculate_level

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
        if profile is None:
            profile = interaction.user

        profile_embed = await self.generate_profile_embed(profile, interaction.guild.id)
        if profile_embed:
            await interaction.response.send_message(embed=profile_embed)
        else:
            await interaction.response.send_message(f"No profile found for {profile.mention}")

    async def generate_profile_embed(self, profile: discord.Member, guild_id: int):
        longid = str(profile.id)  # Get the user's Discord ID
        avatar_url = profile.display_avatar.url

        # Query the profile from the PortalbotProfile database using Peewee
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            return None

        ServerScores = database.ServerScores
        score_query = ServerScores.get_or_none(
            (ServerScores.DiscordLongID == longid) &
            (ServerScores.ServerID == str(guild_id))
        )
        server_score = score_query.Score if score_query else "N/A"

        # Calculate level and progress
        if isinstance(server_score, int):
            level, progress = calculate_level(server_score)
        else:
            level, progress = 0, 0

        # Create the fancy embed
        embed = discord.Embed(
            title=f"{profile.display_name}'s Profile",
            description=f"**Profile for {profile.display_name}**",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text="Generated with PortalBot")

        embed.add_field(name="👤 Discord Name", value=query.DiscordName, inline=True)
        embed.add_field(name="🆔 Long ID", value=query.DiscordLongID, inline=True)
        embed.add_field(name="💬 Server Score", value=server_score, inline=False)
        embed.add_field(name="🎮 Level", value=f"Level {level}", inline=False)

        if query.Timezone != "None":
            embed.add_field(name="🕓 Timezone", value=query.Timezone, inline=False)
        if query.XBOX != "None":
            embed.add_field(name="🎮 XBOX Gamertag", value=query.XBOX, inline=False)
        if query.Playstation != "None":
            embed.add_field(name="🎮 Playstation ID", value=query.Playstation, inline=False)
        if query.Switch != "None":
            embed.add_field(name="🎮 Switch Friend Code", value=query.Switch, inline=False)
        if query.RealmsJoined != "None":
            embed.add_field(name="🏰 Member of Realms", value=query.RealmsJoined, inline=False)
        if query.RealmsAdmin != "None":
            embed.add_field(name="🛡️ Admin of Realms", value=query.RealmsAdmin, inline=False)

        return embed

    # Slash command to generate profile canvas as an image
    @app_commands.command(name="profile_canvas", description="Generates a profile image on a canvas.")
    async def generate_profile_canvas(self, interaction: discord.Interaction, profile: discord.Member):
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Load background image
        background_image_path = './core/images/profilebackground3.png'
        background_image = Image.open(background_image_path).convert('RGBA')
        WIDTH, HEIGHT = background_image.size
        AVATAR_SIZE = 128
        REP_SIZE = 64
        PADDING = 20

        # Create base image
        image = background_image.copy()
        draw = ImageDraw.Draw(image)

        # Load and paste avatar
        avatar_asset = await profile.display_avatar.read()
        avatar_image = Image.open(io.BytesIO(avatar_asset)).resize((AVATAR_SIZE, AVATAR_SIZE))
        mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        image.paste(avatar_image, (PADDING, PADDING), mask)

        # Fonts
        try:
            font = ImageFont.truetype("./core/fonts/OpenSansEmoji.ttf", 40)
            small_font = ImageFont.truetype("./core/fonts/OpenSansEmoji.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Fetch profile data
        longid = str(profile.id)
        try:
            query = database.PortalbotProfile.get(database.PortalbotProfile.DiscordLongID == longid)
        except database.PortalbotProfile.DoesNotExist:
            await interaction.response.send_message("No profile found for this user.")
            return

        ServerScores = database.ServerScores
        guild_id = str(interaction.guild_id)
        score_query = ServerScores.get_or_none(
            (ServerScores.DiscordLongID == longid) &
            (ServerScores.ServerID == guild_id)
        )
        server_score = score_query.Score if score_query else 0

        # Calculate level and progress
        level, progress = calculate_level(server_score)

        # Username and score text
        username = query.DiscordName
        rep_text = "+7 rep"
        score_text = f"Server Score: {server_score}"

        # Add shadow for readability
        shadow_offset = 2
        shadow_color = (0, 0, 0, 200)
        text_color = (255, 255, 255, 255)

        # Draw text
        text_x = PADDING + AVATAR_SIZE + 20
        text_y = PADDING
        draw.text((text_x + shadow_offset, text_y + shadow_offset), username, font=font, fill=shadow_color)
        draw.text((text_x, text_y), username, font=font, fill=text_color)

        # Draw reputation and score
        rep_bg_color = (150, 150, 255, 255)
        rep_box_x, rep_box_y = PADDING, PADDING + AVATAR_SIZE + 10
        draw.rounded_rectangle(
            [(rep_box_x, rep_box_y), (rep_box_x + REP_SIZE * 2, rep_box_y + REP_SIZE)],
            radius=10,
            fill=rep_bg_color
        )
        draw.text((rep_box_x + 10 + shadow_offset, rep_box_y + 10 + shadow_offset), rep_text, font=small_font, fill=shadow_color)
        draw.text((rep_box_x + 10, rep_box_y + 10), rep_text, font=small_font, fill=text_color)

        score_x = text_x
        score_y = text_y + 50
        draw.text((score_x + shadow_offset, score_y + shadow_offset), score_text, font=small_font, fill=shadow_color)
        draw.text((score_x, score_y), score_text, font=small_font, fill=text_color)

        # Draw the progress bar for level
        bar_width = 400
        bar_height = 25
        bar_x = text_x
        bar_y = score_y + 40
        progress_color = (100, 255, 100, 255)
        bar_bg_color = (50, 50, 50, 255)
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=bar_bg_color)
        draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progress), bar_y + bar_height], fill=progress_color)

        # Save the image to buffer
        buffer_output = io.BytesIO()
        image.save(buffer_output, format="PNG")
        buffer_output.seek(0)

        await interaction.followup.send(file=File(fp=buffer_output, filename="profile_card.png"))


# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
