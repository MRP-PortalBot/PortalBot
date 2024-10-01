import discord
from discord import ui

class PaginatorView(ui.View):
    def __init__(self, bot: discord.Client, interaction: discord.Interaction, embed: discord.Embed,
                 population_func, total_pages: int, page: int = 1):
        super().__init__(timeout=60)  # Set a timeout for interaction
        self.bot = bot
        self.interaction = interaction
        self.embed = embed
        self.population_func = population_func
        self.total_pages = total_pages
        self.page = page

        # Initially disable the back button if we're on the first page
        self.back.disabled = self.page == 1
        self.next.disabled = self.page == self.total_pages

    async def update_embed(self, interaction: discord.Interaction):
        """Helper function to update the embed."""
        self.embed = await self.population_func(self.embed, self.page)
        await interaction.response.edit_message(embed=self.embed, view=self)

    @ui.button(label="◀️", style=discord.ButtonStyle.primary, custom_id="back")
    async def back(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()  # Acknowledge the interaction to avoid "failed" messages
        if self.page > 1:
            self.page -= 1
            await self.update_embed(interaction)

        # Disable the button if we reach the first page
        self.back.disabled = self.page == 1
        self.next.disabled = self.page == self.total_pages

    @ui.button(label="▶️", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()  # Acknowledge the interaction to avoid "failed" messages
        if self.page < self.total_pages:
            self.page += 1
            await self.update_embed(interaction)

        # Disable the button if we reach the last page
        self.back.disabled = self.page == 1
        self.next.disabled = self.page == self.total_pages

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the original user can interact with the buttons."""
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("You cannot interact with this menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        """Disable the view after timeout."""
        self.clear_items()  # Remove the buttons when the view times out
        await self.interaction.edit_original_response(view=self)
