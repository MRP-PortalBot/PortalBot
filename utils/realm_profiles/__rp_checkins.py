import datetime

import discord
from peewee import IntegrityError

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.realm_profiles.__rp_logic import has_realm_operator_role

_log = get_log(__name__)

REALM_OP_ROLE_ID = 683430456490065959
MAX_REALMS_PER_CHECKIN_POST = 20


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
    realm_profiles: list[database.RealmProfile] | None = None,
) -> tuple[list[str], list[str]]:
    checkin_month = checkin_month or current_checkin_month()
    if realm_profiles is None:
        query = database.RealmProfile.select().order_by(database.RealmProfile.realm_name)
        if not include_archived:
            query = query.where(database.RealmProfile.archived == False)
        realm_profiles = list(query)

    checked_in: list[str] = []
    missing: list[str] = []
    for realm_profile in realm_profiles:
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


def find_realms_by_emojis(
    emojis: list[discord.PartialEmoji | str],
) -> list[database.RealmProfile]:
    realm_profiles: list[database.RealmProfile] = []
    seen_realm_ids: set[int] = set()
    for emoji in emojis:
        realm_profile = find_realm_by_emoji(emoji)
        if realm_profile and realm_profile.entry_id not in seen_realm_ids:
            realm_profiles.append(realm_profile)
            seen_realm_ids.add(realm_profile.entry_id)
    return sorted(realm_profiles, key=lambda realm_profile: realm_profile.realm_name)


def get_active_realm_profiles() -> list[database.RealmProfile]:
    return list(
        database.RealmProfile.select()
        .where(database.RealmProfile.archived == False)
        .order_by(database.RealmProfile.realm_name)
    )


def chunk_realm_profiles(
    realm_profiles: list[database.RealmProfile],
    chunk_size: int = MAX_REALMS_PER_CHECKIN_POST,
) -> list[list[database.RealmProfile]]:
    return [
        realm_profiles[index : index + chunk_size]
        for index in range(0, len(realm_profiles), chunk_size)
    ]


async def build_monthly_checkin_embed(
    guild_id: int | str,
    checkin_month: str | None = None,
    *,
    realm_profiles: list[database.RealmProfile] | None = None,
    post_number: int | None = None,
    total_posts: int | None = None,
) -> discord.Embed:
    checkin_month = checkin_month or current_checkin_month()
    checked_in, missing = get_checkin_status(
        guild_id,
        checkin_month=checkin_month,
        realm_profiles=realm_profiles,
    )
    title = f"🏰 Realm Monthly Check-In — {display_checkin_month(checkin_month)}"
    if post_number and total_posts and total_posts > 1:
        title = f"{title} ({post_number}/{total_posts})"

    embed = discord.Embed(
        title=title,
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


async def add_realm_reactions(
    message: discord.Message,
    realm_profiles: list[database.RealmProfile],
) -> None:
    for realm_profile in realm_profiles:
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
) -> list[discord.Message] | None:
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

    realm_profiles = get_active_realm_profiles()
    profile_batches = chunk_realm_profiles(realm_profiles) or [[]]
    posted_messages: list[discord.Message] = []
    role_ping = f"<@&{REALM_OP_ROLE_ID}>"
    allowed_mentions = discord.AllowedMentions(roles=True)

    for index, profile_batch in enumerate(profile_batches, start=1):
        embed = await build_monthly_checkin_embed(
            guild.id,
            checkin_month,
            realm_profiles=profile_batch,
            post_number=index,
            total_posts=len(profile_batches),
        )
        message = await channel.send(
            content=role_ping if index == 1 else None,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )
        await add_realm_reactions(message, profile_batch)
        posted_messages.append(message)

    bot_data.last_realm_checkin_posted_month = checkin_month
    bot_data.save(only=[database.BotData.last_realm_checkin_posted_month])
    return posted_messages


def user_can_checkin_realm(member: discord.Member, realm_profile: database.RealmProfile) -> bool:
    member_roles = getattr(member, "roles", [])
    if any(str(role.id) == str(REALM_OP_ROLE_ID) for role in member_roles):
        return True
    return has_realm_operator_role(member, realm_profile.realm_name)
