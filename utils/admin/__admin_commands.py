import discord
from discord import app_commands, ui
from discord.ext import commands
from pathlib import Path
from typing import Union, Literal
from core import database
from core.checks import has_admin_level
from core.logging_module import get_log
from core.common import (
    get_cached_bot_data,
    get_bot_data_for_server,
    refresh_bot_data_cache,
)
from core.constants import EmbedColors

_log = get_log(__name__)


class AdminCommands(commands.GroupCog, name="admin"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="requestdb", description="Request the database file for manual inspection."
    )
    @has_admin_level(4)
    async def requestdb(self, interaction: discord.Interaction):
        try:
            db_file = Path("data.db")
            if not db_file.exists():
                await interaction.response.send_message(
                    "Database does not exist yet.", ephemeral=True
                )
                return

            with db_file.open("rb") as f:
                file = discord.File(f, filename="database.db")
                try:
                    await interaction.user.send(file=file)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "I couldn't DM you the file. Please enable DMs.", ephemeral=True
                    )
                    return

            await interaction.response.send_message(
                "Database file sent to your DMs.", ephemeral=True
            )
            _log.info(f"{interaction.user} requested and received database file.")

        except Exception as e:
            _log.error(f"requestdb error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to send database file.", ephemeral=True
            )

    @app_commands.command(name="deletedb", description="Delete the database file.")
    @has_admin_level(4)
    async def deletedb(self, interaction: discord.Interaction):
        try:
            if not database.db.is_closed():
                await interaction.response.send_message(
                    "Database is in use. Cannot delete.", ephemeral=True
                )
                return

            db_file = Path("data.db")
            if db_file.exists():
                db_file.unlink()
                await interaction.response.send_message(
                    "Database file deleted.", ephemeral=True
                )
                _log.info(f"{interaction.user} deleted the database file.")
            else:
                await interaction.response.send_message(
                    "Database file does not exist.", ephemeral=True
                )

        except Exception as e:
            _log.error(f"deletedb error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to delete database file.", ephemeral=True
            )

    @app_commands.command(
        name="replacedb", description="Replace the database file via upload."
    )
    @has_admin_level(4)
    async def replacedb(self, interaction: discord.Interaction):
        try:
            if not database.db.is_closed():
                await interaction.response.send_message(
                    "Database is in use. Cannot replace.", ephemeral=True
                )
                return

            if not interaction.attachments:
                await interaction.response.send_message(
                    "Attach a `.db` file to replace.", ephemeral=True
                )
                return

            attachment = interaction.attachments[0]
            if not attachment.filename.endswith(".db"):
                await interaction.response.send_message(
                    "Only `.db` files are allowed.", ephemeral=True
                )
                return

            if attachment.size > 10 * 1024 * 1024:
                await interaction.response.send_message(
                    "File too large (10MB max).", ephemeral=True
                )
                return

            db_file = Path("data.db")
            if db_file.exists():
                db_file.unlink()

            with db_file.open("wb+") as f:
                await attachment.save(f)

            await interaction.response.send_message(
                "Database replaced successfully.", ephemeral=True
            )
            _log.info(f"{interaction.user} replaced the database file.")

        except Exception as e:
            _log.error(f"replacedb error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to replace database file.", ephemeral=True
            )

    @app_commands.command(
        name="view", description="View cached bot data for this server."
    )
    @has_admin_level(2)
    async def view_bot_cache(self, interaction: discord.Interaction):
        try:
            bot_data = get_cached_bot_data(interaction.guild.id)
            if not bot_data:
                await interaction.response.send_message(
                    "No bot data found for this server.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title="📊 Cached Bot Data",
                color=discord.Color.blurple(),
                description=f"Server ID: `{interaction.guild.id}`",
            )
            for field, value in bot_data.__data__.items():
                embed.add_field(name=field, value=str(value), inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            _log.error(f"view_bot_cache error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to view cache.", ephemeral=True
            )

    @app_commands.command(
        name="update-cache", description="Refresh cache from database."
    )
    @has_admin_level(4)
    async def update_cache(self, interaction: discord.Interaction):
        try:
            get_bot_data_for_server(interaction.guild.id)
            await interaction.response.send_message(
                "Cache refreshed from database.", ephemeral=True
            )
            _log.info(f"Cache refreshed for {interaction.guild.id}.")
        except Exception as e:
            _log.error(f"update_cache error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to update cache.", ephemeral=True
            )

    @app_commands.command(
        name="update_bot_data", description="Force-refresh cached bot data."
    )
    @has_admin_level(2)
    async def update_bot_data(self, interaction: discord.Interaction):
        try:
            refresh_bot_data_cache(interaction.guild.id)
            await interaction.response.send_message(
                "Bot data cache updated.", ephemeral=True
            )
            _log.info(f"Bot data cache updated for {interaction.guild.id}.")
        except Exception as e:
            _log.error(f"update_bot_data error: {e}", exc_info=True)
            await interaction.response.send_message(
                "Failed to update bot data.", ephemeral=True
            )

    @commands.command(name="sync")
    @has_admin_level(3)
    async def sync_command(
        self,
        ctx: commands.Context,
        action: Union[Literal["global", "all"], discord.Guild],
    ):
        try:
            if isinstance(action, discord.Guild):
                embed = discord.Embed(
                    color=discord.Color.gold(),
                    title="Sync",
                    description=f"Syncing slash commands for guild `{action.name}`...",
                )
                message = await ctx.send(embed=embed)

                await self.bot.tree.sync(guild=discord.Object(action.id))

                embed.color = discord.Color.green()
                embed.description = (
                    f"✅ Successfully synced slash commands for `{action.name}`."
                )
                await message.edit(embed=embed)
                _log.info(f"Synced commands for guild {action.id}")

            elif action in ["global", "all"]:
                view = ui.View(timeout=30)

                async def confirm(interaction: discord.Interaction):
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            color=discord.Color.gold(),
                            title="Sync",
                            description="Syncing all commands... Please wait.",
                        ),
                        view=None,
                    )
                    try:
                        if action == "global":
                            await self.bot.tree.sync()
                        else:
                            for guild in self.bot.guilds:
                                await self.bot.tree.sync(guild=discord.Object(guild.id))

                        await interaction.followup.send(
                            embed=discord.Embed(
                                color=discord.Color.green(),
                                title="Sync Complete",
                                description=f"✅ Successfully synced `{action}` commands.",
                            )
                        )
                    except Exception as e:
                        _log.error(f"sync error: {e}", exc_info=True)
                        await interaction.followup.send(
                            embed=discord.Embed(
                                color=EmbedColors.red,
                                title="Sync Error",
                                description=f"❌ {e}",
                            )
                        )

                async def cancel(interaction: discord.Interaction):
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            color=EmbedColors.red,
                            title="Cancelled",
                            description="❌ Sync operation canceled.",
                        ),
                        view=None,
                    )

                view.add_item(
                    ui.Button(
                        label="Confirm",
                        style=discord.ButtonStyle.green,
                        emoji="✅",
                        custom_id="sync_confirm",
                    )
                )
                view.add_item(
                    ui.Button(
                        label="Cancel",
                        style=discord.ButtonStyle.red,
                        emoji="❌",
                        custom_id="sync_cancel",
                    )
                )

                view.children[0].callback = confirm
                view.children[1].callback = cancel

                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.gold(),
                        title="Confirm Global Sync",
                        description="Are you sure you want to sync all commands?",
                    ),
                    view=view,
                )

        except Exception as e:
            _log.error(f"sync_command error: {e}", exc_info=True)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    title="Sync Error",
                    description=f"❌ {e}",
                )
            )


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
    _log.info("✅ AdminCommands cog loaded.")
