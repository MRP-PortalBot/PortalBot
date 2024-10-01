import discord
import json
from typing import Literal
from discord import app_commands
from discord.ext import commands
from core import database
from core.common import return_banishblacklistform_modal
from core.logging_module import get_log
from core.pagination import paginate_embed 

_log = get_log(__name__)

class BannedlistCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    BL = app_commands.Group(
        name="banned-list",
        description="Manage the posted bannedlist."
    )

    # Helper function to create and send an embed message
    def create_embed(self, title: str, description: str, color=0x18c927):
        e = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        return e

    @BL.command(
        name="post",
        description="Add a person to the banned list"
    )
    @app_commands.describe(
        discord_id="The Discord ID of the user to banish",
        gamertag="The gamertag of the user to banish",
        originating_realm="The realm the user is being banned from",
        ban_type="The type of ban that was applied"
    )
    @app_commands.checks.has_role("Realm OP")
    async def banish_user(
            self,
            interaction: discord.Interaction,
            discord_id: str,
            gamertag: str,
            originating_realm: str,
            ban_type: Literal["Temporary", "Permanent"]
    ):
        """Add a person to the banned list"""
        try:
            found_user = await self.bot.fetch_user(int(discord_id))
        except discord.NotFound:
            await interaction.response.send_message(
                "The Discord ID you provided is invalid!",
                ephemeral=True
            )
            return
        except Exception as e:
            _log.exception(f"Error fetching user: {e}")
            await interaction.response.send_message(
                "An unknown error occurred while checking the Discord ID!",
                ephemeral=True
            )
            return

        view = return_banishblacklistform_modal(self.bot, found_user, gamertag, originating_realm, ban_type)
        await interaction.response.send_modal(view)

    # Searching for a banned user with pagination
    @BL.command(description="Search the banned list")
    @app_commands.describe(
        search_term="The term to search for in the banned list"
    )
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
            database.MRP_Blacklist_Data.BanReporter
        ]
        
        # Collect all query results matching the search term
        results = []
        for data in databaseData:
            query = (database.MRP_Blacklist_Data.select().where(
                data.contains(search_term)))
            
            if query.exists():
                results.extend(query)

        # If no results are found, send a 'No Results' message
        if not results:
            no_results_embed = discord.Embed(
                title="Bannedlist Search",
                description=f"Requested by: {interaction.user.mention}",
                color=0x18c927
            )
            no_results_embed.add_field(
                name="No Results!",
                value=f"No results found for '{search_term}'!"
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
            embed.add_field(name="🔹 Discord Username", value=f"`{page_result.DiscUsername}`", inline=True)
            embed.add_field(name="🔹 Discord ID", value=f"`{page_result.DiscID}`", inline=True)
            embed.add_field(name="🎮 Gamertag", value=f"`{page_result.Gamertag}`", inline=True)
            embed.add_field(name="🏰 Realm Banned From", value=f"`{page_result.BannedFrom}`", inline=True)
            embed.add_field(name="👥 Known Alts", value=f"`{page_result.KnownAlts}`", inline=True)
            embed.add_field(name="⚠️ Ban Reason", value=f"`{page_result.ReasonforBan}`", inline=False)
            embed.add_field(name="📅 Date of Incident", value=f"`{page_result.DateofIncident}`", inline=True)
            embed.add_field(name="⏳ Type of Ban", value=f"`{page_result.TypeofBan}`", inline=True)
            embed.add_field(name="⌛ Ban End Date", value=f"`{page_result.DatetheBanEnds if page_result.DatetheBanEnds else 'Permanent'}`", inline=True)


            # Update the footer with the current page and entry ID
            embed.set_footer(text=f"Entry ID: {page_result.entryid} | Page {page}/{total_pages}")

            return embed

        # Determine total number of pages
        total_pages = len(results)

        # Create the initial embed
        embed = discord.Embed(
            title="Banned User Information",
            description=f"Requested by: {interaction.user.mention}",
            color=0xb10d9f
        )

        # Start paginating the embed with the results
        await paginate_embed(self.bot, interaction, embed, populate_page, total_pages)


    @BL.command(name="edit", description="Edit a banned list entry")
    @app_commands.checks.has_role("Realm OP")
    async def _edit(self, interaction: discord.Interaction, entry_id: int, modify: Literal[
        "Ban Reporter", "Discord Username", "Discord ID", "Gamertag", "Realm Banned from", "Known Alts", "Ban Reason", "Date of Incident", "Type of Ban", "Ban End Date"],
                    new_value: str):
        query = database.MRP_Blacklist_Data.get_or_none(database.MRP_Blacklist_Data.entryid == entry_id)
        if not query:
            await interaction.response.send_message("Invalid Entry ID", ephemeral=True)
            return

        field_mapping = {
            "Ban Reporter": "BanReporter", "Discord Username": "DiscUsername", "Discord ID": "DiscID",
            "Gamertag": "Gamertag", "Realm Banned from": "BannedFrom", "Known Alts": "KnownAlts",
            "Ban Reason": "ReasonforBan", "Date of Incident": "DateofIncident", "Type of Ban": "TypeofBan",
            "Ban End Date": "DatetheBanEnds"
        }

        # Dynamically update the selected field
        setattr(query, field_mapping[modify], new_value)
        query.save()

        await interaction.response.send_message(f"Modified {modify} to {new_value}.")

async def setup(bot):
    await bot.add_cog(BannedlistCMD(bot))
