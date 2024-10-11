import discord
from discord.ext import commands
from core.logging_module import get_log

_log = get_log(__name__)


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="help",
        description="Shows all available commands categorized by their groups.",
    )
    async def help_command(self, ctx: commands.Context):
        try:
            _log.info(f"{ctx.author} requested the help command.")

            # Dictionary to group commands by their categories
            categorized_commands = {}

            # Iterate over all commands in the bot
            for command in self.bot.commands:

                # Check if the command has admin checks; if so, ignore it
                command_checks = getattr(command, "checks", [])
                is_admin_command = False
                for check in command_checks:
                    if check.__closure__:
                        for closure_cell in check.__closure__:
                            check_value = closure_cell.cell_contents
                            if isinstance(check_value, int):  # Skip admin commands
                                is_admin_command = True
                                break

                # If not an admin command, categorize by group
                if not is_admin_command:
                    command_group = command.cog_name or "Ungrouped"
                    if command_group not in categorized_commands:
                        categorized_commands[command_group] = []
                    categorized_commands[command_group].append(
                        f"{command.name} - {command.help or 'No description'}"
                    )

            # Create the embed for displaying the commands
            embed = discord.Embed(
                title="Available Commands",
                description="Here are all the available commands categorized by their groups.",
                color=discord.Color.blue(),
            )

            # Add a field for each command category
            for group, commands_list in categorized_commands.items():
                embed.add_field(
                    name=f"{group} Commands:",
                    value="\n".join(commands_list),
                    inline=False,
                )

            if not categorized_commands:
                embed.description = "No non-admin commands found."

            await ctx.send(embed=embed)

        except Exception as e:
            _log.error(f"Error in help command: {e}", exc_info=True)
            await ctx.send("An error occurred while fetching the commands.")


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
