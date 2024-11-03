import discord
from discord import app_commands
from discord.ext import commands
from discord import Interaction
from discord.app_commands.errors import CheckFailure
from core import database
from core.database import RealmProfile
from PIL import Image, ImageDraw, ImageFont
from core.logging_module import get_log
import io
import requests


_log = get_log(__name__)


class RealmProfiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Constants
    BACKGROUND_IMAGE_PATH = "./core/images/realm_background4.png"  # Path to the Nether Portal background image
    FONT_PATH = "./core/fonts/Minecraft-Seven_v2-1.ttf"  # Example font path
    BANNER_IMAGE_PATH = "./core/images/realm_backround_banner.png"
    AVATAR_SIZE = 100
    PADDING = 20
    TEXT_COLOR = (255, 255, 255, 255)

    async def realm_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete function to suggest realm names based on user input.
        """
        realm_names = [realm.realm_name for realm in database.RealmProfile.select()]
        return [
            app_commands.Choice(name=realm, value=realm)
            for realm in realm_names
            if current.lower() in realm.lower()
        ]

    RP = app_commands.Group(
        name="realm-profile",
        description="View/Configure your Realm Profile.",
    )

    @RP.command(description="View a Realm Profile")
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def view(self, interaction: discord.Interaction, realm_name: str = None):
        """View the details of a Realm Profile."""
        # Use the provided realm_name or default to the channel name
        realm_name = realm_name if realm_name else interaction.channel.name

        # Query the RealmProfile from the database
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)

        if realm_profile:
            # Create an embed to display the profile information
            embed = discord.Embed(
                title=f"{realm_profile.emoji} {realm_profile.realm_name} - Realm Profile",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Realm Name", value=realm_profile.realm_name, inline=False
            )
            embed.add_field(
                name="Description", value=realm_profile.long_desc, inline=False
            )
            embed.add_field(
                name="PvP",
                value="Enabled" if realm_profile.pvp else "Disabled",
                inline=True,
            )
            embed.add_field(
                name="One Player Sleep",
                value="Enabled" if realm_profile.percent_player_sleep else "Disabled",
                inline=True,
            )
            embed.add_field(
                name="World Age", value=realm_profile.world_age, inline=True
            )
            embed.add_field(
                name="Realm Style", value=realm_profile.play_style, inline=True
            )
            embed.add_field(name="Game Mode", value=realm_profile.gamemode, inline=True)

            await interaction.response.send_message(embed=embed)
        else:
            # Send a message if no profile was found for the specified realm
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )

    @RP.command(description="Configure a Realm Profile")
    async def setup(
        self,
        interaction: Interaction,
        realm_name: str,
        realm_emoji: str,
        pvp: bool,
        percent_player_sleep: bool,
        world_age: str,
        play_style: str,
        gamemode: str,
    ):
        """Configure your Realm Profile."""
        try:
            # Use the provided realm_name or default to the channel name
            realm_name = realm_name if realm_name else interaction.channel.name

            realm_profile, created = RealmProfile.get_or_create(
                realm_name=realm_name,
                defaults={
                    "emoji": realm_emoji,
                    "pvp": pvp,
                    "percent_player_sleep": percent_player_sleep,
                    "world_age": world_age,
                    "play_style": play_style,
                    "gamemode": gamemode,
                },
            )

            if not created:
                # Update the existing profile
                realm_profile.emoji = realm_emoji
                realm_profile.pvp = pvp
                realm_profile.percent_player_sleep = percent_player_sleep
                realm_profile.world_age = world_age
                realm_profile.play_style = play_style
                realm_profile.gamemode = gamemode
                realm_profile.save()

            embed = discord.Embed(
                title="Realm Profile Configured",
                description=f"{realm_emoji} {realm_name} has been successfully configured.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="PvP", value="Enabled" if pvp else "Disabled", inline=True
            )
            embed.add_field(
                name="One Player Sleep",
                value="Enabled" if percent_player_sleep else "Disabled",
                inline=True,
            )
            embed.add_field(name="World Age", value=world_age, inline=True)
            embed.add_field(name="Realm Style", value=play_style, inline=True)
            embed.add_field(name="Game Mode", value=gamemode, inline=True)

            await interaction.response.send_message(embed=embed)

        except CheckFailure:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "You do not own this realm channel or lack permissions.",
                    ephemeral=True,
                )

    # Error handling to avoid responding multiple times
    async def on_app_command_error(self, interaction: Interaction, error):
        if isinstance(error, CheckFailure):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Check failed: You don't have permission to run this command.",
                    ephemeral=True,
                )
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while processing your command.", ephemeral=True
                )

        # ------------------View Realm Profile Card-------------------------------------------------------------------

    @RP.command(
        name="generate_realm_profile",
        description="Generate a profile card for a Minecraft Realm.",
    )
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def generate_realm_profile(
        self, interaction: discord.Interaction, realm_name: str
    ):
        """
        Slash command to generate a profile card for a realm.
        """
        try:
            # Defer interaction response
            await interaction.response.defer()

            # Fetch the realm profile from the database
            realm_profile = database.RealmProfile.get_or_none(
                database.RealmProfile.realm_name == realm_name
            )

            if not realm_profile:
                await interaction.followup.send(
                    f"Invalid realm name. Please choose a valid realm.",
                    ephemeral=True,
                )
                return

            # Load the background image
            background_image = Image.open(self.BACKGROUND_IMAGE_PATH).convert("RGBA")
            image = background_image.copy()

            # Load the banner image
            banner_image = Image.open(self.BANNER_IMAGE_PATH).convert("RGBA")
            banner_width, banner_height = banner_image.size

            # Create a new image to paste the banner behind the background
            final_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
            final_image.paste(banner_image, (5, 5), banner_image)
            final_image.paste(image, (0, 0), image)

            # Draw on the image
            draw = ImageDraw.Draw(final_image)
            font = ImageFont.truetype(self.FONT_PATH, 60)  # Increased default font size
            small_font = ImageFont.truetype(self.FONT_PATH, 20)

            # Draw the Realm Logo (top of the image)
            try:
                response = requests.get(realm_profile.logo_url)
                realm_logo = (
                    Image.open(io.BytesIO(response.content))
                    .convert("RGBA")
                    .resize((200, 200))
                )
            except Exception as e:
                _log.error(f"Error loading realm logo: {e}")
                realm_logo = Image.new(
                    "RGBA", (200, 200), (255, 0, 0, 255)
                )  # Placeholder red box

            logo_width, logo_height = realm_logo.size
            final_image.paste(
                realm_logo,
                (self.PADDING + 25, banner_height - 60),
                realm_logo,
            )

            # Draw the Realm Name (below the logo) with text wrapping and resizing
            text_x = self.PADDING + 25 + logo_width + self.PADDING + self.PADDING
            text_y = banner_height - 10
            max_width = final_image.width - text_x - self.PADDING

            # Adjust font size to fit the realm name within max_width
            realm_name_font_size = 60
            words = realm_name.split()
            while (
                font.getbbox(" ".join(words[:3]))[2] > max_width
                and realm_name_font_size > 10
            ):
                realm_name_font_size -= 2
                font = ImageFont.truetype(self.FONT_PATH, realm_name_font_size)

            # Wrap text after the third word
            realm_name_lines = [" ".join(words[:3])]
            if len(words) > 3:
                realm_name_lines.append(" ".join(words[3:]))

            for line in realm_name_lines:
                draw.text((text_x, text_y), line, font=font, fill=self.TEXT_COLOR)
                text_y += font.getbbox(line)[3] + 5

            # Add any other details (e.g., members, description)
            details_y = text_y + 10  # Below the realm name
            details = f"Members: {realm_profile.member_count}\nStatus: Active"
            draw.text(
                (text_x, details_y), details, font=small_font, fill=self.TEXT_COLOR
            )

            # Draw rounded corners for the entire profile card
            mask = Image.new("L", final_image.size, 0)
            corner_radius = 30
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle(
                [(0, 0), final_image.size], radius=corner_radius, fill=255
            )
            final_image.putalpha(mask)

            # Save the image to a buffer
            buffer_output = io.BytesIO()
            final_image.save(buffer_output, format="PNG")
            buffer_output.seek(0)

            # Send the final image as a Discord message
            await interaction.followup.send(
                file=discord.File(buffer_output, "realm_profile_card.png")
            )
            _log.info(f"Successfully generated realm profile card for {realm_name}.")

        except Exception as e:
            _log.error(
                f"Error during realm profile generation for {realm_name}: {e}",
                exc_info=True,
            )
            await interaction.followup.send(
                "An error occurred while generating the realm profile card.",
                ephemeral=True,
            )

    def wrap_text(self, text, font, max_width):
        """
        Wrap text to fit within the max_width.
        """
        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}" if current_line else word
            if font.getbbox(test_line)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines


async def setup(bot):
    await bot.add_cog(RealmProfiles(bot))
