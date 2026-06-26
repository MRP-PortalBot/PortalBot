<<<<<<< ours
import datetime
=======
>>>>>>> theirs
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import __database as database
from utils.database.__database import RealmProfile
from utils.helpers.__checks import has_admin_level
<<<<<<< ours
=======
from utils.realm_profiles.__rp_checkins import (
    build_monthly_checkin_embed,
    current_checkin_month,
    display_checkin_month,
    get_checkin_status,
    get_realm_checkin,
    post_monthly_checkin_message,
    record_realm_checkin,
)
>>>>>>> theirs
from utils.realm_profiles.__rp_logic import (
    realm_name_autocomplete,
    has_realm_operator_role,
    create_realm_channel_link_view,
)
from utils.realm_profiles.__rp_views import RealmManagerPanel
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


def _current_month_bounds() -> tuple[datetime.datetime, datetime.datetime]:
    """Return UTC datetime bounds for the current calendar month."""
    now = datetime.datetime.utcnow()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return start, next_month


def _format_checkin_month(moment: datetime.datetime | None = None) -> str:
    moment = moment or datetime.datetime.utcnow()
    return moment.strftime("%B %Y")


def _has_current_month_checkin(realm_profile: RealmProfile) -> bool:
    start, next_month = _current_month_bounds()
    last_checkin_at = realm_profile.last_checkin_at
    return bool(
        realm_profile.checkin
        and last_checkin_at
        and start <= last_checkin_at < next_month
    )


def _refresh_monthly_checkin_state() -> int:
    """
    Clear stale check-in flags from previous months.

    Returns the number of realm profiles that were updated.
    """
    updated = 0
    for realm_profile in RealmProfile.select().where(RealmProfile.checkin == True):
        if not _has_current_month_checkin(realm_profile):
            realm_profile.checkin = False
            realm_profile.save(only=[RealmProfile.checkin])
            updated += 1
    return updated


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
<<<<<<< ours
        description="Check in your realm for the current month.",
=======
        description="Fallback command to check in your realm for the current month.",
>>>>>>> theirs
    )
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    async def checkin(self, interaction: discord.Interaction, realm_name: str):
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
        if not realm_profile:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )
            return

        if not has_realm_operator_role(interaction.user, realm_name):
            await interaction.response.send_message(
                f"🚫 You must have the `{realm_name} OP` role to check in this realm.",
                ephemeral=True,
            )
            return

<<<<<<< ours
        if _has_current_month_checkin(realm_profile):
            checked_at = realm_profile.last_checkin_at.strftime("%Y-%m-%d")
            await interaction.response.send_message(
                f"✅ **{realm_name}** is already checked in for {_format_checkin_month()} "
                f"(last checked in on {checked_at} UTC).",
=======
        existing = get_realm_checkin(realm_profile, interaction.guild_id)
        if existing:
            await interaction.response.send_message(
                f"✅ **{realm_name}** is already checked in for "
                f"{display_checkin_month()} "
                f"(last checked in on {existing.checked_in_at:%Y-%m-%d} UTC).",
>>>>>>> theirs
                ephemeral=True,
            )
            return

<<<<<<< ours
        now = datetime.datetime.utcnow()
        realm_profile.checkin = True
        realm_profile.last_checkin_at = now
        realm_profile.save(only=[RealmProfile.checkin, RealmProfile.last_checkin_at])

        await interaction.response.send_message(
            f"✅ **{realm_name}** has been checked in for {_format_checkin_month(now)}.",
=======
        record_realm_checkin(
            realm_profile,
            interaction.guild_id,
            interaction.user,
            method="slash",
        )

        await interaction.response.send_message(
            f"✅ **{realm_name}** has been checked in for {display_checkin_month()}.",
>>>>>>> theirs
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
<<<<<<< ours
        cleared = _refresh_monthly_checkin_state()
        query = RealmProfile.select().order_by(RealmProfile.realm_name)
        if not include_archived:
            query = query.where(RealmProfile.archived == False)

        checked_in: list[str] = []
        missing: list[str] = []
        for realm_profile in query:
            line = realm_profile.realm_name
            if realm_profile.last_checkin_at:
                line += f" — {realm_profile.last_checkin_at.strftime('%Y-%m-%d')} UTC"
            if _has_current_month_checkin(realm_profile):
                checked_in.append(line)
            else:
                missing.append(line)

        embed = discord.Embed(
            title=f"Realm Check-In Status — {_format_checkin_month()}",
            color=discord.Color.green() if not missing else discord.Color.orange(),
        )
        embed.description = (
            "Realm admins should use `/realm-profile checkin` once per month."
        )
        if cleared:
            embed.set_footer(text=f"Cleared {cleared} stale check-in flag(s).")
        embed.add_field(
            name=f"✅ Checked In ({len(checked_in)})",
            value="\n".join(checked_in)[:1024] or "None",
            inline=False,
        )
        embed.add_field(
            name=f"❌ Missing ({len(missing)})",
            value="\n".join(missing)[:1024] or "None",
            inline=False,
        )
=======
        checked_in, missing = get_checkin_status(
            interaction.guild_id,
            include_archived=include_archived,
        )
        embed = await build_monthly_checkin_embed(interaction.guild_id)
        embed.color = discord.Color.green() if not missing else discord.Color.orange()
>>>>>>> theirs

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="reset-checkins",
        description="Reset all realm monthly check-ins.",
    )
    @has_admin_level(3)
    async def reset_checkins(self, interaction: discord.Interaction):
<<<<<<< ours
        updated = RealmProfile.update(checkin=False).execute()
        await interaction.response.send_message(
            f"✅ Reset check-in status for {updated} realm profile(s).",
=======
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
        message = await post_monthly_checkin_message(
            interaction.guild,
            bot_data,
            force=force,
        )
        if message is None:
            await interaction.followup.send(
                "ℹ️ This month's check-in message has already been posted. "
                "Run with `force: True` to post another one.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            f"✅ Posted the monthly realm check-in message in {message.channel.mention}.",
>>>>>>> theirs
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    group = RealmProfileCommands(bot)
    bot.tree.add_command(group)
    _log.info("🧭 RealmProfileCommands slash group registered")
