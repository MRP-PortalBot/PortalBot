from __future__ import annotations

import json
import os
import subprocess
import traceback
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING

import discord
import requests
import sentry_sdk
from discord import app_commands
from discord.ext import commands

from core import database
from core.common import ConsoleColors, Colors, Others, QuestionSuggestionManager, get_bot_data_id
from core.logging_module import get_log

if TYPE_CHECKING:
    from main import PortalBot

_log = get_log(__name__)


async def before_invoke_(ctx: commands.Context):
    pass
    """sentry_sdk.set_user(None)
    sentry_sdk.set_user({"id": ctx.author.id, "username": ctx.author.name})
    sentry_sdk.set_tag("username", f"{ctx.author.name}#{ctx.author.discriminator}")
    if ctx.command is None:
        sentry_sdk.set_context(
            "user",
            {
                "name": ctx.author.name,
                "id": ctx.author.id,
                "command": ctx.command,
                "guild": ctx.guild.name,
                "guild_id": ctx.guild.id,
                "channel": ctx.channel.name,
                "channel_id": ctx.channel.id,
            },
        )
    else:
        sentry_sdk.set_context(
            "user",
            {
                "name": ctx.author.name,
                "id": ctx.author.id,
                "command": "Unknown",
                "guild": ctx.guild.name,
                "guild_id": ctx.guild.id,
                "channel": ctx.channel.name,
                "channel_id": ctx.channel.id,
            },
        )"""


async def on_ready_(bot: 'PortalBot'):
    now = datetime.now()
    row_id = get_bot_data_id()

    query: database.BotData = (
        database.BotData.select()
        .where(database.BotData.id == row_id)
        .get()
    )

    if not query.persistent_views:
        bot.add_view(QuestionSuggestionManager())
        query.persistent_views = True
        query.save()

    if not os.getenv("USEREAL"):
        IP = os.getenv("DATABASE_IP")
        databaseField = f"{ConsoleColors.OKGREEN}Selected Database: External ({IP}){ConsoleColors.ENDC}"
    else:
        databaseField = (
            f"{ConsoleColors.FAIL}Selected Database: localhost{ConsoleColors.ENDC}\n{ConsoleColors.WARNING}WARNING: Not "
            f"recommended to use SQLite.{ConsoleColors.ENDC} "
        )

    try:
        p = subprocess.run(
            "git describe --always",
            shell=True,
            text=True,
            capture_output=True,
            check=True,
        )
        output = p.stdout
    except subprocess.CalledProcessError:
        output = "ERROR"

    print(
        f"""

          _____           _        _ ____        _   
         |  __ \         | |      | |  _ \      | |  
         | |__) |__  _ __| |_ __ _| | |_) | ___ | |_ 
         |  ___/ _ \| '__| __/ _` | |  _ < / _ \| __|
         | |  | (_) | |  | || (_| | | |_) | (_) | |_ 
         |_|   \___/|_|   \__\__,_|_|____/ \___/ \__|
                                                                    
                                             
            Bot Account: {bot.user.name} | {bot.user.id}
            {ConsoleColors.OKCYAN}Discord API Wrapper Version: {discord.__version__}{ConsoleColors.ENDC}
            {ConsoleColors.WARNING}PortalBot Version: {output}{ConsoleColors.ENDC}
            {databaseField}

            {ConsoleColors.OKCYAN}Current Time: {now}{ConsoleColors.ENDC}
            {ConsoleColors.OKGREEN}Cogs, libraries, and views have successfully been initalized.{ConsoleColors.ENDC}
            ==================================================
            {ConsoleColors.WARNING}Statistics{ConsoleColors.ENDC}

            Guilds: {len(bot.guilds)}
            Members: {len(bot.users)}
            """
    )


