import discord
from discord.ext import commands
from discord import app_commands, ui


class HelpPaginator(ui.View):
    def __init__(
        self, bot, interaction: discord.Interaction, command_groups: list, per_page=5
    ):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.command_groups = (
            command_groups  # List of tuples with (category_name, [commands])
        )
        self.per_page = per_page
        self.page = 0
        self.total_pages = (
            len(self.command_groups) + self.per_page - 1
        ) // self.per_page

        # Initial button states
        self.first.disabled = self.page == 0
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page >= self.total_pages - 1
        self.last.disabled = self.page >= self.total_pages - 1

    async def update_embed(self):
        """Helper function to update the embed."""
        embed = discord.Embed(
            title="Help Menu",
            description="Use the buttons below to navigate through the commands",
            color=discord.Color.blurple(),
        )

        start = self.page * self.per_page
        end = start + self.per_page
        for category, commands in self.command_groups[start:end]:
            command_list = "\n".join(
                [f"/{cmd.name} - {cmd.description}" for cmd in commands]
            )
            embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")
        await self.interaction.edit_original_response(embed=embed, view=self)

        # Update button states
        self.first.disabled = self.page == 0
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page >= self.total_pages - 1
        self.last.disabled = self.page >= self.total_pages - 1

    @ui.button(label="⏮️ First", style=discord.ButtonStyle.green)
    async def first(self, interaction: discord.Interaction, button: ui.Button):
        self.page = 0
        await self.update_embed()

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        if self.page > 0:
            self.page -= 1
        await self.update_embed()

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        await self.update_embed()

    @ui.button(label="⏭️ Last", style=discord.ButtonStyle.green)
    async def last(self, interaction: discord.Interaction, button: ui.Button):
        self.page = self.total_pages - 1
        await self.update_embed()


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Display the help menu.")
    async def help(self, interaction: discord.Interaction):
        # Grouping commands from different categories
        command_groups = [
            (
                "Banned List Commands",
                [
                    self.bot.tree.get_command("post"),
                    self.bot.tree.get_command("edit"),
                    self.bot.tree.get_command("search"),
                ],
            ),
            (
                "General Commands",
                [
                    self.bot.tree.get_command("ping"),
                    self.bot.tree.get_command("uptime"),
                ],
            ),
        ]

        # Create an initial embed
        embed = discord.Embed(
            title="Help Menu",
            description="Use the buttons below to navigate through the commands",
            color=discord.Color.blurple(),
        )

        # Show the first page of commands
        for category, commands in command_groups[:5]:
            command_list = "\n".join(
                [
                    f"/{cmd.name} - {cmd.description}"
                    for cmd in commands
                    if cmd and cmd.name
                ]
            )
            embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

        embed.set_footer(text="Page 1/{}".format((len(command_groups) + 4) // 5))

        # Send the initial embed and attach the paginator view
        view = HelpPaginator(self.bot, interaction, command_groups)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
