from __future__ import annotations

import datetime
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from . import __bc_logic as logic

_log = get_log("build_comp.commands")

SUBMISSION_TAG = "Submission"
BALLOT_TAG = "Ballot"
WINNER_TAG = "Winner"
NOTIFY_EMOJI = "🏰"  # reaction-role emoji


# ---------------- utilities ----------------

def _get_cfg(guild_id: int) -> Optional[database.BuildConfig]:
    return database.BuildConfig.get_or_none(database.BuildConfig.guild_id == str(guild_id))

async def _get_or_create_announce_role(guild: discord.Guild) -> discord.Role:
    """
    Prefer BuildConfig.announce_role_id; otherwise create a 'Build Comp Notification' role and save it if possible.
    """
    cfg = _get_cfg(guild.id)
    if cfg and getattr(cfg, "announce_role_id", None):
        role = guild.get_role(int(cfg.announce_role_id))
        if role:
            return role
    # Try by name
    role = discord.utils.get(guild.roles, name="Build Comp Notification")
    if role:
        if cfg and hasattr(cfg, "announce_role_id"):
            cfg.announce_role_id = str(role.id)
            cfg.save()
        return role
    # Create it
    role = await guild.create_role(name="Build Comp Notification", mentionable=True, reason="Build competitions notify role")
    if cfg and hasattr(cfg, "announce_role_id"):
        cfg.announce_role_id = str(role.id)
        cfg.save()
    return role


# ------------ Modal for starting a season (single-forum flow) ------------

