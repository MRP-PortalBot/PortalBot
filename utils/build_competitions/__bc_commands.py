from __future__ import annotations
import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers.__logging_module import get_log
from utils.database import BuildConfig, BuildSeason
from .__bc_logic import user_can_submit, create_forum_submission, post_ballot

_log = get_log("build_comp.commands")

class BuildCommands(commands.Cog):
    """All /build commands live here, attached to the top-level group."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(name="build", description="Build competition")

    # ---------------- config ----------------
    @group.command(name="config-set-forum", description="Set the forum used for submissions")
    async def config_set_forum(self, interaction: discord.Interaction, forum_channel: discord.ForumChannel):
        cfg, _ = BuildConfig.get_or_create(guild_id=str(interaction.guild_id))
        cfg.submission_forum_id = str(forum_channel.id)
        cfg.save()
        await interaction.response.send_message(f"Submission forum set to {forum_channel.mention}.", ephemeral=True)

    @group.command(name="config-set-announce", description="Set the announcements channel")
    async def config_set_announce(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg, _ = BuildConfig.get_or_create(guild_id=str(interaction.guild_id))
        cfg.announce_channel_id = str(channel.id)
        cfg.save()
        await interaction.response.send_message(f"Announcements set to {channel.mention}.", ephemeral=True)

    # ---------------- season ----------------
    @group.command(name="start-season", description="Create a season and schedule open/close")
    @app_commands.describe(
        theme="Competition theme",
        submission_start_iso="ISO 8601, e.g. 2025-09-01T14:00:00Z",
        submission_end_iso="ISO 8601",
        voting_start_iso="ISO 8601",
        voting_end_iso="ISO 8601",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start_season(
        self,
        interaction: discord.Interaction,
        theme: str,
        submission_start_iso: str,
        submission_end_iso: str,
        voting_start_iso: str,
        voting_end_iso: str,
    ):
        try:
            ss = datetime.datetime.fromisoformat(submission_start_iso.replace("Z","+00:00")).replace(tzinfo=None)
            se = datetime.datetime.fromisoformat(submission_end_iso.replace("Z","+00:00")).replace(tzinfo=None)
            vs = datetime.datetime.fromisoformat(voting_start_iso.replace("Z","+00:00")).replace(tzinfo=None)
            ve = datetime.datetime.fromisoformat(voting_end_iso.replace("Z","+00:00")).replace(tzinfo=None)
        except Exception:
            return await interaction.response.send_message("Invalid ISO timestamps.", ephemeral=True)

        BuildSeason.create(
            guild_id=str(interaction.guild_id),
            theme=theme,
            submission_start=ss,
            submission_end=se,
            voting_start=vs,
            voting_end=ve,
            status="scheduled",
        )
        await interaction.response.send_message(f"Season created for **{theme}**.", ephemeral=True)

    # ---------------- submit ----------------
    @group.command(name="submit", description="Submit your build (anonymous)")
    @app_commands.describe(
        caption="Short description",
        image1="First image",
        image2="Second image",
        image3="Third image",
        image4="Fourth image",
        image5="Fifth image",
        world_link="Optional world/schematic link",
    )
    async def submit(
        self,
        interaction: discord.Interaction,
        caption: str,
        image1: Optional[discord.Attachment] = None,
        image2: Optional[discord.Attachment] = None,
        image3: Optional[discord.Attachment] = None,
        image4: Optional[discord.Attachment] = None,
        image5: Optional[discord.Attachment] = None,
        world_link: Optional[str] = None,
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        ok, msg = user_can_submit(interaction.user.id, interaction.guild_id)
        if not ok:
            return await interaction.followup.send(msg, ephemeral=True)

        images = [a for a in [image1, image2, image3, image4, image5] if a]
        try:
            entry = await create_forum_submission(
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

    # ---------------- admin safety valve ----------------
    @group.command(name="force-open-voting", description="Force voting to open and post the ballot")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def force_open_voting(self, interaction: discord.Interaction):
        season = (BuildSeason.select()
                  .where((BuildSeason.guild_id == str(interaction.guild_id)) & (BuildSeason.status == "submissions"))
                  .order_by(BuildSeason.id.desc()).first())
        if not season:
            return await interaction.response.send_message("No season in submissions.", ephemeral=True)
        season.status = "voting"; season.save()
        await post_ballot(self.bot, interaction.guild, season)
        await interaction.response.send_message("Voting opened and ballot posted.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BuildCommands(bot))
    _log.info("✅ BuildCommands registered.")
