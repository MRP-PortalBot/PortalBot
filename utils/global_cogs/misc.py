import ast
import json
import random
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import io
import asyncio

import discord
from discord.ext import commands, tasks
from discord import app_commands

from core.checks import slash_is_bot_admin_1
from core.logging_module import get_log
from core import database

from PIL import Image, ImageDraw, ImageFont

_log = get_log(__name__)

# List of server rules
rules = [
    ":one: **No Harassment**, threats, hate speech, inappropriate language, posts or user names!",
    ":two: **No spamming** in chat or direct messages!",
    ":three: **No religious or political topics**, those don’t usually end well!",
    ":four: **Keep pinging to a minimum**, it is annoying!",
    ":five: **No sharing personal information**, it is personal for a reason so keep it to yourself!",
    ":six: **No self-promotion or advertisement outside the appropriate channels!** Want your own realm channel? **Apply for one!**",
    ":seven: **No realm or server is better than another!** It is **not** a competition.",
    ":eight: **Have fun** and happy crafting!",
    ":nine: **Discord Terms of Service apply!** You must be at least **13** years old.",
]


class MiscCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("MiscCMD Cog Loaded")
        self.check_reminders.start()  # Start the background task to check reminders

    def cog_unload(self):
        self.check_reminders.cancel()  # Stop the background task when the cog is unloaded

    ##======================================================Nick Command===========================================================
    @app_commands.command(
        name="nick",
        description="Change a user's nickname based on the channel name emoji.",
    )
    @app_commands.describe(
        user="The user whose nickname you want to change",
        channel="The channel with the emoji in the name",
    )
    @slash_is_bot_admin_1
    async def nick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        channel: discord.TextChannel,
    ):
        """Slash command to change a user's nickname based on the channel's emoji."""
        try:
            _log.info(
                f"{interaction.user} initiated nickname change for {user.display_name} using channel {channel.name}"
            )
            name = user.display_name
            channel_parts = channel.name.split("-")

            # Determine the emoji and realm format based on the channel name
            if len(channel_parts) == 2:  # realm-emoji format
                realm, emoji = channel_parts
            else:  # realm-name-emoji format
                realm, emoji = channel_parts[0], channel_parts[-1]

            # Update user's nickname with the emoji
            await user.edit(nick=f"{name} {emoji}")
            await interaction.response.send_message(
                f"Changed {user.mention}'s nickname!"
            )
            _log.info(
                f"Successfully changed {user.display_name}'s nickname to {name} {emoji}"
            )

        except Exception as e:
            _log.error(f"Error in changing nickname for {user.display_name}: {e}")
            await interaction.response.send_message(
                "An error occurred while changing the nickname.", ephemeral=True
            )
            
    ##======================================================Rule Command [INT]===========================================================
    @app_commands.command(name="rule", description="Sends out MRP Server Rules")
    async def rule(self, interaction: discord.Interaction, number: int = None):
        """Send the requested server rule."""
        try:
            if 1 <= number <= len(rules):
                await interaction.response.send_message(rules[number - 1])
                _log.info(f"Rule {number} sent by {interaction.user}")
            else:
                await interaction.response.send_message(
                    f"Please choose a valid rule number between 1 and {len(rules)}."
                )
                _log.warning(
                    f"Invalid rule number {number} requested by {interaction.user}"
                )
        except Exception as e:
            _log.error(f"Error in rule command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the rule.", ephemeral=True
            )

    ##======================================================Ping Command===========================================================
    @app_commands.command(description="Ping the bot")
    async def ping(self, interaction: discord.Interaction):
        """Display the bot's ping and system resource usage."""
        try:
            _log.info(f"Ping command initiated by {interaction.user}")
            uptime = timedelta(seconds=int(time.time() - self.bot.start_time))
            ping_latency = round(self.bot.latency * 1000)

            pingembed = discord.Embed(
                title="Pong! ⌛",
                color=discord.Color.purple(),
                description="Current Discord API Latency",
            )
            pingembed.set_author(name="PortalBot")
            pingembed.add_field(
                name="Ping & Uptime:",
                value=f"```diff\n+ Ping: {ping_latency}ms\n+ Uptime: {str(uptime)}\n```",
            )

            # Adding system resource usage details
            memory = psutil.virtual_memory()
            pingembed.add_field(
                name="System Resource Usage",
                value=f"```diff\n- CPU Usage: {psutil.cpu_percent()}%\n- Memory Usage: {memory.percent}%\n"
                f"- Total Memory: {memory.total / (1024**3):.2f} GB\n- Available Memory: {memory.available / (1024**3):.2f} GB\n```",
                inline=False,
            )

            pingembed.set_footer(
                text=f"PortalBot Version: {self.bot.version}",
                icon_url=interaction.user.display_avatar.url,
            )

            await interaction.response.send_message(embed=pingembed)
            _log.info(
                f"Ping and system resource information sent to {interaction.user}"
            )

        except Exception as e:
            _log.error(f"Error in ping command: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching the ping information.", ephemeral=True
            )

    ##======================================================Remind Me Command===========================================================
    @app_commands.command(name="remind_me", description="Set a reminder to be notified later about a message.")
    async def remind_me(self, interaction: discord.Interaction, message_link: str, remind_after: str):
        """
        Slash command to set a reminder for a message.
        Parameters:
        - message_link: Link to the message the user wants to be reminded about.
        - remind_after: Duration after which the user wants to be reminded (e.g., '10m', '2h').
        """
        try:
            # Parse the remind_after input
            time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            unit = remind_after[-1]
            if unit not in time_units:
                raise ValueError("Invalid time unit.")
            duration = int(remind_after[:-1]) * time_units[unit]

            remind_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)

            # Store reminder in the database
            database.Reminder.create(
                user_id=interaction.user.id,
                message_link=message_link,
                remind_at=remind_at
            )

            # Confirm reminder creation
            await interaction.response.send_message(
                f"Okay {interaction.user.mention}, I will remind you in {remind_after}.", ephemeral=True
            )
            _log.info(f"Set reminder for user {interaction.user} for message: {message_link}")

        except ValueError:
            await interaction.response.send_message(
                "Invalid time format! Please use a valid format like '10m', '2h', or '1d'.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error setting reminder for user {interaction.user}: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while setting your reminder.", ephemeral=True
            )

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """
        Background task that runs every minute to check for due reminders.
        """
        try:
            now = datetime.datetime.utcnow()
            due_reminders = database.Reminder.select().where(database.Reminder.remind_at <= now)

            for reminder in due_reminders:
                user = self.bot.get_user(reminder.user_id)
                if user:
                    reminder_message = f"Hey {user.mention}, here's your reminder for the message: {reminder.message_link}"
                    try:
                        await user.send(reminder_message)
                        _log.info(f"Sent reminder to user {user.id} for message: {reminder.message_link}")
                    except Exception as e:
                        _log.error(f"Failed to send reminder to user {user.id}: {e}", exc_info=True)

                # Delete the reminder after sending it
                reminder.delete_instance()

        except Exception as e:
            _log.error(f"Error checking reminders: {e}", exc_info=True)


# Set up the cog
async def setup(bot):
    await bot.add_cog(MiscCMD(bot))
    _log.info("MiscCMD Cog setup completed")
