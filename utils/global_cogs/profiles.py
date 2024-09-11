import asyncio
import io
import logging
import re
import discord
from PIL import Image, ImageDraw, ImageFont
from discord import File
from discord.ext import commands
from core import database
from core.logging_module import get_log

_log = get_log(__name__)

# Load the background image
background_image = Image.open('./core/images/profilebackground2.png').convert('RGBA')

# ------------------- Google Sheets Configuration -------------------
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

try:
    profilesheet = client.open("PortalbotProfile").sheet1
    sheet = client.open("MRP Bannedlist Data").sheet1
except Exception as e:
    _log.error(f"Error: {e}")

# ------------------- Profile Command Cog -------------------
class ProfileCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx, *, profile: discord.Member = None):
        """
        Displays the profile of a user. If no user is specified, displays the author's profile.
        """
        if profile is None:
            profile = ctx.author

        profile_embed = await self.generate_profile_embed(profile)
        if profile_embed:
            await ctx.send(embed=profile_embed)
        else:
            await ctx.send(f"No profile found for {profile.mention}")

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

    @profile.error
    async def profile_error(self, ctx, error):
        """
        Error handler for the profile command.
        """
        if isinstance(error, commands.UserNotFound):
            await ctx.send(f"Sorry, {ctx.author.mention}, no user by that name was found.")
        else:
            raise error

    @profile.command()
    async def edit(self, ctx):
        """
        Allows the user to edit their profile information.
        """
        await ctx.send("Editing your profile... (placeholder for the edit command)")

    @profile.command()
    async def canvas(self, ctx, *, profile: discord.Member = None):
        """
        Generates a profile image on a canvas.
        """
        if profile is None:
            profile = ctx.author

        avatar_url = profile.display_avatar.url
        profile_embed = await self.generate_profile_embed(profile)

        if profile_embed:
            await ctx.send(embed=profile_embed)
        else:
            await ctx.send(f"No profile found for {profile.mention}")

        # Avatar and Canvas Logic (using PIL)...
        await self.generate_profile_canvas(ctx, profile, avatar_url)

    async def generate_profile_canvas(self, ctx, profile, avatar_url):
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

        await ctx.send(file=File(fp=buffer_output, filename="profile_canvas.png"))

# Set up the cog
async def setup(bot):
    await bot.add_cog(ProfileCMD(bot))
