import discord
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Callable


# ---------- Base Section Select View ---------- #
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


# ---------- Section Button ---------- #
class ConfigSectionButton(Button):
    def __init__(self, label: str, section: str, bot_data: dict, on_update: Callable):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.section = section
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        views = {
            "welcome_rules": WelcomeRulesView,
            "bot_settings": BotSettingsView,
            "channel_assignments": ChannelAssignmentView,
            "log_channels": LogChannelAssignmentView,
        }

        await interaction.response.send_message(
            f"🛠️ Editing: {self.label}",
            view=views[self.section](self.bot_data, self.on_update),
            ephemeral=True,
        )


# ---------- Input Modal ---------- #
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


# ---------- Paginated Channel Dropdown ---------- #
class ChannelSelectDropdown(Select):
    def __init__(
        self,
        field_name: str,
        channels: list[discord.TextChannel],
        page: int,
        callback: Callable,
    ):
        self.field_name = field_name
        self.page = page
        self.callback = callback

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in channels[page * 25 : (page + 1) * 25]
        ]

        super().__init__(
            placeholder="Choose a channel...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"{field_name}_channel_dropdown",
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.values[0])


# ---------- Paginated Role Dropdown ---------- #
class RoleSelectDropdown(Select):
    def __init__(
        self, field_name: str, roles: list[discord.Role], page: int, callback: Callable
    ):
        self.field_name = field_name
        self.page = page
        self.callback = callback

        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles[page * 25 : (page + 1) * 25]
        ]

        super().__init__(
            placeholder="Choose a role...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"{field_name}_role_dropdown",
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.values[0])


# ---------- Paginated Multi-Channel Dropdown ---------- #
class MultiChannelSelectDropdown(Select):
    def __init__(
        self,
        field_name: str,
        channels: list[discord.TextChannel],
        page: int,
        callback: Callable,
    ):
        self.field_name = field_name
        self.page = page
        self.callback = callback

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in channels[page * 25 : (page + 1) * 25]
        ]

        super().__init__(
            placeholder="Select channels to block...",
            options=options,
            min_values=1,
            max_values=len(options),
            custom_id=f"{field_name}_multi_channel_dropdown",
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.values)


# ---------- View with Prev/Next Navigation ---------- #
class PaginatedDropdownView(View):
    def __init__(
        self, label, field_name, data_list, is_multi, is_roles, callback, page=0
    ):
        super().__init__(timeout=60)
        self.label = label
        self.field_name = field_name
        self.page = page
        self.data = data_list
        self.callback = callback
        self.is_multi = is_multi
        self.is_roles = is_roles

        if is_roles:
            self.add_item(RoleSelectDropdown(field_name, data_list, page, callback))
        elif is_multi:
            self.add_item(
                MultiChannelSelectDropdown(field_name, data_list, page, callback)
            )
        else:
            self.add_item(ChannelSelectDropdown(field_name, data_list, page, callback))

        if len(data_list) > 25:
            if page > 0:
                self.add_item(PageButton("⬅️ Prev", -1, self))
            if (page + 1) * 25 < len(data_list):
                self.add_item(PageButton("Next ➡️", 1, self))


class PageButton(Button):
    def __init__(self, label: str, direction: int, parent: PaginatedDropdownView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.direction = direction
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        new_page = self.parent.page + self.direction
        await interaction.response.edit_message(
            content=f"Select a new option for **{self.parent.label}**:",
            view=PaginatedDropdownView(
                self.parent.label,
                self.parent.field_name,
                self.parent.data,
                self.parent.is_multi,
                self.parent.is_roles,
                self.parent.callback,
                page=new_page,
            ),
        )


# ---------- Button Logic ---------- #
class SettingButton(Button):
    def __init__(
        self,
        label: str,
        field_name: str,
        is_channel: bool,
        is_roles: bool,
        is_multi: bool,
        bot_data: dict,
        on_update: Callable,
    ):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.label_text = label
        self.field_name = field_name
        self.is_channel = is_channel
        self.is_roles = is_roles
        self.is_multi = is_multi
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        if self.is_channel:
            items = interaction.guild.text_channels
        elif self.is_roles:
            items = interaction.guild.roles
        else:
            items = None

        if items:
            await interaction.response.send_message(
                f"Select a new option for **{self.label_text}**:",
                ephemeral=True,
                view=PaginatedDropdownView(
                    self.label_text,
                    self.field_name,
                    items,
                    self.is_multi,
                    self.is_roles,
                    self.on_update,
                ),
            )
        else:
            await interaction.response.send_modal(
                SingleValueInputModal(
                    self.field_name,
                    str(self.bot_data.get(self.field_name, "")),
                    self.on_update,
                )
            )


# ---------- Section Views ---------- #
class WelcomeRulesView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        for label, key in [
            ("Server Name", "server_name"),
            ("Server Description", "server_desc"),
            ("Invite Link", "server_invite"),
            ("Other Info 1 Title", "other_info_1_title"),
            ("Other Info 1 Text", "other_info_1_text"),
            ("Other Info 2 Title", "other_info_2_title"),
            ("Other Info 2 Text", "other_info_2_text"),
        ]:
            self.add_item(
                SettingButton(label, key, False, False, False, bot_data, on_update)
            )

        self.add_item(
            SettingButton(
                "Welcome Channel",
                "welcome_channel",
                True,
                False,
                False,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Rule Channel", "rule_channel", True, False, False, bot_data, on_update
            )
        )


class BotSettingsView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(
            SettingButton("Prefix", "prefix", False, False, False, bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Admin Role ID", "admin_role", False, True, False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Daily Questions Enabled",
                "daily_question_enabled",
                False,
                False,
                False,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Cooldown Time",
                "cooldown_time",
                False,
                False,
                False,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Points Per Message",
                "points_per_message",
                False,
                False,
                False,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Blocked Channels",
                "blocked_channels",
                True,
                False,
                True,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Enable Weekly Audit",
                "enable_weekly_audit",
                False,
                False,
                False,
                bot_data,
                on_update,
            )
        )


class ChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        for label, key in [
            ("Banned List Channel", "bannedlist_response_channel"),
            ("Daily Question Channel", "daily_question_channel"),
            ("Suggestions Channel", "question_suggest_channel"),
            ("Bot Spam Channel", "bot_spam_channel"),
            ("Realm Response Channel", "realm_channel_response"),
            ("General Channel", "general_channel"),
            ("Mod Channel", "mod_channel"),
        ]:
            self.add_item(
                SettingButton(label, key, True, False, False, bot_data, on_update)
            )


class LogChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        for label, key in [
            ("Message Log Channel", "message_log"),
            ("Member Log Channel", "member_log"),
            ("Server Log Channel", "server_log"),
        ]:
            self.add_item(
                SettingButton(label, key, True, False, False, bot_data, on_update)
            )
