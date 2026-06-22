# utils/admin_mrp/__admin_realm_management.py

from typing import Optional
import datetime
import io
import re
import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from utils.admin.bot_management.__bm_logic import get_bot_data_for_server

_log = get_log(__name__)
STOP_WORDS = {"the", "a", "an", "smp", "realm", "realms", "server", "room"}


def _safe_int(value: object) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _channel_topic(description: object) -> str:
    text = str(description or "").strip()
    if not text:
        text = "The newest Realm on the Minecraft Realm Portal."
    return text[:1024]


def _normalize_discord_name(value: object) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(value or ""))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _name_tokens(value: object) -> list[str]:
    return [
        token
        for token in _normalize_discord_name(value).split("-")
        if token and token not in STOP_WORDS
    ]


def _candidate_score(realm_name: str, candidate_name: str, suffix: str = "") -> int:
    realm_key = _normalize_discord_name(realm_name)
    candidate_key = _normalize_discord_name(candidate_name)
    if suffix:
        suffix_key = _normalize_discord_name(suffix)
        candidate_key = re.sub(rf"(^|-){re.escape(suffix_key)}($|-)", "-", candidate_key)
        candidate_key = candidate_key.strip("-")

    if not realm_key or not candidate_key:
        return 0
    if candidate_key == realm_key:
        return 100
    if candidate_key.startswith(f"{realm_key}-"):
        return 95
    if realm_key.startswith(f"{candidate_key}-"):
        return 90

    realm_tokens = _name_tokens(realm_name)
    candidate_tokens = _name_tokens(candidate_key)
    if not realm_tokens or not candidate_tokens:
        return 0

    overlap = set(realm_tokens) & set(candidate_tokens)
    if not overlap:
        return 0

    coverage = len(overlap) / len(realm_tokens)
    candidate_coverage = len(overlap) / len(candidate_tokens)
    if coverage >= 0.5 or (len(overlap) >= 2 and candidate_coverage >= 0.67):
        return int(60 + (coverage * 20) + (candidate_coverage * 15))

    return 0


def _best_scored_match(candidates, realm_name: str, suffix: str = ""):
    scored = [
        (_candidate_score(realm_name, candidate.name, suffix), candidate)
        for candidate in candidates
    ]
    scored = [(score, candidate) for score, candidate in scored if score > 0]
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def _find_realm_op_role(guild: discord.Guild, realm_name: str) -> Optional[discord.Role]:
    op_roles = [role for role in guild.roles if "op" in _name_tokens(role.name)]
    return _best_scored_match(op_roles, realm_name, suffix="OP")


def _find_realm_channel(
    guild: discord.Guild, realm_name: str
) -> Optional[discord.TextChannel]:
    category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")
    channels = list(category.text_channels) if category else list(guild.text_channels)

    match = _best_scored_match(channels, realm_name)
    if match:
        return match

    if category:
        fallback_channels = [
            channel
            for channel in guild.text_channels
            if channel.category_id != category.id
        ]
        return _best_scored_match(fallback_channels, realm_name)

    return None


