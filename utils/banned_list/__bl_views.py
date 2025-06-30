# utils/banned_list/__bl_views.py

import datetime
import discord
from discord import ui
from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.admin.bot_management.__bm_logic import get_cached_bot_data

from .__bl_logic import create_ban_embed, send_to_log_channel, entry_to_user_data_dict

_log = get_log(__name__)


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

    discord_username = ui.TextInput(
        label="Banished User's Username",
        style=discord.TextStyle.short,
        placeholder="Enter Discord username",
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
        placeholder="DD-MM-YYYY",
        default=datetime.datetime.now().strftime("%d-%m-%Y"),
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
    try:
        await interaction.response.defer()
        bot_data = get_cached_bot_data(interaction.guild.id)
        log_channel = self.bot.get_channel(bot_data.bannedlist_channel)

        # Save to database
        entry = database.MRP_Blacklist_Data.create(
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
        entry.save()

        # Build and send embed
        user_data = entry_to_user_data_dict(entry)
        embed = create_ban_embed(
            entry.entryid,
            interaction,
            user_data,
            get_cached_bot_data(interaction.guild.id).asdict(),
        )

        await send_to_log_channel(interaction, log_channel, embed)

    except Exception as e:
        _log.error(f"Error in blacklist submission: {e}", exc_info=True)
        await interaction.followup.send(
            "❌ Error occurred during submission.", ephemeral=True
        )


def return_banishblacklistform_modal(
    bot, user: discord.User, gamertag: str, originating_realm: str, type_of_ban: str
):
    return BanishBlacklistForm(bot, user, gamertag, originating_realm, type_of_ban)
