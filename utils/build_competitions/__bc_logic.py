from __future__ import annotations
import datetime
from typing import List, Tuple, Optional

import discord
from utils.helpers.__logging_module import get_log
from utils.database import __database as database

_log = get_log("build_comp.logic")

SUBMISSION_TAG = "Submission"
BALLOT_TAG = "Ballot"
WINNER_TAG = "Winner"


# ---------------- helpers ----------------

def get_active_submission_season(guild_id: int) -> Tuple[bool, str, Optional[database.BuildSeason]]:
    season = (
        database.BuildSeason.select()
        .where(
            (database.BuildSeason.guild_id == str(guild_id))
            & (database.BuildSeason.status.in_(("scheduled", "submissions")))
        )
        .first()
    )
    if not season:
        return False, "No season open for submissions.", None
    now = datetime.datetime.utcnow()
    if not (season.submission_start <= now <= season.submission_end):
        return False, "Submissions are closed.", None
    return True, "", season


def get_active_voting_season(guild_id: int) -> Tuple[bool, str, Optional[database.BuildSeason]]:
    season = (
        database.BuildSeason.select()
        .where(
            (database.BuildSeason.guild_id == str(guild_id))
            & (database.BuildSeason.status.in_(("submissions", "voting")))
        )
        .first()
    )
    if not season:
        return False, "No season available.", None
    now = datetime.datetime.utcnow()
    if not (season.voting_start <= now <= season.voting_end) or season.status != "voting":
        return False, "Voting is not open.", None
    return True, "", season


def user_can_submit(user_id: int, guild_id: int) -> Tuple[bool, str]:
    ok, msg, season = get_active_submission_season(guild_id)
    if not ok:
        return False, msg
    if not season.allow_multiple_entries:
        exists = database.BuildEntry.get_or_none(
            (database.BuildEntry.season == season) & (database.BuildEntry.user_id == str(user_id))
        )
        if exists:
            return False, "You already submitted this season."
    return True, "OK"


# ---------------- submissions ----------------