def _upsert_realm_profile_from_application(
    application: "database.RealmApplications",
    channel: discord.TextChannel,
    role: discord.Role,
) -> database.RealmProfile:
    profile, _ = database.RealmProfile.get_or_create(
        realm_name=application.realm_name,
        defaults={
            "discord_id": application.discord_id,
            "discord_name": application.discord_name,
            "emoji": application.emoji,
            "play_style": application.play_style,
            "gamemode": application.gamemode,
            "short_desc": application.short_desc,
            "long_desc": application.long_desc,
            "application_process": application.application_process,
            "admin_team": application.admin_team,
            "members": "",
            "member_count": application.member_count,
            "community_age": application.community_age,
            "world_age": application.world_age,
            "reset_schedule": application.reset_schedule,
            "foreseeable_future": application.foreseeable_future,
            "realm_addons": application.realm_addons,
            "pvp": application.pvp,
            "percent_player_sleep": application.percent_player_sleep,
            "portal_invite": "https://discord.gg/tfQKjFK8x4",
            "channel_id": str(channel.id),
            "op_role_id": str(role.id),
            "checkin": False,
            "archived": False,
        },
    )

    profile.discord_id = application.discord_id
    profile.discord_name = application.discord_name
    profile.emoji = application.emoji
    profile.play_style = application.play_style
    profile.gamemode = application.gamemode
    profile.short_desc = application.short_desc
    profile.long_desc = application.long_desc
    profile.application_process = application.application_process
    profile.admin_team = application.admin_team
    profile.member_count = application.member_count
    profile.community_age = application.community_age
    profile.world_age = application.world_age
    profile.reset_schedule = application.reset_schedule
    profile.foreseeable_future = application.foreseeable_future
    profile.realm_addons = application.realm_addons
    profile.pvp = application.pvp
    profile.percent_player_sleep = application.percent_player_sleep
    profile.channel_id = str(channel.id)
    profile.op_role_id = str(role.id)
    profile.archived = False
    profile.save()

    application.approval = True
    application.save()
    return profile


REALM_APPLICATION_PAGES = [
    [
        {
            "key": "realm_name",
            "label": "Realm Name",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "emoji",
            "label": "Emoji",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "play_style",
            "label": "Play Style",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "gamemode",
            "label": "Game Mode",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "short_description",
            "label": "Short Description",
            "required": True,
            "style": discord.TextStyle.long,
        },
    ],
    [
        {
            "key": "long_description",
            "label": "Long Description",
            "required": True,
            "style": discord.TextStyle.long,
        },
        {
            "key": "application_process",
            "label": "Application Process",
            "required": True,
            "style": discord.TextStyle.long,
        },
        {
            "key": "admin_team",
            "label": "Admin Team",
            "required": True,
            "style": discord.TextStyle.long,
        },
        {
            "key": "member_count",
            "label": "Member Count",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "community_age",
            "label": "Community Age",
            "required": True,
            "style": discord.TextStyle.short,
        },
    ],
    [
        {
            "key": "world_age",
            "label": "World Age",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "reset_schedule",
            "label": "Reset Schedule",
            "required": True,
            "style": discord.TextStyle.short,
        },
        {
            "key": "foreseeable_future",
            "label": "Foreseeable Future",
            "required": True,
            "style": discord.TextStyle.long,
        },
        {
            "key": "realm_addons",
            "label": "Realm Addons",
            "required": True,
            "style": discord.TextStyle.long,
        },
        {
            "key": "pvp",
            "label": "PvP Enabled?",
            "required": True,
            "style": discord.TextStyle.short,
        },
    ],
    [
        {
            "key": "percent_player_sleep",
            "label": "Percent Player Sleep",
            "required": True,
            "style": discord.TextStyle.short,
        },
    ],
]


class RealmApplicationContinueView(ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        page_index: int,
        application_data: dict[str, str],
        user_id: int,
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.page_index = page_index
        self.application_data = application_data
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This realm application belongs to another user.",
                ephemeral=True,
            )
            return False

        return True

    @ui.button(
        label="Continue Application",
        style=discord.ButtonStyle.primary,
    )
    async def continue_application(
        self,
        interaction: discord.Interaction,
        button: ui.Button,
    ):
        modal = RealmApplicationModal(
            bot=self.bot,
            page_index=self.page_index,
            application_data=self.application_data,
            user_id=self.user_id,
        )

        await interaction.response.send_modal(modal)


