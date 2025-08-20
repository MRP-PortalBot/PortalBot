# admin/bot_management/__bm_commands.py
import discord
import json
from discord import app_commands
from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from .__bm_views import BotConfigSectionSelectView
from utils.admin.bot_management.__bm_logic import (
    get_bot_data_for_server,
    fetch_admins_by_level,
)

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

    @app_commands.command(name="listguilds")
    @app_commands.is_owner()  # restricts to bot owner for safety
    async def list_guilds(self, ctx: commands.Context):
        """Lists all guilds the bot is currently in with ID and name."""
        guilds = sorted(self.bot.guilds, key=lambda g: g.name.lower())
        description = "\n".join([f"`{g.id}` - {g.name}" for g in guilds])

        embed = discord.Embed(
            title="📋 Guilds I'm In",
            description=description or "No guilds found.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Total: {len(guilds)} guilds")

        await ctx.send(embed=embed)

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

    @app_commands.command(name="bot_data", description="Edit server bot configuration.")
    @has_admin_level(2)
    async def bot_data(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )
        if not bot_data:
            await interaction.followup.send(
                "❌ BotData not found for this server.", ephemeral=True
            )
            return

        bot_data_dict = {
            field.name: getattr(bot_data, field.name)
            for field in bot_data._meta.sorted_fields
        }

        view = BotConfigSectionSelectView(bot_data_dict, self._wrap_update(interaction))
        await interaction.followup.send("Edit config:", view=view, ephemeral=True)

    def _wrap_update(self, source_interaction: discord.Interaction):
        async def update_callback(
            interaction: discord.Interaction, field_name: str, value
        ):
            updated = {}
            if field_name == "blocked_channels" and isinstance(value, list):
                updated[field_name] = value
            else:
                updated[field_name] = value
            await self.handle_botdata_update(source_interaction, updated)

        return update_callback

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


async def setup(bot: discord.Client):
    bot.tree.add_command(PermitCommands())
    bot.tree.add_command(ConfigCommands())
