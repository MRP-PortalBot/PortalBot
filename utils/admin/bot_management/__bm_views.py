import discord
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Callable, Optional


# ---------- Section Select View ---------- #
class BotConfigSectionSelectView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=120)
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


# ---------- Section Button ---------- #
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
                "🪵 Edit Log Channels",
                view=LogChannelAssignmentView(self.bot_data, self.on_update),
                ephemeral=True,
            )


# ---------- Modal for Input ---------- #
class SingleValueInputModal(Modal):
    def __init__(self, field_name: str, default: str, callback: Callable):
        super().__init__(title=f"Set {field_name.replace('_', ' ').title()}")
        self.field_name = field_name
        self.callback = callback

        self.input = TextInput(
            label="New Value", default=default, required=True, max_length=300
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.input.value)


# ---------- Dropdown Wrappers with Pagination ---------- #
class PaginatedDropdownView(View):
    def __init__(
        self,
        options: list,
        field_name: str,
        callback: Callable,
        is_multi: bool = False,
        page_size: int = 25,
    ):
        super().__init__(timeout=60)
        self.options = options
        self.field_name = field_name
        self.callback = callback
        self.page_size = page_size
        self.page = 0
        self.is_multi = is_multi
        self._update_dropdown()

    def _update_dropdown(self):
        self.clear_items()
        start = self.page * self.page_size
        end = start + self.page_size
        page_options = self.options[start:end]

        if self.is_multi:
            dropdown = MultiSelectDropdown(self.field_name, page_options, self.callback)
        else:
            dropdown = SingleSelectDropdown(
                self.field_name, page_options, self.callback
            )

        self.add_item(dropdown)

        if self.page > 0:
            self.add_item(PaginateButton("⬅️ Prev", self, -1))
        if end < len(self.options):
            self.add_item(PaginateButton("Next ➡️", self, 1))


class PaginateButton(Button):
    def __init__(self, label: str, view: PaginatedDropdownView, direction: int):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_ref = view
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.page += self.direction
        self.view_ref._update_dropdown()
        await interaction.response.edit_message(view=self.view_ref)


class SingleSelectDropdown(Select):
    def __init__(self, field_name: str, options: list, callback: Callable):
        self.field_name = field_name
        self._wrapped_callback = lambda i: callback(i, self.field_name, self.values[0])

        super().__init__(
            placeholder="Choose an option...",
            options=[
                discord.SelectOption(label=o.name, value=str(o.id)) for o in options
            ],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # <--- ADD THIS
        await self._wrapped_callback(interaction)



class MultiSelectDropdown(Select):
    def __init__(self, field_name: str, options: list, callback: Callable):
        self.field_name = field_name
        self._wrapped_callback = lambda i: callback(i, self.field_name, self.values)

        super().__init__(
            placeholder="Select multiple...",
            options=[
                discord.SelectOption(label=o.name, value=str(o.id)) for o in options
            ],
            min_values=0,
            max_values=min(25, len(options)),
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # <--- ADD THIS
        await self._wrapped_callback(interaction)



# ---------- Buttons ---------- #
class SettingButton(Button):
    def __init__(
        self,
        label: str,
        field_name: str,
        setting_type: str,
        bot_data: dict,
        on_update: Callable,
    ):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.field_name = field_name
        self.setting_type = setting_type  # 'text', 'channel', 'role', 'multi_channel'
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        if self.setting_type == "text":
            await interaction.response.send_modal(
                SingleValueInputModal(
                    self.field_name,
                    str(self.bot_data.get(self.field_name, "")),
                    self.on_update,
                )
            )
        elif self.setting_type == "channel":
            channels = interaction.guild.text_channels
            await interaction.response.send_message(
                f"Select a new channel for **{self.label}**:",
                ephemeral=True,
                view=PaginatedDropdownView(
                    list(channels), self.field_name, self.on_update
                ),
            )
        elif self.setting_type == "multi_channel":
            channels = interaction.guild.text_channels
            await interaction.response.send_message(
                f"Select channels to block for **{self.label}**:",
                ephemeral=True,
                view=PaginatedDropdownView(
                    list(channels), self.field_name, self.on_update, is_multi=True
                ),
            )
        elif self.setting_type == "role":
            roles = interaction.guild.roles
            await interaction.response.send_message(
                f"Select a new role for **{self.label}**:",
                ephemeral=True,
                view=PaginatedDropdownView(
                    list(roles), self.field_name, self.on_update
                ),
            )


# ---------- Section Views ---------- #
class WelcomeRulesView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.add_item(
            SettingButton("Server Name", "server_name", "text", bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Server Description", "server_desc", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton("Invite Link", "server_invite", "text", bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Other Info 1 Title", "other_info_1_title", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 1 Text", "other_info_1_text", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 2 Title", "other_info_2_title", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 2 Text", "other_info_2_text", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Welcome Channel", "welcome_channel", "channel", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Rule Channel", "rule_channel", "channel", bot_data, on_update
            )
        )


class BotSettingsView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.add_item(SettingButton("Prefix", "prefix", "text", bot_data, on_update))
        self.add_item(
            SettingButton("Admin Role ID", "admin_role", "role", bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Daily Questions Enabled",
                "daily_question_enabled",
                "text",
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton("Cooldown Time", "cooldown_time", "text", bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Points Per Message", "points_per_message", "text", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Blocked Channels",
                "blocked_channels",
                "multi_channel",
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Enable Weekly Audit",
                "enable_weekly_audit",
                "text",
                bot_data,
                on_update,
            )
        )


class ChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        fields = [
            ("Banned List Channel", "bannedlist_response_channel"),
            ("Daily Question Channel", "daily_question_channel"),
            ("Suggestions Channel", "question_suggest_channel"),
            ("Bot Spam Channel", "bot_spam_channel"),
            ("Realm Response Channel", "realm_channel_response"),
            ("General Channel", "general_channel"),
            ("Mod Channel", "mod_channel"),
        ]
        for label, field in fields:
            self.add_item(SettingButton(label, field, "channel", bot_data, on_update))


class LogChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.add_item(
            SettingButton(
                "Message Log Channel", "message_log", "channel", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Member Log Channel", "member_log", "channel", bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Server Log Channel", "server_log", "channel", bot_data, on_update
            )
        )
