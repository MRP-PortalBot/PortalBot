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
    async def sync(self, ctx: commands.Context, action: Union[Literal["global"], Literal["all"], discord.Guild]):
        if isinstance(action, discord.Guild):
            guild = action
            message_sync = await self.send_sync_embed(ctx, "Sync", f"Syncing slash commands for guild `{guild.name}`...")
            await self.bot.tree.sync(guild=discord.Object(guild.id))
            await message_sync.edit(embed=discord.Embed(title="Sync", description=f"Successfully synced for `{guild.name}`!", color=discord.Color.green()))

        elif action == "global":
            confirmation = await self.handle_confirmation(ctx, "Are you sure you want to sync globally? This may take up to 1 hour.")
            if confirmation == "Confirm":
                message_sync = await self.send_sync_embed(ctx, "Sync", "Syncing slash commands globally...\nThis may take a while.")
                await self.bot.tree.sync()
                await message_sync.edit(embed=discord.Embed(title="Sync", description="Successfully synced globally!", color=discord.Color.green()))
            elif confirmation == "Cancel":
                await self.send_sync_embed(ctx, "Sync", "Sync canceled.", Colors.red)
            else:
                await self.send_sync_embed(ctx, "Sync", "Sync canceled due to timeout.", Colors.red)

        elif action == "all":
            confirmation = await self.handle_confirmation(ctx, "Are you sure you want to sync all local guild commands?")
            if confirmation == "Confirm":
                message_sync = await self.send_sync_embed(ctx, "Sync", "Syncing all local guild slash commands...\nThis may take a while.")
                for guild in self.bot.guilds:
                    await self.bot.tree.sync(guild=discord.Object(guild.id))
                await message_sync.edit(embed=discord.Embed(title="Sync", description="Successfully synced in all servers!", color=discord.Color.green()))
            elif confirmation == "Cancel":
                await self.send_sync_embed(ctx, "Sync", "Sync canceled.", Colors.red)
            else:
                await self.send_sync_embed(ctx, "Sync", "Sync canceled due to timeout.", Colors.red)


async def setup(bot):
    await bot.add_cog(BackupRegularCommands(bot))
