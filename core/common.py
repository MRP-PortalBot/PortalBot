from pathlib import Path
from types import CoroutineType
from typing import Tuple, Union, List
import asyncio
import discord
import json
import os
import requests
import random

from discord import ButtonStyle, ui, SelectOption

from core import database
from datetime import datetime

from core.logging_module import get_log
from main import PortalBot

_log = get_log(__name__)
_log.info("Starting PortalBot...")


def load_config() -> Tuple[dict, Path]:
    """Load data from the botconfig.json.\n
    Returns a tuple containing the data as a dict, and the file as a Path"""
    config_file = Path("botconfig.json")
    config_file.touch(exist_ok=True)
    if config_file.read_text() == "":
        config_file.write_text("{}")
    with config_file.open("r") as f:
        config = json.load(f)
    return config, config_file


def prompt_config(msg, key):
    """Ensure a value exists in the botconfig.json, if it doesn't prompt the bot owner to input via the console."""
    config, config_file = load_config()
    if key not in config:
        config[key] = input(msg)
        with config_file.open("w+") as f:
            json.dump(config, f, indent=4)


async def paginate_embed(bot: discord.Client,
                         ctx,
                         embed: discord.Embed,
                         population_func,
                         end: int,
                         begin: int = 1,
                         page=1):
    emotes = ["◀️", "▶️"]

    async def check_reaction(reaction, user):
        return await user == ctx.author and str(reaction.emoji) in emotes

    embed = await population_func(embed, page)
    if isinstance(embed, discord.Embed):
        message = await ctx.send(embed=embed)
    else:
        await ctx.send(str(type(embed)))
        return
    await message.add_reaction(emotes[0])
    await message.add_reaction(emotes[1])
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                timeout=60,
                                                check=check_reaction)
            if user == bot.user:
                continue
            if str(reaction.emoji) == emotes[1] and page < end:
                page += 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
            elif str(reaction.emoji) == emotes[0] and page > begin:
                page -= 1
                embed = await population_func(embed, page)
                await message.remove_reaction(reaction, user)
                await message.edit(embed=embed)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break


def solve(s):
    a = s.split(' ')
    for i in range(len(a)):
        a[i] = a[i].capitalize()
    return ' '.join(a)


config, _ = load_config()


async def mainTask2(client):
    while True:
        d = datetime.utcnow()
        if d.hour == 16 or d.hour == "16":
            guild = client.get_guild(config['ServerID'])
            channel = guild.get_channel(config['dqchannel'])
            limit = int(database.Question.select().count())
            print(limit)
            Rnum = random.randint(1, limit)
            q: database.Question = database.Question.select().where(
                database.Question.usage == True).count()
            print(f"{str(limit)}: limit\n{str(q)}: true count")
            if limit == q:
                query = database.Question.select().where(
                    database.Question.usage == True)
                for question in query:
                    question.usage = False
                    question.save()

            posted = 0
            while (posted < 1):
                Rnum = random.randint(1, limit)
                print(str(Rnum))
                q: database.Question = database.Question.select().where(
                    database.Question.id == Rnum).get()
                print(q.id)
                if q.usage == False or q.usage == "False":
                    q.usage = True
                    q.save()
                    posted = 2
                    print(posted)
                    embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓",
                                          description=f"**{q.question}**",
                                          color=0xb10d9f)
                    embed.set_footer(text=f"Question ID: {q.id}")
                    await channel.send(embed=embed)
                else:
                    posted = 0
                    print(posted)

        await asyncio.sleep(3600)


async def missing_arguments(ctx, example):
    em = discord.Embed(
        title="Missing Required Arguments!",
        description=
        f"You have missed one or several arguments in this command\n**Example Usage:** `>{example}`",
        color=0xf5160a)
    await ctx.send(embed=em)
    return


