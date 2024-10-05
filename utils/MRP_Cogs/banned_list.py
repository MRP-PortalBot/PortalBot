import discord
import json
import datetime
from typing import Literal
from discord import app_commands, ui
from discord.ext import commands
from core import database
from core.common import load_config
from core.logging_module import get_log
from core.pagination import paginate_embed

# Load configuration
config, _ = load_config()

# Logger setup
_log = get_log(__name__)


# Helper function to create the embed
def create_ban_embed(entry_id, interaction, user_data, config) -> discord.Embed:
    """Creates the embed report for the banned user."""
    embed = discord.Embed(
        title=f"🚫 Banned User Report - {user_data['discord_username']}",
        description=f"This user has been added to the banned list.",
        color=discord.Color.red(),
        timestamp=datetime.datetime.now(),
    )
    embed.set_thumbnail(
        url=config.get(
            "ban_image_url",
            "https://cdn.discordapp.com/attachments/788873229136560140/1290737175666888875/no_entry.png",
        )
    )
    embed.add_field(
        name="🔹 Discord Username",
        value=f"`{user_data['discord_username']}`",
        inline=True,
    )
    embed.add_field(
        name="🔹 Discord ID", value=f"`{user_data['disc_id']}`", inline=True
    )
    embed.add_field(name="🎮 Gamertag", value=f"`{user_data['gamertag']}`", inline=True)
    embed.add_field(
        name="🏰 Realm Banned From",
        value=f"`{user_data['originating_realm']}`",
        inline=True,
    )
    embed.add_field(
        name="👥 Known Alts", value=f"`{user_data['known_alts']}`", inline=True
    )
    embed.add_field(
        name="⚠️ Ban Reason", value=f"`{user_data['reason_for_ban']}`", inline=False
    )
    embed.add_field(
        name="📅 Date of Incident",
        value=f"`{user_data['date_of_ban']}`",
        inline=True,
    )
    embed.add_field(
        name="⏳ Type of Ban", value=f"`{user_data['type_of_ban']}`", inline=True
    )
    embed.add_field(
        name="⌛ Ban End Date",
        value=f"`{user_data['ban_end_date'] or 'Permanent'}`",
        inline=True,
    )

    embed.set_footer(
        text=f"Entry ID: {entry_id} | Reported by {interaction.user.display_name}",
        icon_url=(interaction.user.avatar.url if interaction.user.avatar else None),
    )
    return embed


# Helper function to send embed to the log channel
async def send_to_log_channel(interaction, log_channel, embed):
    """Helper function to send the embed to the log channel."""
    if log_channel:
        await log_channel.send(embed=embed)
        await interaction.followup.send(
            "Banned User Added Successfully", ephemeral=True
        )
        _log.info("Submission process completed successfully.")
    else:
        _log.warning("Log channel not found!")
        await interaction.followup.send("An Error Occurred, Try Again", ephemeral=True)


class BannedlistCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Group for Banned List commands
    BL = app_commands.Group(
        name="banned-list", description="Manage the posted banned list."
    )

    # Helper function to create and send an embed message
    def create_embed(
        self, title: str, description: str, color=0x18C927
    ) -> discord.Embed:
        """Utility to create a styled embed."""
        return discord.Embed(title=title, description=description, color=color)

    async def log_error(self, interaction: discord.Interaction, message: str):
        """Logs an error and sends a message to the user."""
        _log.exception(message)
        await interaction.response.send_message(message, ephemeral=True)

    async def fetch_user(self, interaction: discord.Interaction, discord_id: str):
        """Attempts to fetch a Discord user by ID and handles any errors."""
        try:
            return await self.bot.fetch_user(discord_id)
        except discord.NotFound:
            await interaction.response.send_message(
                "The Discord ID you provided is invalid!", ephemeral=True
            )
            return None
        except Exception as e:
            await self.log_error(interaction, f"Error fetching user: {e}")
            return None

    # Command to add a user to the banned list
    @BL.command(name="post", description="Add a person to the banned list")
    @app_commands.describe(
        discord_id="The Discord ID of the user to banish",
        gamertag="The gamertag of the user to banish",
        originating_realm="The realm the user is being banned from",
        ban_type="The type of ban that was applied",
    )
    @app_commands.checks.has_role("Realm OP")
    async def banish_user(
        self,
        interaction: discord.Interaction,
        discord_id: str,
        gamertag: str,
        originating_realm: str,
        ban_type: Literal["Temporary", "Permanent"],
    ):
        """Command handler to add a user to the banned list."""
        found_user = await self.fetch_user(interaction, discord_id)
        if not found_user:
            return

        view = self.return_banishblacklistform_modal(
            self.bot, found_user, gamertag, originating_realm, ban_type
        )
        await interaction.response.send_modal(view)

    def return_banishblacklistform_modal(
        self,
        bot,
        user: discord.User,
        gamertag: str,
        originating_realm: str,
        type_of_ban: str,
    ):
        class BanishBlacklistForm(ui.Modal, title="Blacklist Form"):
            def __init__(
                self,
                bot,
                user: discord.User,
                gamertag: str,
                originating_realm: str,
                type_of_ban: str,
            ):
                super().__init__(timeout=None)
                self.bot = bot
                self.user = user
                self.gamertag = gamertag
                self.originating_realm = originating_realm
                self.type_of_ban = type_of_ban

            # Input fields
            discord_username = ui.TextInput(
                label="Banished User's Username",
                style=discord.TextStyle.short,
                default=user.name,
                required=True,
            )
            known_alts = ui.TextInput(
                label="Known Alts",
                style=discord.TextStyle.long,
                placeholder="Separate each alt with a comma",
                required=True,
            )
            reason = ui.TextInput(
                label="Reason",
                style=discord.TextStyle.long,
                placeholder="Reason for ban",
                required=True,
            )
            date_of_ban = ui.TextInput(
                label="Date of Ban",
                style=discord.TextStyle.short,
                placeholder="Date of ban",
                required=True,
            )
            ban_end_date = ui.TextInput(
                label="Ban End Date",
                style=discord.TextStyle.short,
                placeholder="Leave blank if permanent",
                default="Permanent",
                required=False,
            )

            async def on_submit(self, interaction: discord.Interaction):
                """Handles form submission for banishing users."""
                try:
                    # Log the start of the submission process
                    _log.info(
                        "Starting the submission process for user: %s",
                        self.discord_username.value,
                    )

                    # Defer response early to avoid timeouts
                    await interaction.response.defer()

                    # Get log channel for the report
                    log_channel = self.bot.get_channel(config["bannedlistChannel"])
                    if not log_channel:
                        raise ValueError("Log channel not found!")

                    # Connect to the database and add the ban report
                    _log.info("Connecting to the database...")
                    database.db.connect(reuse_if_open=True)

                    q = database.MRP_Blacklist_Data.create(
                        BanReporter=interaction.user.display_name,
                        DiscUsername=self.discord_username.value,
                        DiscID=self.user.id,
                        Gamertag=self.gamertag,
                        BannedFrom=self.originating_realm,
                        KnownAlts=self.known_alts.value,
                        ReasonforBan=self.reason.value,
                        DateofIncident=self.date_of_ban.value,
                        TypeofBan=self.type_of_ban,
                        DatetheBanEnds=self.ban_end_date.value,
                    )
                    q.save()
                    _log.info(
                        "Ban report for user %s saved successfully.",
                        self.discord_username.value,
                    )

                    entry_id = q.entryid

                    user_data = {
                        "discord_username": self.discord_username.value,
                        "disc_id": self.user.id,
                        "gamertag": self.gamertag,
                        "originating_realm": self.originating_realm,
                        "known_alts": self.known_alts.value,
                        "reason_for_ban": self.reason.value,
                        "date_of_ban": self.date_of_ban.value,
                        "type_of_ban": self.type_of_ban,
                        "ban_end_date": self.ban_end_date.value,
                    }

                    # Create a more refined embed report
                    bannedlist_embed = create_ban_embed(
                        entry_id, interaction, user_data, config
                    )

                    # Send the embed report to the log channel
                    _log.info("Sending embed report to log channel...")
                    await send_to_log_channel(
                        interaction, log_channel, bannedlist_embed
                    )

                except Exception as e:
                    # Log the error and notify the user
                    _log.error("Error occurred during submission: %s", str(e))
                    await interaction.followup.send(
                        "An error occurred while submitting the report.", ephemeral=True
                    )

                finally:
                    # Close the database connection
                    if not database.db.is_closed():
                        database.db.close()
                    _log.debug("Database connection closed.")

        return BanishBlacklistForm(bot, user, gamertag, originating_realm, type_of_ban)

    # Searching for a banned user with pagination
    @BL.command(description="Search the banned list")
    @app_commands.describe(search_term="The term to search for in the banned list")
    @app_commands.checks.has_role("Realm OP")
    async def search(self, interaction: discord.Interaction, *, search_term: str):
        databaseData = [
            database.MRP_Blacklist_Data.DiscUsername,
            database.MRP_Blacklist_Data.DiscID,
            database.MRP_Blacklist_Data.Gamertag,
            database.MRP_Blacklist_Data.BannedFrom,
            database.MRP_Blacklist_Data.KnownAlts,
            database.MRP_Blacklist_Data.ReasonforBan,
            database.MRP_Blacklist_Data.DateofIncident,
            database.MRP_Blacklist_Data.TypeofBan,
            database.MRP_Blacklist_Data.DatetheBanEnds,
            database.MRP_Blacklist_Data.entryid,
            database.MRP_Blacklist_Data.BanReporter,
        ]

        # Collect all query results matching the search term
        results = []
        for data in databaseData:
            query = database.MRP_Blacklist_Data.select().where(
                data.contains(search_term)
            )

            if query.exists():
                results.extend(query)

        # If no results are found, send a 'No Results' message
        if not results:
            no_results_embed = discord.Embed(
                title="Bannedlist Search",
                description=f"Requested by: {interaction.user.mention}",
                color=0x18C927,
            )
            no_results_embed.add_field(
                name="No Results!", value=f"No results found for '{search_term}'!"
            )
            await interaction.response.send_message(embed=no_results_embed)
            return

        # Paginating banned user data search results (1 user per page)
        async def populate_page(embed: discord.Embed, page: int):
            # Calculate the index for the current page (1 user per page)
            index = page - 1
            page_result = results[index]

            # Clear previous fields in the embed
            embed.clear_fields()

            # Add the current user's data
            embed.add_field(
                name="🔹 Discord Username",
                value=f"`{page_result.DiscUsername}`",
                inline=True,
            )
            embed.add_field(
                name="🔹 Discord ID", value=f"`{page_result.DiscID}`", inline=True
            )
            embed.add_field(
                name="🎮 Gamertag", value=f"`{page_result.Gamertag}`", inline=True
            )
            embed.add_field(
                name="🏰 Realm Banned From",
                value=f"`{page_result.BannedFrom}`",
                inline=True,
            )
            embed.add_field(
                name="👥 Known Alts", value=f"`{page_result.KnownAlts}`", inline=True
            )
            embed.add_field(
                name="⚠️ Ban Reason", value=f"`{page_result.ReasonforBan}`", inline=False
            )
            embed.add_field(
                name="📅 Date of Incident",
                value=f"`{page_result.DateofIncident}`",
                inline=True,
            )
            embed.add_field(
                name="⏳ Type of Ban", value=f"`{page_result.TypeofBan}`", inline=True
            )
            embed.add_field(
                name="⌛ Ban End Date",
                value=f"`{page_result.DatetheBanEnds if page_result.DatetheBanEnds else 'Permanent'}`",
                inline=True,
            )

            # Update the footer with the current page and entry ID
            embed.set_footer(
                text=f"Entry ID: {page_result.entryid} | Page {page}/{total_pages}"
            )

            return embed

        # Determine total number of pages
        total_pages = len(results)

        # Create the initial embed
        embed = discord.Embed(
            title="Banned User Information",
            description=f"Requested by: {interaction.user.mention}",
            color=0xB10D9F,
        )

        # Start paginating the embed with the results
        await paginate_embed(self.bot, interaction, embed, populate_page, total_pages)

    @BL.command(name="edit", description="Edit a banned list entry")
    @app_commands.checks.has_role("Realm OP")
    async def _edit(
        self,
        interaction: discord.Interaction,
        entry_id: int,
        modify: Literal[
            "Ban Reporter",
            "Discord Username",
            "Discord ID",
            "Gamertag",
            "Realm Banned from",
            "Known Alts",
            "Ban Reason",
            "Date of Incident",
            "Type of Ban",
            "Ban End Date",
        ],
        new_value: str,
    ):
        # Fetch the entry from the database
        query = database.MRP_Blacklist_Data.get_or_none(
            database.MRP_Blacklist_Data.entryid == entry_id
        )

        # Check if the entry exists
        if not query:
            await interaction.response.send_message(
                "Invalid Entry ID. Please check the ID and try again.", ephemeral=True
            )
            return

        # Field Mapping for the attribute to update
        field_mapping = {
            "Ban Reporter": "BanReporter",
            "Discord Username": "DiscUsername",
            "Discord ID": "DiscID",
            "Gamertag": "Gamertag",
            "Realm Banned from": "BannedFrom",
            "Known Alts": "KnownAlts",
            "Ban Reason": "ReasonforBan",
            "Date of Incident": "DateofIncident",
            "Type of Ban": "TypeofBan",
            "Ban End Date": "DatetheBanEnds",
        }

        # Check if the field to modify exists in the mapping
        if modify not in field_mapping:
            await interaction.response.send_message(
                "Invalid field selection.", ephemeral=True
            )
            return

        # Additional validation for specific fields (e.g., dates, IDs)
        if modify == "Date of Incident" or modify == "Ban End Date":
            try:
                datetime.datetime.strptime(new_value, "%Y-%m-%d")
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date format. Use YYYY-MM-DD.", ephemeral=True
                )
                return

        # Dynamically update the selected field
        setattr(query, field_mapping[modify], new_value)

        # Save the updated record
        query.save()

        # Send a detailed success message
        await interaction.response.send_message(
            f"Successfully updated **{modify}** to **{new_value}** for Entry ID: {entry_id}.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(BannedlistCMD(bot))
