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

            # Fetch list of available realms from the database
            realm_names = [realm.realm_name for realm in database.RealmProfile.select()]

            # Check if the provided realm_name is valid
            if realm_name not in realm_names:
                await interaction.followup.send(
                    f"Invalid realm name. Please choose from the following: {', '.join(realm_names)}",
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
            font = ImageFont.truetype(self.FONT_PATH, 40)
            small_font = ImageFont.truetype(self.FONT_PATH, 20)

            # Draw the Realm Logo - Placeholder (top of the image)
            realm_logo = Image.new(
                "RGBA", (200, 200), (255, 0, 0, 255)
            )  # Placeholder red box
            final_image.paste(
                realm_logo,
                (self.PADDING + 20, banner_height - 20),
                realm_logo,
            )

            # Draw the Realm Name (below the logo)
            text_x = self.PADDING + self.AVATAR_SIZE + self.PADDING
            text_y = self.PADDING + banner_height + 10
            draw.text((text_x, text_y), realm_name, font=font, fill=self.TEXT_COLOR)

            # Add any other details (e.g., members, description)
            details_y = text_y + 50  # Below the realm name
            details = "Members: 45\nStatus: Active"
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


async def setup(bot):
    await bot.add_cog(RealmProfiles(bot))