class SelectMenuHandler(ui.Select):
    """Adds a SelectMenu to a specific message and returns it's value when option selected.

    Usage:
        To do something after the callback function is invoked (the button is pressed), you have to pass a
        coroutine to the class. IMPORTANT: The coroutine has to take two arguments (discord.Interaction, discord.View)
        to work.
    """

    def __init__(
            self,
            options: List[SelectOption],
            custom_id: Union[str, None] = None,
            place_holder: Union[str, None] = None,
            max_values: int = 1,
            min_values: int = 1,
            disabled: bool = False,
            select_user: Union[discord.Member, discord.User, None] = None,
            roles: List[discord.Role] = None,
            interaction_message: Union[str, None] = None,
            ephemeral: bool = True,
            coroutine: CoroutineType = None,
            view_response=None,
            modal_response=None,
    ):
        """
        Parameters:
            options: List of discord.SelectOption
            custom_id: Custom ID of the view. Default to None.
            place_holder: Placeholder string for the view. Default to None.
            max_values Maximum values that are selectable. Default to 1.
            min_values: Minimum values that are selectable. Default to 1.
            disabled: Whenever the button is disabled or not. Default to False.
            select_user: The user that can perform this action, leave blank for everyone. Defaults to None.
            interaction_message: The response message when pressing on a selection. Default to None.
            ephemeral: Whenever the response message should only be visible for the select_user or not. Default to True.
            coroutine: A coroutine that gets invoked after the button is pressed. If None is passed, the view is stopped after the button is pressed. Default to None.
            view_response: The response of the view. Default to None.
            modal_response: The response of the modal. Default to None.
        """

        self.options_ = options
        self.custom_id_ = custom_id
        self.select_user = select_user
        self.roles = roles
        self.disabled_ = disabled
        self.placeholder_ = place_holder
        self.max_values_ = max_values
        self.min_values_ = min_values
        self.interaction_message_ = interaction_message
        self.ephemeral_ = ephemeral
        self.coroutine = coroutine
        self.view_response = view_response
        self.modal_response = modal_response

        if self.custom_id_:
            super().__init__(
                options=self.options_,
                placeholder=self.placeholder_,
                custom_id=self.custom_id_,
                disabled=self.disabled_,
                max_values=self.max_values_,
                min_values=self.min_values_,
            )
        else:
            super().__init__(
                options=self.options_,
                placeholder=self.placeholder_,
                disabled=self.disabled_,
                max_values=self.max_values_,
                min_values=self.min_values_,
            )

    async def callback(self, interaction: discord.Interaction):
        if self.select_user in [None, interaction.user] or any(
                role in interaction.user.roles for role in self.roles
        ):

            self.view.value = self.values[0]
            self.view_response = self.values[0]

            if self.modal_response:
                await interaction.response.send_modal(self.modal_response)

            elif self.interaction_message_:
                await interaction.response.send_message(
                    content=self.interaction_message_, ephemeral=self.ephemeral_
                )

            if self.coroutine is not None:
                await self.coroutine(interaction, self.view)
            else:
                self.view.stop()
        else:
            await interaction.response.send_message(
                content="You're not allowed to interact with that!", ephemeral=True
            )


class ButtonHandler(ui.Button):
    """
    Adds a Button to a specific message and returns it's value when pressed.

    Usage:
        To do something after the callback function is invoked (the button is pressed), you have to pass a
        coroutine to the class. IMPORTANT: The coroutine has to take two arguments (discord.Interaction, discord.View)
        to work.
    """

    def __init__(
            self,
            style: ButtonStyle,
            label: str,
            custom_id: Union[str, None] = None,
            emoji: Union[str, None] = None,
            url: Union[str, None] = None,
            disabled: bool = False,
            button_user: Union[discord.Member, discord.User, None] = None,
            roles: List[discord.Role] = None,
            interaction_message: Union[str, None] = None,
            ephemeral: bool = True,
            coroutine: CoroutineType = None,
            view_response=None,
    ):
        """
        Parameters:
            style: Label for the button
            label: Custom ID that represents this button. Default to None.
            custom_id: Style for this button. Default to None.
            emoji: An emoji for this button. Default to None.
            url: A URL for this button. Default to None.
            disabled: Whenever the button should be disabled or not. Default to False.
            button_user: The user that can perform this action, leave blank for everyone. Defaults to None.
            roles: The roles which the user needs to be able to click the button.
            interaction_message: The response message when pressing on a selection. Default to None.
            ephemeral: Whenever the response message should only be visible for the select_user or not. Default to True.
            coroutine: A coroutine that gets invoked after the button is pressed. If None is passed, the view is stopped after the button is pressed. Default to None.
        """
        self.style_ = style
        self.label_ = label
        self.custom_id_ = custom_id
        self.emoji_ = emoji
        self.url_ = url
        self.disabled_ = disabled
        self.button_user = button_user
        self.roles = roles
        self.interaction_message_ = interaction_message
        self.ephemeral_ = ephemeral
        self.coroutine = coroutine
        self.view_response = view_response

        if self.custom_id_:
            super().__init__(
                style=self.style_,
                label=self.label_,
                custom_id=self.custom_id_,
                emoji=self.emoji_,
                url=self.url_,
                disabled=self.disabled_,
            )
        else:
            super().__init__(
                style=self.style_,
                label=self.label_,
                emoji=self.emoji_,
                url=self.url_,
                disabled=self.disabled_,
            )

    async def callback(self, interaction: discord.Interaction):
        if self.button_user in [None, interaction.user] or any(
                role in interaction.user.roles for role in self.roles
        ):
            if self.custom_id_ is None:
                self.view.value = self.label_
                self.view_response = self.label_
            else:
                self.view.value = self.custom_id_
                self.view_response = self.custom_id_

            if self.interaction_message_:
                await interaction.response.send_message(
                    content=self.interaction_message_, ephemeral=self.ephemeral_
                )

            if self.coroutine is not None:
                await self.coroutine(interaction, self.view)
            else:
                self.view.stop()
        else:
            await interaction.response.send_message(
                content="You're not allowed to interact with that!", ephemeral=True
            )


