import discord
from discord.ui import View, Select
from typing import Callable
from utils.database import __database as database
import asyncio


class BotConfigSectionSelect(View):
    def __init__(self, bot_data: dict, on_submit_callback: Callable):
        super().__init__(timeout=60)
        self.bot_data = bot_data
        self.on_submit_callback = on_submit_callback
        self.add_item(BotConfigSectionDropdown(bot_data, on_submit_callback))


class BotConfigSectionDropdown(Select):
    def __init__(self, bot_data: dict, on_submit_callback: Callable):
        self.bot_data = bot_data
        self.on_submit_callback = on_submit_callback

        options = [
            discord.SelectOption(
                label="Welcome / Rules",
                value="welcome",
                description="Configure server name, desc, rules, invite",
            ),
            discord.SelectOption(
                label="Bot Settings",
                value="settings",
                description="Prefix, cooldowns, features",
            ),
            discord.SelectOption(
                label="Channel Assignments",
                value="channels",
                description="Feature-specific channels",
            ),
            discord.SelectOption(
                label="Log Channels", value="logs", description="Set log destinations"
            ),
        ]

        super().__init__(
            placeholder="Select a configuration section to edit...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        section = self.values[0]

        if section == "welcome":
            await interaction.response.send_modal(
                BotConfigModal_WelcomeRules(self.bot_data, self.on_submit_callback)
            )
            await interaction.followup.send(
                "📥 Select which channel to assign (optional):",
                ephemeral=True,
                view=BotWelcomeRuleChannelView(self.bot_data, self.on_submit_callback),
            )

        elif section == "settings":
            await interaction.response.send_modal(
                BotConfigModal_BotSettings(self.bot_data, self.on_submit_callback)
            )

        elif section == "channels":
            await interaction.response.send_message(
                "🔧 Select a channel to update:",
                ephemeral=True,
                view=BotChannelAssignmentView(self.bot_data, self.on_submit_callback),
            )

        elif section == "logs":
            await interaction.response.send_message(
                "🪵 Select a log channel to update:",
                ephemeral=True,
                view=BotLogChannelAssignmentView(
                    self.bot_data, self.on_submit_callback
                ),
            )


class BotConfigModal_WelcomeRules(
    discord.ui.Modal, title="Edit Welcome / Rules Settings"
):
    def __init__(self, bot_data: dict, on_submit_callback: Callable):
        super().__init__()
        self.bot_data = bot_data
        self.on_submit_callback = on_submit_callback

        self.server_name = discord.ui.TextInput(
            label="Server Name", default=bot_data.get("server_name", ""), max_length=100
        )
        self.add_item(self.server_name)

        self.server_desc = discord.ui.TextInput(
            label="Server Description",
            style=discord.TextStyle.paragraph,
            default=bot_data.get("server_desc", ""),
            max_length=300,
        )
        self.add_item(self.server_desc)

        self.server_invite = discord.ui.TextInput(
            label="Invite Link",
            default=bot_data.get("server_invite", ""),
            max_length=200,
        )
        self.add_item(self.server_invite)

        self.other_info_1_title = discord.ui.TextInput(
            label="Other Info Title #1",
            default=bot_data.get("other_info_1_title", ""),
            max_length=100,
        )
        self.add_item(self.other_info_1_title)

        self.other_info_1_text = discord.ui.TextInput(
            label="Other Info Text #1",
            style=discord.TextStyle.paragraph,
            default=bot_data.get("other_info_1_text", ""),
            max_length=300,
        )
        self.add_item(self.other_info_1_text)

    async def on_submit(self, interaction: discord.Interaction):
        new_data = {
            "server_name": self.server_name.value.strip(),
            "server_desc": self.server_desc.value.strip(),
            "server_invite": self.server_invite.value.strip(),
            "other_info_1_title": self.other_info_1_title.value.strip(),
            "other_info_1_text": self.other_info_1_text.value.strip(),
        }
        await self.on_submit_callback(interaction, new_data)


class BotWelcomeRuleChannelView(discord.ui.View):
    def __init__(self, bot_data: dict, on_channel_updated: Callable):
        super().__init__(timeout=120)
        self.bot_data = bot_data
        self.on_channel_updated = on_channel_updated

        self.add_item(ChannelButton("Welcome Channel", "welcome_channel"))
        self.add_item(ChannelButton("Rule Channel", "rule_channel"))


# -------- Modal: Bot Settings Section (Page 1) -------- #
class BotConfigModal_BotSettings(discord.ui.Modal, title="Edit Bot Settings (1/2)"):
    def __init__(self, bot_data: dict, on_submit_callback: Callable):
        super().__init__()
        self.bot_data = bot_data
        self.on_submit_callback = on_submit_callback

        self.prefix = discord.ui.TextInput(
            label="Bot Prefix", default=bot_data.get("prefix", "!"), max_length=5
        )
        self.admin_role = discord.ui.TextInput(
            label="Admin Role ID", default=bot_data.get("admin_role", ""), max_length=25
        )
        self.cooldown_time = discord.ui.TextInput(
            label="Cooldown Time (sec)",
            default=str(bot_data.get("cooldown_time", 120)),
            max_length=5,
        )
        self.points_per_message = discord.ui.TextInput(
            label="Points per Message",
            default=str(bot_data.get("points_per_message", 10)),
            max_length=5,
        )
        self.daily_question_enabled = discord.ui.TextInput(
            label="Enable Daily Questions (True/False)",
            default=str(bot_data.get("daily_question_enabled", True)),
            max_length=5,
        )

        self.add_item(self.prefix)
        self.add_item(self.admin_role)
        self.add_item(self.cooldown_time)
        self.add_item(self.points_per_message)
        self.add_item(self.daily_question_enabled)

    async def on_submit(self, interaction: discord.Interaction):
        new_data = {
            "prefix": self.prefix.value.strip(),
            "admin_role": self.admin_role.value.strip(),
            "cooldown_time": int(self.cooldown_time.value.strip()),
            "points_per_message": int(self.points_per_message.value.strip()),
            "daily_question_enabled": self.daily_question_enabled.value.strip().lower()
            in ("true", "1", "yes", "y"),
        }

        await self.on_submit_callback(interaction, new_data)

        # Automatically trigger the advanced modal
        await interaction.response.send_modal(
            BotConfigModal_BotSettingsAdvanced(self.bot_data, self.on_submit_callback)
        )


# -------- Modal: Bot Settings Section (Page 2) -------- #
class BotConfigModal_BotSettingsAdvanced(discord.ui.Modal, title="Bot Settings (2/2)"):
    def __init__(self, bot_data: dict, on_submit_callback: Callable):
        super().__init__()
        self.bot_data = bot_data
        self.on_submit_callback = on_submit_callback

        self.blocked_channels = discord.ui.TextInput(
            label="Blocked Channel IDs (comma-separated)",
            default=bot_data.get("blocked_channels", ""),
            placeholder="1234567890,0987654321",
            max_length=500,
        )
        self.enable_weekly_audit = discord.ui.TextInput(
            label="Enable Weekly Audit (True/False)",
            default=str(bot_data.get("enable_weekly_audit", True)),
            max_length=5,
        )

        self.add_item(self.blocked_channels)
        self.add_item(self.enable_weekly_audit)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.blocked_channels.value.strip()
        new_data = {
            "blocked_channels": [ch.strip() for ch in raw.split(",") if ch.strip()],
            "enable_weekly_audit": self.enable_weekly_audit.value.strip().lower()
            in ("true", "1", "yes", "y"),
        }

        await self.on_submit_callback(interaction, new_data)
        await interaction.followup.send("✅ Bot settings updated.", ephemeral=True)


class BotChannelAssignmentView(discord.ui.View):
    def __init__(self, bot_data: dict, on_channel_updated: Callable):
        super().__init__(timeout=120)
        self.bot_data = bot_data
        self.on_channel_updated = on_channel_updated

        self.add_item(ChannelButton("Mod Channel", "mod_channel"))
        self.add_item(ChannelButton("General Channel", "general_channel"))
        self.add_item(ChannelButton("Bot Spam Channel", "bot_spam_channel"))
        self.add_item(ChannelButton("Realm Channel", "realm_channel_response"))
        self.add_item(ChannelButton("Daily Question", "daily_question_channel"))
        self.add_item(ChannelButton("Suggestions", "question_suggest_channel"))
        self.add_item(ChannelButton("Banned List", "bannedlist_response_channel"))


class BotLogChannelAssignmentView(discord.ui.View):
    def __init__(self, bot_data: dict, on_channel_updated: Callable):
        super().__init__(timeout=120)
        self.bot_data = bot_data
        self.on_channel_updated = on_channel_updated

        self.add_item(ChannelButton("Message Log", "message_log"))
        self.add_item(ChannelButton("Member Log", "member_log"))
        self.add_item(ChannelButton("Server Log", "server_log"))


class ChannelButton(discord.ui.Button):
    def __init__(self, label: str, field_name: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.field_name = field_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Please tag the new channel for **{self.label}**.", ephemeral=True
        )

        def check(m: discord.Message):
            return (
                m.author.id == interaction.user.id
                and m.channel.id == interaction.channel.id
                and m.channel_mentions
            )

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30)
            new_channel = msg.channel_mentions[0]

            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(interaction.guild_id)
            )

            if not bot_data:
                await interaction.followup.send(
                    "❌ Bot data not found.", ephemeral=True
                )
                return

            setattr(bot_data, self.field_name, str(new_channel.id))
            bot_data.save()

            await msg.reply(
                f"✅ **{self.label}** updated to {new_channel.mention}",
                mention_author=False,
            )

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "❌ Timed out waiting for channel mention.", ephemeral=True
            )