async def create_forum_submission(
    bot: discord.Client,
    guild: discord.Guild,
    author: discord.User | discord.Member,
    caption: str,
    images: List[discord.Attachment],
    world_link: Optional[str],
) -> database.BuildEntry:
    ok, msg, season = get_active_submission_season(guild.id)
    if not ok:
        raise RuntimeError(msg)

    cfg = database.BuildConfig.get_or_none(database.BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.submission_forum_id:
        raise RuntimeError("Submission forum not configured.")

    forum = guild.get_channel(int(cfg.submission_forum_id))
    if not isinstance(forum, discord.ForumChannel):
        raise RuntimeError("Configured submission channel is not a ForumChannel.")

    # tag
    sub_tag = next((t for t in forum.available_tags if t.name == SUBMISSION_TAG), None)

    # files
    files = [await a.to_file() for a in images[: season.max_images]]

    idx = database.BuildEntry.select().where(database.BuildEntry.season == season).count() + 1
    title = f"Entry #{idx:03d} — {season.theme}"
    body = f"**Caption**: {caption}\n"
    if world_link:
        body += f"**World/Schematic**: {world_link}\n"
    body += "\n*Author is hidden until results are posted.*"

    created = await forum.create_thread(
        name=title,
        content=body,
        files=files if files else discord.utils.MISSING,
        applied_tags=[sub_tag] if sub_tag else discord.utils.MISSING,
        auto_archive_duration=10080,
        reason=f"Build submission by {author} ({author.id})",
    )

    entry = database.BuildEntry.create(
        season=season,
        user_id=str(author.id),
        message_id=str(created.message.id) if created.message else None,
        thread_id=str(created.id),
        caption=caption,
        image_urls="[]",
        world_url=world_link,
    )
    return entry


# ---------------- voting ----------------

async def record_vote(inter: discord.Interaction, season_id: int, entry_id: int) -> str:
    season = database.BuildSeason.get_or_none(database.BuildSeason.id == season_id)
    if not season or season.status != "voting":
        return "Voting is not open."
    entry = database.BuildEntry.get_or_none(
        (database.BuildEntry.id == entry_id) & (database.BuildEntry.season == season)
    )
    if not entry:
        return "That entry is not valid."
    if str(inter.user.id) == entry.user_id:
        return "You cannot vote for your own entry."
    try:
        database.BuildVote.create(season=season, entry=entry, voter_id=str(inter.user.id))
    except Exception:
        return "You already cast a vote this season."
    return "Your vote has been recorded."


def tally_results(season: database.BuildSeason):
    vote_counts: dict[int, int] = {}
    for v in database.BuildVote.select().where(database.BuildVote.season == season):
        vote_counts[v.entry_id] = vote_counts.get(v.entry_id, 0) + 1
    entries = list(database.BuildEntry.select().where(database.BuildEntry.season == season))
    scored = [(e, vote_counts.get(e.id, 0)) for e in entries]
    scored.sort(key=lambda x: (-x[1], x[0].created_at))  # tie: earlier submission wins
    return scored


# ---------------- forum ballot + results (same forum) ----------------

async def post_ballot(bot: discord.Client, guild: discord.Guild, season: database.BuildSeason):
    """Create a Ballot thread inside the submission forum and post the voting buttons."""
    cfg = database.BuildConfig.get_or_none(database.BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.submission_forum_id:
        raise RuntimeError("Submission forum is not configured.")

    forum = guild.get_channel(int(cfg.submission_forum_id))
    if not isinstance(forum, discord.ForumChannel):
        raise RuntimeError("Configured submission channel is not a ForumChannel.")

    # Tags
    ballot_tag = next((t for t in forum.available_tags if t.name == BALLOT_TAG), None)

    # First message content
    ping = ""
    if getattr(cfg, "announce_role_id", None):
        role = guild.get_role(int(cfg.announce_role_id)) if str(cfg.announce_role_id).isdigit() else None
        ping = f"{role.mention} " if role else ""

    desc = (
        f"{ping}**Theme:** {season.theme}\n"
        f"Voting closes <t:{int(season.voting_end.timestamp())}:R>.\n"
        f"Click a button to cast your single vote."
    ).strip()

    # Create the Ballot thread
    created = await forum.create_thread(
        name=f"Ballot — {season.theme}",
        content=desc,
        applied_tags=[ballot_tag] if ballot_tag else discord.utils.MISSING,
        auto_archive_duration=10080,
        reason=f"Ballot opened for season {season.id}",
    )

    # Post the interactive embed with buttons inside the thread
    from .__bc_views import make_ballot_view
    thread = created.thread if hasattr(created, "thread") else created
    embed = discord.Embed(title="Community Ballot", description=desc, color=discord.Color.blurple())
    view = await make_ballot_view(season)
    await thread.send(embed=embed, view=view)

    # Optional: pin the open message
    try:
        if created.message:
            await created.message.pin(reason="Ballot")
    except Exception:
        pass


async def announce_winners(bot: discord.Client, guild: discord.Guild, season: database.BuildSeason):
    """Post results as a reply in the ballot thread and tag the winning entry."""
    results = tally_results(season)
    cfg = database.BuildConfig.get_or_none(database.BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.submission_forum_id:
        return

    forum = guild.get_channel(int(cfg.submission_forum_id))
    if not isinstance(forum, discord.ForumChannel):
        return

    if not results:
        # Post a small results thread if no entries
        content = f"No valid entries for **{season.theme}**."
        try:
            await forum.create_thread(
                name=f"Results — {season.theme}",
                content=content,
                auto_archive_duration=10080,
                reason="Results post (no entries)",
            )
        except Exception:
            pass
        return

    winner, top_votes = results[0]
    total_votes = database.BuildVote.select().where(database.BuildVote.season == season).count()

    # Find the latest ballot thread for this theme
    ballot_tag = next((t for t in forum.available_tags if t.name == BALLOT_TAG), None)
    # Fetch active threads; forum.threads may be limited to active — safe fallback by name
    candidates = [t for t in forum.threads if t.name.startswith("Ballot — ")]
    target_thread: Optional[discord.Thread] = None

    if ballot_tag:
        # prefer tagged
        tagged = [t for t in candidates if ballot_tag in getattr(t, "applied_tags", [])]
        target_thread = tagged[0] if tagged else None

    if not target_thread:
        # fallback: pick most recent by created_at or snowflake time
        def _created(ts: discord.Thread):
            if ts.created_at:
                return ts.created_at
            try:
                return discord.utils.snowflake_time(int(ts.id))
            except Exception:
                return datetime.datetime.utcnow()
        for t in sorted(candidates, key=_created, reverse=True):
            if season.theme in t.name:
                target_thread = t
                break

    ping = ""
    if getattr(cfg, "announce_role_id", None):
        role = guild.get_role(int(cfg.announce_role_id)) if str(cfg.announce_role_id).isdigit() else None
        ping = f"{role.mention} " if role else ""

    embed = discord.Embed(
        title=f"Winner — {season.theme}",
        description=f"**Entry ID**: #{int(winner.id)}\n**Votes**: {top_votes}/{total_votes}",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Entry link", value=f"https://discord.com/channels/{guild.id}/{winner.thread_id}")

    if isinstance(target_thread, discord.Thread):
        await target_thread.send(f"{ping}Results are in! 🏆", embed=embed)
        # Optional: lock the ballot thread
        try:
            await target_thread.edit(locked=True, archived=False)
        except Exception:
            pass
    else:
        # Fallback: create a results thread
        await forum.create_thread(
            name=f"Results — {season.theme}",
            content=f"{ping}Winner posted for **{season.theme}**.\n{embed.description}\n{embed.fields[0].value}",
            auto_archive_duration=10080,
            reason="Results post",
        )

    # Tag the winning entry thread
    entry_thread = guild.get_channel(int(winner.thread_id))
    if isinstance(entry_thread, discord.Thread):
        parent = entry_thread.parent
        if isinstance(parent, discord.ForumChannel):
            win_tag = next((t for t in parent.available_tags if t.name == WINNER_TAG), None)
            if win_tag:
                try:
                    await entry_thread.edit(applied_tags=[*entry_thread.applied_tags, win_tag])
                except Exception:
                    pass


# ---------------- announcements (forum-first; channel optional) ----------------

async def announce(bot: discord.Client, season: database.BuildSeason, message: str):
    guild = bot.get_guild(int(season.guild_id))
    if not guild:
        return
    cfg = database.BuildConfig.get_or_none(database.BuildConfig.guild_id == str(guild.id))

    # Prepend ping if announce role is configured
    content = message
    if cfg and getattr(cfg, "announce_role_id", None):
        role = guild.get_role(int(cfg.announce_role_id)) if str(cfg.announce_role_id).isdigit() else None
        if role:
            content = f"{role.mention} {message}"

    # Prefer announcements channel if configured
    if cfg and cfg.announce_channel_id:
        chan = guild.get_channel(int(cfg.announce_channel_id))
        if isinstance(chan, (discord.TextChannel, discord.Thread)):
            await chan.send(content)
            return

    # Otherwise, post a small update thread in the forum
    if cfg and cfg.submission_forum_id:
        forum = guild.get_channel(int(cfg.submission_forum_id))
        if isinstance(forum, discord.ForumChannel):
            try:
                await forum.create_thread(
                    name=f"Update — {season.theme}",
                    content=content,
                    auto_archive_duration=4320,  # 3 days
                    reason="Season status update",
                )
            except Exception:
                pass


# ---------------- scheduler ----------------

async def process_scheduled_events(bot: discord.Client):
    now = datetime.datetime.utcnow()
    for season in database.BuildSeason.select():
        try:
            if season.status == "scheduled" and now >= season.submission_start:
                season.status = "submissions"
                season.save()
                await announce(bot, season, f"Submissions are open for **{season.theme}**!")

            if season.status == "submissions" and now >= season.submission_end:
                season.status = "voting"
                season.save()
                await announce(bot, season, "Submissions closed. Voting is now open!")
                guild = bot.get_guild(int(season.guild_id))
                if guild:
                    await post_ballot(bot, guild, season)

            if season.status == "voting" and now >= season.voting_end:
                season.status = "closed"
                season.save()
                guild = bot.get_guild(int(season.guild_id))
                if guild:
                    await announce_winners(bot, guild, season)
                    await announce(bot, season, "Season closed. Thanks for voting!")
        except Exception as e:
            _log.exception(f"Scheduler error for season {season.id}: {e}")
