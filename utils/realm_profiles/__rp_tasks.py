import datetime

import discord
from discord.ext import commands, tasks

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_checkins import (
    MAX_REALMS_PER_CHECKIN_POST,
    build_monthly_checkin_embed,
    find_realm_by_emoji,
    get_active_realm_profiles,
    get_realm_profiles_from_embed,
    post_monthly_checkin_message,
    record_realm_checkin,
    user_can_checkin_realm,
)

_log = get_log(__name__)


class RealmCheckInCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.monthly_checkin_poster.start()

    def cog_unload(self):
        self.monthly_checkin_poster.cancel()

    @tasks.loop(hours=1)
    async def monthly_checkin_poster(self):
        now = datetime.datetime.utcnow()
        if now.day != 1:
            return

        for guild in self.bot.guilds:
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(guild.id)
            )
            if not bot_data:
                continue

            try:
                await post_monthly_checkin_message(guild, bot_data)
            except (discord.Forbidden, discord.HTTPException, ValueError):
                _log.warning(
                    "Could not post monthly realm check-in for guild %s",
                    guild.id,
                    exc_info=True,
                )

    @monthly_checkin_poster.before_loop
    async def before_monthly_checkin_poster(self):
        await self.bot.wait_until_ready()

    async def _resolve_member(
        self,
        guild: discord.Guild,
        user: discord.abc.User,
        payload_member: discord.Member | None = None,
    ) -> discord.Member | None:
        if isinstance(payload_member, discord.Member):
            return payload_member

        member = guild.get_member(user.id)
        if member:
            return member

        try:
            return await guild.fetch_member(user.id)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            _log.warning(
                "Could not resolve member %s for realm check-in reaction.",
                user.id,
                exc_info=True,
            )
            return None

    def _is_monthly_checkin_message(self, message: discord.Message) -> bool:
        return bool(
            message.embeds
            and message.embeds[0].title
            and "Realm Monthly Check-In" in message.embeds[0].title
        )

    def _get_message_realms(self, message: discord.Message):
        active_realms = get_active_realm_profiles()
        if len(active_realms) <= MAX_REALMS_PER_CHECKIN_POST:
            return active_realms
        if message.embeds:
            return get_realm_profiles_from_embed(message.embeds[0])
        return []

    async def _sync_checkin_reactions(
        self,
        guild: discord.Guild,
        message: discord.Message,
        payload_member: discord.Member | None = None,
    ) -> int:
        checked_in_count = 0
        for reaction in message.reactions:
            realm_profile = find_realm_by_emoji(reaction.emoji)
            if realm_profile is None:
                continue

            async for user in reaction.users():
                if user.id == self.bot.user.id or getattr(user, "bot", False):
                    continue

                member = await self._resolve_member(
                    guild,
                    user,
                    payload_member if user.id == getattr(payload_member, "id", None) else None,
                )
                if member is None:
                    continue

                if not user_can_checkin_realm(member, realm_profile):
                    _log.info(
                        "Ignoring check-in reaction from %s for %s: missing realm OP access.",
                        member,
                        realm_profile.realm_name,
                    )
                    continue

                record_realm_checkin(
                    realm_profile,
                    guild.id,
                    member,
                    method="reaction",
                    message_id=message.id,
                )
                checked_in_count += 1

        return checked_in_count

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id or payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(payload.guild_id)
        )
        if (
            not bot_data
            or str(payload.channel_id) != str(bot_data.monthly_checkin_channel)
        ):
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await guild.fetch_channel(payload.channel_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
            if not self._is_monthly_checkin_message(message):
                return

            await self._sync_checkin_reactions(
                guild,
                message,
                getattr(payload, "member", None),
            )
            message_realms = self._get_message_realms(message)
            await message.edit(
                embed=await build_monthly_checkin_embed(
                    guild.id,
                    realm_profiles=message_realms or None,
                )
            )
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            _log.warning(
                "Could not update monthly check-in message %s",
                payload.message_id,
                exc_info=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(RealmCheckInCog(bot))
    _log.info("📅 Realm monthly check-in scheduler loaded.")
