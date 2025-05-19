import discord
from discord.ext import commands
from discord import app_commands, ui
from pathlib import Path
from typing import Union, Literal

from utils.database import __database
from utils.helpers.__checks import has_admin_level
from utils.core_features.constants import EmbedColors
from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class AdminCommands(commands.GroupCog, name="admin"):
    def __init__(self, bot: commands.Bot):
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
            if not __database.db.is_closed():
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
            if not __database.db.is_closed():
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
                        color=EmbedColors.gold,
                        title="Confirm Global Sync",
                        description="Are you sure you want to sync all commands?",
                    ),
                    view=view,
                )
        except Exception as e:
            _log.error(f"sync_command error: {e}", exc_info=True)
            await ctx.send(
                embed=discord.Embed(
                    color=EmbedColors.red,
                    title="Sync Error",
                    description=f"❌ {e}",
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))
    _log.info("✅ AdminCommands cog loaded.")
