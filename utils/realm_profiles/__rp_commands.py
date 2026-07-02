import discord
from discord import app_commands
from discord.ext import commands

from utils.database import __database as database
from utils.database.__database import RealmProfile
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_checkins import (
    current_checkin_month,
    display_checkin_month,
    get_checkin_status,
    get_realm_checkin,
    post_monthly_checkin_message,
    record_realm_checkin,
    realm_profile_is_checked_in,
    user_can_checkin_realm,
)
from utils.realm_profiles.__rp_logic import (
    create_realm_channel_link_view,
    has_realm_operator_role,
    realm_name_autocomplete,
)
from utils.realm_profiles.__rp_views import RealmManagerPanel

_log = get_log(__name__)


def _chunk_field_lines(lines: list[str], limit: int = 1024) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or ["None"]


def _format_op_role(realm_profile: RealmProfile) -> str:
    role_id = str(realm_profile.op_role_id or "0")
    if role_id != "0":
        return f"<@&{role_id}>"
    return f"`{realm_profile.realm_name} OP`"


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
            await interaction.response.defer()

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
        name="assign-owner",
        description="Assign the stored owner for a realm profile.",
    )
    @app_commands.autocomplete(realm_name=realm_name_autocomplete)
    @has_admin_level(3)
    async def assign_owner(
        self,
        interaction: discord.Interaction,
        realm_name: str,
        owner: discord.Member,
    ):
        realm_profile = RealmProfile.get_or_none(RealmProfile.realm_name == realm_name)
        if not realm_profile:
            await interaction.response.send_message(
                f"No profile found for realm '{realm_name}'", ephemeral=True
            )
            return

        realm_profile.discord_name = owner.name
        realm_profile.discord_id = str(owner.id)
        realm_profile.save(only=[RealmProfile.discord_name, RealmProfile.discord_id])

        await interaction.response.send_message(
            f"✅ Realm owner for **{realm_name}** set to "
            f"`{owner.name}` (`{owner.id}`).",
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
                f"🚫 You must have the `{realm_name} OP` role to check in this realm.",
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
        checkin_month = current_checkin_month()
        checked_in, missing = get_checkin_status(
            interaction.guild_id,
            include_archived=include_archived,
            checkin_month=checkin_month,
        )
        query = RealmProfile.select().order_by(RealmProfile.realm_name)
        if not include_archived:
            query = query.where(RealmProfile.archived == False)

        embed = discord.Embed(
            title=f"Realm Check-In Summary — {display_checkin_month(checkin_month)}",
            color=discord.Color.green() if not missing else discord.Color.orange(),
        )
        embed.description = (
            f"Checked in: **{len(checked_in)}**\n"
            f"Missing: **{len(missing)}**\n"
            f"Total shown: **{len(checked_in) + len(missing)}**"
        )

        detail_lines: list[str] = []
        for realm_profile in query:
            checkin = get_realm_checkin(
                realm_profile,
                interaction.guild_id,
                checkin_month,
            )
            checked = realm_profile_is_checked_in(realm_profile, checkin_month)
            status = "Checked in" if checked else "Missing"
            op_role = _format_op_role(realm_profile)
            last_seen = (
                f"{realm_profile.last_checkin_at:%Y-%m-%d} UTC"
                if realm_profile.last_checkin_at
                else "Never"
            )
            actor = checkin.checked_in_by_name if checkin else "None"
            method = checkin.method if checkin else "None"
            archived = " archived" if realm_profile.archived else ""
            detail_lines.append(
                f"{realm_profile.emoji} **{realm_profile.realm_name}**{archived}: "
                f"{status}\n"
                f"OP: {op_role} | Last: {last_seen} | By: {actor} | Method: {method}"
            )

        for index, chunk in enumerate(_chunk_field_lines(detail_lines), start=1):
            field_name = "Realm Details" if index == 1 else f"Realm Details {index}"
            embed.add_field(name=field_name, value=chunk, inline=False)

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
