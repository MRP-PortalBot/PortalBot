import asyncio
import discord
from typing import Union, Literal
from discord import ui, ButtonStyle
from discord.ext import commands
from core import database
from core.checks import is_bot_Admin_3
from core.common import Colors, ButtonHandler
from core.logging_module import get_log

_log = get_log(__name__)

class BackupRegularCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_sync_embed(
        self,
        ctx: commands.Context,
        title: str,
        description: str,
        color=discord.Color.gold(),
    ):
        """Helper function to send a sync embed."""
        embed = discord.Embed(title=title, description=description, color=color)
        return await ctx.send(embed=embed)

    async def handle_confirmation(self, ctx: commands.Context, description: str) -> str:
        """Helper function to handle confirmation with buttons."""
        view = ui.View(timeout=30)
        button_confirm = ButtonHandler(
            style=ButtonStyle.green,
            label="Confirm",
            emoji="✅",
            button_user=ctx.author,  # button_user is passed correctly now
        )
        button_cancel = ButtonHandler(
            style=ButtonStyle.red, label="Cancel", emoji="❌", button_user=ctx.author
        )
        view.add_item(button_confirm)
        view.add_item(button_cancel)

        embed_confirm = discord.Embed(
            title="Sync Confirmation",
            description=description,
            color=discord.Color.gold(),
        )
        message_confirm = await ctx.send(embed=embed_confirm, view=view)

        timeout = await view.wait()

        if timeout:
            return "timeout"
        return view.value

    @commands.command()
    @is_bot_Admin_3
    async def sync(
        self,
        ctx: commands.Context,
        action: Union[Literal["global"], Literal["all"], discord.Guild],
    ):
        if isinstance(action, discord.Guild):
            guild = action
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
                description=f"Successfully synced slash commands for guild `{guild.name}`!",
            )
            await message_sync.edit(embed=embed_done)

        elif action in ["global", "all"]:
            await ctx.defer()  # Defer the response to prevent interaction failure

            # Create a View with Confirm and Cancel buttons
            view = ui.View(timeout=30)
            confirm_button = ui.Button(
                style=discord.ButtonStyle.green, label="Confirm", emoji="✅"
            )
            cancel_button = ui.Button(
                style=discord.ButtonStyle.red, label="Cancel", emoji="❌"
            )

            async def confirm_button_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        color=discord.Color.gold(),
                        title="Sync",
                        description=f"Syncing {action} commands... This may take a while.",
                    ),
                    view=None,
                )

                # Perform the sync based on the action
                if action == "global":
                    await self.bot.tree.sync()  # Sync globally
                else:
                    for guild in self.bot.guilds:
                        await self.bot.tree.sync(guild=discord.Object(guild.id))

                await interaction.followup.send(
                    embed=discord.Embed(
                        color=discord.Color.green(),
                        title="Sync",
                        description=f"Successfully synced slash commands {action}!",
                    )
                )

            async def cancel_button_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(
                    embed=discord.Embed(
                        color=Colors.red, title="Sync", description="Sync canceled."
                    ),
                    view=None,
                )

            # Add callbacks to buttons
            confirm_button.callback = confirm_button_callback
            cancel_button.callback = cancel_button_callback

            # Add buttons to the view
            view.add_item(confirm_button)
            view.add_item(cancel_button)

            embed_confirm = discord.Embed(
                color=discord.Color.gold(),
                title="Sync Confirmation",
                description=(
                    f"Are you sure you want to sync globally? This may take up to 1 hour."
                    if action == "global"
                    else "Are you sure you want to sync all local guild commands?"
                ),
            )
            await ctx.send(embed=embed_confirm, view=view)


async def setup(bot):
    await bot.add_cog(BackupRegularCommands(bot))
