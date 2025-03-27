import asyncio
import discord
from typing import Union, Literal
from discord import ui, ButtonStyle
from discord.ext import commands

from core import database
from core.checks import has_admin_level
from core.common import ButtonHandler
from core.constants import EmbedColors
from core.logging_module import get_log

_log = get_log(__name__)


class BackupRegularCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("BackupRegularCommands cog loaded.")

    @commands.command(name="sync")
    @has_admin_level(3)
    async def sync_command(
        self,
        ctx: commands.Context,
        action: Union[Literal["global", "all"], discord.Guild],
    ):
        try:
            if isinstance(action, discord.Guild):
                guild = action
                _log.info(
                    f"Initiating guild-level sync for guild {guild.name} ({guild.id}) by {ctx.author}."
                )

                embed_processing = discord.Embed(
                    color=discord.Color.gold(),
                    title="Sync",
                    description=f"Syncing slash commands for guild `{guild.name}`...",
                )
                message_sync = await ctx.send(embed=embed_processing)

                await self.bot.tree.sync(guild=discord.Object(guild.id))

                embed_done = discord.Embed(
                    color=discord.Color.green(),
                    title="Sync",
                    description=f"✅ Successfully synced slash commands for guild `{guild.name}`!",
                )
                await message_sync.edit(embed=embed_done)
                _log.info(f"Successfully synced commands for guild {guild.name}.")

            elif action in ["global", "all"]:
                view = ui.View(timeout=30)
                confirm_button = ui.Button(
                    style=discord.ButtonStyle.green, label="Confirm", emoji="✅"
                )
                cancel_button = ui.Button(
                    style=discord.ButtonStyle.red, label="Cancel", emoji="❌"
                )

                async def confirm_callback(interaction: discord.Interaction):
                    _log.info(f"{interaction.user} confirmed {action} sync.")
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            color=discord.Color.gold(),
                            title="Sync",
                            description=f"Syncing `{action}` commands... This may take a while.",
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
                        _log.info(f"Successfully completed {action} sync.")
                    except Exception as e:
                        _log.error(f"Error during sync: {e}", exc_info=True)
                        await interaction.followup.send(
                            embed=discord.Embed(
                                color=EmbedColors.red,
                                title="Sync Error",
                                description=f"❌ An error occurred while syncing:\n`{e}`",
                            )
                        )

                async def cancel_callback(interaction: discord.Interaction):
                    _log.info(f"{interaction.user} canceled the sync.")
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            color=EmbedColors.red,
                            title="Sync Canceled",
                            description="❌ Sync operation canceled.",
                        ),
                        view=None,
                    )

                confirm_button.callback = confirm_callback
                cancel_button.callback = cancel_callback

                view.add_item(confirm_button)
                view.add_item(cancel_button)

                confirm_embed = discord.Embed(
                    color=discord.Color.gold(),
                    title="Confirm Sync",
                    description=(
                        "Are you sure you want to **globally sync** all commands?"
                        if action == "global"
                        else "Are you sure you want to sync all **guild commands**?"
                    ),
                )

                await ctx.send(embed=confirm_embed, view=view)

        except Exception as e:
            _log.error(f"An error occurred during sync: {e}", exc_info=True)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    title="Sync Error",
                    description=f"❌ An error occurred:\n`{e}`",
                )
            )


async def setup(bot):
    await bot.add_cog(BackupRegularCommands(bot))
    _log.info("BackupRegularCommands cog setup complete.")
