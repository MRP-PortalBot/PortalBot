import asyncio
import discord
from typing import Union, Literal
from discord import ui, ButtonStyle
from discord.ext import commands
from core import database
from core.checks import is_botAdmin3
from core.common import Colors, ButtonHandler
from core.logging_module import get_log

_log = get_log(__name__)


class BackupRegularCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_sync_embed(self, ctx: commands.Context, title: str, description: str, color=discord.Color.gold()):
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
            style=ButtonStyle.red,
            label="Cancel",
            emoji="❌",
            button_user=ctx.author
        )
        view.add_item(button_confirm)
        view.add_item(button_cancel)

        embed_confirm = discord.Embed(title="Sync Confirmation", description=description, color=discord.Color.gold())
        message_confirm = await ctx.send(embed=embed_confirm, view=view)

        timeout = await view.wait()

        if timeout:
            return "timeout"
        return view.value

    @commands.command()
    @is_botAdmin3
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

        elif action == "global" or action == "all":
            # Defer interaction to avoid timeout
            await ctx.defer() 

            view = ui.View(timeout=30)
            button_confirm = ButtonHandler(
                style=ButtonStyle.green,
                label="Confirm",
                emoji="✅",
                button_user=ctx.author,
            )
            button_cancel = ButtonHandler(
                style=ButtonStyle.red, label="Cancel", emoji="❌", button_user=ctx.author
            )
            view.add_item(button_confirm)
            view.add_item(button_cancel)

            embed_confirm = discord.Embed(
                color=discord.Color.gold(),
                title="Sync Confirmation",
                description=f"Are you sure you want to sync globally? This may take up to 1 hour." if action == "global" else "Are you sure you want to sync all local guild commands?",
            )
            message_confirm = await ctx.send(embed=embed_confirm, view=view)

            timeout = await view.wait()
            if not timeout:
                if view.value == "Confirm":

                    embed_processing = discord.Embed(
                        color=discord.Color.gold(),
                        title="Sync",
                        description=f"Syncing slash commands {action}..."
                        f"\nThis may take a while.",
                    )
                    await message_confirm.edit(embed=embed_processing, view=None)

                    if action == "global":
                        await self.bot.tree.sync()
                    else:
                        for guild in self.bot.guilds:
                            await self.bot.tree.sync(guild=discord.Object(guild.id))

                    embed_processing = discord.Embed(
                        color=discord.Color.green(),
                        title="Sync",
                        description=f"Successfully synced slash commands {action}!",
                    )
                    await message_confirm.edit(embed=embed_processing)

                elif view.value == "Cancel":
                    embed_cancel = discord.Embed(
                        color=Colors.red, title="Sync", description="Sync canceled."
                    )
                    await message_confirm.edit(embed=embed_cancel, view=None)

            else:
                embed_timeout = discord.Embed(
                    color=Colors.red,
                    title="Sync",
                    description="Sync canceled due to timeout.",
                )
                await message_confirm.edit(embed=embed_timeout, view=None)



async def setup(bot):
    await bot.add_cog(BackupRegularCommands(bot))
