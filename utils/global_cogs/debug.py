from core.cache_state import bot_data_cache
from core.checks import has_admin_level
import discord
from discord.ext import commands
from discord import app_commands, ui


class BotCachePaginator(ui.View):
    """UI View for paginating through bot_data_cache."""

    def __init__(self, pages, interaction):
        super().__init__(timeout=60)
        self.pages = pages
        self.page = 0
        self.interaction = interaction

    async def update(self, interaction: discord.Interaction):
        """Update the message with the current page."""
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    @ui.button(label="⏮️", style=discord.ButtonStyle.green)
    async def first(self, interaction: discord.Interaction, _):
        self.page = 0
        await self.update(interaction)

    @ui.button(label="◀️", style=discord.ButtonStyle.blurple)
    async def prev(self, interaction: discord.Interaction, _):
        if self.page > 0:
            self.page -= 1
            await self.update(interaction)

    @ui.button(label="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, _):
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update(interaction)

    @ui.button(label="⏭️", style=discord.ButtonStyle.green)
    async def last(self, interaction: discord.Interaction, _):
        self.page = len(self.pages) - 1
        await self.update(interaction)


class DebugCMD(commands.Cog):
    """Cog for administrative debug commands."""

    def __init__(self, bot):
        self.bot = bot

    debug_group = app_commands.Group(name="debug", description="Debug commands")

    @debug_group.command(
        name="all_bot_cache", description="View cached bot data for all guilds."
    )
    @has_admin_level(4)
    async def all_bot_cache(self, interaction: discord.Interaction):
        """Display cached BotData for all guilds with pagination."""
        if not bot_data_cache:
            await interaction.response.send_message(
                "⚠️ No bot data is currently cached.", ephemeral=True
            )
            return

        pages = []
        fields_per_page = 5
        items = list(bot_data_cache.items())

        for i in range(0, len(items), fields_per_page):
            chunk = items[i : i + fields_per_page]
            embed = discord.Embed(
                title="📦 Cached BotData",
                description=f"Showing {i + 1} to {i + len(chunk)} of {len(items)}",
                color=discord.Color.teal(),
            )

            for guild_id, data in chunk:
                value = (
                    f"**Prefix:** {data.prefix or 'None'}\n"
                    f"**Rule Channel:** {data.rule_channel or 'None'}\n"
                    f"**Rule Message ID:** {data.rule_message_id or 'None'}"
                )
                embed.add_field(
                    name=f"Guild ID: {str(guild_id)}", value=value, inline=False
                )

            pages.append(embed)

        view = BotCachePaginator(pages, interaction)
        await interaction.response.send_message(
            embed=pages[0], view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DebugCMD(bot))
