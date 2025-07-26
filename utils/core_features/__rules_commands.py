import discord
from discord import app_commands
from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log

from .__rules_logic import update_rule_embed

_log = get_log(__name__)


class RulesCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="rules", description="Manage or view server rules")

    @app_commands.command(
        name="show", description="Show a specific rule by category and number."
    )
    @app_commands.describe(
        category="Category of the rule", number="Number of the rule in that category"
    )
    async def show_rule(
        self, interaction: discord.Interaction, category: str, number: int
    ):
        try:
            rule = (
                database.Rule.select()
                .where(
                    (database.Rule.guild_id == str(interaction.guild_id))
                    & (database.Rule.category == category)
                    & (database.Rule.number == number)
                )
                .first()
            )
            if not rule:
                await interaction.response.send_message(
                    "Rule not found.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title=f"📜 Rule {rule.number} - {rule.category}",
                description=rule.text,
                color=discord.Color.blurple(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            _log.error(f"Error fetching rule {category} #{number}: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while retrieving the rule.", ephemeral=True
            )

    @show_rule.autocomplete("category")
    async def autocomplete_category(
        self, interaction: discord.Interaction, current: str
    ):
        try:
            query = (
                database.Rule.select(database.Rule.category)
                .where(database.Rule.guild_id == str(interaction.guild_id))
                .distinct()
            )
            choices = [
                r.category
                for r in query
                if r.category.lower().startswith(current.lower())
            ]
            return [app_commands.Choice(name=cat, value=cat) for cat in choices[:25]]

        except Exception as e:
            _log.error(f"Autocomplete category failed: {e}", exc_info=True)
            return []

    @show_rule.autocomplete("number")
    async def autocomplete_rule_number(
        self, interaction: discord.Interaction, current: int
    ):
        try:
            category = interaction.namespace.category
            query = (
                database.Rule.select(database.Rule.number)
                .where(
                    (database.Rule.guild_id == str(interaction.guild_id))
                    & (database.Rule.category == category)
                )
                .order_by(database.Rule.number)
            )
            return [
                app_commands.Choice(name=f"Rule #{r.number}", value=r.number)
                for r in query
                if str(r.number).startswith(str(current)) or current == 0
            ][:25]

        except Exception as e:
            _log.error(f"Autocomplete rule number failed: {e}", exc_info=True)
            return []

    @app_commands.command(name="list", description="List all server rules.")
    async def list_rules(self, interaction: discord.Interaction):
        rules = (
            database.Rule.select()
            .where(database.Rule.guild_id == str(interaction.guild_id))
            .order_by(database.Rule.category, database.Rule.number)
        )

        if not rules.exists():
            await interaction.response.send_message(
                "No rules configured yet.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Server Rules",
            color=discord.Color.blurple(),
        )

        categories = {}
        for rule in rules:
            categories.setdefault(rule.category, []).append((rule.number, rule.text))

        for category, rule_list in categories.items():
            value = "\n".join([f"**{num}.** {text}" for num, text in rule_list])
            embed.add_field(name=category, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add", description="Add a rule to the server.")
    @app_commands.describe(
        category="The category for this rule", text="The text of the rule"
    )
    @has_admin_level(2)
    async def add_rule(
        self, interaction: discord.Interaction, category: str, text: str
    ):
        guild_id = str(interaction.guild_id)
        count = (
            database.Rule.select()
            .where(
                (database.Rule.guild_id == guild_id)
                & (database.Rule.category == category)
            )
            .count()
        )
        rule = database.Rule.create(
            guild_id=guild_id,
            category=category,
            number=count + 1,
            text=text,
        )

        await interaction.response.send_message(
            f"✅ Rule added in **{category}** as #{rule.number}.", ephemeral=True
        )
        await update_rule_embed(interaction.guild)

    @app_commands.command(
        name="remove", description="Remove a rule by number and category."
    )
    @app_commands.describe(
        category="The category of the rule", number="The number of the rule to remove"
    )
    @has_admin_level(2)
    async def remove_rule(
        self, interaction: discord.Interaction, category: str, number: int
    ):
        guild_id = str(interaction.guild_id)
        rule = (
            database.Rule.select()
            .where(
                (database.Rule.guild_id == guild_id)
                & (database.Rule.category == category)
                & (database.Rule.number == number)
            )
            .first()
        )

        if not rule:
            await interaction.response.send_message("Rule not found.", ephemeral=True)
            return

        rule.delete_instance()

        remaining_rules = (
            database.Rule.select()
            .where(
                (database.Rule.guild_id == guild_id)
                & (database.Rule.category == category)
            )
            .order_by(database.Rule.number)
        )

        for i, r in enumerate(remaining_rules, start=1):
            r.number = i
            r.save()

        await interaction.response.send_message(
            f"❌ Rule #{number} removed from **{category}**.", ephemeral=True
        )
        await update_rule_embed(interaction.guild)

    @app_commands.command(name="edit", description="Edit a rule's text.")
    @app_commands.describe(
        category="The category of the rule",
        number="The rule number",
        new_text="The new rule text",
    )
    @has_admin_level(2)
    async def edit_rule(
        self,
        interaction: discord.Interaction,
        category: str,
        number: int,
        new_text: str,
    ):
        rule = (
            database.Rule.select()
            .where(
                (database.Rule.guild_id == str(interaction.guild_id))
                & (database.Rule.category == category)
                & (database.Rule.number == number)
            )
            .first()
        )

        if not rule:
            await interaction.response.send_message("Rule not found.", ephemeral=True)
            return

        rule.text = new_text
        rule.save()
        await interaction.response.send_message(
            f"✏️ Rule #{number} in **{category}** updated.", ephemeral=True
        )
        await update_rule_embed(interaction.guild)

    @app_commands.command(
        name="set_channel", description="Set the channel to post server rules."
    )
    @has_admin_level(2)
    async def set_rule_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(interaction.guild_id)
            )

            if not bot_data:
                await interaction.followup.send(
                    "Bot data not found for this server.", ephemeral=True
                )
                return

            _log.info(f"Channel ID is {str(channel.id)}")

            bot_data.rule_channel = channel.id
            bot_data.save()

            await update_rule_embed(interaction.guild)
            await interaction.followup.send(
                f"✅ Rule channel set to {channel.mention} and rules posted.",
                ephemeral=True,
            )

        except Exception as e:
            _log.error(
                f"Error setting rule channel and posting embed: {e}", exc_info=True
            )
            await interaction.followup.send(
                "❌ Failed to set rule channel.", ephemeral=True
            )


async def setup(bot: discord.Client):
    bot.tree.add_command(RulesCommands())
