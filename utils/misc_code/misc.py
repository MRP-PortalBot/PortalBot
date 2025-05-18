import asyncio
import time
import psutil
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from discord import app_commands

from core.checks import has_admin_level
from core.logging_module import get_log
from core import database

_log = get_log(__name__)


class MiscCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("MiscCMD Cog Loaded")
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    ##============================== /nick ==================================================
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
                f"{interaction.user} initiated nickname change for {user.display_name} using channel {channel.name}"
            )
            name = user.display_name
            channel_parts = channel.name.split("-")

            if len(channel_parts) == 2:
                realm, emoji = channel_parts
            else:
                realm, emoji = channel_parts[0], channel_parts[-1]

            await user.edit(nick=f"{name} {emoji}")
            await interaction.response.send_message(
                f"Changed {user.mention}'s nickname!"
            )
            _log.info(
                f"Successfully changed {user.display_name}'s nickname to {name} {emoji}"
            )

        except Exception as e:
            _log.error(f"Error changing nickname: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while changing the nickname.", ephemeral=True
            )

    ##============================== /ping ==================================================
    @app_commands.command(description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        try:
            _log.info(f"Ping command initiated by {interaction.user}")
            uptime = timedelta(seconds=int(time.time() - self.bot.start_time))
            ping_latency = round(self.bot.latency * 1000)

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
                text=f"PortalBot Version: {self.bot.version}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.response.send_message(embed=embed)
            _log.info("Ping and system resource info sent successfully.")

        except Exception as e:
            _log.error(f"Error in /ping command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching the ping information.",
                ephemeral=True,
            )

    ##============================== /remind_me ============================================
    @app_commands.command(
        name="remind_me",
        description="Set a reminder to be notified later about a message.",
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
            # Parse time unit
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            unit = remind_after[-1].lower()
            if unit not in time_units:
                raise ValueError("Invalid time unit.")
            duration = int(remind_after[:-1]) * time_units[unit]
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
            _log.info(
                f"Set reminder for {interaction.user} - message: {message_link} at {remind_at}"
            )

        except ValueError:
            await interaction.response.send_message(
                "⚠️ Invalid time format! Use something like `10m`, `2h`, or `1d`.",
                ephemeral=True,
            )
        except Exception as e:
            _log.error(f"Error setting reminder: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An error occurred while setting your reminder.", ephemeral=True
            )

    ##============================== Background Task =======================================
    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """
        Periodically check for reminders that are due and send DMs.
        """
        try:
            now = datetime.now()
            due_reminders = database.Reminder.select().where(
                database.Reminder.remind_at <= now
            )

            for reminder in due_reminders:
                user = self.bot.get_user(int(reminder.user_id))
                if user:
                    try:
                        await user.send(
                            f"🔔 Hey {user.mention}, here's your reminder for the message:\n{reminder.message_link}"
                        )
                        _log.info(
                            f"Reminder sent to {user.id}: {reminder.message_link}"
                        )
                    except Exception as e:
                        _log.warning(f"Failed to DM reminder to {user.id}: {e}")

                reminder.delete_instance()

        except Exception as e:
            _log.error(f"Error in reminder check loop: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(MiscCMD(bot))
    _log.info("MiscCMD Cog setup completed.")
