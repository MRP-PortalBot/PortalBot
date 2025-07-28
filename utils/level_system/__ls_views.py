import discord
from discord.ui import View, Button


class LeaderboardView(View):
    def __init__(
        self, interaction: discord.Interaction, entries: list, per_page: int = 10
    ):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.entries = entries
        self.per_page = per_page
        self.page = 0
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.page > 0:
            self.add_item(
                Button(
                    label="⬅️ Previous",
                    style=discord.ButtonStyle.secondary,
                    custom_id="prev",
                )
            )
        if (self.page + 1) * self.per_page < len(self.entries):
            self.add_item(
                Button(
                    label="Next ➡️",
                    style=discord.ButtonStyle.secondary,
                    custom_id="next",
                )
            )

    def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        embed = discord.Embed(
            title=f"🏆 {self.interaction.guild.name} Leaderboard",
            description=f"Top XP earners (Page {self.page + 1}/{(len(self.entries)-1)//self.per_page+1}):",
            color=discord.Color.gold(),
        )

        for i, entry in enumerate(self.entries[start:end], start=start + 1):
            username = entry.DiscordName or f"<@{entry.DiscordLongID}>"
            embed.add_field(
                name=f"{i}. {username}",
                value=f"Level: {entry.Level} | XP: {entry.Score}",
                inline=False,
            )

        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction.user.id

    @discord.ui.button(
        label="⬅️ Previous", style=discord.ButtonStyle.secondary, custom_id="prev", row=0
    )
    async def previous(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(
        label="Next ➡️", style=discord.ButtonStyle.secondary, custom_id="next", row=0
    )
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
