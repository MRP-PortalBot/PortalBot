import traceback
from typing import Union
import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers.__logging_module import get_log
from utils.core_features.__constants import EmbedColors, BotAssets
from utils.helpers.__embeds import permission_error_embed, argument_error_embed, cooldown_embed
from utils.helpers.__gist import create_gist_from_traceback
from utils.admin.admin_core.__admin_logic import get_permitlist

_log = get_log(__name__)

async def on_command_error_(bot, ctx: commands.Context, error: Exception):
    error = getattr(error, "original", error)
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))
    _log.error(f"Error in command '{getattr(ctx, 'command', None)}': {exception_msg}")

    if getattr(ctx, "command", None) and ctx.command.name == "rule":
        return await ctx.send("No Rule...")

    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.invoked_with
        matches = [c.name for c in bot.commands]
        from difflib import get_close_matches
        close = get_close_matches(cmd, matches)
        if close:
            return await ctx.send(f'Command "{cmd}" not found. Did you mean "{close[0]}"?')
        return await ctx.message.add_reaction("❌")
    if isinstance(error, (commands.MissingRequiredArgument, commands.TooManyArguments)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        return await ctx.send(embed=argument_error_embed("Missing or Extra Arguments", signature))
    if isinstance(error, (commands.MissingPermissions, commands.MissingRole, commands.MissingAnyRole)):
        return await ctx.send(embed=permission_error_embed())
    if isinstance(error, (commands.BadArgument, commands.BadLiteralArgument)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        return await ctx.send(embed=argument_error_embed("Bad Argument", signature))
    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(embed=cooldown_embed(error.retry_after))

    gist_url = await create_gist_from_traceback(exception_msg)
    permitlist = get_permitlist()

    embed = discord.Embed(
        title=("Traceback Detected" if ctx.author.id in permitlist else "An Error Occurred"),
        description=("Traceback details have been attached." if ctx.author.id in permitlist else "An unexpected error occurred. The developers have been notified."),
        color=EmbedColors.red,
    )
    if ctx.author.id in permitlist and gist_url:
        embed.add_field(name="Gist URL", value=gist_url)
    embed.set_footer(text=f"Error: {str(error)}")
    embed.set_thumbnail(url=BotAssets.error_png)
    await ctx.send(embed=embed)

    raise error


async def on_app_command_error_(bot, interaction: discord.Interaction, error: app_commands.AppCommandError):
    error = getattr(error, "original", error)
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))
    _log.error(f"Error in command '{getattr(interaction, 'command', None)}': {exception_msg}")

    if isinstance(error, app_commands.CommandOnCooldown):
        await _send_response(interaction, cooldown_embed(error.retry_after))
        return
    if isinstance(error, app_commands.CheckFailure):
        await _send_response(interaction, "You cannot run this command!", ephemeral=True)
        return
    if isinstance(error, app_commands.CommandNotFound):
        await _send_response(interaction, "That command does not exist.", ephemeral=True)
        return

    gist_url = await create_gist_from_traceback(exception_msg)
    await _notify_error(interaction, error, gist_url)
    raise error


async def _send_response(interaction: discord.Interaction, content: Union[discord.Embed, str], ephemeral=False):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content=content, ephemeral=ephemeral)
    except Exception as e:
        _log.error(f"Error sending response: {e}")


async def _notify_error(interaction: discord.Interaction, error: Exception, gist_url: str):
    permitlist = get_permitlist()
    if interaction.user.id not in permitlist:
        embed = discord.Embed(
            title="Error Detected!",
            description="An unexpected error occurred. The developers have been notified.",
            color=discord.Color.brand_red(),
        )
        embed.add_field(name="Error Message", value="Please double check your command. The developers are investigating.")
    else:
        embed = discord.Embed(
            title="Traceback Detected!",
            description="An error occurred in PortalBot. Traceback details have been attached below.",
            color=EmbedColors.red,
        )
        if gist_url:
            embed.add_field(name="GIST URL", value=gist_url)

    embed.set_footer(text=f"Error: {str(error)}")
    await _send_response(interaction, embed)
