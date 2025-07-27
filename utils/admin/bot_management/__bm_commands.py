# admin/bot_management/__bm_commands.py
import discord
import json
from discord import app_commands
from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__logging_module import get_log
from .__bm_views import BotConfigSectionSelectView
from utils.core_features.__constants import EmbedColors

_log = get_log(__name__)


class ConfigCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="configure", description="Bot configuration commands")

    @app_commands.command(
        name="edit_data", description="Edit server bot configuration."
    )
    @has_admin_level(2)
    async def edit_data(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(interaction.guild.id)
        )
        if not bot_data:
            await interaction.followup.send(
                "❌ BotData not found for this server.", ephemeral=True
            )
            return

        # Convert to dict for UI use
        bot_data_dict = {
            field.name: getattr(bot_data, field.name)
            for field in bot_data._meta.sorted_fields
        }

        view = BotConfigSectionSelectView(bot_data_dict, self.handle_botdata_update)
        await interaction.followup.send(
            "🛠 Select a config section to edit:", view=view, ephemeral=True
        )

    async def handle_botdata_update(
        self, interaction: discord.Interaction, updated_fields: dict
    ):
        try:
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(interaction.guild.id)
            )
            if not bot_data:
                await interaction.response.send_message(
                    "❌ BotData not found.", ephemeral=True
                )
                return

            for key, value in updated_fields.items():
                setattr(bot_data, key, value)

            bot_data.save()
            await interaction.response.send_message(
                "✅ Configuration updated.", ephemeral=True
            )

        except Exception as e:
            _log.error(f"Error updating bot data: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to update config.", ephemeral=True
            )


async def setup(bot: discord.Client):
    bot.tree.add_command(ConfigCommands())
