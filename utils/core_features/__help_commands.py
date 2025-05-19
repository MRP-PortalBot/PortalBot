import discord
from discord import app_commands, ui
from difflib import get_close_matches
from core.logging_module import get_log
from .__help_views import HelpPaginator


_log = get_log(__name__)


class HelpCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="help", description="Help and command lookup")

    def categorize_commands(self, bot, admin_only=False, operator_only=False):
        categorized_commands = {}

        for command in bot.tree.walk_commands():
            command_checks = getattr(command, "checks", [])
            admin_level = None
            is_operator_command = False

            for check in command_checks:
                if hasattr(check, "__closure__") and check.__closure__:
                    for cell in check.__closure__:
                        val = cell.cell_contents
                        if isinstance(val, int):
                            admin_level = val
                        if isinstance(val, str) and val.endswith(" OP"):
                            is_operator_command = True

            if admin_only and admin_level is None:
                continue
            if operator_only and not is_operator_command:
                continue
            if not admin_only and not operator_only and (admin_level or is_operator_command):
                continue

            parent_name = command.parent.name if command.parent else "General"
            categorized_commands.setdefault(parent_name, []).append((command, admin_level))

        return categorized_commands

    @app_commands.command(description="Display the general help menu.")
    async def general(self, interaction: discord.Interaction):
        try:
            categorized = self.categorize_commands(interaction.client)
            command_groups = list(categorized.items())

            embed = discord.Embed(
                title="Help Menu",
                description="Use the buttons below to navigate through the commands",
                color=discord.Color.blurple(),
            )

            for category, commands in command_groups[:5]:
                embed.add_field(
                    name=f"🔹 {category}",
                    value="\n".join(f"/{cmd.name} - {cmd.description}" for cmd, _ in commands),
                    inline=False
                )

            embed.set_footer(text=f"Page 1/{(len(command_groups) + 4) // 5}")
            view = HelpPaginator(interaction.client, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            _log.error(f"Error displaying general help: {e}")
            await interaction.response.send_message("Error displaying help.", ephemeral=True)

    @app_commands.command(description="Display the admin help menu.")
    async def admin(self, interaction: discord.Interaction):
        try:
            categorized = self.categorize_commands(interaction.client, admin_only=True)
            level_colors = {1: "🟩", 2: "🟨", 3: "🟧", 4: "🟥"}

            embed = discord.Embed(
                title="Admin Help Menu",
                description="Admin commands grouped by category, color-coded by admin level.",
                color=discord.Color.red(),
            )

            for category, commands in categorized.items():
                embed.add_field(
                    name=f"🔹 {category}",
                    value="\n".join(
                        f"{level_colors.get(level, '⚪')} /{cmd.name} - {cmd.description}"
                        for cmd, level in commands
                    ),
                    inline=False,
                )

            embed.add_field(
                name="Admin Levels Key",
                value="\n".join([
                    "🟩 **Level 1**: Basic admin",
                    "🟨 **Level 2**: Elevated admin",
                    "🟧 **Level 3**: High admin",
                    "🟥 **Level 4**: Owner-level access",
                ]),
                inline=False,
            )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            _log.error(f"Error displaying admin help: {e}")
            await interaction.response.send_message("Error displaying admin help.", ephemeral=True)

    @app_commands.command(description="Display the operator help menu.")
    async def operator(self, interaction: discord.Interaction):
        try:
            categorized = self.categorize_commands(interaction.client, operator_only=True)
            command_groups = list(categorized.items())

            embed = discord.Embed(
                title="Operator Help Menu",
                description="Use the buttons below to navigate through the commands",
                color=discord.Color.green(),
            )

            for category, commands in command_groups[:5]:
                embed.add_field(
                    name=f"🔹 {category}",
                    value="\n".join(f"/{cmd.name} - {cmd.description}" for cmd, _ in commands),
                    inline=False,
                )

            embed.set_footer(text=f"Page 1/{(len(command_groups) + 4) // 5}")
            view = HelpPaginator(interaction.client, interaction, command_groups)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            _log.error(f"Error displaying operator help: {e}")
            await interaction.response.send_message("Error displaying operator help.", ephemeral=True)

    @app_commands.command(name="search", description="Look up help for a specific command.")
    @app_commands.describe(name="The name of the command to search for.")
    async def search(self, interaction: discord.Interaction, name: str):
        try:
            all_commands = list(interaction.client.tree.walk_commands())
            match = discord.utils.find(lambda c: c.name == name, all_commands)

            if not match:
                close = get_close_matches(name, [c.name for c in all_commands], n=1)
                if close:
                    match = discord.utils.find(lambda c: c.name == close[0], all_commands)

            if not match:
                await interaction.response.send_message(f"❌ Command `{name}` not found.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"Help: /{match.name}",
                description=match.description or "No description available.",
                color=discord.Color.blurple(),
            )

            if match.parameters:
                for param in match.parameters:
                    embed.add_field(
                        name=f"`{param.name}`",
                        value=f"Required: `{param.required}`\nType: `{param.type}`\n{param.description or ''}",
                        inline=False,
                    )

            aliases = getattr(match, "aliases", [])
            if aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in aliases), inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            _log.error(f"Error in help search: {e}", exc_info=True)
            await interaction.response.send_message("Something went wrong with help search.", ephemeral=True)

    @search.autocomplete("name")
    async def search_autocomplete(self, interaction: discord.Interaction, current: str):
        names = [cmd.name for cmd in interaction.client.tree.walk_commands()]
        matches = get_close_matches(current, names, n=10)
        return [app_commands.Choice(name=m, value=m) for m in matches]


async def setup(bot: discord.Client):
    bot.tree.add_command(HelpCommands())
