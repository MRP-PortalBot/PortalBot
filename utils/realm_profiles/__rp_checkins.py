import datetime

import discord
from peewee import IntegrityError

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_logic import has_realm_operator_role

_log = get_log(__name__)


def current_checkin_month(moment: datetime.datetime | None = None) -> str:
    moment = moment or datetime.datetime.utcnow()
    return moment.strftime("%Y-%m")


def display_checkin_month(checkin_month: str | None = None) -> str:
    if not checkin_month:
        return datetime.datetime.utcnow().strftime("%B %Y")
    return datetime.datetime.strptime(checkin_month, "%Y-%m").strftime("%B %Y")


def get_realm_checkin(
    realm_profile: database.RealmProfile,
    guild_id: int | str,
    checkin_month: str | None = None,
) -> database.RealmCheckIn | None:
    return database.RealmCheckIn.get_or_none(
        (database.RealmCheckIn.realm == realm_profile)
        & (database.RealmCheckIn.guild_id == str(guild_id))
        & (
            database.RealmCheckIn.checkin_month
            == (checkin_month or current_checkin_month())
        )
    )


def record_realm_checkin(
    realm_profile: database.RealmProfile,
    guild_id: int | str,
    user: discord.abc.User,
    *,
    method: str,
    message_id: int | str | None = None,
    checkin_month: str | None = None,
) -> tuple[database.RealmCheckIn, bool]:
    checkin_month = checkin_month or current_checkin_month()
    now = datetime.datetime.utcnow()
    defaults = {
        "checked_in_by_id": str(user.id),
        "checked_in_by_name": str(user),
        "method": method,
        "message_id": str(message_id) if message_id else None,
        "checked_in_at": now,
    }

    try:
        checkin, created = database.RealmCheckIn.get_or_create(
            realm=realm_profile,
            guild_id=str(guild_id),
            checkin_month=checkin_month,
            defaults=defaults,
        )
    except IntegrityError:
        checkin = get_realm_checkin(realm_profile, guild_id, checkin_month)
        created = False

    if not created and checkin:
        for field_name, value in defaults.items():
            setattr(checkin, field_name, value)
        checkin.save()

    realm_profile.checkin = True
    realm_profile.last_checkin_at = now
    realm_profile.save(only=[database.RealmProfile.checkin, database.RealmProfile.last_checkin_at])
    return checkin, created


def get_checkin_status(
    guild_id: int | str,
    *,
    include_archived: bool = False,
    checkin_month: str | None = None,
) -> tuple[list[str], list[str]]:
    checkin_month = checkin_month or current_checkin_month()
    query = database.RealmProfile.select().order_by(database.RealmProfile.realm_name)
    if not include_archived:
        query = query.where(database.RealmProfile.archived == False)

    checked_in: list[str] = []
    missing: list[str] = []
    for realm_profile in query:
        checkin = get_realm_checkin(realm_profile, guild_id, checkin_month)
        if checkin:
            checked_in.append(
                f"{realm_profile.emoji} {realm_profile.realm_name} — "
                f"{checkin.checked_in_at.strftime('%Y-%m-%d')} UTC"
            )
        else:
            missing.append(f"{realm_profile.emoji} {realm_profile.realm_name}")
    return checked_in, missing


def find_realm_by_emoji(emoji: discord.PartialEmoji | str) -> database.RealmProfile | None:
    emoji_text = str(emoji)
    matches = list(
        database.RealmProfile.select().where(
            (database.RealmProfile.emoji == emoji_text)
            & (database.RealmProfile.archived == False)
        )
    )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        _log.warning("Multiple active realm profiles use emoji %s", emoji_text)
    return None


async def build_monthly_checkin_embed(
    guild_id: int | str,
    checkin_month: str | None = None,
) -> discord.Embed:
    checkin_month = checkin_month or current_checkin_month()
    checked_in, missing = get_checkin_status(guild_id, checkin_month=checkin_month)
    embed = discord.Embed(
        title=f"🏰 Realm Monthly Check-In — {display_checkin_month(checkin_month)}",
        description=(
            "Realm admins: react to this message with your realm emoji to check in "
            "for the month. You can also use `/realm-profile checkin` as a fallback."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name=f"✅ Checked In ({len(checked_in)})",
        value="\n".join(checked_in)[:1024] or "None yet",
        inline=False,
    )
    embed.add_field(
        name=f"⏳ Waiting On ({len(missing)})",
        value="\n".join(missing)[:1024] or "Everyone is checked in!",
        inline=False,
    )
    embed.set_footer(text="This check-in resets automatically every calendar month.")
    return embed


async def add_realm_reactions(message: discord.Message) -> None:
    query = database.RealmProfile.select().where(database.RealmProfile.archived == False)
    for realm_profile in query:
        emoji = str(realm_profile.emoji or "").strip()
        if not emoji:
            continue
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            _log.warning(
                "Could not add check-in reaction %s for realm %s",
                emoji,
                realm_profile.realm_name,
                exc_info=True,
            )


async def post_monthly_checkin_message(
    guild: discord.Guild,
    bot_data: database.BotData,
    *,
    force: bool = False,
) -> discord.Message | None:
    checkin_month = current_checkin_month()
    if not force and bot_data.last_realm_checkin_posted_month == checkin_month:
        return None

    channel_id = str(bot_data.monthly_checkin_channel or "0")
    if channel_id == "0":
        return None

    channel = guild.get_channel(int(channel_id))
    if channel is None:
        channel = await guild.fetch_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return None

    embed = await build_monthly_checkin_embed(guild.id, checkin_month)
    message = await channel.send(embed=embed)
    await add_realm_reactions(message)

    bot_data.last_realm_checkin_posted_month = checkin_month
    bot_data.save(only=[database.BotData.last_realm_checkin_posted_month])
    return message


def user_can_checkin_realm(member: discord.Member, realm_profile: database.RealmProfile) -> bool:
    return has_realm_operator_role(member, realm_profile.realm_name)
