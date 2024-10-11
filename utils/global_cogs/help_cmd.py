import discord
from discord.ext import commands
from discord import app_commands, ui
from core.logging_module import get_log  # Import your logging module

_log = get_log(__name__)


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
        try:
            embed = discord.Embed(
                title="Admin Help Menu",
                description="Use the buttons below to navigate through the admin commands",
                color=discord.Color.blurple(),
            )

            start = self.page * self.per_page
            end = start + self.per_page
            for category, commands_info in self.command_groups[start:end]:
                category_name, commands, color = commands_info
                command_list = "\n".join(
                    [f"/{cmd.name} - {cmd.description}" for cmd in commands if cmd]
                )
                embed.add_field(
                    name=f"🔹 {category_name}", value=command_list, inline=False
                )

            embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")
            await self.interaction.edit_original_response(embed=embed, view=self)

            # Update button states
            self.first.disabled = self.page == 0
            self.previous.disabled = self.page == 0
            self.next.disabled = self.page >= self.total_pages - 1
            self.last.disabled = self.page >= self.total_pages - 1
        except Exception as e:
            self.bot._log.error(f"Error updating help embed: {e}")

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
        self._log = get_log(__name__)

    help_group = app_commands.Group(
        name="help",
        description="Help commands",
    )

    def categorize_commands(self, admin_only=False):
        categorized_commands = {}
        for command in self.bot.tree.walk_commands():
            command_checks = getattr(command, "checks", [])
            admin_level = None

            for check in command_checks:
                if check.__closure__:
                    for closure_cell in check.__closure__:
                        check_value = closure_cell.cell_contents
                        if isinstance(check_value, int):
                            admin_level = check_value
                            break

            if admin_only and admin_level is None:
                continue
            if not admin_only and admin_level is not None:
                continue

            parent_name = command.parent.name if command.parent else "General"
            if parent_name not in categorized_commands:
                categorized_commands[parent_name] = []
            categorized_commands[parent_name].append((command, admin_level))

        return categorized_commands

    # Helper method to assign color based on admin level
    def get_level_color(self, admin_level):
        level_colors = {
            1: discord.Color.green(),
            2: discord.Color.gold(),
            3: discord.Color.orange(),
            4: discord.Color.red(),
        }
        return level_colors.get(admin_level, discord.Color.blurple())

    # Help command
    @help_group.command(description="Display the general help menu.")
    async def general(self, interaction: discord.Interaction):
        try:
            self._log.info(f"{interaction.user} requested the general help command.")
            categorized_commands = self.categorize_commands(admin_only=False)
            command_groups = [
                (category, commands_list)
                for category, commands_list in categorized_commands.items()
            ]

            embed = discord.Embed(
                title="Help Menu",
                description="Use the buttons below to navigate through the commands",
                color=discord.Color.blurple(),
            )

            for category, commands in command_groups[:5]:
                command_list = "\n".join(
                    [f"/{cmd.name} - {cmd.description}" for cmd, _ in commands]
                )
                embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

            embed.set_footer(text="Page 1/{}".format((len(command_groups) + 4) // 5))
            view = HelpPaginator(self.bot, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            self._log.error(f"Error in help command: {e}")
            await interaction.response.send_message(
                "Sorry, something went wrong while trying to display the help menu.",
                ephemeral=True,
            )

    # Admin help command
    @help_group.command(description="Display the admin help menu.")
    async def admin(self, interaction: discord.Interaction):
        try:
            self._log.info(f"{interaction.user} requested the admin help command.")
            categorized_commands = self.categorize_commands(admin_only=True)
            command_groups = []

            # Admin levels to color mapping
            level_colors = {
                1: discord.Color.green(),
                2: discord.Color.gold(),
                3: discord.Color.orange(),
                4: discord.Color.red(),
            }

            for category, commands_list in categorized_commands.items():
                for command, level in commands_list:
                    color = level_colors.get(level, discord.Color.default())
                    command_groups.append((category, [command], color))

            embed = discord.Embed(
                title="Admin Help Menu",
                description="Use the buttons below to navigate through the admin commands",
                color=discord.Color.blurple(),
            )

            for category, commands, color in command_groups[:5]:
                command_list = "\n".join(
                    [f"/{cmd.name} - {cmd.description}" for cmd in commands]
                )
                embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

            # Add the color-coded admin levels key at the bottom
            embed.add_field(
                name="Admin Levels Key",
                value=(
                    "🟩 **Level 1**: Basic admin privileges\n"
                    "🟨 **Level 2**: Elevated admin privileges\n"
                    "🟧 **Level 3**: High admin privileges\n"
                    "🟥 **Level 4**: Full admin privileges"
                ),
                inline=False,
            )

            embed.set_footer(text="Page 1/{}".format((len(command_groups) + 4) // 5))
            view = HelpPaginator(self.bot, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            self._log.error(f"Error in admin help command: {e}")
            await interaction.response.send_message(
                "Sorry, something went wrong while trying to display the admin help menu.",
                ephemeral=True,
            )


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
        try:
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
        except Exception as e:
            self.bot._log.error(f"Error updating help embed: {e}")

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
        try:
            self._log.info(f"{interaction.user} requested the help command.")

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
                            if isinstance(
                                check_value, int
                            ):  # Admin levels are int values
                                is_admin_command = True
                                break

                # Skip admin commands
                if is_admin_command:
                    continue

                # Use parent (grouping of commands) instead of cog_name
                parent_name = command.parent.name if command.parent else "General"
                if parent_name not in categorized_commands:
                    categorized_commands[parent_name] = []
                categorized_commands[parent_name].append(command)

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
            self._log.info("Help menu successfully sent.")

        except Exception as e:
            self._log.error(f"Error in help command: {e}")
            await interaction.response.send_message(
                "Sorry, something went wrong while trying to display the help menu.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))'''


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