class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Colors:
    red = discord.Color.red()


class Others:
    error_png = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png"


class Me:
    TracebackChannel = 797193549992165456


def return_banishblacklistform_modal(bot: PortalBot,
                                     sheet,
                                     user: discord.User,
                                     gamertag: str,
                                     originating_realm: str,
                                     type_of_ban: str):
    class BanishBlacklistForm(ui.Modal, title="Blacklist Form"):
        def __init__(self, sheet, bot: PortalBot, user: discord.User, gamertag: str, originating_realm: str, type_of_ban: str):
            super().__init__(timeout=None)
            self.sheet = sheet
            self.bot = bot
            self.user = user
            self.gamertag = gamertag
            self.originating_realm = originating_realm
            self.type_of_ban = type_of_ban

        discord_username = ui.TextInput(
            label="Banished User's Username",
            style=discord.TextStyle.short,
            default=user.name,
            required=True
        )

        known_alts = ui.TextInput(
            label="Known Alts",
            style=discord.TextStyle.long,
            placeholder="Separate each alt with a comma",
            required=True
        )

        reason = ui.TextInput(
            label="Reason",
            style=discord.TextStyle.long,
            placeholder="Reason for ban",
            required=True
        )

        date_of_ban = ui.TextInput(
            label="Date of Ban",
            style=discord.TextStyle.short,
            placeholder="Date of ban",
            required=True
        )

        ban_end_date = ui.TextInput(
            label="Ban End Date",
            style=discord.TextStyle.short,
            placeholder="Leave blank if permanent",
            default="Permanent",
            required=True
        )

    async def on_submit(self, interaction: discord.Interaction):
        entry_id = (int(self.sheet.acell('A3').value) + 1)
        log_channel = self.bot.get_channel(config['bannedlistChannel'])
        row = [
            entry_id, interaction.user.display_name, self.discord_username.value,
            self.user.id, self.gamertag, self.originating_realm, self.known_alts.value, self.reason.value, self.date_of_ban.value,
            self.ban_end_date.value
        ]
        self.sheet.insert_row(row, 3)

        database.db.connect(reuse_if_open=True)
        q: database.MRP_Blacklist_Data = database.MRP_Blacklist_Data.create(
            BanReporter=interaction.user.display_name,
            DiscUsername=self.discord_username.value,
            DiscID=self.user.id,
            Gamertag=self.gamertag,
            BannedFrom=self.originating_realm,
            KnownAlts=self.known_alts.value,
            ReasonforBan=self.reason.value,
            DateofIncident=self.date_of_ban.value,
            TypeofBan=self.type_of_ban,
            DatetheBanEnds=self.ban_end_date.value)
        q.save()
        database.db.close()

        bannedlistembed = discord.Embed(title="Bannedlist Report",
                                        description="Sent from: " +
                                                    interaction.user.mention,
                                        color=0xb10d9f)

        bannedlistembed.add_field(name="User's Discord",
                                  value=self.discord_username.value + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Discord ID",
                                  value=self.user.id + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="User's Gamertag",
                                  value=self.gamertag + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Realm Banned from",
                                  value=self.originating_realm + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Known Alts",
                                  value=self.known_alts.value + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Ban Reason",
                                  value=self.reason.value + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Date of Incident",
                                  value=self.date_of_ban.value + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Type of Ban",
                                  value=self.type_of_ban + "\n",
                                  inline=False)
        bannedlistembed.add_field(name="Ban End Date",
                                  value=self.ban_end_date.value + "\n",
                                  inline=False)

        timestamp = datetime.now()
        bannedlistembed.set_footer(text=interaction.guild.name + " | Date: " +
                                        str(timestamp.strftime(r"%x")) +
                                        " | ID: " + str(entry_id))
        await log_channel.send(embed=bannedlistembed)

        await interaction.response.send_message(
            content="Your report has been submitted!",
            ephemeral=True
        )
    return BanishBlacklistForm(sheet, bot, user, gamertag, originating_realm, type_of_ban)








