import discord
from discord.ui import View, Select, Button, Modal, TextInput
from typing import Callable, List
from utils.database import __database as database


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


# ---------- Dropdown for Channel Selection ---------- #
class ChannelSelectDropdown(Select):
    def __init__(
        self, field_name: str, channels: List[discord.TextChannel], callback: Callable
    ):
        self.field_name = field_name
        self.callback = callback
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in channels[:25]
        ]

        super().__init__(
            placeholder="Choose a channel...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, {self.field_name: self.values[0]})


# ---------- Multi-select Dropdown for Blocked Channels ---------- #
class MultiChannelSelectDropdown(Select):
    def __init__(
        self, field_name: str, channels: List[discord.TextChannel], callback: Callable
    ):
        self.field_name = field_name
        self.callback = callback
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in channels[:25]
        ]

        super().__init__(
            placeholder="Select one or more blocked channels...",
            options=options,
            min_values=1,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, {self.field_name: self.values})


# ---------- Dropdown for Role Selection ---------- #
class RoleSelectDropdown(Select):
    def __init__(self, field_name: str, roles: List[discord.Role], callback: Callable):
        self.field_name = field_name
        self.callback = callback
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in sorted(roles, key=lambda r: r.position, reverse=True)
            if not role.is_default()
        ][:25]

        super().__init__(
            placeholder="Choose a role...", options=options, min_values=1, max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, {self.field_name: self.values[0]})


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
        # Special case: role picker
        if self.field_name == "admin_role":
            roles = [role for role in interaction.guild.roles if not role.is_default()]
            view = View()
            view.add_item(RoleSelectDropdown(self.field_name, roles, self.on_update))
            await interaction.response.send_message(
                f"Select a role for **{self.label}**:",
                ephemeral=True,
                view=view,
            )
        # Special case: blocked channel multi-select
        elif self.field_name == "blocked_channels":
            channels = [ch for ch in interaction.guild.text_channels]
            view = View()
            view.add_item(
                MultiChannelSelectDropdown(self.field_name, channels, self.on_update)
            )
            await interaction.response.send_message(
                f"Select blocked channels:",
                ephemeral=True,
                view=view,
            )
        # Regular channel select
        elif self.is_channel:
            channels = [ch for ch in interaction.guild.text_channels]
            view = View()
            view.add_item(
                ChannelSelectDropdown(self.field_name, channels, self.on_update)
            )
            await interaction.response.send_message(
                f"Select a new channel for **{self.label}**:",
                ephemeral=True,
                view=view,
            )
        # Fallback to text modal
        else:
            await interaction.response.send_modal(
                SingleValueInputModal(
                    self.field_name,
                    str(self.bot_data.get(self.field_name, "")),
                    self.on_update,
                )
            )


# ---------- Views Per Section ---------- #
class WelcomeRulesView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(
            SettingButton("Server Name", "server_name", False, bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Server Description", "server_desc", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton("Invite Link", "server_invite", False, bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Other Info 1 Title", "other_info_1_title", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 1 Text", "other_info_1_text", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 2 Title", "other_info_2_title", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Other Info 2 Text", "other_info_2_text", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Welcome Channel", "welcome_channel", True, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton("Rule Channel", "rule_channel", True, bot_data, on_update)
        )


class BotSettingsView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(SettingButton("Prefix", "prefix", False, bot_data, on_update))
        self.add_item(
            SettingButton("Admin Role ID", "admin_role", False, bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Daily Questions Enabled",
                "daily_question_enabled",
                False,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton("Cooldown Time", "cooldown_time", False, bot_data, on_update)
        )
        self.add_item(
            SettingButton(
                "Points Per Message", "points_per_message", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Blocked Channels", "blocked_channels", False, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Enable Weekly Audit", "enable_weekly_audit", False, bot_data, on_update
            )
        )


class ChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(
            SettingButton(
                "Banned List Channel",
                "bannedlist_response_channel",
                True,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Daily Question Channel",
                "daily_question_channel",
                True,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Suggestions Channel",
                "question_suggest_channel",
                True,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "Bot Spam Channel", "bot_spam_channel", True, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton(
                "Realm Response Channel",
                "realm_channel_response",
                True,
                bot_data,
                on_update,
            )
        )
        self.add_item(
            SettingButton(
                "General Channel", "general_channel", True, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton("Mod Channel", "mod_channel", True, bot_data, on_update)
        )


class LogChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(
            SettingButton(
                "Message Log Channel", "message_log", True, bot_data, on_update
            )
        )
        self.add_item(
            SettingButton("Member Log Channel", "member_log", True, bot_data, on_update)
        )
        self.add_item(
            SettingButton("Server Log Channel", "server_log", True, bot_data, on_update)
        )
