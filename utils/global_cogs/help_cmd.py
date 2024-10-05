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

        # Disable previous button at the start
        self.previous.disabled = True

        # Disable next button if there's only one page
        self.next.disabled = self.page >= self.total_pages - 1

    async def update_embed(self):
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

    @ui.button(label="⏮️ First", style=discord.ButtonStyle.green)
    async def first(self, interaction: discord.Interaction, button: ui.Button):
        self.page = 0
        self.previous.disabled = True
        self.next.disabled = False
        await self.update_embed()

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        if self.page > 0:
            self.page -= 1
            self.next.disabled = False
        if self.page == 0:
            self.previous.disabled = True
        await self.update_embed()

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            self.previous.disabled = False
        if self.page >= self.total_pages - 1:
            self.next.disabled = True
        await self.update_embed()

    @ui.button(label="⏭️ Last", style=discord.ButtonStyle.green)
    async def last(self, interaction: discord.Interaction, button: ui.Button):
        self.page = self.total_pages - 1
        self.previous.disabled = False
        self.next.disabled = True
        await self.update_embed()


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Display the help menu.")
    async def help(self, interaction: discord.Interaction):
        command_groups = [
            (
                "Banned List Commands",
                [
                    app_commands.Command(
                        name="post", description="Post a new ban entry."
                    ),
                    app_commands.Command(
                        name="edit", description="Edit an existing ban entry."
                    ),
                    app_commands.Command(
                        name="search", description="Search the banned list."
                    ),
                ],
            ),
            (
                "General Commands",
                [
                    app_commands.Command(
                        name="ping", description="Ping the bot to check latency."
                    ),
                    app_commands.Command(
                        name="uptime", description="Check the bot's uptime."
                    ),
                ],
            ),
            # Add more categories and commands as necessary
        ]

        embed = discord.Embed(
            title="Help Menu",
            description="Use the buttons below to navigate through the commands",
            color=discord.Color.blurple(),
        )

        # Display the first page
        for category, commands in command_groups[:5]:
            command_list = "\n".join(
                [f"/{cmd.name} - {cmd.description}" for cmd in commands]
            )
            embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

        embed.set_footer(text="Page 1/{}".format((len(command_groups) + 4) // 5))

        view = HelpPaginator(self.bot, interaction, command_groups)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
