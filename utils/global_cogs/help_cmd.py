import discord
from discord import app_commands, ui
from discord.ext import commands


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def help(self, interaction: discord.Interaction):
        all_commands = [
            {"name": "/help", "description": "Displays this help message."},
            {"name": "/ping", "description": "Check the bot's latency."},
            # Add more commands here...
        ]

        # Helper function to create paginated embeds
        async def paginate_embed(page: int, per_page: int = 25):
            start = (page - 1) * per_page
            end = start + per_page
            embed = discord.Embed(
                title="Help Menu",
                description="Commands available:",
                color=discord.Color.blue(),
            )

            for cmd in all_commands[start:end]:
                embed.add_field(
                    name=cmd["name"], value=cmd["description"], inline=False
                )

            total_pages = (len(all_commands) + per_page - 1) // per_page
            embed.set_footer(text=f"Page {page}/{total_pages}")

            return embed

        # Initial embed
        current_page = 1
        embed = await paginate_embed(current_page)

        # Create the button view for navigation
        class PaginatorView(ui.View):
            def __init__(
                self, interaction: discord.Interaction, page: int, total_pages: int
            ):
                super().__init__(timeout=60)
                self.interaction = interaction
                self.page = page
                self.total_pages = total_pages

                # Disable back button if on the first page
                self.children[0].disabled = self.page == 1
                # Disable next button if on the last page
                self.children[1].disabled = self.page == self.total_pages

            @ui.button(label="◀️", style=discord.ButtonStyle.primary)
            async def previous_page(
                self, interaction: discord.Interaction, button: ui.Button
            ):
                if self.page > 1:
                    self.page -= 1
                    embed = await paginate_embed(self.page)
                    await interaction.response.edit_message(embed=embed, view=self)

            @ui.button(label="▶️", style=discord.ButtonStyle.primary)
            async def next_page(
                self, interaction: discord.Interaction, button: ui.Button
            ):
                if self.page < self.total_pages:
                    self.page += 1
                    embed = await paginate_embed(self.page)
                    await interaction.response.edit_message(embed=embed, view=self)

        total_pages = (len(all_commands) + 24) // 25
        view = PaginatorView(interaction, current_page, total_pages)

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
