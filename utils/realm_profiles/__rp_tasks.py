import datetime

import discord
from discord.ext import commands, tasks

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_checkins import (
    build_monthly_checkin_embed,
    find_realm_by_emoji,
    find_realms_by_emojis,
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

        realm_profile = find_realm_by_emoji(payload.emoji)
        if realm_profile is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return

        if not user_can_checkin_realm(member, realm_profile):
            return

        record_realm_checkin(
            realm_profile,
            payload.guild_id,
            member,
            method="reaction",
            message_id=payload.message_id,
        )

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
            message_realms = find_realms_by_emojis(
                [reaction.emoji for reaction in message.reactions]
            )
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
