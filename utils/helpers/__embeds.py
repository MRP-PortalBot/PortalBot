import discord
from utils.core_features.constants import EmbedColors
from data import images


def permission_error_embed():
    return (
        discord.Embed(
            title="Insufficient Permissions",
            description="You don't have the required role or permissions for this command.",
            color=EmbedColors.red,
        )
        .set_thumbnail(url=images.no_entry.png)
        .set_footer(text="Try /help or !help for more info.")
    )


def argument_error_embed(title: str, signature: str):
    return (
        discord.Embed(
            title=title,
            description=f"Usage:\n`{signature}`",
            color=EmbedColors.red,
        )
        .set_thumbnail(url=images.no_entry.png)
        .set_footer(text="Try /help or !help for more info.")
    )


def cooldown_embed(retry_after: float):
    m, s = divmod(retry_after, 60)
    h, m = divmod(m, 60)
    msg = f"Try again in {int(h)}h {int(m)}m {int(s)}s."
    return discord.Embed(
        title="Command On Cooldown",
        description=msg,
        color=EmbedColors.red,
    ).set_footer(text="Use /help to check usage.")
