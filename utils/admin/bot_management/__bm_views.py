import discord
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Callable
from utils.database import __database as database

MAX_OPTIONS = 25


# ---------- Modal for Text/Number/Boolean ---------- #
class SingleValueInputModal(Modal):
    def __init__(self, field_name: str, default: str, callback: Callable):
        super().__init__(title=f"Set {field_name.replace('_', ' ').title()}")
        self.field_name = field_name
        self.callback = callback

        self.input = TextInput(
            label="New Value",
            default=default,
            required=True,
            max_length=300,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.input.value)


# ---------- Paginated Channel View ---------- #
class PaginatedChannelView(View):
    def __init__(
        self,
        field_name: str,
        channels: list[discord.TextChannel],
        callback: Callable,
        label: str,
        page: int = 0,
    ):
        super().__init__(timeout=60)
        self.field_name = field_name
        self.channels = channels
        self.callback = callback
        self.label = label
        self.page = page

        self.max_pages = (len(channels) - 1) // MAX_OPTIONS

        self.select = ChannelSelectDropdown(
            self.field_name,
            self.channels[self.page * MAX_OPTIONS : (self.page + 1) * MAX_OPTIONS],
            callback,
        )
        self.add_item(self.select)

        if self.page > 0:
            self.add_item(NavButton("◀️ Prev", -1, self))
        if self.page < self.max_pages:
            self.add_item(NavButton("▶️ Next", 1, self))


class NavButton(Button):
    def __init__(self, label: str, direction: int, parent_view: PaginatedChannelView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.direction = direction
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        new_page = self.parent_view.page + self.direction
        new_view = PaginatedChannelView(
            self.parent_view.field_name,
            self.parent_view.channels,
            self.parent_view.callback,
            self.parent_view.label,
            new_page,
        )
        await interaction.response.edit_message(
            content=f"Select a new channel for **{self.parent_view.label}**:",
            view=new_view,
        )


class ChannelSelectDropdown(Select):
    def __init__(
        self, field_name: str, channels: list[discord.TextChannel], callback: Callable
    ):
        self.field_name = field_name
        self.callback = callback

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels
        ]

        super().__init__(
            placeholder="Choose a channel...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.values[0])


# ---------- Setting Button ---------- #
class SettingButton(Button):
    def __init__(
        self,
        label: str,
        field_name: str,
        is_channel: bool,
        bot_data: dict,
        on_update: Callable,
    ):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.label = label
        self.field_name = field_name
        self.is_channel = is_channel
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        if self.is_channel:
            channels = [ch for ch in interaction.guild.text_channels]
            view = PaginatedChannelView(
                self.field_name, channels, self.on_update, self.label
            )
            await interaction.response.send_message(
                f"Select a new channel for **{self.label}**:",
                ephemeral=True,
                view=view,
            )
        else:
            await interaction.response.send_modal(
                SingleValueInputModal(
                    self.field_name,
                    str(self.bot_data.get(self.field_name, "")),
                    self.on_update,
                )
            )


# ---------- Section Select View ---------- #
class BotConfigSectionSelectView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=120)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(
            ConfigSectionButton("Welcome / Rules", "welcome_rules", bot_data, on_update)
        )
        self.add_item(
            ConfigSectionButton("Bot Settings", "bot_settings", bot_data, on_update)
        )
        self.add_item(
            ConfigSectionButton(
                "Channel Assignments", "channel_assignments", bot_data, on_update
            )
        )
        self.add_item(
            ConfigSectionButton("Log Channels", "log_channels", bot_data, on_update)
        )


class ConfigSectionButton(Button):
    def __init__(self, label: str, section: str, bot_data: dict, on_update: Callable):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.section = section
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        if self.section == "welcome_rules":
            await interaction.response.send_message(
                "📋 Edit Welcome / Rules Settings",
                view=WelcomeRulesView(self.bot_data, self.on_update),
                ephemeral=True,
            )
        elif self.section == "bot_settings":
            await interaction.response.send_message(
                "⚙️ Edit Bot Settings",
                view=BotSettingsView(self.bot_data, self.on_update),
                ephemeral=True,
            )
        elif self.section == "channel_assignments":
            await interaction.response.send_message(
                "📺 Edit Channel Assignments",
                view=ChannelAssignmentView(self.bot_data, self.on_update),
                ephemeral=True,
            )
        elif self.section == "log_channels":
            await interaction.response.send_message(
                "📋 Edit Log Channels",
                view=LogChannelAssignmentView(self.bot_data, self.on_update),
                ephemeral=True,
            )


# ---------- Views Per Section ---------- #
class WelcomeRulesView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        for label, field, is_channel in [
            ("Server Name", "server_name", False),
            ("Server Description", "server_desc", False),
            ("Invite Link", "server_invite", False),
            ("Other Info 1 Title", "other_info_1_title", False),
            ("Other Info 1 Text", "other_info_1_text", False),
            ("Other Info 2 Title", "other_info_2_title", False),
            ("Other Info 2 Text", "other_info_2_text", False),
            ("Welcome Channel", "welcome_channel", True),
            ("Rule Channel", "rule_channel", True),
        ]:
            self.add_item(SettingButton(label, field, is_channel, bot_data, on_update))


class BotSettingsView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        for label, field in [
            ("Prefix", "prefix"),
            ("Admin Role ID", "admin_role"),
            ("Daily Questions Enabled", "daily_question_enabled"),
            ("Cooldown Time", "cooldown_time"),
            ("Points Per Message", "points_per_message"),
            ("Blocked Channels (JSON List)", "blocked_channels"),
            ("Enable Weekly Audit", "enable_weekly_audit"),
        ]:
            self.add_item(SettingButton(label, field, False, bot_data, on_update))


class ChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        for label, field in [
            ("Banned List Channel", "bannedlist_response_channel"),
            ("Daily Question Channel", "daily_question_channel"),
            ("Suggestions Channel", "question_suggest_channel"),
            ("Bot Spam Channel", "bot_spam_channel"),
            ("Realm Response Channel", "realm_channel_response"),
            ("General Channel", "general_channel"),
            ("Mod Channel", "mod_channel"),
        ]:
            self.add_item(SettingButton(label, field, True, bot_data, on_update))


class LogChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        for label, field in [
            ("Message Log Channel", "message_log"),
            ("Member Log Channel", "member_log"),
            ("Server Log Channel", "server_log"),
        ]:
            self.add_item(SettingButton(label, field, True, bot_data, on_update))
