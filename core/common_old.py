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
from dotenv import load_dotenv

from core import database
from datetime import datetime

from core.logging_module import get_log

_log = get_log(__name__)



class Me:
    TracebackChannel = 797193549992165456


def return_banishblacklistform_modal(bot,
                                     user: discord.User,
                                     gamertag: str,
                                     originating_realm: str,
                                     type_of_ban: str):
    class BanishBlacklistForm(ui.Modal, title="Blacklist Form"):
        def __init__(self, bot, user: discord.User, gamertag: str, originating_realm: str,
                     type_of_ban: str):
            super().__init__(timeout=None)
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

    return BanishBlacklistForm(bot, user, gamertag, originating_realm, type_of_ban)


def return_applyfornewrealm_modal(
        bot,
        realm_name: str,
        type_of_realm: str,
        emoji: str,
        member_count: str,
        community_duration: str,
        world_duration: str,
        reset_schedule: str
):
    class ApplyForNewRealmForm(ui.Modal, title="Realm Application"):
        def __init__(self, bot, realm_name: str, type_of_realm: str, emoji: str, member_count: str,
                     community_duration: str, world_duration: str, reset_schedule: str):
            super().__init__(timeout=None)
            self.bot = bot
            self.realm_name = realm_name
            self.type_of_realm = type_of_realm
            self.emoji = emoji
            self.member_count = member_count
            self.community_duration = community_duration
            self.world_duration = world_duration
            self.reset_schedule = reset_schedule

        short_description = ui.TextInput(
            label="Short Description",
            style=discord.TextStyle.short,
            placeholder="Short description of the realm",
            required=True
        )

        long_description = ui.TextInput(
            label="Long Description",
            style=discord.TextStyle.long,
            placeholder="Long description of the realm",
            required=True
        )

        application_process = ui.TextInput(
            label="Application Process",
            style=discord.TextStyle.long,
            placeholder="Application process for the realm",
            required=True
        )

        foreseeable_future = ui.TextInput(
            label="Foreseeable Future",
            style=discord.TextStyle.long,
            placeholder="Will your Realm/Server have the ability to continue for the foreseeable future?",
            required=True
        )

        admin_team = ui.TextInput(
            label="Admin Team",
            style=discord.TextStyle.long,
            placeholder="Who is on your admin team and how long have they been with you?",
            required=True
        )

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = self.bot.get_channel(config['realmChannelResponse'])
        admin = discord.utils.get(interaction.guild.roles, name="Admin")
        q: database.RealmApplications = database.RealmApplications.create(
            discord_id=interaction.user.id,
            realm_name=self.realm_name,
            type_of_realm=self.type_of_realm,
            emoji=self.emoji,
            member_found=self.member_count,
            realm_age=self.community_duration,
            world_age=self.world_duration,
            reset_schedule=self.reset_schedule,
            short_desc=self.short_description.value,
            long_desc=self.long_description.value,
            application_process=self.application_process.value,
            foreseeable_future=self.foreseeable_future.value,
            admin_team=self.admin_team.value)
        q.save()
        database.db.close()

        embed = discord.Embed(title="Realm Application", description="__**Realm Owner:**__\n" +
                                                                     interaction.user.mention + "\n============================================",
                              color=0xb10d9f)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png")
        embed.add_field(name="__**Realm Name**__",
                        value=q.realm_name, inline=True)
        embed.add_field(name="__**Realm or Server?**__",
                        value=q.type_of_realm, inline=True)
        embed.add_field(name="__**Emoji**__",
                        value=q.emoji, inline=True)
        embed.add_field(name="__**Short Description**__",
                        value=q.short_desc, inline=False)
        embed.add_field(name="__**Long Description**__",
                        value=q.long_desc, inline=False)
        embed.add_field(name="__**Application Process**__",
                        value=q.application_process, inline=False)
        embed.add_field(name="__**Current Member Count**__",
                        value=q.member_count, inline=True)
        embed.add_field(name="__**Age of Community**__",
                        value=q.realm_age, inline=True)
        embed.add_field(name="__**Age of Current World**__",
                        value=q.world_age, inline=True)
        embed.add_field(name="__**How often do you reset**__",
                        value=q.reset_schedule, inline=True)
        embed.add_field(name="__**Will your Realm/Server have the ability to continue for the foreseeable future?**__",
                        value=q.foreseeable_future, inline=True)
        embed.add_field(name="__**Members of the OP Team, and How long they have been an OP**__",
                        value=q.admin_team, inline=False)
        embed.add_field(name="__**Reaction Codes**__",
                        value="Please react with the following codes to show your thoughts on this applicant.",
                        inline=False)
        embed.add_field(name="----💚----", value="Approved", inline=True)
        embed.add_field(name="----💛----",
                        value="More Time in Server", inline=True)
        embed.add_field(name="----❤️----", value="Rejected", inline=True)
        embed.set_footer(text="Realm Application #" + str(q.id) + " | " + datetime.now().strftime(r"%x"))
        await log_channel.send(admin.mention)

    return ApplyForNewRealmForm(bot, realm_name, type_of_realm, emoji, member_count, community_duration, world_duration,
                                reset_schedule)


class DisabledQuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(
        label="Add Question",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="persistent_view:qsm_add_question",
        disabled=True
    )
    async def add_question(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        pass

    @discord.ui.button(label="Discard Question", style=discord.ButtonStyle.red, emoji="❌",  custom_id="persistent_view:qsm_discard_question", disabled=True)
    async def discard_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class QuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(
        label="Add Question",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="persistent_view:qsm_add_question"
    )
    async def add_question(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        q: database.QuestionSuggestionQueue = database.QuestionSuggestionQueue.select().where(database.QuestionSuggestionQueue.message_id == interaction.message.id).get()

        move_to: database.Question = database.Question.create(
            question=q.question,
            usage=False
        )
        move_to.save()
        q.delete_instance()

        new_embed = discord.Embed(
            title="Question Suggestion",
            description="This question has been added to the database!",
            color=discord.Color.green()
        )
        new_embed.add_field(name="Question", value=q.question)
        new_embed.add_field(name="Added By", value=interaction.user.mention)
        new_embed.set_footer(text=f"Question ID: {move_to.id}")
        await interaction.message.edit(embed=new_embed, view=DisabledQuestionSuggestionManager())
        await interaction.response.send_message("Operation Complete.", ephemeral=True)

    @discord.ui.button(label="Discard Question", style=discord.ButtonStyle.red, emoji="❌",  custom_id="persistent_view:qsm_discard_question")
    async def discard_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable both buttons
        for child in self.children:
            child.disabled = True

        q: database.QuestionSuggestionQueue = database.QuestionSuggestionQueue.select().where(database.QuestionSuggestionQueue.message_id == interaction.message.id).get()
        q.delete_instance()

        new_embed = discord.Embed(
            title="Question Suggestion",
            description="This question has been discarded!",
            color=discord.Color.red()
        )
        new_embed.add_field(name="Question", value=q.question)
        new_embed.add_field(name="Discarded By", value=interaction.user.mention)
        new_embed.set_footer(text=f"Question ID: {q.id}")
        await interaction.message.edit(embed=new_embed, view=DisabledQuestionSuggestionManager())
        await interaction.response.send_message("Operation Complete.", ephemeral=True)


def get_bot_data_id():
    load_dotenv()
    os.getenv("bot_type")
    key_value = {
        "STABLE": 1,
        "BETA": 2
    }

    return key_value[os.getenv("bot_type")]


class SuggestModalNEW(discord.ui.Modal, title="Suggest a Question"):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    short_description = ui.TextInput(
        label="Daily Question",
        style=discord.TextStyle.long,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        row_id = get_bot_data_id()
        q: database.BotData = database.BotData.select().where(database.BotData.id == row_id).get()
        await interaction.response.defer(thinking=True)
        embed = discord.Embed(title="Question Suggestion",
                              description=f"Requested by {interaction.user.mention}", color=0x18c927)
        embed.add_field(name="Question:", value=f"{self.short_description.value}")
        log_channel = await self.bot.fetch_channel(777987716008509490)
        msg = await log_channel.send(embed=embed, view=QuestionSuggestionManager())
        q: database.QuestionSuggestionQueue = database.QuestionSuggestionQueue.create(
            question=self.short_description.value,
            discord_id=interaction.user.id,
            message_id=msg.id,
        )
        q.save()

        await interaction.followup.send("Thank you for your suggestion!")


class SuggestQuestionFromDQ(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.value = None
        self.bot = bot

    @discord.ui.button(
        label="Suggest a Question!",
        style=discord.ButtonStyle.blurple,
        emoji="📝",
        custom_id="persistent_view:qsm_sug_question",
    )
    async def add_question(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))


def return_realm_profile_modal(
        bot,
        realm_name: str,
        emoji: str,
        member_count: str,
        community_duration: str,
        world_duration: str,
        reset_schedule: str
):
    class ApplyForNewRealmForm(ui.Modal, title="Realm Application"):
        def __init__(self, bot, realm_name: str, type_of_realm: str, emoji: str, member_count: str,
                     community_duration: str, world_duration: str, reset_schedule: str):
            super().__init__(timeout=None)
            self.bot = bot
            self.realm_name = realm_name
            self.type_of_realm = type_of_realm
            self.emoji = emoji
            self.member_count = member_count
            self.community_duration = community_duration
            self.world_duration = world_duration
            self.reset_schedule = reset_schedule

        short_description = ui.TextInput(
            label="Short Description",
            style=discord.TextStyle.short,
            placeholder="Short description of the realm",
            required=True
        )

        long_description = ui.TextInput(
            label="Long Description",
            style=discord.TextStyle.long,
            placeholder="Long description of the realm",
            required=True
        )

        application_process = ui.TextInput(
            label="Application Process",
            style=discord.TextStyle.long,
            placeholder="Application process for the realm",
            required=True
        )

        foreseeable_future = ui.TextInput(
            label="Foreseeable Future",
            style=discord.TextStyle.long,
            placeholder="Will your Realm/Server have the ability to continue for the foreseeable future?",
            required=True
        )

        admin_team = ui.TextInput(
            label="Admin Team",
            style=discord.TextStyle.long,
            placeholder="Who is on your admin team and how long have they been with you?",
            required=True
        )

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = self.bot.get_channel(config['realmChannelResponse'])
        admin = discord.utils.get(interaction.guild.roles, name="Admin")
        q: database.RealmApplications = database.RealmApplications.create(
            discord_id=interaction.user.id,
            realm_name=self.realm_name,
            type_of_realm=self.type_of_realm,
            emoji=self.emoji,
            member_found=self.member_count,
            realm_age=self.community_duration,
            world_age=self.world_duration,
            reset_schedule=self.reset_schedule,
            short_desc=self.short_description.value,
            long_desc=self.long_description.value,
            application_process=self.application_process.value,
            foreseeable_future=self.foreseeable_future.value,
            admin_team=self.admin_team.value)
        q.save()
        database.db.close()

        embed = discord.Embed(title="Realm Application", description="__**Realm Owner:**__\n" +
                                                                     interaction.user.mention + "\n============================================",
                              color=0xb10d9f)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png")
        embed.add_field(name="__**Realm Name**__",
                        value=q.realm_name, inline=True)
        embed.add_field(name="__**Realm or Server?**__",
                        value=q.type_of_realm, inline=True)
        embed.add_field(name="__**Emoji**__",
                        value=q.emoji, inline=True)
        embed.add_field(name="__**Short Description**__",
                        value=q.short_desc, inline=False)
        embed.add_field(name="__**Long Description**__",
                        value=q.long_desc, inline=False)
        embed.add_field(name="__**Application Process**__",
                        value=q.application_process, inline=False)
        embed.add_field(name="__**Current Member Count**__",
                        value=q.member_count, inline=True)
        embed.add_field(name="__**Age of Community**__",
                        value=q.realm_age, inline=True)
        embed.add_field(name="__**Age of Current World**__",
                        value=q.world_age, inline=True)
        embed.add_field(name="__**How often do you reset**__",
                        value=q.reset_schedule, inline=True)
        embed.add_field(name="__**Will your Realm/Server have the ability to continue for the foreseeable future?**__",
                        value=q.foreseeable_future, inline=True)
        embed.add_field(name="__**Members of the OP Team, and How long they have been an OP**__",
                        value=q.admin_team, inline=False)
        embed.add_field(name="__**Reaction Codes**__",
                        value="Please react with the following codes to show your thoughts on this applicant.",
                        inline=False)
        embed.add_field(name="----💚----", value="Approved", inline=True)
        embed.add_field(name="----💛----",
                        value="More Time in Server", inline=True)
        embed.add_field(name="----❤️----", value="Rejected", inline=True)
        embed.set_footer(text="Realm Application #" + str(q.id) + " | " + datetime.now().strftime(r"%x"))
        await log_channel.send(admin.mention)

    return ApplyForNewRealmForm(bot, realm_name, type_of_realm, emoji, member_count, community_duration, world_duration,
                                reset_schedule)

def calculate_level(score):
    level = int((score // 100) ** 0.5)  # Adjust the divisor and power for level scaling
    next_level_score = (level + 1) ** 2 * 100  # Points needed for next level
    prev_level_score = level ** 2 * 100  # Points needed for the current level
    progress = (score - prev_level_score) / (next_level_score - prev_level_score)  # Progress percentage
    return level, progress