class RealmApplicationModal(ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        page_index: int = 0,
        application_data: Optional[dict[str, str]] = None,
        user_id: Optional[int] = None,
    ):
        super().__init__(
            title=f"Realm Application {page_index + 1}/{len(REALM_APPLICATION_PAGES)}",
            timeout=None,
        )

        self.bot = bot
        self.page_index = page_index
        self.application_data = application_data or {}
        self.user_id = user_id
        self.inputs: dict[str, ui.TextInput] = {}

        for field in REALM_APPLICATION_PAGES[self.page_index]:
            text_input = ui.TextInput(
                label=field["label"],
                required=field["required"],
                style=field["style"],
                default=self.application_data.get(field["key"]),
            )

            self.inputs[field["key"]] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.user_id is not None and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This realm application belongs to another user.",
                ephemeral=True,
            )
            return

        if self.user_id is None:
            self.user_id = interaction.user.id

        for key, text_input in self.inputs.items():
            self.application_data[key] = str(text_input.value).strip()

        next_page_index = self.page_index + 1

        if next_page_index < len(REALM_APPLICATION_PAGES):
            view = RealmApplicationContinueView(
                bot=self.bot,
                page_index=next_page_index,
                application_data=self.application_data,
                user_id=self.user_id,
            )

            await interaction.response.send_message(
                f"✅ Page {self.page_index + 1} saved. Click below to continue.",
                view=view,
                ephemeral=True,
            )
            return

        await self.finish_application(interaction)

    async def finish_application(self, interaction: discord.Interaction):
        bot_data = get_bot_data_for_server(interaction.guild.id)

        if bot_data is None:
            await interaction.response.send_message(
                "Bot data is not configured for this server.",
                ephemeral=True,
            )
            return

        realm_channel_id = _safe_int(bot_data.realm_channel_response)
        admin_role_id = _safe_int(bot_data.admin_role)

        log_channel = (
            self.bot.get_channel(realm_channel_id) if realm_channel_id else None
        )
        admin_role = (
            interaction.guild.get_role(admin_role_id) if admin_role_id else None
        )

        if log_channel is None:
            await interaction.response.send_message(
                "Realm response channel is not configured correctly.",
                ephemeral=True,
            )
            return

        if admin_role is None:
            await interaction.response.send_message(
                "Admin role is not configured correctly.",
                ephemeral=True,
            )
            return

        member_count = _safe_int(self.application_data.get("member_count"))

        if member_count is None:
            await interaction.response.send_message(
                "Member Count must be a number. Please run `/realm apply` again and enter a number for Member Count.",
                ephemeral=True,
            )
            return

        try:
            _log.info(
                f"Realm application submitted by {interaction.user.display_name} for "
                f"'{self.application_data.get('realm_name', 'Unknown Realm')}'"
            )

            self.save_application(interaction, member_count)
            embed = self.build_embed(interaction.user)

            await log_channel.send(content=admin_role.mention, embed=embed)

            await interaction.response.send_message(
                "✅ Realm application submitted successfully!",
                ephemeral=True,
            )

        except Exception as e:
            _log.exception(f"Error submitting application: {e}")

            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred while submitting your application.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while submitting your application.",
                    ephemeral=True,
                )

    def save_application(
        self,
        interaction: discord.Interaction,
        member_count: int,
    ):
        database.RealmApplications.create(
            discord_id=interaction.user.id,
            discord_name=interaction.user.display_name,
            realm_name=self.application_data.get("realm_name"),
            emoji=self.application_data.get("emoji"),
            play_style=self.application_data.get("play_style"),
            gamemode=self.application_data.get("gamemode"),
            short_desc=self.application_data.get("short_description"),
            long_desc=self.application_data.get("long_description"),
            application_process=self.application_data.get("application_process"),
            admin_team=self.application_data.get("admin_team"),
            member_count=member_count,
            community_age=self.application_data.get("community_age"),
            world_age=self.application_data.get("world_age"),
            reset_schedule=self.application_data.get("reset_schedule"),
            foreseeable_future=self.application_data.get("foreseeable_future"),
            realm_addons=self.application_data.get("realm_addons"),
            pvp=self.application_data.get("pvp"),
            percent_player_sleep=self.application_data.get("percent_player_sleep"),
            approval=False,
        )

    def build_embed(self, user: discord.Member):
        embed = discord.Embed(
            title="Realm Application",
            description=f"**Realm Owner:** {user.mention}",
            color=discord.Color.blurple(),
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="Realm Name",
            value=self.application_data.get("realm_name", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Emoji",
            value=self.application_data.get("emoji", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Play Style",
            value=self.application_data.get("play_style", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Game Mode",
            value=self.application_data.get("gamemode", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Short Description",
            value=self.application_data.get("short_description", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="Long Description",
            value=self.application_data.get("long_description", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="Application Process",
            value=self.application_data.get("application_process", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="Admin Team",
            value=self.application_data.get("admin_team", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="Member Count",
            value=self.application_data.get("member_count", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Community Age",
            value=self.application_data.get("community_age", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="World Age",
            value=self.application_data.get("world_age", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Reset Schedule",
            value=self.application_data.get("reset_schedule", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Foreseeable Future",
            value=self.application_data.get("foreseeable_future", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="Realm Addons",
            value=self.application_data.get("realm_addons", "Not provided"),
            inline=False,
        )
        embed.add_field(
            name="PvP Enabled?",
            value=self.application_data.get("pvp", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Percent Player Sleep",
            value=self.application_data.get("percent_player_sleep", "Not provided"),
            inline=True,
        )
        embed.add_field(
            name="Reaction Codes",
            value="💚 Approve\n💛 More Info Needed\n❤️ Reject",
            inline=False,
        )

        embed.set_footer(
            text=f"Submitted on {datetime.datetime.now().strftime('%Y-%m-%d')}"
        )

        return embed


class AdminRealmManagement(commands.GroupCog, name="realm"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="apply",
        description="Apply for a realm channel (realm owners only).",
    )
    async def apply_for_realm(self, interaction: discord.Interaction):
        modal = RealmApplicationModal(
            bot=self.bot,
            user_id=interaction.user.id,
        )
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="approve_realm",
        description="Approve a submitted realm application and create its channel and role.",
    )
    @app_commands.describe(
        app_number="Application number that corresponds with the realm you're approving."
    )
    @has_admin_level(3)
    async def approve_realm(self, interaction: discord.Interaction, app_number: int):
        await interaction.response.defer(thinking=True)

        guild = interaction.guild
        author = interaction.user

        try:
            q: database.RealmApplications = (
                database.RealmApplications.select()
                .where(database.RealmApplications.entry_id == app_number)
                .get()
            )
        except database.RealmApplications.DoesNotExist:
            return await interaction.followup.send(
                "❌ Application not found with that ID.",
                ephemeral=True,
            )

        log = {
            "RoleCreated": "❌",
            "ChannelCreated": "❌",
            "RoleAssigned": "❌",
            "PermissionsSet": "❌",
            "ProfileSaved": "❌",
            "DMStatus": "❌",
        }

        try:
            role = await guild.create_role(
                name=f"{q.realm_name} OP",
                color=discord.Color.blue(),
                mentionable=True,
            )
            log["RoleCreated"] = "✅"

            category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")

            if category is None:
                raise ValueError("Could not find category named 🎮 Realms & Servers.")

            channel = await category.create_text_channel(f"{q.realm_name}-{q.emoji}")
            log["ChannelCreated"] = "✅"

            welcome_embed = discord.Embed(
                title="Welcome to the MRP!",
                description=(
                    f"{role.mention} Welcome to the Portal! "
                    "You should receive a DM with more info shortly."
                ),
                color=0x4C594B,
            )

            await channel.send(embed=welcome_embed)

            await channel.edit(
                topic=_channel_topic(q.short_desc)
            )

            user = await guild.fetch_member(q.discord_id)
            await user.add_roles(role)
            log["RoleAssigned"] = "✅"

            perms = channel.overwrites_for(role)
            perms.manage_channels = True
            perms.manage_webhooks = True
            perms.manage_messages = True
            await channel.set_permissions(role, overwrite=perms)

            muted = discord.utils.get(guild.roles, name="muted")

            if muted:
                perms_muted = channel.overwrites_for(muted)
                perms_muted.read_messages = False
                perms_muted.send_messages = False
                await channel.set_permissions(muted, overwrite=perms_muted)

            log["PermissionsSet"] = "✅"

            _upsert_realm_profile_from_application(q, channel, role)
            log["ProfileSaved"] = "✅"

            if guild.id == 587495640502763521:
                op_rules = guild.get_channel(683454087206928435)

                if op_rules:
                    await op_rules.send(
                        f"{role.mention}\nPlease agree to the rules to access Realm OP channels."
                    )

                    perms_rules = op_rules.overwrites_for(role)
                    perms_rules.read_messages = True
                    await op_rules.set_permissions(role, overwrite=perms_rules)

            dm_embed = discord.Embed(
                title="Congrats On Your New Realm Channel!",
                description=f"Your new channel: <#{channel.id}>",
                color=0x42F5BC,
            )

            dm_embed.add_field(
                name="Information",
                value=(
                    "You now have moderation privileges in your realm channel. "
                    "You can update the topic, manage messages, and add OPs using "
                    "`/operator manage_operators`.\n\n"
                    "To update your realm listing, keep ]]Realm: XYZ[[ in your topic."
                ),
                inline=False,
            )

            await user.send(embed=dm_embed)
            log["DMStatus"] = "✅"

        except Exception as e:
            _log.error(f"Failed to complete realm approval: {e}", exc_info=True)

        finally:
            summary = discord.Embed(
                title="Realm Approval Summary",
                description=f"Approved by: {author.mention}\nApplication ID: {app_number}",
                color=discord.Color.green(),
            )

            for k, v in log.items():
                summary.add_field(name=k, value=v)

            summary.set_footer(text="Command completed.")
            await interaction.followup.send(embed=summary)

    @app_commands.command(
        name="sync_realm_ids",
        description="Find and save RealmProfile channel and OP role IDs by name.",
    )
    @has_admin_level(3)
    async def sync_realm_ids(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send(
                "❌ This command must be run in a server.",
                ephemeral=True,
            )
            return

        updated = 0
        role_matches = 0
        channel_matches = 0
        missing_roles = []
        missing_channels = []
        report_lines = []

        for profile in database.RealmProfile.select().order_by(
            database.RealmProfile.realm_name
        ):
            changed = False
            role = _find_realm_op_role(guild, profile.realm_name)
            channel = _find_realm_channel(guild, profile.realm_name)

            if role:
                role_matches += 1
                if str(profile.op_role_id) != str(role.id):
                    profile.op_role_id = str(role.id)
                    changed = True
            else:
                missing_roles.append(profile.realm_name)

            if channel:
                channel_matches += 1
                if str(profile.channel_id) != str(channel.id):
                    profile.channel_id = str(channel.id)
                    changed = True
            else:
                missing_channels.append(profile.realm_name)

            if changed:
                profile.save()
                updated += 1

            report_lines.append(
                f"{profile.realm_name}: "
                f"role={role.name if role else '❌'} "
                f"channel={channel.name if channel else '❌'}"
            )

        summary = (
            "✅ Realm ID sync complete.\n"
            f"Profiles updated: {updated}\n"
            f"OP roles matched: {role_matches}\n"
            f"Channels matched: {channel_matches}\n"
            f"Missing OP roles: {len(missing_roles)}\n"
            f"Missing channels: {len(missing_channels)}"
        )

        details = "\n".join(report_lines)
        if len(details) > 1500:
            file = discord.File(
                fp=io.BytesIO(details.encode("utf-8")),
                filename="realm_id_sync_report.txt",
            )
            await interaction.followup.send(summary, file=file, ephemeral=True)
        else:
            await interaction.followup.send(
                f"{summary}\n```text\n{details}\n```",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminRealmManagement(bot))
    _log.info("✅ AdminRealmManagement loaded.")
