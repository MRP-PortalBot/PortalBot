import discord
from discord import app_commands
from discord.ext import commands


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Reference to documentation")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help Menu",
            description="Here are the available commands organized by category:",
            color=discord.Color.blue(),
        )

        # General commands
        embed.add_field(
            name="**General Commands**",
            value="Basic bot interaction and system monitoring commands.",
            inline=False,
        )
        embed.add_field(
            name="`/help`",
            value="Displays this help message.\n*Usage:* `/help`",
            inline=False,
        )
        embed.add_field(
            name="`/ping`",
            value="Check the bot's latency and system resource usage.\n*Usage:* `/ping`",
            inline=False,
        )

        # Banned list commands
        embed.add_field(
            name="**Banned List Commands**",
            value="Manage and query the banned list.",
            inline=False,
        )
        embed.add_field(
            name="`/banned-list post`",
            value="Add a person to the banned list.\n*Usage:* `/banned-list post [discord_id] [gamertag] [originating_realm] [ban_type]`",
            inline=False,
        )
        embed.add_field(
            name="`/banned-list search <term>`",
            value="Search for a user in the banned list.\n*Usage:* `/banned-list search [term]`",
            inline=False,
        )
        embed.add_field(
            name="`/banned-list edit <entry_id> <field> <new_value>`",
            value="Edit an entry in the banned list.\n*Usage:* `/banned-list edit [entry_id] [field] [new_value]`",
            inline=False,
        )

        # Dynamically generate help for other cogs
        for cog_name, cog in self.bot.cogs.items():
            if cog_name not in ["HelpCMD"]:  # Skip the help command itself
                cog_commands = [
                    cmd
                    for cmd in cog.get_app_commands()
                    if isinstance(cmd, app_commands.Command)
                ]
                if cog_commands:
                    embed.add_field(
                        name=f"**{cog_name} Commands**",
                        value=f"Commands under the `{cog_name}` module.",
                        inline=False,
                    )
                    for command in cog_commands:
                        embed.add_field(
                            name=f"`/{command.name}`",
                            value=f"{command.description}\n*Usage:* `/{command.name} [parameters]`",
                            inline=False,
                        )

        embed.set_footer(
            text=f"Requested by {interaction.user}",
            icon_url=interaction.user.avatar.url,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCMD(bot))
