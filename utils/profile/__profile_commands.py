# utils/profiles/__profile_commands.py

import io
import discord
from discord import app_commands
from discord.ext import commands
from discord import File
from core import database, checks
from core.logging_module import get_log
from core.common import ensure_profile_exists
from .__profile_logic import (
    generate_profile_embed,
    generate_profile_card,
)
from .__profile_views import ProfileEditModal, RealmSelectionView

_log = get_log(__name__)


class ProfileCommands(commands.GroupCog, name="profile"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="view", description="Generate your profile card.")
    async def view(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        member = member or interaction.user

        if ensure_profile_exists(member) is None:
            await interaction.response.send_message(
                "An error occurred while loading your profile.", ephemeral=True
            )
            return

        try:
            await interaction.response.defer()
            file, error = await generate_profile_card(self.bot, interaction, member)
            if file is None:
                await interaction.followup.send(
                    error or "Failed to generate profile card.", ephemeral=True
                )
                return

            await interaction.followup.send(file=file)
        except Exception as e:
            _log.error(
                f"Failed to generate profile card for {member.id}: {e}", exc_info=True
            )
            await interaction.followup.send(
                "Failed to generate profile card.", ephemeral=True
            )

    @app_commands.command(name="embed", description="View your profile as an embed.")
    async def embed(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        member = member or interaction.user

        if ensure_profile_exists(member) is None:
            await interaction.response.send_message(
                "An error occurred while loading the profile.", ephemeral=True
            )
            return

        user_id = str(member.id)
        discordname = f"{member.name}#{member.discriminator}"

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

        embed = await generate_profile_embed(member, interaction.guild.id)
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"No profile found for {member.mention}", ephemeral=True
            )

    @app_commands.command(name="edit", description="Edit your profile details.")
    async def edit(self, interaction: discord.Interaction):
        user = interaction.user
        profile = ensure_profile_exists(user)
        if profile is None:
            await interaction.response.send_message(
                "An error occurred while preparing your profile.", ephemeral=True
            )
            return
        try:
            await interaction.response.send_modal(ProfileEditModal(self.bot, user.id))
        except Exception as e:
            _log.error(
                f"Unexpected error while opening profile modal for {user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "An error occurred while trying to edit your profile.", ephemeral=True
            )

    @app_commands.command(
        name="set_realm", description="Update the realms you are a member or admin of."
    )
    async def set_realm(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Select Your Realms",
                description=(
                    "**🛡️ Realms you are an OP in:**\nUse the first dropdown below to select realms where you're an operator.\n\n"
                    "**🏰 Realms you are a member of:**\nUse the second dropdown to select realms you’ve joined."
                ),
                color=discord.Color.blurple(),
            ),
            view=RealmSelectionView(self.bot, interaction.user.id),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCommands(bot))
    _log.info("✅ ProfileCommands cog loaded.")
