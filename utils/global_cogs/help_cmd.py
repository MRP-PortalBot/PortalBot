import discord
from discord.ext import commands
from discord import app_commands, ui
from core.logging_module import get_log  # Import your logging module


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
                [f"/{cmd.name} - {cmd.description}" for cmd in commands if cmd]
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
        self._log = get_log(__name__)  # Initialize the logger

    @app_commands.command(description="Display the help menu.")
    async def help(self, interaction: discord.Interaction):
        # Gather all commands excluding admin-related ones
        command_groups = []
        categorized_commands = {}

        # Iterate through bot's slash commands
        for command in self.bot.tree.walk_commands():
            command_checks = getattr(command, "checks", [])
            is_admin_command = False

            for check in command_checks:
                if check.__closure__:
                    for closure_cell in check.__closure__:
                        check_value = closure_cell.cell_contents
                        if isinstance(check_value, int):  # Admin levels are int values
                            is_admin_command = True
                            break

            # Skip admin commands
            if is_admin_command:
                continue

            # Categorize commands by their group (cog_name)
            category_name = command.cog_name or "General"
            if category_name not in categorized_commands:
                categorized_commands[category_name] = []
            categorized_commands[category_name].append(command)

        # Convert dictionary to list of tuples for pagination
        for category, commands_list in categorized_commands.items():
            command_groups.append((category, commands_list))

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


'''import discord
from discord.ext import commands
from discord import app_commands, ui
from core.logging_module import get_log  # Import your logging module


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
        self._log = get_log(__name__)  # Initialize the logger

    @app_commands.command(description="Display the help menu.")
    async def help(self, interaction: discord.Interaction):
        # Fetch commands from the banned list group
        bl_group = self.bot.tree.get_command("banned-list")
        bl_commands = bl_group.commands if bl_group else []
        dq_group = self.bot.tree.get_command("daily-question")
        dq_commands = dq_group.commands if dq_group else []

        # Log the fetched banned list commands for debugging
        self._log.info(f"Available commands in banned-list group: {dq_commands}")

        # Grouping commands from different categories
        command_groups = [
            (
                "Banned List Commands",
                bl_commands,  # Include the banned list group commands
            ),
            (
                "Daily Question Commands",
                dq_commands,  # Include the daily question group commands
            ),
            (
                "General Commands",
                [
                    self.bot.tree.get_command("ping"),
                    self.bot.tree.get_command("uptime"),
                ],
            ),
            # Add more categories and commands as necessary
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
    await bot.add_cog(HelpCMD(bot))'''