class StartSeasonModal(ui.Modal, title="Start Build Season"):
    theme = ui.TextInput(label="Theme", placeholder="e.g., Sky Islands", required=True, max_length=100)
    description = ui.TextInput(
        label="Theme Description",
        style=discord.TextStyle.paragraph,
        placeholder="What should builders aim for? Any constraints?",
        required=False,
        max_length=2000,
    )
    start_date = ui.TextInput(label="Start Date (UTC)", placeholder="YYYY-MM-DD or 2025-09-01T14:00:00Z", required=True)
    end_date = ui.TextInput(label="End Date (UTC)", placeholder="YYYY-MM-DD or 2025-09-07T14:00:00Z", required=True)

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @staticmethod
    def _parse_date_utc(text: str, is_end: bool) -> datetime.datetime:
        t = text.strip()
        if len(t) == 10:
            d = datetime.date.fromisoformat(t)
            if is_end:
                dt = datetime.datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=datetime.timezone.utc)
            else:
                dt = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
            return dt.replace(tzinfo=None)
        t = t.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(t)
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send("❌ Use this in a server.", ephemeral=True)

        # Parse dates
        try:
            ss = self._parse_date_utc(str(self.start_date.value), is_end=False)
            se = self._parse_date_utc(str(self.end_date.value), is_end=True)
            if se <= ss:
                return await interaction.followup.send("❌ End date must be after start date.", ephemeral=True)
            vs = se
            ve = se + datetime.timedelta(days=3)
        except Exception as e:
            return await interaction.followup.send(f"❌ Could not parse dates: {e}", ephemeral=True)

        theme = str(self.theme.value).strip()
        desc = (str(self.description.value).strip() or None)

        # Require central forum
        cfg = _get_cfg(guild.id)
        if not cfg or not cfg.submission_forum_id:
            return await interaction.followup.send(
                "❌ Submission/Judging forum not configured. Run `/build config-set-forum`.", ephemeral=True
            )
        forum = guild.get_channel(int(cfg.submission_forum_id))
        if not isinstance(forum, discord.ForumChannel):
            return await interaction.followup.send("❌ Configured submission channel is not a Forum.", ephemeral=True)

        # Ensure tags
        want = {SUBMISSION_TAG, BALLOT_TAG, WINNER_TAG}
        have = {t.name for t in forum.available_tags}
        to_add = list(want - have)
        if to_add:
            try:
                await forum.edit(available_tags=[*forum.available_tags, *[discord.ForumTag(name=n) for n in to_add]])
            except Exception:
                pass

        # Create Season row
        season = database.BuildSeason.create(
            guild_id=str(guild.id),
            theme=theme,
            theme_description=desc,
            submission_start=ss,
            submission_end=se,
            voting_start=vs,
            voting_end=ve,
            status="scheduled",
        )

        # Create pinned season announcement thread
        body = (
            f"**Theme:** {theme}\n"
            f"{desc or ''}\n\n"
            f"**Submissions (UTC):** <t:{int(ss.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>"
            f" → <t:{int(se.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>\n"
            f"**Voting (UTC):** <t:{int(vs.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>"
            f" → <t:{int(ve.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>\n\n"
            f"Use `/build submit` to create your entry."
        )
        ballot_tag = next((t for t in forum.available_tags if t.name == BALLOT_TAG), None)
        created = await forum.create_thread(
            name=f"{theme}",
            content=body,
            applied_tags=[ballot_tag] if ballot_tag else discord.utils.MISSING,
            auto_archive_duration=10080,
            reason=f"Season {season.id} thread",
        )
        season_thread: discord.Thread = created.thread if hasattr(created, "thread") else created
        try:
            await season_thread.edit(pinned=True)
        except Exception:
            pass

        season.season_thread_id = str(season_thread.id) if hasattr(season, "season_thread_id") else None
        try:
            season.save()
        except Exception:
            pass

        # Announce (role + channel optional)
        role = await _get_or_create_announce_role(guild)
        embed = discord.Embed(
            title=f"🏆 New Build Season: {theme}",
            description=desc or "Build a creation that matches the theme.",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Forum Post", value=f"<#{season_thread.id}>", inline=False)
        embed.add_field(
            name="Timeline (UTC)",
            value=(
                f"**Submissions:** <t:{int(ss.replace(tzinfo=datetime.timezone.utc).timestamp())}:F> "
                f"→ <t:{int(se.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>\n"
                f"**Voting:** <t:{int(vs.replace(tzinfo=datetime.timezone.utc).timestamp())}:F> "
                f"→ <t:{int(ve.replace(tzinfo=datetime.timezone.utc).timestamp())}:F>"
            ),
            inline=False,
        )
        destination: discord.abc.Messageable = interaction.channel
        if cfg and getattr(cfg, "announce_channel_id", None):
            ch = guild.get_channel(int(cfg.announce_channel_id))
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                destination = ch
        try:
            await destination.send(content=f"{role.mention} A new build competition has started!", embed=embed)
        except Exception as e:
            _log.warning(f"Announcement send failed: {e}")

        await interaction.followup.send(f"✅ Season created. Pinned post: <#{season_thread.id}>", ephemeral=True)


# ---------------- Cog ----------------

class BuildCommands(commands.Cog):
    """Build competition commands (single-forum flow)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="build", description="Build competition")

    # ---- Configs ----

    @group.command(name="config-set-forum", description="Select the Forum used for submissions & season posts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_set_forum(self, interaction: discord.Interaction, forum_channel: discord.ForumChannel):
        cfg, _ = database.BuildConfig.get_or_create(guild_id=str(interaction.guild_id))
        cfg.submission_forum_id = str(forum_channel.id)
        cfg.save()
        await interaction.response.send_message(
            f"Submission & judging forum set to {forum_channel.mention}.", ephemeral=True
        )

    @group.command(name="config-set-announce", description="(Optional) Set an announcements channel for cross-posts")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_set_announce(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg, _ = database.BuildConfig.get_or_create(guild_id=str(interaction.guild_id))
        cfg.announce_channel_id = str(channel.id)
        cfg.save()
        await interaction.response.send_message(f"Announcements set to {channel.mention}.", ephemeral=True)

    @group.command(name="config-set-announce-role", description="(Optional) Set a role to ping for comp updates")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_set_announce_role(self, interaction: discord.Interaction, role: discord.Role):
        cfg, _ = database.BuildConfig.get_or_create(guild_id=str(interaction.guild_id))
        if hasattr(cfg, "announce_role_id"):
            cfg.announce_role_id = str(role.id)
            cfg.save()
            await interaction.response.send_message(f"Announcement role set to {role.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Heads up: your BuildConfig is missing `announce_role_id` (TextField, null=True).", ephemeral=True
            )

    # ---- Start season (modal) ----
    @group.command(name="start-season", description="Open a modal to start a new season")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start_season(self, interaction: discord.Interaction):
        await interaction.response.send_modal(StartSeasonModal(self.bot))

    # ---- Submit entry (images required) ----
    @group.command(name="submit", description="Submit your build (anonymous)")
    @app_commands.describe(
        caption="Short description",
        world_link="Optional world/schematic link",
        image1="Image 1",
        image2="Image 2",
        image3="Image 3",
        image4="Image 4",
        image5="Image 5",
    )
    async def submit(
        self,
        interaction: discord.Interaction,
        caption: str,
        image1: discord.Attachment,
        world_link: Optional[str] = None,
        image2: Optional[discord.Attachment] = None,
        image3: Optional[discord.Attachment] = None,
        image4: Optional[discord.Attachment] = None,
        image5: Optional[discord.Attachment] = None,
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        ok, msg = logic.user_can_submit(interaction.user.id, interaction.guild_id)
        if not ok:
            return await interaction.followup.send(msg, ephemeral=True)

        images = [a for a in [image1, image2, image3, image4, image5] if a]
        try:
            entry = await logic.create_forum_submission(
                bot=self.bot,
                guild=interaction.guild,
                author=interaction.user,
                caption=caption,
                images=images,
                world_link=world_link,
            )
        except Exception as e:
            return await interaction.followup.send(f"Submission failed: {e}", ephemeral=True)

        await interaction.followup.send(
            f"✅ Submitted. Your anonymous entry is live: "
            f"https://discord.com/channels/{interaction.guild_id}/{entry.thread_id}",
            ephemeral=True,
        )

    # ---- Post rules + reaction role ----
    @group.command(
        name="post-rules",
        description="Post rules/parameters in a channel with a reaction role at the bottom.",
    )
    @app_commands.describe(
        rules_channel="Channel to post the rules in",
        forum_channel="Your central build forum channel",
        discussion_channel="Channel for build competition discussion",
        champion_role="Role awarded to winners (for mention in rules)",
        template_image_1="Optional template image",
        template_image_2="Optional template image",
        max_images="Max images per submission (default 3)",
        chunk_size="Default plot size (e.g., 2x2 chunks)",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def post_rules(
        self,
        interaction: discord.Interaction,
        rules_channel: discord.TextChannel,
        forum_channel: discord.ForumChannel,
        discussion_channel: discord.TextChannel,
        champion_role: Optional[discord.Role] = None,
        template_image_1: Optional[discord.Attachment] = None,
        template_image_2: Optional[discord.Attachment] = None,
        max_images: int = 3,
        chunk_size: str = "2x2",
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send("❌ Use this in a server.", ephemeral=True)

        # Ensure notify role exists
        notify_role = await _get_or_create_announce_role(guild)

        # --- Embed 1: Rules ---
        e1 = discord.Embed(title="Build Competition Rules", color=discord.Color.blurple())
        e1.description = (
            "1. A new competition starts after the previous one ends.\n"
            "2. Submissions are open until staff announces the next competition.\n"
            "3. Community voting runs for **1 week** after submissions close.\n"
            "4. Winner announced after voting concludes.\n"
            f"5. Winner receives the {champion_role.mention if champion_role else '**Build Champion**'} role "
            "and chooses the next theme.\n"
            "6. **Vanilla only** — no mods or texture packs allowed.\n"
            "7. Your build **must follow the theme** to be considered.\n"
            f"8. Default plot size is **{chunk_size} chunks** (unless the theme says otherwise). "
            "Please build on a clearly marked platform so it's easy to count."
        )

        # --- Embed 2: Submissions & Voting ---
        e2 = discord.Embed(title="Build Competition Submissions", color=discord.Color.green())
        e2.description = (
            f"**Post all submissions in:** {forum_channel.mention}\n\n"
            f"**Each person may submit 1 entry per competition.**\n"
            f"1. Attach **up to {max_images} images** of your build.\n"
            "2. Include a short description.\n"
            "3. Put the description and images in the **same post**.\n\n"
            "__**Voting**__\n"
            "• Each person gets **one vote**.\n"
            "• You can vote for **any** entry.\n"
            "• You **cannot** vote more than once."
        )
        e2.add_field(name="Discussion", value=f"Talk about builds in {discussion_channel.mention}", inline=False)

        # Send messages
        msg_rules = await rules_channel.send(embed=e1)
        msg_submit = await rules_channel.send(embed=e2)

        # Template images (optional)
        if template_image_1 or template_image_2:
            files = []
            if template_image_1:
                files.append(await template_image_1.to_file())
            if template_image_2:
                files.append(await template_image_2.to_file())
            await rules_channel.send("World Template images:", files=files)

        # Reaction role notice
        notify_embed = discord.Embed(
            title="Build Competition Notifications",
            description=f"If you want to receive build competition **announcements**, react to this message with {NOTIFY_EMOJI}.",
            color=discord.Color.gold(),
        )
        notify_msg = await rules_channel.send(embed=notify_embed)
        try:
            await notify_msg.add_reaction(NOTIFY_EMOJI)
        except Exception as e:
            _log.info(f"Could not add reaction: {e}")

        # Persist message id/role id if columns exist
        cfg = _get_cfg(guild.id)
        if cfg:
            if hasattr(cfg, "reaction_message_id"):
                cfg.reaction_message_id = str(notify_msg.id)
            if hasattr(cfg, "rules_channel_id"):
                cfg.rules_channel_id = str(rules_channel.id)
            if hasattr(cfg, "discussion_channel_id"):
                cfg.discussion_channel_id = str(discussion_channel.id)
            if hasattr(cfg, "announce_role_id"):
                cfg.announce_role_id = str(notify_role.id)
            try:
                cfg.save()
            except Exception:
                pass

        await interaction.followup.send(f"✅ Rules posted in {rules_channel.mention}.", ephemeral=True)

    # ---- Admin safety valve ----
    @group.command(name="force-open-voting", description="Force voting to open and post the ballot")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def force_open_voting(self, interaction: discord.Interaction):
        season = (
            database.BuildSeason.select()
            .where(
                (database.BuildSeason.guild_id == str(interaction.guild_id))
                & (database.BuildSeason.status == "submissions")
            )
            .order_by(database.BuildSeason.id.desc())
            .first()
        )
        if not season:
            return await interaction.response.send_message("No season in submissions.", ephemeral=True)
        season.status = "voting"
        season.save()
        await logic.post_ballot(self.bot, interaction.guild, season)
        await interaction.response.send_message("Voting opened and ballot posted.", ephemeral=True)

    # Listen for reaction-role add/remove
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or str(payload.emoji) != NOTIFY_EMOJI:
            return
        cfg = _get_cfg(payload.guild_id)
        if not cfg or not getattr(cfg, "reaction_message_id", None) or int(cfg.reaction_message_id) != payload.message_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = None
        if cfg and getattr(cfg, "announce_role_id", None):
            role = guild.get_role(int(cfg.announce_role_id))
        if role is None:
            role = await _get_or_create_announce_role(guild)
        member = guild.get_member(payload.user_id)
        if member and role and role not in member.roles:
            try:
                await member.add_roles(role, reason="Opt-in build comp notifications")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or str(payload.emoji) != NOTIFY_EMOJI:
            return
        cfg = _get_cfg(payload.guild_id)
        if not cfg or not getattr(cfg, "reaction_message_id", None) or int(cfg.reaction_message_id) != payload.message_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = None
        if cfg and getattr(cfg, "announce_role_id", None):
            role = guild.get_role(int(cfg.announce_role_id))
        if role is None:
            role = await _get_or_create_announce_role(guild)
        member = guild.get_member(payload.user_id)
        if member and role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Opt-out build comp notifications")
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(BuildCommands(bot))
    _log.info("✅ BuildCommands (rules + reaction role) registered.")
