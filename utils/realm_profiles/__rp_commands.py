import discord
from discord import app_commands
from discord.ext import commands
from utils.database import __database as database
from utils.database.__database import RealmProfile
from utils.helpers.__checks import has_admin_level
from utils.realm_profiles.__rp_checkins import (
    build_monthly_checkin_embed,
    current_checkin_month,
    display_checkin_month,
    get_checkin_status,
    get_realm_checkin,
    post_monthly_checkin_message,
    record_realm_checkin,
    user_can_checkin_realm,
)
from utils.realm_profiles.__rp_logic import (
    realm_name_autocomplete,
    has_realm_operator_role,
    create_realm_channel_link_view,
)
from utils.realm_profiles.__rp_views import RealmManagerPanel
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class RealmProfileCommands(app_commands.Group, name="realm-profile"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="view", description="View a Realm Profile")
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def view(self, interaction: discord.Interaction, realm_name: str = None):
        """View the details of a Realm Profile, as a card if possible, or fallback to embed."""
        realm_name = realm_name or interaction.channel.name
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)

        if not realm_profile:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )
            return

        try:
            # Defer the response while generating the image
            await interaction.response.defer()

            # Generate the image buffer from your existing generator function
            from utils.realm_profiles.__rp_logic import generate_realm_profile_card

            image_bytes, error = await generate_realm_profile_card(interaction, realm_name)

            if error:
                await interaction.followup.send(error, ephemeral=True)
            else:
                file = discord.File(image_bytes, filename="realm_profile_card.png")
                await interaction.followup.send(
                    file=file,
                    view=create_realm_channel_link_view(
                        realm_profile, interaction.guild_id
                    ),
                    ephemeral=True,
                )

        except Exception as e:
            _log.error(
                f"Error generating realm card for {realm_name}: {e}", exc_info=True
            )
            from utils.realm_profiles.__rp_logic import create_realm_embed

            embed = create_realm_embed(realm_profile)
            await interaction.followup.send(
                embed=embed,
                view=create_realm_channel_link_view(realm_profile, interaction.guild_id),
                ephemeral=True,
            )

    @app_commands.command(name="edit", description="Edit a Realm Profile")
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def open_realm_panel(self, interaction: discord.Interaction, realm_name: str):
        if not has_realm_operator_role(interaction.user, realm_name):
            await interaction.response.send_message(
                f"🚫 You must have the `{realm_name} OP` role to manage this realm.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🔧 Opening management panel for `{realm_name}`.",
            view=RealmManagerPanel(interaction.user, realm_name),
            ephemeral=True,
        )

    @app_commands.command(
        name="checkin",
        description="Fallback command to check in your realm for the current month.",
    )
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def checkin(self, interaction: discord.Interaction, realm_name: str):
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
        if not realm_profile:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )
            return

        if not user_can_checkin_realm(interaction.user, realm_profile):
            await interaction.response.send_message(
                f"🚫 You must have the `{realm_name} OP` role or Realm OP role "
                "to check in this realm.",
                ephemeral=True,
            )
            return

        existing = get_realm_checkin(realm_profile, interaction.guild_id)
        if existing:
            await interaction.response.send_message(
                f"✅ **{realm_name}** is already checked in for "
                f"{display_checkin_month()} "
                f"(last checked in on {existing.checked_in_at:%Y-%m-%d} UTC).",
                ephemeral=True,
            )
            return

        record_realm_checkin(
            realm_profile,
            interaction.guild_id,
            interaction.user,
            method="slash",
        )

        await interaction.response.send_message(
            f"✅ **{realm_name}** has been checked in for {display_checkin_month()}.",
            ephemeral=True,
        )

    @app_commands.command(
        name="checkin-status",
        description="Show realm monthly check-in status.",
    )
    @has_admin_level(3)
    async def checkin_status(
        self,
        interaction: discord.Interaction,
        include_archived: bool = False,
    ):
        checked_in, missing = get_checkin_status(
            interaction.guild_id,
            include_archived=include_archived,
        )
        embed = await build_monthly_checkin_embed(interaction.guild_id)
        embed.color = discord.Color.green() if not missing else discord.Color.orange()

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="reset-checkins",
        description="Reset all realm monthly check-ins.",
    )
    @has_admin_level(3)
    async def reset_checkins(self, interaction: discord.Interaction):
        checkin_month = current_checkin_month()
        deleted = (
            database.RealmCheckIn.delete()
            .where(
                (database.RealmCheckIn.guild_id == str(interaction.guild_id))
                & (database.RealmCheckIn.checkin_month == checkin_month)
            )
            .execute()
        )
        RealmProfile.update(checkin=False, last_checkin_at=None).execute()
        await interaction.response.send_message(
            f"✅ Reset {deleted} realm check-in record(s) for "
            f"{display_checkin_month(checkin_month)}.",
            ephemeral=True,
        )

    @app_commands.command(
        name="post-checkin",
        description="Post this month's realm check-in message now.",
    )
    @has_admin_level(3)
    async def post_checkin(self, interaction: discord.Interaction, force: bool = False):
        if not interaction.guild:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )
        if not bot_data:
            await interaction.response.send_message(
                "❌ BotData not found for this server.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        messages = await post_monthly_checkin_message(
            interaction.guild,
            bot_data,
            force=force,
        )
        if messages is None:
            await interaction.followup.send(
                "ℹ️ This month's check-in message has already been posted. "
                "Run with `force: True` to post another one.",
                ephemeral=True,
            )
            return
        channel_mention = messages[0].channel.mention
        message_count = len(messages)
        await interaction.followup.send(
            f"✅ Posted {message_count} monthly realm check-in message(s) in "
            f"{channel_mention}.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    group = RealmProfileCommands(bot)
    bot.tree.add_command(group)
    _log.info("🧭 RealmProfileCommands slash group registered")
