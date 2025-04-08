# profile/profile_embed.py

import logging
import discord
from discord import app_commands
from core import database
from core.common import calculate_level, get_user_rank
from core.common import ensure_profile_exists

_log = logging.getLogger(__name__)


def add_embed_commands(group: app_commands.Group):
    @group.command(
        name="embed", description="Displays the profile of a user as an embed."
    )
    async def profile_embed(
        interaction: discord.Interaction, profile: discord.Member = None
    ):
        # Inside the command:
        if ensure_profile_exists(profile) is None:
            await interaction.response.send_message(
                "An error occurred while loading the profile.", ephemeral=True
            )
            return

        if profile is None:
            profile = interaction.user

        guild_id = interaction.guild.id
        user_id = str(profile.id)
        discordname = f"{profile.name}#{profile.discriminator}"

        # --- 🔄 Fallback: Ensure profile exists ---
        try:
            database.db.connect(reuse_if_open=True)
            profile_record, created = database.PortalbotProfile.get_or_create(
                DiscordLongID=user_id, defaults={"DiscordName": discordname}
            )
            if created:
                _log.info(f"Auto-created profile for {discordname} (embed fallback)")
        except Exception as e:
            _log.error(
                f"Failed to auto-create profile for {discordname}: {e}", exc_info=True
            )
            await interaction.response.send_message(
                "An error occurred while loading the profile.", ephemeral=True
            )
            return
        finally:
            if not database.db.is_closed():
                database.db.close()

        # --- Fetch and send embed ---
        embed = await generate_profile_embed(profile, guild_id)
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"No profile found for {profile.mention}", ephemeral=True
            )


async def generate_profile_embed(
    profile: discord.Member, guild_id: int
) -> discord.Embed | None:
    longid = str(profile.id)
    avatar_url = profile.display_avatar.url

    try:
        query = database.PortalbotProfile.get(
            database.PortalbotProfile.DiscordLongID == longid
        )
    except database.PortalbotProfile.DoesNotExist:
        return None

    score_query = database.ServerScores.get_or_none(
        (database.ServerScores.DiscordLongID == longid)
        & (database.ServerScores.ServerID == str(guild_id))
    )
    server_score = score_query.Score if score_query else "N/A"
    level, progress, next_level_score = (
        calculate_level(server_score) if isinstance(server_score, int) else (0, 0, 0)
    )
    rank = get_user_rank(guild_id, profile.id)

    embed = discord.Embed(
        title=f"{profile.display_name}'s Profile",
        description=f"**Profile for {profile.display_name}**",
        color=discord.Color.blurple(),
    )
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Generated with PortalBot")

    embed.add_field(name="👤 Discord Name", value=query.DiscordName, inline=True)
    embed.add_field(name="🆔 Long ID", value=query.DiscordLongID, inline=True)
    embed.add_field(
        name="💬 Server Score",
        value=f"{server_score} / {next_level_score}",
        inline=False,
    )
    embed.add_field(name="🎮 Level", value=f"Level {level}", inline=True)
    embed.add_field(
        name="📈 % to Next Level", value=f"{round(progress * 100, 2)}%", inline=True
    )
    embed.add_field(name="🏆 Server Rank", value=rank, inline=False)

    if query.Timezone != "None":
        embed.add_field(name="🕓 Timezone", value=query.Timezone, inline=False)
    if query.XBOX != "None":
        embed.add_field(name="🎮 XBOX Gamertag", value=query.XBOX, inline=False)
    if query.Playstation != "None":
        embed.add_field(name="🎮 Playstation ID", value=query.Playstation, inline=False)
    if query.Switch != "None":
        embed.add_field(
            name="🎮 Switch Friend Code",
            value=f"{query.Switch} - {query.SwitchNNID}",
            inline=False,
        )
    if query.RealmsJoined != "None":
        embed.add_field(
            name="🏰 Member of Realms", value=query.RealmsJoined, inline=False
        )
    if query.RealmsAdmin != "None":
        embed.add_field(name="🛡️ Admin of Realms", value=query.RealmsAdmin, inline=False)

    return embed
