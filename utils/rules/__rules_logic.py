import discord
from utils.database import __database as database
from utils.helpers.__logging_module import get_log

_log = get_log("rules_logic")


async def update_rule_embed(guild: discord.Guild):
    try:
        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(guild.id)
        )
        if not bot_data or not bot_data.rule_channel:
            _log.warning(f"No rule channel configured for guild: {guild.name}")
            return

        channel = guild.get_channel(int(bot_data.rule_channel))
        if not channel:
            _log.warning(
                f"Rule channel ID {bot_data.rule_channel} not found in guild: {guild.name}"
            )
            return

        rules = (
            database.Rule.select()
            .where(database.Rule.guild_id == str(guild.id))
            .order_by(database.Rule.category, database.Rule.number)
        )

        if not rules.exists():
            _log.info(f"No rules found for guild: {guild.name}")
            return

        # Group rules by category
        categorized = {}
        for rule in rules:
            categorized.setdefault(rule.category, []).append((rule.number, rule.text))

        # Format each category block
        formatted_blocks = []
        for category, rule_list in categorized.items():
            formatted_rules = "\n".join([f"{num}: {text}" for num, text in rule_list])
            formatted_blocks.append(f"• **{category}**\n{formatted_rules}")

        # Combine final rules text
        rules_text = "\n\n".join(formatted_blocks)
        if len(rules_text) > 1024:
            rules_text = rules_text[:1021] + "..."

        # Create embed
        embed = discord.Embed(
            title=f"__📜 About {bot_data.server_name.strip()}__",
            description=bot_data.server_desc.strip() + "\n\u200b",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="════════════════════════════════════", value="\u200b", inline=False
        )

        embed.add_field(
            name="*📣 Invite your friends! The more the merrier*",
            value=bot_data.server_invite.strip() + "\n\u200b",
            inline=False,
        )

        embed.add_field(
            name="════════════════════════════════════", value="\u200b", inline=False
        )

        embed.add_field(
            name="__📏 Rules__",
            value="\u200b\n"
            + rules_text
            + "\n\u200b",  # Adds blank line before and after
            inline=False,
        )

        # Optional Section 1
        if bot_data.other_info_1_text.strip():
            embed.add_field(
                name="════════════════════════════════════",
                value="\u200b",
                inline=False,
            )
            embed.add_field(
                name=f"__{bot_data.other_info_1_title.strip()}__",
                value=bot_data.other_info_1_text.strip() + "\n\u200b",
                inline=False,
            )

        # Optional Section 2
        if bot_data.other_info_2_text.strip():
            embed.add_field(
                name="════════════════════════════════════",
                value="\u200b",
                inline=False,
            )
            embed.add_field(
                name=f"__{bot_data.other_info_2_title.strip()}__",
                value=bot_data.other_info_2_text.strip() + "\n\u200b",
                inline=False,
            )

        # Final divider before footer
        embed.add_field(
            name="════════════════════════════════════", value="\u200b", inline=False
        )

        embed.set_footer(text="Last updated")
        embed.timestamp = discord.utils.utcnow()

        # Update or post new
        if bot_data.rule_message_id != "0":
            try:
                message = await channel.fetch_message(int(bot_data.rule_message_id))
                await message.edit(embed=embed)
                _log.info(f"Updated rule embed for guild {guild.name}.")
                return
            except discord.NotFound:
                _log.warning(
                    f"Rule message ID {bot_data.rule_message_id} not found; will re-post."
                )

        new_msg = await channel.send(embed=embed)
        bot_data.rule_message_id = str(new_msg.id)
        bot_data.save()
        _log.info(f"Posted new rule embed and saved message ID for {guild.name}.")

    except Exception as e:
        _log.error(f"Failed to update rule embed for {guild.name}: {e}", exc_info=True)
