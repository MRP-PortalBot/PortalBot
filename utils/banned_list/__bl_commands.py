# utils/banned_list/__bl_commands.py

import discord
import datetime
from typing import Literal
from discord import app_commands, ui
from discord.ext import commands
from core import database
from core.logging_module import get_log
from core.common import load_config
from core.pagination import paginate_embed

from .__bl_logic import create_ban_embed, send_to_log_channel
from .__bl_views import return_banishblacklistform_modal

_log = get_log(__name__)
config, _ = load_config()


class BannedListCommands(commands.GroupCog, name="banned-list"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post", description="Add a person to the banned list.")
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
        found_user = await self.fetch_user(interaction, discord_id)
        if not found_user:
            return

        view = return_banishblacklistform_modal(
            self.bot, found_user, gamertag, originating_realm, ban_type
        )
        await interaction.response.send_modal(view)

    @app_commands.command(name="search", description="Search the banned list.")
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

        results = []
        for data in databaseData:
            query = database.MRP_Blacklist_Data.select().where(data.contains(search_term))
            if query.exists():
                results.extend(query)

        if not results:
            embed = discord.Embed(
                title="Bannedlist Search",
                description=f"Requested by: {interaction.user.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="No Results!", value=f"No results found for '{search_term}'")
            await interaction.response.send_message(embed=embed)
            return

        total_pages = len(results)

        async def populate_page(embed: discord.Embed, page: int):
            entry = results[page - 1]
            embed.clear_fields()
            embed.add_field(name="🔹 Discord Username", value=f"`{entry.DiscUsername}`", inline=True)
            embed.add_field(name="🔹 Discord ID", value=f"`{entry.DiscID}`", inline=True)
            embed.add_field(name="🎮 Gamertag", value=f"`{entry.Gamertag}`", inline=True)
            embed.add_field(name="🏰 Realm Banned From", value=f"`{entry.BannedFrom}`", inline=True)
            embed.add_field(name="👥 Known Alts", value=f"`{entry.KnownAlts}`", inline=True)
            embed.add_field(name="⚠️ Ban Reason", value=f"`{entry.ReasonforBan}`", inline=False)
            embed.add_field(name="📅 Date of Incident", value=f"`{entry.DateofIncident}`", inline=True)
            embed.add_field(name="⏳ Type of Ban", value=f"`{entry.TypeofBan}`", inline=True)
            embed.add_field(
                name="⌛ Ban End Date",
                value=f"`{entry.DatetheBanEnds or 'Permanent'}`",
                inline=True,
            )
            embed.set_footer(text=f"Entry ID: {entry.entryid} | Page {page}/{total_pages}")
            return embed

        embed = discord.Embed(
            title="Banned User Information",
            description=f"Requested by: {interaction.user.mention}",
            color=discord.Color.red()
        )
        await paginate_embed(self.bot, interaction, embed, populate_page, total_pages)

    @app_commands.command(name="edit", description="Edit a banned list entry.")
    @app_commands.checks.has_role("Realm OP")
    async def edit(
        self,
        interaction: discord.Interaction,
        entry_id: int,
        modify: Literal[
            "Ban Reporter", "Discord Username", "Discord ID", "Gamertag",
            "Realm Banned from", "Known Alts", "Ban Reason",
            "Date of Incident", "Type of Ban", "Ban End Date"
        ],
        new_value: str,
    ):
        query = database.MRP_Blacklist_Data.get_or_none(
            database.MRP_Blacklist_Data.entryid == entry_id
        )

        if not query:
            await interaction.response.send_message(
                "Invalid Entry ID. Please check the ID and try again.", ephemeral=True
            )
            return

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

        if modify in ["Date of Incident", "Ban End Date"]:
            try:
                datetime.datetime.strptime(new_value, "%d-%m-%Y")
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date format. Use DD-MM-YYYY.", ephemeral=True
                )
                return

        old_value = getattr(query, field_mapping[modify])
        setattr(query, field_mapping[modify], new_value)
        query.save()

        await interaction.response.send_message(
            f"✅ Updated **{modify}** from **{old_value}** to **{new_value}** for Entry ID: `{entry_id}`.",
            ephemeral=True,
        )

    async def fetch_user(self, interaction: discord.Interaction, discord_id: str):
        try:
            return await self.bot.fetch_user(discord_id)
        except discord.NotFound:
            await interaction.response.send_message("Invalid Discord ID!", ephemeral=True)
            return None
        except Exception as e:
            _log.error(f"fetch_user error: {e}", exc_info=True)
            await interaction.response.send_message("Error fetching user.", ephemeral=True)
            return None


async def setup(bot):
    await bot.add_cog(BannedListCommands(bot))
    _log.info("✅ BannedListCommands cog loaded.")
