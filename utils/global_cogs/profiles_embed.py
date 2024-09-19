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

# ------------------- Profile Embed Command Cog -------------------
class Profile_EmbedCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to view a profile with a fancy embed
    @app_commands.command(name="profile_embed", description="Displays the profile of a user.")
    async def profile_embed(self, interaction: discord.Interaction, profile: discord.Member = None):
        """
        Slash command to display a profile in an enhanced embed format.
        If no user is specified, displays the author's profile.
        """
        if profile is None:
            profile = interaction.user

        # Automatically grab the guild ID from where the command is executed
        guild_id = interaction.guild.id

        profile_embed = await self.generate_profile_embed(profile, guild_id)  # Passing guild_id to fetch score
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
        
        # If the score entry exists, get the score, otherwise show "N/A"
        server_score = score_query.Score if score_query else "N/A"

        # Calculate level and progress if server_score is valid
        if isinstance(server_score, int):
            level, progress = calculate_level(server_score)
        else:
            level, progress = 0, 0

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
        embed.add_field(name="📈 % to Next Level", value=f"{round(progress * 100, 2)}%", inline=True)

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


# Set up the cog
async def setup(bot):
    await bot.add_cog(Profile_EmbedCMD(bot))
