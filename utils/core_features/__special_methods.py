from __future__ import annotations

import json
import os
import traceback
import asyncio
from datetime import datetime
from difflib import get_close_matches
from typing import TYPE_CHECKING, Union

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import __database as database
from utils.admin.bot_management.__bm_logic import (
    get_bot_data_for_server
)
from utils.core_features.__constants import ConsoleColors, EmbedColors, BotAssets, Dev
from utils.helpers.__logging_module import get_log
from utils.helpers.__embeds import (
    permission_error_embed,
    argument_error_embed,
    cooldown_embed,
)
from utils.helpers.__gist import create_gist_from_traceback

if TYPE_CHECKING:
    from main import PortalBot

_log = get_log(__name__)


def get_permitlist() -> list[int]:
    """
    Returns a hardcoded list of developer IDs with permission to view full tracebacks.
    """
    return [
        306070011028439041,  # Your dev ID
        1064878683823605851,  # Secondary admin/dev
        1158653259171659797,  # PortalBot
    ]

async def on_ready_(bot: "PortalBot"):
    now = datetime.now()
    _log.info(f"Bot ready at {now}. Preloading bot data for guilds.")
    await preload_bot_data(bot)

    for guild in bot.guilds:
        bot_data = get_bot_data_for_server(guild.id)
        if not bot_data:
            _log.warning(f"Bot data not found for guild {guild.id}. Skipping views.")
            continue
        initialize_persistent_views(bot, bot_data)

    database_source = "External" if not os.getenv("USEREAL") else "localhost"
    db_color = (
        ConsoleColors.OKGREEN if database_source == "External" else ConsoleColors.FAIL
    )
    db_warning = (
        f"{ConsoleColors.WARNING}WARNING: Not recommended to use SQLite.{ConsoleColors.ENDC}"
        if database_source == "localhost"
        else ""
    )
    database_message = f"{db_color}Selected Database: {database_source}{ConsoleColors.ENDC}\n{db_warning}"

    try:
        process = await asyncio.create_subprocess_shell(
            "git describe --always",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        git_version = stdout.decode().strip() if process.returncode == 0 else "ERROR"
        if git_version == "ERROR":
            _log.error(f"Git version fetch failed. Stderr: {stderr.decode().strip()}")
    except Exception as e:
        git_version = f"ERROR: {str(e)}"
        _log.error(f"Error fetching Git version: {e}", exc_info=True)

    print(f"Bot Account: {bot.user.name} | {bot.user.id}")
    _log.info("Bot initialization complete. Stats logged.")

    bot_data = get_bot_data_for_server(448488274562908170)
    if not bot_data or not hasattr(bot_data, "pb_test_server_id"):
        _log.error("pb_test_server_id not found in bot data.")
        return

    pb_guild = bot.get_guild(int(bot_data.pb_test_server_id))
    if not pb_guild:
        _log.error(f"Guild with ID {bot_data.pb_test_server_id} not found.")
        return

    github_channel = discord.utils.get(pb_guild.channels, name="github-log")
    if github_channel:
        await github_channel.send("Github Synced, and bot is restarted")
        _log.info("Sync message sent to 'github-log' channel.")
    else:
        _log.error("'github-log' channel not found in the guild.")

    print(
        f"""
      _____           _        _ ____        _   
     |  __ \         | |      | |  _ \      | |  
     | |__) |__  _ __| |_ __ _| | |_) | ___ | |_ 
     |  ___/ _ \| '__| __/ _  | |  _ < / _ \| __|
     | |  | (_) | |  | || (_| | | |_) | (_) | |_ 
     |_|   \___/|_|   \__\__,_|_|____/ \___/ \__|

    Bot Account: {bot.user.name} | {bot.user.id}
    {ConsoleColors.OKCYAN}Discord API Version: {discord.__version__}{ConsoleColors.ENDC}
    {ConsoleColors.WARNING}PortalBot Version: {git_version}{ConsoleColors.ENDC}
    {database_message}

    {ConsoleColors.OKCYAN}Current Time: {now}{ConsoleColors.ENDC}
    {ConsoleColors.OKGREEN}Initialization complete: Cogs, libraries, and views have successfully been loaded.{ConsoleColors.ENDC}
    ==================================================
    {ConsoleColors.WARNING}Statistics{ConsoleColors.ENDC}
    Guilds: {len(bot.guilds)}
    Members: {len(bot.users)}
    """
    )


async def preload_bot_data(bot: "PortalBot"):
    _log.info("Preloading bot data for all guilds...")
    for guild in bot.guilds:
        _log.info(f"Guild Data {guild}: {guild.id}")
        bot_init = await get_bot_data_for_server(guild.id)
        if bot_init is None:
            _log.warning(
                f"No bot data initialized for guild {guild.id}. Attempting to create default bot data."
            )
            _create_bot_data(
                guild.id, guild.text_channels[0].id if guild.text_channels else None
            )
    _log.info("Bot data preloaded for all guilds.")


def initialize_persistent_views(bot, bot_data):
    from utils.daily_questions.__dq_views import QuestionSuggestionManager

    if not bot_data.persistent_views:
        bot.add_view(QuestionSuggestionManager())
        bot_data.persistent_views = True
        bot_data.save()
        _log.info("Persistent views initialized and saved to the database.")
    else:
        _log.debug("Persistent views already initialized for this guild.")


def initialize_db(bot):
    try:
        _log.info("Initializing database...")
        database.db.connect(reuse_if_open=True)
        for guild in bot.guilds:
            bot_data = database.BotData.select().where(
                database.BotData.server_id == str(guild.id)
            )
            if not bot_data.exists():
                initial_channel_id = (
                    guild.system_channel.id if guild.system_channel else None
                )
                _create_bot_data(guild.id, initial_channel_id)
        if database.Administrators.select().count() == 0:
            _create_administrators(bot.owner_ids)
    except Exception as e:
        _log.error(f"Error during database initialization: {e}")
    finally:
        if not database.db.is_closed():
            database.db.close()


def _create_bot_data(server_id, initial_channel_id):
    if initial_channel_id is None:
        _log.warning(
            f"No initial channel found for server {server_id}, skipping creation."
        )
        return
    database.BotData.create(
        server_id=server_id,
        prefix=">",
        persistent_views=False,
        bannedlist_response_channel=initial_channel_id,
        question_suggest_channel=initial_channel_id,
        bot_spam_channel=initial_channel_id,
        realm_channel_response=initial_channel_id,
        daily_question_enabled=True,
        last_question_posted=None,
        last_question_posted_time=None,
        daily_question_channel=initial_channel_id,
        welcome_channel=initial_channel_id,
        mod_log_channel=initial_channel_id,
        pb_test_server_id=448488274562908170,
    )


def _create_administrators(owner_ids):
    for owner_id in owner_ids:
        database.Administrators.create(discordID=str(owner_id), TierLevel=4)
    database.Administrators.create(discordID="306070011028439041", TierLevel=4)


async def on_command_error_(bot, ctx: commands.Context, error: Exception):
    error = getattr(error, "original", error)
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))
    _log.error(f"Error in command '{ctx.command}': {exception_msg}")

    if ctx.command and ctx.command.name == "rule":
        return await ctx.send("No Rule...")

    if isinstance(error, commands.CheckFailure):
        return

    if isinstance(error, commands.CommandNotFound):
        cmd = ctx.invoked_with
        matches = get_close_matches(cmd, [c.name for c in bot.commands])
        if matches:
            return await ctx.send(
                f'Command "{cmd}" not found. Did you mean "{matches[0]}"?'
            )
        return await ctx.message.add_reaction("❌")

    if isinstance(error, (commands.MissingRequiredArgument, commands.TooManyArguments)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        return await ctx.send(
            embed=argument_error_embed("Missing or Extra Arguments", signature)
        )

    if isinstance(
        error,
        (commands.MissingPermissions, commands.MissingRole, commands.MissingAnyRole),
    ):
        return await ctx.send(embed=permission_error_embed())

    if isinstance(error, (commands.BadArgument, commands.BadLiteralArgument)):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        return await ctx.send(embed=argument_error_embed("Bad Argument", signature))

    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(embed=cooldown_embed(error.retry_after))

    gist_url = await create_gist_from_traceback(exception_msg)
    permitlist = get_permitlist()

    embed = discord.Embed(
        title=(
            "Traceback Detected" if ctx.author.id in permitlist else "An Error Occurred"
        ),
        description=(
            "Traceback details have been attached."
            if ctx.author.id in permitlist
            else "An unexpected error occurred. The developers have been notified."
        ),
        color=EmbedColors.red,
    )
    if ctx.author.id in permitlist and gist_url:
        embed.add_field(name="Gist URL", value=gist_url)
    embed.set_footer(text=f"Error: {str(error)}")
    embed.set_thumbnail(url=BotAssets.error_png)
    await ctx.send(embed=embed)

    raise error


async def on_app_command_error_(
    bot: "PortalBot",
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    error = getattr(error, "original", error)
    tb = error.__traceback__
    etype = type(error)
    exception_msg = "".join(traceback.format_exception(etype, error, tb, chain=True))
    _log.error(f"Error in command '{interaction.command}': {exception_msg}")

    if isinstance(error, app_commands.CommandOnCooldown):
        await _send_response(interaction, cooldown_embed(error.retry_after))
        return

    if isinstance(error, app_commands.CheckFailure):
        await _send_response(
            interaction, "You cannot run this command!", ephemeral=True
        )
        return

    if isinstance(error, app_commands.CommandNotFound):
        await _send_response(
            interaction, "That command does not exist.", ephemeral=True
        )
        return

    gist_url = await create_gist_from_traceback(exception_msg)
    await _notify_error(interaction, error, gist_url)
    raise error


async def _send_response(
    interaction: discord.Interaction,
    content: Union[discord.Embed, str],
    ephemeral=False,
):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(
                content=content, ephemeral=ephemeral
            )
    except Exception as e:
        _log.error(f"Error sending response: {e}")


async def _notify_error(
    interaction: discord.Interaction, error: Exception, gist_url: str
):
    permitlist = get_permitlist()
    if interaction.user.id not in permitlist:
        embed = discord.Embed(
            title="Error Detected!",
            description="An unexpected error occurred. The developers have been notified.",
            color=discord.Color.brand_red(),
        )
        embed.add_field(
            name="Error Message",
            value="Please double check your command. The developers are investigating.",
        )
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


async def on_command_(bot: "PortalBot", ctx: commands.Context):
    bypass_commands = {"sync", "ping", "kill", "jsk", "py", "jishaku"}
    _log.info(f"User {ctx.author} invoked command: {ctx.command.name}")
    if ctx.command.name in bypass_commands:
        return
    await ctx.reply(
        f"❌ The command `{ctx.command.name}` is deprecated. Please use the slash command `/{ctx.command.name}` instead."
    )
