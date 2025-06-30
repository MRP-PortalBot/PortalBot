# utils/events/__events_logic.py

import discord
from utils.database import __database as database
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


def handle_profile_update(member: discord.Member) -> str:
    """Create or update the user's profile when they join."""
    user_id = str(member.id)
    discordname = f"{member.name}#{member.discriminator}"

    try:
        database.db.connect(reuse_if_open=True)
        profile, created = database.PortalbotProfile.get_or_create(
            DiscordLongID=user_id, defaults={"DiscordName": discordname}
        )
        if created:
            _log.info(f"Profile created for {discordname}")
            return f"{profile.DiscordName}'s profile has been created successfully."
        else:
            profile.DiscordName = discordname
            profile.save()
            _log.info(f"Profile updated for {discordname}")
            return f"{profile.DiscordName}'s profile has been updated successfully."
    finally:
        if not database.db.is_closed():
            database.db.close()
            _log.debug("Database connection closed.")


def build_welcome_embed(guild: discord.Guild, member: discord.Member) -> discord.Embed:
    """Construct the welcome message embed."""
    count = guild.member_count
    embed = discord.Embed(
        title=f"Welcome to {guild.name}!",
        description=f"**{member.mention}** is the **{count}** member!",
        color=0xB10D9F,
    )
    embed.add_field(
        name="Getting Started",
        value="Feel free to introduce yourself and check out the community!",
        inline=False,
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    if guild.icon:
        embed.set_footer(text=f"Welcome to {guild.name}!", icon_url=guild.icon.url)
    return embed
