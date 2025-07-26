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

        # Flatten all rules into a numbered list
        flat_rules = [f"{r.number}: {r.text}" for r in rules]
        rules_text = "\n".join(flat_rules)

        # Build the full message string
        full_message = f"""__**About {bot_data.server_name.strip()}**__
{bot_data.server_desc.strip()}

════════════════════════════════════

📣 **Invite your friends! The more the merrier**
{bot_data.server_invite.strip()}

════════════════════════════════════

📏 **Rules**
{rules_text}"""

        # Optional: Append Other Info Section 1
        if bot_data.other_info_1_text.strip():
            full_message += f"""

════════════════════════════════════

📌 **{bot_data.other_info_1_title.strip()}**
{bot_data.other_info_1_text.strip()}"""

        # Optional: Append Other Info Section 2
        if bot_data.other_info_2_text.strip():
            full_message += f"""

════════════════════════════════════

📌 **{bot_data.other_info_2_title.strip()}**
{bot_data.other_info_2_text.strip()}"""

        # Send or update the message
        if bot_data.rule_message_id != "0":
            try:
                message = await channel.fetch_message(int(bot_data.rule_message_id))
                await message.edit(content=full_message, embed=None)
                _log.info(f"Updated rule message for guild {guild.name}.")
                return
            except discord.NotFound:
                _log.warning(
                    f"Rule message ID {bot_data.rule_message_id} not found; will re-post."
                )

        # Post new message
        new_msg = await channel.send(content=full_message)
        bot_data.rule_message_id = str(new_msg.id)
        bot_data.save()
        _log.info(f"Posted new rule message and saved ID for {guild.name}.")

    except Exception as e:
        _log.error(
            f"Failed to update rule message for {guild.name}: {e}", exc_info=True
        )
