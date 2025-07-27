# admin/bot_management/__bm_commands.py (UPDATED)
import discord
import json
from discord import app_commands
from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from .__bm_logic import fetch_admins_by_level
from .__bm_views import BotConfigSectionDropdown
from utils.admin.bot_management.__bm_logic import (
    get_bot_data_for_server,
)
from utils.core_features.__constants import EmbedColors

_log = get_log(__name__)


class PermitCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="permit", description="Manage bot permits")

    @app_commands.command(name="list", description="List all permit levels.")
    @has_admin_level(1)
    async def list(self, interaction: discord.Interaction):
        levels = [1, 2, 3, 4]
        names = ["Moderators", "Administrators", "Bot Manager", "Owners"]
        embeds = []

        for level, label in zip(levels, names):
            admins = await fetch_admins_by_level(interaction.client, level)
            embeds.append(f"**Permit {level}: {label}**\n" + "\n".join(admins))

        embed = discord.Embed(
            title="Bot Administrators",
            description="\n\n".join(embeds),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Only Permit 4 users can modify administrator list.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add", description="Add a bot administrator.")
    @app_commands.describe(user="User to add", level="Permit level (1–4)")
    @has_admin_level(4)
    async def add(
        self, interaction: discord.Interaction, user: discord.User, level: int
    ):
        if level not in (1, 2, 3, 4):
            await interaction.response.send_message(
                "Permit level must be 1–4.", ephemeral=True
            )
            return

        database.db.connect(reuse_if_open=True)
        try:
            query = database.Administrators.get_or_none(
                database.Administrators.discordID == str(user.id)
            )
            if query:
                query.TierLevel = level
                query.discord_name = user.name
                query.save()
                msg = f"{user.name}'s permit level updated to `{level}`."
            else:
                database.Administrators.create(
                    discordID=str(user.id), discord_name=user.name, TierLevel=level
                )
                msg = f"{user.name} added with permit level `{level}`."

            embed = discord.Embed(
                title="✅ User Updated", description=msg, color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error adding/updating {user}: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to update user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()

    @app_commands.command(name="remove", description="Remove a bot administrator.")
    @app_commands.describe(user="User to remove")
    @has_admin_level(4)
    async def remove(self, interaction: discord.Interaction, user: discord.User):
        database.db.connect(reuse_if_open=True)
        try:
            query = database.Administrators.get_or_none(
                database.Administrators.discordID == str(user.id)
            )
            if query:
                query.delete_instance()
                msg = f"{user.name} has been removed."
                color = discord.Color.green()
            else:
                msg = f"No record found for {user.name}."
                color = discord.Color.red()

            embed = discord.Embed(
                title="🔧 Removal Result", description=msg, color=color
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error removing {user}: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to remove user.", ephemeral=True
            )
        finally:
            if not database.db.is_closed():
                database.db.close()


class ConfigCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="configure", description="Bot configuration commands")

    @app_commands.command(
        name="edit_data", description="Edit server bot configuration."
    )
    @has_admin_level(2)
    async def edit_data(self, interaction: discord.Interaction):
        await interaction.defer(ephemeral=True)

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )

        if not bot_data:
            await interaction.followup.send(
                "❌ BotData not found for this server.", ephemeral=True
            )
            return

        # Convert model to dict for ease of use
        bot_data_dict = {
            field.name: getattr(bot_data, field.name)
            for field in bot_data._meta.sorted_fields
        }

        # Show select dropdown
        view = discord.ui.View(timeout=180)
        dropdown = BotConfigSectionDropdown(bot_data_dict, self.handle_botdata_update)
        view.add_item(dropdown)

        await interaction.followup.send(
            "🛠 Choose a section to edit from the dropdown menu:",
            ephemeral=True,
            view=view,
        )

    # Callback to apply modal changes
    async def handle_botdata_update(
        self, interaction: discord.Interaction, updated_fields: dict
    ):
        try:
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(interaction.guild.id)
            )
            if not bot_data:
                await interaction.followup.send("❌ BotData not found.", ephemeral=True)
                return

            for key, value in updated_fields.items():
                setattr(bot_data, key, value)

            bot_data.save()
            await interaction.followup.send("✅ Bot settings updated.", ephemeral=True)

        except Exception as e:
            _log.error(f"Error updating bot data: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ Failed to update settings.", ephemeral=True
            )

    @app_commands.command(
        name="view_data", description="View current bot configuration for this server."
    )
    @has_admin_level(2)
    async def view_data(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )

        if not bot_data:
            await interaction.followup.send("❌ BotData not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔎 Bot Configuration", color=discord.Color.blurple()
        )

        for field in bot_data._meta.sorted_fields:
            value = getattr(bot_data, field.name)
            display_value = str(value)
            if field.name in {"blocked_channels"}:
                display_value = "\n".join(json.loads(value)) if value else "[]"
            elif field.name.endswith("_channel") or field.name.endswith("_log"):
                display_value = f"<#{value}>" if value and value.isdigit() else value
            elif len(display_value) > 1024:
                display_value = display_value[:1021] + "..."
            embed.add_field(
                name=field.name, value=display_value or "None", inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="setup", description="Initialize bot configuration for this server."
    )
    @has_admin_level(2)
    async def setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        existing = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )

        if existing:
            await interaction.followup.send(
                "ℹ️ Bot configuration already exists.", ephemeral=True
            )
            return

        try:
            database.BotData.create(
                server_id=str(interaction.guild.id),
                server_name=interaction.guild.name,
                bot_id=str(interaction.client.user.id),
            )
            await interaction.followup.send(
                "✅ Bot configuration initialized.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Bot setup failed: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ Failed to initialize BotData.", ephemeral=True
            )

    @app_commands.command(name="set_cooldown", description="Set score cooldown time.")
    @has_admin_level(3)
    async def set_cooldown(self, interaction: discord.Interaction, cooldown: int):
        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        if bot_data:
            bot_data.cooldown_time = cooldown
            bot_data.save()
            await interaction.response.send_message(
                f"Cooldown updated to {cooldown} seconds."
            )
        else:
            await interaction.response.send_message("BotData not found.")

    @app_commands.command(
        name="set_points", description="Set score points per message."
    )
    @has_admin_level(3)
    async def set_points(self, interaction: discord.Interaction, points: int):
        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        if bot_data:
            bot_data.points_per_message = points
            bot_data.save()
            await interaction.response.send_message(
                f"Points per message updated to {points}."
            )
        else:
            await interaction.response.send_message("BotData not found.")

    @app_commands.command(name="add_blocked_channel", description="Block a channel.")
    @has_admin_level(3)
    async def add_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        if not bot_data:
            await interaction.response.send_message("BotData not found.")
            return

        try:
            blocked = json.loads(bot_data.blocked_channels or "[]")
            if str(channel.id) not in blocked:
                blocked.append(str(channel.id))
                bot_data.blocked_channels = json.dumps(blocked)
                bot_data.save()
                await interaction.response.send_message(
                    f"{channel.mention} has been blocked."
                )
            else:
                await interaction.response.send_message(
                    f"{channel.mention} is already blocked."
                )
        except Exception as e:
            _log.error(f"Error blocking channel: {e}")
            await interaction.response.send_message(
                "Failed to update blocked channels.", ephemeral=True
            )

    @app_commands.command(
        name="remove_blocked_channel", description="Unblock a channel."
    )
    @has_admin_level(3)
    async def remove_blocked_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        if not bot_data:
            await interaction.response.send_message("BotData not found.")
            return

        blocked = bot_data.get_blocked_channels()
        if channel.id in blocked:
            blocked.remove(channel.id)
            bot_data.set_blocked_channels(blocked)
            bot_data.save()
            await interaction.response.send_message(
                f"{channel.mention} has been unblocked."
            )
        else:
            await interaction.response.send_message(
                f"{channel.mention} is not blocked."
            )

    @app_commands.command(name="view", description="View current bot configuration.")
    @has_admin_level(3)
    async def view_config(self, interaction: discord.Interaction):
        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        if not bot_data:
            await interaction.response.send_message(
                "BotData not found.", ephemeral=True
            )
            return

        blocked_ids = bot_data.get_blocked_channels()
        blocked_mentions = [
            (
                interaction.guild.get_channel(int(cid)).mention
                if interaction.guild.get_channel(int(cid))
                else f"`{cid}`"
            )
            for cid in blocked_ids
        ]

        embed = discord.Embed(
            title=f"🔧 Bot Configuration for {interaction.guild.name}",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="⏱️ Cooldown Time", value=f"{bot_data.cooldown_time}s", inline=True
        )
        embed.add_field(
            name="🏅 Points per Message",
            value=str(bot_data.points_per_message),
            inline=True,
        )
        embed.add_field(
            name="🚫 Blocked Channels",
            value="\n".join(blocked_mentions) or "*None*",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Register both slash command groups with the bot in the setup function
async def setup(bot: discord.Client):
    bot.tree.add_command(PermitCommands())
    bot.tree.add_command(ConfigCommands())