async def on_command_error_(bot, ctx: commands.Context, error: Exception):
    tb = error.__traceback__
    etype = type(error)
    exception = traceback.format_exception(etype, error, tb, chain=True)
    exception_msg = ""
    for line in exception:
        exception_msg += line

    error = getattr(error, "original", error)
    if ctx.command is not None:
        if ctx.command.name == "rule":
            return "No Rule..."

    if isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
        return

    if hasattr(ctx.command, "on_error"):
        return

    elif isinstance(error, (commands.CommandNotFound, commands.errors.CommandNotFound)):
        cmd = ctx.invoked_with
        cmds = [cmd.name for cmd in bot.commands]
        matches = get_close_matches(cmd, cmds)
        if len(matches) > 0:
            return await ctx.send(
                f'Command "{cmd}" not found, maybe you meant "{matches[0]}"?'
            )
        else:
            """return await ctx.send(
                f'Command "{cmd}" not found, use the help command to know what commands are available. '
                f"Some commands have moved over to slash commands, please check "
                f"https://timmy.schoolsimplified.org/#slash-command-port "
                f"for more updates! "
            )"""
            return await ctx.message.add_reaction("❌")

    elif isinstance(
            error, (commands.MissingRequiredArgument, commands.TooManyArguments)
    ):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"

        em = discord.Embed(
            title="Missing/Extra Required Arguments Passed In!",
            description="You have missed one or several arguments in this command"
                        "\n\nUsage:"
                        f"\n`{signature}`",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(
            text="Consult the Help Command if you are having trouble or call over a Bot Manager!"
        )
        return await ctx.send(embed=em)

    elif isinstance(
            error,
            (
                    commands.MissingAnyRole,
                    commands.MissingRole,
                    commands.MissingPermissions,
                    commands.errors.MissingAnyRole,
                    commands.errors.MissingRole,
                    commands.errors.MissingPermissions,
            ),
    ):
        em = discord.Embed(
            title="Invalid Permissions!",
            description="You do not have the associated role in order to successfully invoke this command! "
                        "Contact an administrator/developer if you believe this is invalid.",
            color=Colors.red,
        )
        em.set_thumbnail(url=Others.error_png)
        em.set_footer(
            text="Consult the Help Command if you are having trouble or call over a Bot Manager!"
        )
        await ctx.send(embed=em)
        return

    elif isinstance(
            error,
            (commands.BadArgument, commands.BadLiteralArgument, commands.BadUnionArgument),
    ):
        signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
        if ctx.command.name == "schedule":
            em = discord.Embed(
                title="Bad Argument!",
                description=f"Looks like you messed up an argument somewhere here!\n\n**Check the "
                            f"following:**\nUsage:\n`{signature}`\n-> If you seperated the time and the AM/PM. (Eg; "
                            f"5:00 PM)\n-> If you provided a valid student's ID\n-> If you followed the MM/DD "
                            f"Format.\n-> Keep all the arguments in one word.\n-> If you followed the [documentation "
                            f"for schedule.](https://timmy.schoolsimplified.org/tutorbot#schedule)",
                color=Colors.red,
            )
            em.set_thumbnail(url=Others.error_png)
            em.set_footer(
                text="Consult the Help Command if you are having trouble or call over a Bot Manager!"
            )
            return await ctx.send(embed=em)
        else:
            em = discord.Embed(
                title="Bad Argument!",
                description=f"Unable to parse arguments, check what arguments you provided."
                            f"\n\nUsage:\n`{signature}`",
                color=Colors.red,
            )
            em.set_thumbnail(url=Others.error_png)
            em.set_footer(
                text="Consult the Help Command if you are having trouble or call over a Bot Manager!"
            )
            return await ctx.send(embed=em)

    elif isinstance(
            error, (commands.CommandOnCooldown, commands.errors.CommandOnCooldown)
    ):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)

        msg = "This command cannot be used again for {} minutes and {} seconds".format(
            round(m), round(s)
        )

        embed = discord.Embed(
            title="Command On Cooldown", description=msg, color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    else:
        error_file = Path("error.txt")
        error_file.touch()
        with error_file.open("w") as f:
            f.write(exception_msg)
        with error_file.open("r") as f:
            # config, _ = core.common.load_config()
            data = "\n".join([l.strip() for l in f])

            GITHUB_API = "https://api.github.com"
            API_TOKEN = os.getenv("github_gist")
            url = GITHUB_API + "/gists"
            headers = {"Authorization": "token %s" % API_TOKEN}
            params = {"scope": "gist"}
            payload = {
                "description": "PortalBot encountered a Traceback!",
                "public": True,
                "files": {"error": {"content": f"{data}"}},
            }
            res = requests.post(
                url, headers=headers, params=params, data=json.dumps(payload)
            )
            j = json.loads(res.text)
            ID = j["id"]
            gisturl = f"https://gist.github.com/{ID}"
            _log.info(f"Gist URL: {gisturl}")

            permitlist = []
            query = database.Administrators.select().where(
                database.Administrators.TierLevel >= 3
            )
            for user in query:
                permitlist.append(user.discordID)

            if ctx.author.id not in permitlist:
                embed = discord.Embed(
                    title="Error Detected!",
                    description="Seems like I've ran into an unexpected error!",
                    color=Colors.red,
                )
                embed.set_thumbnail(url=Others.error_png)
                embed.set_footer(text=f"Error: {str(error)}")
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(
                    title="Traceback Detected!",
                    description="PortalBot here has ran into an error!\nTraceback has been attached below.",
                    color=Colors.red,
                )
                embed.add_field(name="GIST URL", value=gisturl)
                embed.set_thumbnail(url=Others.error_png)
                embed.set_footer(text=f"Error: {str(error)}")
                await ctx.send(embed=embed)

            error_file.unlink()

    raise error


async def on_app_command_error_(
        bot: 'PortalBot',
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
):
    tb = error.__traceback__
    etype = type(error)
    exception = traceback.format_exception(etype, error, tb, chain=True)
    exception_msg = ""
    for line in exception:
        exception_msg += line

    if isinstance(error, app_commands.CommandOnCooldown):
        m, s = divmod(error.retry_after, 60)
        h, m = divmod(m, 60)

        msg = "This command cannot be used again for {} minutes and {} seconds".format(
            round(m), round(s)
        )

        embed = discord.Embed(
            title="Command On Cooldown", description=msg, color=discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, app_commands.CheckFailure):
        if interaction.response.is_done():
            await interaction.followup.send(
                "You cannot run this command!", ephemeral=True
            )
        await interaction.response.send_message(
            "You cannot run this command!", ephemeral=True
        )

    elif isinstance(error, app_commands.CommandNotFound):
        await interaction.response.send_message(
            f"Command /{interaction.command.name} not found."
        )

    else:
        error_file = Path("error.txt")
        error_file.touch()
        with error_file.open("w") as f:
            f.write(exception_msg)
        with error_file.open("r") as f:
            # config, _ = core.common.load_config()
            data = "\n".join([l.strip() for l in f])

            GITHUB_API = "https://api.github.com"
            API_TOKEN = os.getenv("GITHUB")
            url = GITHUB_API + "/gists"
            headers = {"Authorization": "token %s" % API_TOKEN}
            params = {"scope": "gist"}
            payload = {
                "description": "PortalBot encountered a Traceback!",
                "public": True,
                "files": {"error": {"content": f"{data}"}},
            }
            res = requests.post(
                url, headers=headers, params=params, data=json.dumps(payload)
            )
            j = json.loads(res.text)
            ID = j["id"]
            gisturl = f"https://gist.github.com/{ID}"

            permitlist = []
            query = database.Administrators.select().where(
                database.Administrators.TierLevel >= 3
            )
            for user in query:
                permitlist.append(user.discordID)

            if interaction.user.id not in permitlist:
                embed = discord.Embed(
                    title="Error Detected!",
                    description="Seems like I've ran into an unexpected error!",
                    color=discord.Color.brand_red(),
                )
                embed.add_field(
                    name="Error Message",
                    value="I've contacted the Bot Developers and they have been notified, meanwhile, please double "
                          "check the command you've sent for any issues.\n "
                          "Consult the help command for more information.",
                )
                embed.set_footer(text="Submit a bug report or feedback below!")
                if interaction.response.is_done():
                    await interaction.followup.send(
                        embed=embed
                    )
                else:
                    await interaction.response.send_message(
                        embed=embed
                    )
            else:
                embed = discord.Embed(
                    title="Traceback Detected!",
                    description="PortalBot here has ran into an error!\nTraceback has been attached below.",
                    color=Colors.red,
                )
                embed.add_field(name="GIST URL", value=gisturl)
                embed.set_footer(text=f"Error: {str(error)}")
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.response.send_message(embed=embed)

    raise error


async def on_command_(bot: 'PortalBot', ctx: commands.Context):
    if ctx.command.name in ["sync", "ping", "kill", "jsk", "py", "jishaku"]:
        return

    await ctx.reply(
        f":x: This command usage is deprecated. Use the equivalent slash command by using `/{ctx.command.name}` instead."
    )


def initialize_db(bot):
    """
    Initializes the database, and creates the needed table data if they don't exist.
    """
    database.db.connect(reuse_if_open=True)
    row_id = get_bot_data_id()
    bot_data = database.BotData.select().where(database.BotData.id == row_id)

    if not bot_data.exists():
        q = database.BotData.create(
            prefix=">",
            persistent_views=False,
            blacklist_response_channel=995819431538217093,
            question_suggest_channel=787803726168588318,
            bot_spam_channel=588728994661138494,
            realm_channel_response=588408514796322816,
            server_id=587495640502763521
        )
        q.save()
        _log.info("Created CheckInformation Entry.")

    if len(database.Administrators) == 0:
        for person in bot.owner_ids:
            database.Administrators.create(discordID=person, TierLevel=4)
            _log.info("Created Administrator Entry.")
        database.Administrators.create(discordID=409152798609899530, TierLevel=4)

    database.db.close()
