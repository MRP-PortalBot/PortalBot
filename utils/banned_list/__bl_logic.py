# utils/banned_list/__bl_logic.py

import discord
import datetime
from utils.helpers.logging_module import get_log

_log = get_log(__name__)


def create_ban_embed(entry_id, interaction, user_data, config) -> discord.Embed:
    embed = discord.Embed(
        title=f"🚫 Banned User Report - {user_data['discord_username']}",
        description=f"This user was added to the banned list by {user_data['ban_reporter']}.",
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
        name="📅 Date of Incident", value=f"`{user_data['date_of_ban']}`", inline=True
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
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None,
    )
    return embed


async def send_to_log_channel(interaction, log_channel, embed):
    if log_channel:
        await log_channel.send(embed=embed)
        await interaction.followup.send(
            "Banned User Added Successfully", ephemeral=True
        )
        _log.info("Submission process completed successfully.")
    else:
        _log.warning("Log channel not found!")
        await interaction.followup.send("An Error Occurred, Try Again", ephemeral=True)


def entry_to_user_data_dict(entry) -> dict:
    return {
        "discord_username": entry.DiscUsername,
        "disc_id": entry.DiscID,
        "gamertag": entry.Gamertag,
        "originating_realm": entry.BannedFrom,
        "known_alts": entry.KnownAlts,
        "reason_for_ban": entry.ReasonforBan,
        "date_of_ban": entry.DateofIncident,
        "type_of_ban": entry.TypeofBan,
        "ban_end_date": entry.DatetheBanEnds,
        "ban_reporter": entry.BanReporter,
    }
