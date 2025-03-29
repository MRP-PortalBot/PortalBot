import discord
from discord.ext import commands
from discord import app_commands
from core import database
from core.logging_module import get_log
from core.checks import has_admin_level
from core.common import get_cached_bot_data

_log = get_log(__name__)


class RulesCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("RulesCMD Cog Loaded")

    rules_group = app_commands.Group(
        name="rules", description="Manage or view server rules"
    )

    async def update_rule_embed(self, guild: discord.Guild):
        """Update or send the rule embed in the configured rule channel."""
        bot_data = get_cached_bot_data(guild.id)
        if not bot_data or not bot_data.rule_channel:
            _log.warning(
                f"No rule channel configured for guild {guild.name} ({guild.id})"
            )
            return

        channel = guild.get_channel(bot_data.rule_channel)
        if not channel:
            _log.error(
                f"Configured rule channel {bot_data.rule_channel} not found in guild {guild.name}"
            )
            return

        rules = (
            database.Rule.select()
            .where(database.Rule.guild_id == guild.id)
            .order_by(database.Rule.category, database.Rule.number)
        )

        if not rules.exists():
            await channel.send("No rules configured for this server.")
            return

        embed = discord.Embed(
            title=f"{guild.name} - Server Rules",
            description="These rules are actively enforced. Please read carefully.",
            color=discord.Color.blurple(),
        )

        categories = {}
        for rule in rules:
            categories.setdefault(rule.category, []).append((rule.number, rule.text))

        for category, rule_list in categories.items():
            value = "\n".join([f"**{num}.** {text}" for num, text in rule_list])
            embed.add_field(name=category, value=value, inline=False)

        try:
            # Try to update the existing embed using rule_message_id
            if bot_data.rule_message_id:
                try:
                    msg = await channel.fetch_message(bot_data.rule_message_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound:
                    _log.warning("Rule message ID not found. Reposting rule embed.")
                    bot_data.rule_message_id = None

            # Send new message and store ID
            new_msg = await channel.send(embed=embed)
            bot_data.rule_message_id = new_msg.id
            bot_data.save()
            _log.info(f"Rule embed message ID saved: {new_msg.id}")

        except Exception as e:
            _log.error(
                f"Failed to update rule embed in {channel.name}: {e}", exc_info=True
            )

    @rules_group.command(name="list", description="List all server rules.")
    async def list_rules(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        rules = (
            database.Rule.select()
            .where(database.Rule.guild_id == guild_id)
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

    @rules_group.command(name="add", description="Add a rule to the server.")
    @app_commands.describe(
        category="The category for this rule", text="The text of the rule"
    )
    @has_admin_level(2)
    async def add_rule(
        self, interaction: discord.Interaction, category: str, text: str
    ):
        guild_id = interaction.guild_id
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
        await self.update_rule_embed(interaction.guild)

    @rules_group.command(
        name="remove", description="Remove a rule by number and category."
    )
    @app_commands.describe(
        category="The category of the rule", number="The number of the rule to remove"
    )
    @has_admin_level(2)
    async def remove_rule(
        self, interaction: discord.Interaction, category: str, number: int
    ):
        guild_id = interaction.guild_id
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

        # Reorder remaining rules in the same category
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
        await self.update_rule_embed(interaction.guild)

    @rules_group.command(name="edit", description="Edit a rule's text.")
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
                (database.Rule.guild_id == interaction.guild_id)
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
        await self.update_rule_embed(interaction.guild)


async def setup(bot):
    await bot.add_cog(RulesCMD(bot))
    _log.info("RulesCMD Cog setup complete.")
