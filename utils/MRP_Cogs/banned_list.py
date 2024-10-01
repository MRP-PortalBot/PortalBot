import discord
import json
from typing import Literal
from discord import app_commands
from discord.ext import commands
from core import database
from core.common import return_banishblacklistform_modal
from core.logging_module import get_log

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
            database.MRP_Blacklist_Data.BanReporter
        ]
        ResultsGiven = False

        for data in databaseData:
            query = database.MRP_Blacklist_Data.select().where(data.contains(search_term))
            if query.exists():
                for p in query:
                    e = discord.Embed(
                        title="Bannedlist Search",
                        description=f"Requested by {interaction.user.mention}",
                        color=0x18c927
                    )
                    e.add_field(
                        name="Results:",
                        value=f"```autohotkey\nDiscord Username: {p.DiscUsername}\nDiscord ID: {p.DiscID}\nGamertag: {p.Gamertag}\nBanned From: {p.BannedFrom}\nKnown Alts: {p.KnownAlts}\nBan Reason: {p.ReasonforBan}\nDate of Ban: {p.DateofIncident}\nType of Ban: {p.TypeofBan}\nDate the Ban Ends: {p.DatetheBanEnds}\nReported by: {p.BanReporter}\n```",
                        inline=False
                    )
                    e.set_footer(text=f"Querying from MRP_Bannedlist_Data | Entry ID: {p.entryid}")
                    if ResultsGiven:
                        await interaction.followup.send(embed=e)
                    else:
                        await interaction.response.send_message(embed=e)
                        ResultsGiven = True

        if not ResultsGiven:
            e = discord.Embed(
                title="Bannedlist Search",
                description=f"Requested by {interaction.user.mention}",
                color=0x18c927
            )
            e.add_field(
                name="No Results!",
                value=f"`{search_term}`'s query did not bring back any results!"
            )
            await interaction.response.send_message(embed=e)


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
