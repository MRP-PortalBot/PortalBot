"""Live directory. Active profiles are created by the realm approval workflow."""

import asyncio

import discord
from discord.ext import commands, tasks

from utils.database.__database import RealmProfile
from utils.helpers.__logging_module import get_log

DIRECTORY_CHANNEL_ID = 588070315117117440
REALMS_CATEGORY_ID = 587627871216861244
MARKER = "PortalBot realm directory · v1"
APPLICATION_STATUSES = ("Open", "Waitlist", "Closed", "Not specified")
COMMUNITY_TYPES = ("Realm", "Server")
_log = get_log(__name__)


def directory_embeds(profiles, channels):
    """Build sorted entries only for active profiles with a member channel."""
    eligible = []
    for profile in profiles:
        try:
            channel = channels.get(int(profile.channel_id))
        except (TypeError, ValueError):
            continue
        if not profile.archived and channel and channel.category_id == REALMS_CATEGORY_ID:
            eligible.append(profile)
    eligible.sort(key=lambda p: (p.realm_name.strip().casefold(), p.entry_id))
    header = discord.Embed(
        title="Realms & Servers",
        description=(
            "Discover our independently hosted Bedrock communities, listed A–Z.\n"
            "Visit a community's channel to learn more and apply.\n"
            "Listings update automatically from realm profiles."
        ),
        color=0x9B59B6,
    )
    header.set_footer(text=MARKER)
    result = [header]
    for profile in eligible:
        embed = discord.Embed(
            title=f"{profile.emoji or ''} {profile.realm_name}".strip()[:256],
            description=(profile.short_desc or "")[:4096],
            color=0x9B59B6,
        )
        if profile.community_type in COMMUNITY_TYPES:
            embed.add_field(name="Type", value=profile.community_type)
        status = profile.application_status
        embed.add_field(
            name="Applications",
            value=status if status in APPLICATION_STATUSES else "Not specified",
        )
        embed.add_field(name="Channel", value=f"<#{int(profile.channel_id)}>", inline=False)
        embed.set_footer(text=MARKER)
        result.append(embed)
    return result


def owned_message(message, bot_id):
    return (
        message.author.id == bot_id
        and len(message.embeds) == 1
        and message.embeds[0].footer.text == MARKER
    )


def same_embed(left, right):
    # Discord adds serialization metadata; compare just the authored content.
    def content(embed):
        data = embed.to_dict()
        return {key: data.get(key) for key in ("title", "description", "color", "fields", "footer")}
    return content(left) == content(right)


async def reconcile_messages(channel, bot_id, desired):
    # History provides durable recovery after restarts or partially completed syncs.
    # Never adopt or remove legacy messages, even those authored by this bot.
    existing = [
        message async for message in channel.history(limit=None, oldest_first=True)
        if owned_message(message, bot_id)
    ]
    for index, embed in enumerate(desired):
        if index < len(existing):
            message = existing[index]
            if not same_embed(message.embeds[0], embed):
                await message.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        else:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    for message in existing[len(desired):]:
        await message.delete()


class RealmDirectoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self.refresh_directory.start()

    def cog_unload(self):
        self.refresh_directory.cancel()

    async def sync(self):
        async with self._lock:
            channel = self.bot.get_channel(DIRECTORY_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                return False
            try:
                # Fetch channels to avoid removing entries because of a stale cache.
                channels = {c.id: c for c in await channel.guild.fetch_channels()
                            if isinstance(c, discord.TextChannel)}
                profiles = list(RealmProfile.select().where(RealmProfile.archived == False))
                await reconcile_messages(
                    channel, self.bot.user.id, directory_embeds(profiles, channels)
                )
                return True
            except Exception:
                # Leave the loop alive so transient database/API failures retry.
                _log.exception("Realm directory sync failed; will retry automatically.")
                return False

    @tasks.loop(minutes=5)
    async def refresh_directory(self):
        await self.sync()

    @refresh_directory.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_realm_profile_updated(self):
        await self.sync()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        before_category = getattr(before, "category_id", None)
        after_category = getattr(after, "category_id", None)
        if before_category != after_category and REALMS_CATEGORY_ID in (
            before_category, after_category
        ):
            await self.sync()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if getattr(channel, "category_id", None) == REALMS_CATEGORY_ID:
            await self.sync()


async def setup(bot):
    await bot.add_cog(RealmDirectoryCog(bot))
