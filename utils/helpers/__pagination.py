import discord
from discord import ui


class PaginatorView(ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        embed: discord.Embed,
        population_func,
        total_pages: int,
        page: int = 1,
        timeout: int = 60,
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.embed = embed
        self.population_func = population_func
        self.total_pages = total_pages
        self.page = page

        self.update_button_states()

    def update_button_states(self):
        """Enable or disable navigation buttons based on the current page."""
        self.back.disabled = self.page == 1
        self.next.disabled = self.page == self.total_pages

    async def update_embed(self, interaction: discord.Interaction):
        """Helper function to update the embed content and footer."""
        self.embed = await self.population_func(self.embed, self.page)
        self.embed.set_footer(text=f"Page {self.page} of {self.total_pages}")

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=self.embed, view=self)
        else:
            await interaction.response.edit_message(embed=self.embed, view=self)

    @ui.button(label="◀️", style=discord.ButtonStyle.primary, custom_id="back")
    async def back(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        if self.page > 1:
            self.page -= 1
            self.update_button_states()
            await self.update_embed(interaction)

    @ui.button(label="▶️", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        if self.page < self.total_pages:
            self.page += 1
            self.update_button_states()
            await self.update_embed(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the original user can interact with the menu."""
        if interaction.user != self.interaction.user:
            await interaction.response.send_message(
                "You cannot interact with this menu.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable the view after it times out."""
        self.clear_items()
        await self.interaction.edit_original_response(view=self)


async def paginate_embed(
    interaction: discord.Interaction,
    embed: discord.Embed,
    population_func,
    total_pages: int,
    page: int = 1,
    timeout: int = 60,
):
    """
    Create a paginated embed using buttons.

    Args:
        interaction (discord.Interaction): The triggering interaction.
        embed (discord.Embed): The initial embed to display.
        population_func (callable): Async function to populate the embed for a given page.
        total_pages (int): Total number of pages.
        page (int, optional): Starting page number. Defaults to 1.
        timeout (int, optional): How long the buttons remain active. Defaults to 60 seconds.
    """
    embed = await population_func(embed, page)
    embed.set_footer(text=f"Page {page} of {total_pages}")
    view = PaginatorView(
        interaction, embed, population_func, total_pages, page, timeout
    )
    await interaction.response.send_message(embed=embed, view=view)
