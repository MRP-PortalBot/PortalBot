import discord
from discord.ext import commands
from discord import app_commands, ui
from core.logging_module import get_log  # Import your logging module
from core.checks import slash_is_realm_op, slash_owns_realm_channel

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

        _log.debug(f"Paginator initialized with {len(command_groups)} command groups.")

    async def update_embed(self):
        """Helper function to update the embed."""
        try:
            _log.debug(
                f"Updating help embed for page {self.page + 1}/{self.total_pages}."
            )

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
            self.bot._log.error(
                f"Error updating help embed for {self.interaction.user}: {e}"
            )

    @ui.button(label="⏮️ First", style=discord.ButtonStyle.green)
    async def first(self, interaction: discord.Interaction, button: ui.Button):
        self.page = 0
        _log.debug(f"User {interaction.user} navigated to first page.")
        await self.update_embed()

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        if self.page > 0:
            self.page -= 1
            _log.debug(
                f"User {interaction.user} navigated to previous page: {self.page + 1}."
            )
        await self.update_embed()

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            _log.debug(
                f"User {interaction.user} navigated to next page: {self.page + 1}."
            )
        await self.update_embed()

    @ui.button(label="⏭️ Last", style=discord.ButtonStyle.green)
    async def last(self, interaction: discord.Interaction, button: ui.Button):
        self.page = self.total_pages - 1
        _log.debug(f"User {interaction.user} navigated to last page.")
        await self.update_embed()


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._log = get_log(__name__)
        _log.info("HelpCMD Cog initialized.")

    help_group = app_commands.Group(name="help", description="Help commands")

    def categorize_commands(self, admin_only=False, operator_only=False):
        categorized_commands = {}
        for command in self.bot.tree.walk_commands():
            command_checks = getattr(command, "checks", [])
            admin_level = None
            is_operator_command = False

            # Detect admin and operator commands
            for check in command_checks:
                if check.__closure__:
                    for closure_cell in check.__closure__:
                        check_value = closure_cell.cell_contents
                        if isinstance(check_value, int):
                            admin_level = check_value
                        if isinstance(check_value, str) and check_value in [
                            "Realm OP",
                            "Moderator",
                        ]:
                            is_operator_command = True
                        if isinstance(check_value, str) and check_value.endswith(" OP"):
                            is_operator_command = True

            # Filtering logic
            if admin_only and admin_level is None:
                continue
            if operator_only and not is_operator_command:
                continue
            if (
                not admin_only
                and not operator_only
                and (admin_level is not None or is_operator_command)
            ):
                continue

            parent_name = command.parent.name if command.parent else "General"
            if parent_name not in categorized_commands:
                categorized_commands[parent_name] = []
            categorized_commands[parent_name].append((command, admin_level))

        _log.debug(
            f"Categorized commands for admin_only={admin_only}, operator_only={operator_only}"
        )
        return categorized_commands

    # General help command
    @help_group.command(description="Display the general help menu.")
    async def general(self, interaction: discord.Interaction):
        try:
            self._log.info(f"{interaction.user} requested the general help command.")
            categorized_commands = self.categorize_commands(
                admin_only=False, operator_only=False
            )
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

            embed.set_footer(text=f"Page 1/{(len(command_groups) + 4) // 5}")
            view = HelpPaginator(self.bot, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            self._log.error(
                f"Error displaying general help for {interaction.user}: {e}"
            )
            await interaction.response.send_message(
                "Sorry, something went wrong while displaying the help menu.",
                ephemeral=True,
            )

    # Admin help command
    @help_group.command(description="Display the admin help menu.")
    async def admin(self, interaction: discord.Interaction):
        try:
            self._log.info(f"{interaction.user} requested the admin help command.")
            categorized_commands = self.categorize_commands(admin_only=True)

            # Admin levels to color mapping
            level_colors = {
                1: "🟩",  # Basic admin privileges
                2: "🟨",  # Elevated admin privileges
                3: "🟧",  # High admin privileges
                4: "🟥",  # Full admin privileges
            }

            embed = discord.Embed(
                title="Admin Help Menu",
                description="Admin commands grouped by their command category, color-coded by admin level.",
                color=discord.Color.red(),
            )

            # Loop through the command groups and display commands within each group
            for category, commands in categorized_commands.items():
                command_list = "\n".join(
                    f"{level_colors.get(level, '⚪')} /{cmd.name} - {cmd.description}"
                    for cmd, level in commands
                )
                embed.add_field(
                    name=f"🔹 {category}",
                    value=command_list if command_list else "No commands available.",
                    inline=False,
                )

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

            await interaction.response.send_message(embed=embed)
            _log.info("Admin help command displayed successfully.")

        except Exception as e:
            self._log.error(f"Error in admin help command for {interaction.user}: {e}")
            await interaction.response.send_message(
                "Sorry, something went wrong while trying to display the admin help menu.",
                ephemeral=True,
            )

    # Operator help command
    @help_group.command(description="Display the operator help menu.")
    async def operator(self, interaction: discord.Interaction):
        try:
            self._log.info(f"{interaction.user} requested the operator help command.")
            categorized_commands = self.categorize_commands(operator_only=True)
            command_groups = [
                (category, commands_list)
                for category, commands_list in categorized_commands.items()
            ]

            embed = discord.Embed(
                title="Operator Help Menu",
                description="Use the buttons below to navigate through the commands",
                color=discord.Color.green(),
            )

            for category, commands in command_groups[:5]:
                command_list = "\n".join(
                    [f"/{cmd.name} - {cmd.description}" for cmd, _ in commands]
                )
                embed.add_field(name=f"🔹 {category}", value=command_list, inline=False)

            embed.set_footer(text="Page 1/{}".format((len(command_groups) + 4) // 5))
            view = HelpPaginator(self.bot, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)
            _log.info("Operator help command displayed successfully.")

        except Exception as e:
            self._log.error(
                f"Error in operator help command for {interaction.user}: {e}"
            )
            await interaction.response.send_message(
                "Sorry, something went wrong while trying to display the operator help menu.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
    _log.info("HelpCMD Cog set up and ready.")
