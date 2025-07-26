import discord
from utils.database import __database as database
from utils.helpers.__logging_module import get_log

_log = get_log("rules_logic")


async def update_rule_embed(guild: discord.Guild):
    """
    Update (or post) the full rules embed in the configured rule channel for the given guild.
    """
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

        embed = discord.Embed(
            title=f"📜 {guild.name} Server Rules",
            color=discord.Color.blurple(),
        )

        categorized = {}
        for rule in rules:
            categorized.setdefault(rule.category, []).append((rule.number, rule.text))

        for category, rule_list in categorized.items():
            text = "\n".join([f"**{num}.** {text}" for num, text in rule_list])
            embed.add_field(name=category, value=text, inline=False)

        # Update existing message or send new one
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

                # Post new embed and save message ID
                new_msg = await channel.send(embed=embed)
                bot_data.rule_message_id = str(new_msg.id)
                _log.info(f"Rule message ID {bot_data.rule_message_id}.")
                bot_data.save()
                _log.info(
                    f"Posted new rule embed and saved message ID for {guild.name}."
                )

    except Exception as e:
        _log.error(f"Failed to update rule embed for {guild.name}: {e}", exc_info=True)
