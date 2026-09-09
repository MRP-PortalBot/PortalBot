import asyncio
import time
import psutil
from datetime import datetime, timedelta

import discord
from discord.ext import tasks
from discord import app_commands

from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from utils.database import __database as database

from .__utility_logic import build_utility_embed, run_reminder_loop


_log = get_log(__name__)


class UtilityCommands(app_commands.Group):
    def __init__(self, bot: discord.Client):
        super().__init__(name="utility", description="General utility commands")
        self.bot = bot  # 🔧 Save it here
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        await run_reminder_loop(self.bot)

    # ========== /utility ping ==========
    @app_commands.command(name="ping", description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        try:
            _log.info(f"Ping command initiated by {interaction.user}")
            uptime = timedelta(seconds=int(time.time() - interaction.client.start_time))
            ping_latency = round(interaction.client.latency * 1000)

            memory = psutil.virtual_memory()

            embed = discord.Embed(
                title="Pong! ⌛",
                description="Current Discord API Latency",
                color=discord.Color.purple(),
            )
            embed.set_author(name="PortalBot")
            embed.add_field(
                name="Ping & Uptime:",
                value=f"```diff\n+ Ping: {ping_latency}ms\n+ Uptime: {str(uptime)}\n```",
            )
            embed.add_field(
                name="System Resource Usage",
                value=f"```diff\n- CPU Usage: {psutil.cpu_percent()}%\n- Memory Usage: {memory.percent}%\n"
                f"- Total Memory: {memory.total / (1024**3):.2f} GB\n- Available Memory: {memory.available / (1024**3):.2f} GB\n```",
                inline=False,
            )
            embed.set_footer(
                text=f"PortalBot Version: {interaction.client.version}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            _log.error(f"Error in /ping command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching ping information.",
                ephemeral=True,
            )

    # ========== /utility nick ==========
    @app_commands.command(
        name="nick",
        description="Change a user's nickname based on the channel name emoji.",
    )
    @app_commands.describe(
        user="The user whose nickname you want to change",
        channel="The channel with the emoji in the name",
    )
    @has_admin_level(1)
    async def nick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        channel: discord.TextChannel,
    ):
        try:
            _log.info(
                f"{interaction.user} initiated nickname change for {user.display_name} using {channel.name}"
            )
            name = user.display_name
            parts = channel.name.split("-")

            realm, emoji = (parts[0], parts[-1]) if len(parts) != 2 else parts
            await user.edit(nick=f"{name} {emoji}")
            await interaction.response.send_message(
                f"Changed {user.mention}'s nickname!"
            )

        except Exception as e:
            _log.error(f"Error changing nickname: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while changing the nickname.", ephemeral=True
            )

    # ========== /utility remind_me ==========
    @app_commands.command(
        name="remind_me",
        description="Set a reminder to be notified later about a message.",
    )
    @app_commands.describe(
        message_link="A link to the message you want to be reminded about.",
        remind_after="How long until you're reminded (e.g., 10m, 2h, 1d)",
    )
    async def remind_me(
        self, interaction: discord.Interaction, message_link: str, remind_after: str
    ):
        if not message_link.startswith("https://discord.com/channels/"):
            await interaction.response.send_message(
                "⚠️ Please provide a valid Discord message link.", ephemeral=True
            )
            return

        try:
            units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            unit = remind_after[-1].lower()
            if unit not in units:
                raise ValueError("Invalid time unit.")
            duration = int(remind_after[:-1]) * units[unit]
            remind_at = datetime.now() + timedelta(seconds=duration)

            database.Reminder.create(
                user_id=str(interaction.user.id),
                message_link=message_link,
                remind_at=remind_at,
            )

            await interaction.response.send_message(
                f"⏰ Okay {interaction.user.mention}, I'll remind you in `{remind_after}`.",
                ephemeral=True,
            )

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Invalid time format! Use `10m`, `2h`, `1d`, etc.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error setting reminder: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to set reminder.", ephemeral=True
            )


    # ========== /utility embed ==========
    @has_admin_level(3)
    @app_commands.command(name="embed", description="Post a custom embed in this channel.")
    @app_commands.guild_only()
    @app_commands.describe(
        title="Embed title (up to 256 characters)",
        body="Main text; Discord Markdown is supported (up to 4,096 characters)",
        color="Six-digit hex color, e.g. #9B59B6",
        url="Link opened when the title is clicked",
        thumbnail="Small image URL at the top right", image="Large image URL below the text",
        author="Author name above the title", author_url="Link for the author name",
        author_icon="Small author icon URL", footer="Footer text", footer_icon="Footer icon URL",
        timestamp="now or an ISO date/time; times without an offset use UTC",
        fields="One per line: Name | Value | inline (inline is optional)",
    )
    async def embed(
        self, interaction: discord.Interaction, title: str, body: str,
        color: str | None = None, url: str | None = None,
        thumbnail: str | None = None, image: str | None = None,
        author: str | None = None, author_url: str | None = None,
        author_icon: str | None = None, footer: str | None = None,
        footer_icon: str | None = None, timestamp: str | None = None,
        fields: str | None = None,
    ):
        if not interaction.guild or not interaction.channel:
            await interaction.response.send_message("Use this command in a server channel.", ephemeral=True)
            return
        try:
            embed = build_utility_embed(
                title, body, color=color, url=url, thumbnail=thumbnail, image=image,
                author=author, author_url=author_url, author_icon=author_icon,
                footer=footer, footer_icon=footer_icon, timestamp=timestamp, fields=fields,
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            await interaction.followup.send(
                "I couldn't post the embed. Check my Send Messages and Embed Links permissions.",
                ephemeral=True,
            )
            return
        await interaction.followup.send("Embed posted.", ephemeral=True)


async def setup(bot: discord.Client):
    bot.tree.add_command(UtilityCommands(bot))  # ✅ Pass it in
