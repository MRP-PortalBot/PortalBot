import discord
from datetime import datetime, timezone
from urllib.parse import urlsplit
from utils.database import __database as database
from utils.helpers.__logging_module import get_log

_log = get_log("reminder_logic")


async def run_reminder_loop(bot: discord.Client):
    """
    Check and send reminders. Intended to be called by a scheduled task every minute.
    """
    try:
        now = datetime.now()
        due = database.Reminder.select().where(database.Reminder.remind_at <= now)

        for reminder in due:
            user = bot.get_user(int(reminder.user_id))
            if user:
                try:
                    await user.send(
                        f"🔔 Hey {user.mention}, here's your reminder:\n{reminder.message_link}"
                    )
                    _log.info(f"Reminder sent to {user.id}")
                except Exception as e:
                    _log.warning(f"Failed to DM reminder to {user.id}: {e}")
            reminder.delete_instance()

    except Exception as e:
        _log.error(f"Reminder loop error: {e}", exc_info=True)


def build_utility_embed(title, body, *, color=None, url=None, thumbnail=None,
                        image=None, author=None, author_url=None, author_icon=None,
                        footer=None, footer_icon=None, timestamp=None, fields=None):
    if not title.strip() or not body.strip():
        raise ValueError("Title and body cannot be blank.")
    if len(title) > 256 or len(body) > 4096:
        raise ValueError("Title must be at most 256 characters; body at most 4,096.")
    for label, value in (("URL", url), ("Thumbnail", thumbnail), ("Image", image),
                         ("Author URL", author_url), ("Author icon", author_icon),
                         ("Footer icon", footer_icon)):
        if value:
            try:
                parsed = urlsplit(value)
                valid = parsed.scheme in ("https", "http") and parsed.netloc
            except ValueError:
                valid = False
            if not valid:
                raise ValueError(f"{label} must be a full http:// or https:// URL.")
    if (author_url or author_icon) and not author:
        raise ValueError("An author name is required with an author URL or icon.")
    if footer_icon and not footer:
        raise ValueError("Footer text is required with a footer icon.")
    colour = 0x9B59B6
    if color:
        value = color.removeprefix("#").removeprefix("0x")
        if len(value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in value):
            raise ValueError("Color must be a six-digit hex code, for example #9B59B6.")
        colour = int(value, 16)
    date = None
    if timestamp:
        try:
            date = (datetime.now(timezone.utc) if timestamp.lower() == "now"
                    else datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("Timestamp must be 'now' or an ISO date/time, such as 2026-09-09T12:00:00Z.")
    embed = discord.Embed(title=title, description=body, color=colour, url=url, timestamp=date)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if author:
        if len(author) > 256:
            raise ValueError("Author name must be at most 256 characters.")
        embed.set_author(name=author, url=author_url, icon_url=author_icon)
    if footer:
        if len(footer) > 2048:
            raise ValueError("Footer must be at most 2,048 characters.")
        embed.set_footer(text=footer, icon_url=footer_icon)
    if fields:
        lines = [line for line in fields.splitlines() if line.strip()]
        if len(lines) > 25:
            raise ValueError("An embed supports at most 25 fields.")
        for line in lines:
            parts = [part.strip() for part in line.split("|", 2)]
            if len(parts) < 2 or not parts[0] or not parts[1]:
                raise ValueError("Use one field per line: Name | Value | inline (the last part is optional).")
            if len(parts[0]) > 256 or len(parts[1]) > 1024:
                raise ValueError("Field names allow 256 characters; values allow 1,024.")
            if len(parts) == 3 and parts[2].lower() not in ("inline", "true", "false", ""):
                raise ValueError("A field's optional third part must be inline, true, or false.")
            embed.add_field(name=parts[0], value=parts[1],
                            inline=len(parts) == 3 and parts[2].lower() in ("inline", "true"))
    if len(embed) > 6000:
        raise ValueError("The combined embed text must be at most 6,000 characters.")
    return embed
