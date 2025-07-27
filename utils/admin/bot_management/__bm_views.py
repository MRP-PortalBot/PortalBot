# admin/bot_management/__bm_views.py
import discord
from discord.ui import View, Button, Modal, TextInput, Select
from typing import Callable


class BotConfigSectionSelectView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=120)
        self.bot_data = bot_data
        self.on_update = on_update

        self.add_item(ConfigSectionButton("Welcome / Rules", "welcome_rules", bot_data, on_update))
        self.add_item(ConfigSectionButton("Bot Settings", "bot_settings", bot_data, on_update))
        self.add_item(ConfigSectionButton("Channel Assignments", "channel_assignments", bot_data, on_update))
        self.add_item(ConfigSectionButton("Log Channels", "log_channels", bot_data, on_update))


class ConfigSectionButton(Button):
    def __init__(self, label: str, section: str, bot_data: dict, on_update: Callable):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.section = section
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        section_view_map = {
            "welcome_rules": WelcomeRulesView,
            "bot_settings": BotSettingsView,
            "channel_assignments": ChannelAssignmentView,
            "log_channels": LogChannelAssignmentView,
        }

        view_class = section_view_map.get(self.section)
        if view_class:
            await interaction.response.send_message(
                f"📋 Edit: {self.label}",
                view=view_class(self.bot_data, self.on_update),
                ephemeral=True,
            )


class SingleValueInputModal(Modal):
    def __init__(self, field_name: str, default: str, callback: Callable):
        super().__init__(title=f"Set {field_name.replace('_', ' ').title()}")
        self.field_name = field_name
        self.callback = callback

        self.input = TextInput(label="New Value", default=default, required=True, max_length=300)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.input.value)


class ChannelSelectDropdown(Select):
    def __init__(self, field_name: str, channels: list[discord.TextChannel], callback: Callable):
        self.field_name = field_name
        self.callback = callback

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels
        ]

        super().__init__(placeholder="Choose a channel...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await self.callback(interaction, self.field_name, self.values[0])


class SettingButton(Button):
    def __init__(self, label: str, field_name: str, is_channel: bool, bot_data: dict, on_update: Callable):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.field_name = field_name
        self.is_channel = is_channel
        self.bot_data = bot_data
        self.on_update = on_update

    async def callback(self, interaction: discord.Interaction):
        if self.is_channel:
            channels = [ch for ch in interaction.guild.text_channels]
            view = View()
            view.add_item(ChannelSelectDropdown(self.field_name, channels, self.on_update))
            await interaction.response.send_message(
                f"📺 Select a new channel for **{self.label}**:",
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


class WelcomeRulesView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        items = [
            ("Server Name", False), ("Server Description", False), ("Invite Link", False),
            ("Other Info 1 Title", False), ("Other Info 1 Text", False),
            ("Other Info 2 Title", False), ("Other Info 2 Text", False),
            ("Welcome Channel", True), ("Rule Channel", True)
        ]
        for label, is_channel in items:
            field_name = label.lower().replace(" ", "_")
            self.add_item(SettingButton(label, field_name, is_channel, bot_data, on_update))


class BotSettingsView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        items = [
            ("Prefix", False), ("Admin Role ID", False), ("Daily Questions Enabled", False),
            ("Cooldown Time", False), ("Points Per Message", False),
            ("Blocked Channels (JSON List)", False), ("Enable Weekly Audit", False)
        ]
        for label, is_channel in items:
            field_name = label.lower().replace(" ", "_").replace("(json_list)", "blocked_channels").strip("()")
            self.add_item(SettingButton(label, field_name, is_channel, bot_data, on_update))


class ChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        labels = [
            "Banned List Channel", "Daily Question Channel", "Suggestions Channel",
            "Bot Spam Channel", "Realm Response Channel", "General Channel", "Mod Channel"
        ]
        for label in labels:
            field_name = label.lower().replace(" ", "_")
            self.add_item(SettingButton(label, field_name, True, bot_data, on_update))


class LogChannelAssignmentView(View):
    def __init__(self, bot_data: dict, on_update: Callable):
        super().__init__(timeout=180)
        labels = ["Message Log Channel", "Member Log Channel", "Server Log Channel"]
        for label in labels:
            field_name = label.lower().replace(" ", "_")
            self.add_item(SettingButton(label, field_name, True, bot_data, on_update))
