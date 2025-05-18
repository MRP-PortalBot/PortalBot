# utils/banned_list/__bl_views.py

import datetime
import discord
from discord import ui
from core import database
from core.logging_module import get_log
from core.common import get_cached_bot_data

_log = get_log(__name__)

class BanishBlacklistForm(ui.Modal, title="Blacklist Form"):
    def __init__(self, bot, user: discord.User, gamertag: str, originating_realm: str, type_of_ban: str):
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

            embed = discord.Embed(
                title=f"🚫 Banned User Report - {self.discord_username.value}",
                description=f"This user has been added to the banned list.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/788873229136560140/1290737175666888875/no_entry.png")
            embed.add_field(name="🔹 Discord Username", value=f"`{self.discord_username.value}`", inline=True)
            embed.add_field(name="🔹 Discord ID", value=f"`{self.user.id}`", inline=True)
            embed.add_field(name="🎮 Gamertag", value=f"`{self.gamertag}`", inline=True)
            embed.add_field(name="🏰 Realm Banned From", value=f"`{self.originating_realm}`", inline=True)
            embed.add_field(name="👥 Known Alts", value=f"`{self.known_alts.value}`", inline=True)
            embed.add_field(name="⚠️ Ban Reason", value=f"`{self.reason.value}`", inline=False)
            embed.add_field(name="📅 Date of Incident", value=f"`{self.date_of_ban.value}`", inline=True)
            embed.add_field(name="⏳ Type of Ban", value=f"`{self.type_of_ban}`", inline=True)
            embed.add_field(name="⌛ Ban End Date", value=f"`{self.ban_end_date.value}`", inline=True)
            embed.set_footer(text=f"Entry ID: {q.entryid} | Reported by {interaction.user.display_name}",
                             icon_url=interaction.user.display_avatar.url)

            if log_channel:
                await log_channel.send(embed=embed)
                await interaction.followup.send("✅ Banned User Added Successfully", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ Log channel not found!", ephemeral=True)

        except Exception as e:
            _log.error(f"Error in blacklist submission: {e}", exc_info=True)
            await interaction.followup.send("❌ Error occurred during submission.", ephemeral=True)
