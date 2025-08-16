from __future__ import annotations
import datetime
import discord
from typing import List, Tuple, Optional
from utils.helpers.__logging_module import get_log
from utils.database import (
    BuildConfig, BuildSeason, BuildEntry, BuildVote, __database as database
)

_log = get_log("build_comp")
SUBMISSION_TAG = "Submission"
WINNER_TAG = "Winner"

# ---------------- helpers ----------------

def get_active_submission_season(guild_id: int) -> Tuple[bool, str, Optional[BuildSeason]]:
    season = (BuildSeason
              .select()
              .where((BuildSeason.guild_id == str(guild_id)) &
                     (BuildSeason.status.in_(("scheduled", "submissions"))))
              .first())
    if not season:
        return False, "No season open for submissions.", None
    now = datetime.datetime.utcnow()
    if not (season.submission_start <= now <= season.submission_end):
        return False, "Submissions are closed.", None
    return True, "", season

def get_active_voting_season(guild_id: int) -> Tuple[bool, str, Optional[BuildSeason]]:
    season = (BuildSeason
              .select()
              .where((BuildSeason.guild_id == str(guild_id)) &
                     (BuildSeason.status.in_(("submissions", "voting"))))
              .first())
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
        exists = BuildEntry.get_or_none(
            (BuildEntry.season == season) & (BuildEntry.user_id == str(user_id))
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
) -> BuildEntry:
    ok, msg, season = get_active_submission_season(guild.id)
    if not ok:
        raise RuntimeError(msg)

    cfg = BuildConfig.get_or_none(BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.submission_forum_id:
        raise RuntimeError("Submission forum not configured.")

    forum = guild.get_channel(int(cfg.submission_forum_id))
    if not isinstance(forum, discord.ForumChannel):
        raise RuntimeError("Configured submission channel is not a ForumChannel.")

    # tag
    sub_tag = next((t for t in forum.available_tags if t.name == SUBMISSION_TAG), None)

    # files
    files = [await a.to_file() for a in images[: season.max_images]]

    idx = BuildEntry.select().where(BuildEntry.season == season).count() + 1
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

    entry = BuildEntry.create(
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
    season = BuildSeason.get_or_none(BuildSeason.id == season_id)
    if not season or season.status != "voting":
        return "Voting is not open."
    entry = BuildEntry.get_or_none((BuildEntry.id == entry_id) & (BuildEntry.season == season))
    if not entry:
        return "That entry is not valid."
    if str(inter.user.id) == entry.user_id:
        return "You cannot vote for your own entry."
    try:
        BuildVote.create(season=season, entry=entry, voter_id=str(inter.user.id))
    except Exception:
        return "You already cast a vote this season."
    return "Your vote has been recorded."

def tally_results(season: BuildSeason):
    vote_counts = {}
    for v in BuildVote.select().where(BuildVote.season == season):
        vote_counts[v.entry_id] = vote_counts.get(v.entry_id, 0) + 1
    entries = list(BuildEntry.select().where(BuildEntry.season == season))
    scored = [(e, vote_counts.get(e.id, 0)) for e in entries]
    scored.sort(key=lambda x: (-x[1], x[0].created_at))  # tie: earlier submission wins
    return scored

async def post_ballot(bot: discord.Client, guild: discord.Guild, season: BuildSeason):
    cfg = BuildConfig.get_or_none(BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.announce_channel_id:
        raise RuntimeError("Announcement channel is not configured.")
    channel = guild.get_channel(int(cfg.announce_channel_id))
    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        raise RuntimeError("Announcement channel is not a text channel.")
    from .__bc_views import make_ballot_view
    desc = (
        f"**Theme:** {season.theme}\n"
        f"Voting closes <t:{int(season.voting_end.timestamp())}:R>.\n"
        f"Click a button to cast your single vote."
    )
    embed = discord.Embed(title="Community Ballot", description=desc, color=discord.Color.blurple())
    view = await make_ballot_view(season)
    await channel.send(embed=embed, view=view)

async def announce_winners(bot: discord.Client, guild: discord.Guild, season: BuildSeason):
    results = tally_results(season)
    cfg = BuildConfig.get_or_none(BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.announce_channel_id:
        return
    channel = guild.get_channel(int(cfg.announce_channel_id))
    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        return
    if not results:
        await channel.send(f"No valid entries for **{season.theme}**.")
        return
    winner, top_votes = results[0]
    total_votes = BuildVote.select().where(BuildVote.season == season).count()
    embed = discord.Embed(
        title=f"Winner — {season.theme}",
        description=f"**Entry ID**: #{int(winner.id)}\n**Votes**: {top_votes}/{total_votes}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Entry link", value=f"https://discord.com/channels/{guild.id}/{winner.thread_id}")
    await channel.send(embed=embed)

    thread = guild.get_channel(int(winner.thread_id))
    if isinstance(thread, discord.Thread):
        parent = thread.parent
        if isinstance(parent, discord.ForumChannel):
            win_tag = next((t for t in parent.available_tags if t.name == WINNER_TAG), None)
            if win_tag:
                try:
                    await thread.edit(applied_tags=[*thread.applied_tags, win_tag])
                except Exception:
                    pass

# ---------------- scheduler ----------------

async def announce(bot: discord.Client, season: BuildSeason, message: str):
    guild = bot.get_guild(int(season.guild_id))
    if not guild:
        return
    cfg = BuildConfig.get_or_none(BuildConfig.guild_id == str(guild.id))
    if not cfg or not cfg.announce_channel_id:
        return
    chan = guild.get_channel(int(cfg.announce_channel_id))
    if isinstance(chan, (discord.TextChannel, discord.Thread)):
        await chan.send(message)

async def process_scheduled_events(bot: discord.Client):
    now = datetime.datetime.utcnow()
    for season in BuildSeason.select():
        try:
            if season.status == "scheduled" and now >= season.submission_start:
                season.status = "submissions"; season.save()
                await announce(bot, season, f"Submissions are open for **{season.theme}**!")

            if season.status == "submissions" and now >= season.submission_end:
                season.status = "voting"; season.save()
                await announce(bot, season, "Submissions closed. Voting is now open!")
                guild = bot.get_guild(int(season.guild_id))
                if guild:
                    await post_ballot(bot, guild, season)

            if season.status == "voting" and now >= season.voting_end:
                season.status = "closed"; season.save()
                guild = bot.get_guild(int(season.guild_id))
                if guild:
                    await announce_winners(bot, guild, season)
                    await announce(bot, season, "Season closed. Thanks for voting!")
        except Exception as e:
            _log.exception(f"Scheduler error for season {season.id}: {e}")
