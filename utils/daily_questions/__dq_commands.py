# utils/daily_questions/dq_main.py

import math
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands

from utils.database import __database as database
from utils.helpers.__checks import has_admin_level
from utils.helpers.__pagination import paginate_embed
from utils.admin.bot_management.__bm_logic import get_bot_data_for_server
from utils.helpers.__logging_module import get_log

from .__dq_logic import (
    send_specific_question_to_guild_no_usage,
    renumber_display_order,
    reset_question_usage,
)
from .__dq_views import (
    DailyQuestionActionView,
    SuggestModalNEW,
    QuestionVoteView,
    create_question_embed
)

_log = get_log(__name__)


class DailyQuestionCommands(commands.GroupCog, name="daily-question"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="manage", description="Manage daily questions.")
    @has_admin_level(2)
    async def manage(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🔧 Manage Daily Questions:",
            view=DailyQuestionActionView(self.get_callback),
            ephemeral=True,
        )

    # ---------- Callbacks ---------- #
    def get_callback(self, action: str):
        match action:
            case "post":
                return self.post_question
            case "repost":
                return self.repost_last_question
            case "new":
                return self.new_question
            case "modify":
                return self.modify_question
            case "delete":
                return self.delete_question
            case "list":
                return self.list_questions
            case "reset-usage":
                return self.reset_usage
            case "toggle":
                return self.toggle_daily_question
            case "suggest":
                return self.suggest_question


    async def post_question(self, interaction: discord.Interaction, id: str):
        await interaction.response.defer(ephemeral=True)  # keeps UI snappy and avoids double-send errors

        bot_data = get_bot_data_for_server(str(interaction.guild.id))
        # Prefer explicit id, otherwise fall back to last recorded
        question_id = id or (bot_data.last_question_posted if bot_data else None)

        if not question_id:
            await interaction.followup.send("No recent question found and no id provided.", ephemeral=True)
            return

        try:
            # Ensure we’re dealing with an int display_order
            question_display_order = int(str(question_id).strip())
        except ValueError:
            await interaction.followup.send(f"Invalid question id `{question_id}`. Expecting a display order number.", ephemeral=True)
            return

        try:
            await send_specific_question_to_guild_no_usage(
                self.bot,
                interaction.guild.id,
                question_display_order,
            )
            await interaction.followup.send(f"✅ Question `{question_display_order}` posted to this server (no usage change).", ephemeral=True)
        except Exception:
            await interaction.followup.send("❌ Failed to post that question here. Check logs for details.", ephemeral=True)


    async def repost_last_question(self, interaction: discord.Interaction):
        try:
            database.ensure_database_connection()

            bot_data = get_bot_data_for_server(interaction.guild.id)
            if not bot_data or not bot_data.last_question_posted:
                await interaction.response.send_message(
                    "No previous question found to repost.", ephemeral=True
                )
                return

            # Fetch the last posted question
            question = database.Question.get(
                database.Question.display_order == bot_data.last_question_posted
            )

            # Build the embed via the shared factory in __dq_views.py
            embed = create_question_embed(question)

            # Resolve the send channel
            channel_id = int(bot_data.daily_question_channel)
            channel = interaction.client.get_channel(channel_id) or interaction.guild.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message(
                    "Daily question channel not found.", ephemeral=True
                )
                return

            # Send with the standard voting view
            await channel.send(
                embed=embed,
                view=QuestionVoteView(self.bot, question.display_order),
            )

            await interaction.response.send_message(
                f"✅ Reposted Question #{question.display_order} in {channel.mention}.",
                ephemeral=True,
            )

        except database.Question.DoesNotExist:
            await interaction.response.send_message(
                "That question no longer exists.", ephemeral=True
            )
        except Exception as e:
            # Optional: _log.error("repost_last_question failed", exc_info=True)
            await interaction.response.send_message(
                "There was an error reposting the question.", ephemeral=True
            )

    async def new_question(self, interaction: discord.Interaction, question: str):
        try:
            database.Question.create(question=question, usage="False")
            renumber_display_order()
            await interaction.response.send_message(
                "✅ Question added.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error adding question: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to add question.", ephemeral=True
            )

    async def modify_question(
        self, interaction: discord.Interaction, id: str, question: str
    ):
        try:
            q = database.Question.get(display_order=id)
            q.question = question
            q.save()
            await interaction.response.send_message(
                f"✅ Modified question `{id}`.", ephemeral=True
            )
        except database.Question.DoesNotExist:
            await interaction.response.send_message(
                "❌ Question not found.", ephemeral=True
            )

    async def delete_question(self, interaction: discord.Interaction, id: str):
        try:
            q = database.Question.get(display_order=id)
            q.delete_instance()
            renumber_display_order()
            await interaction.response.send_message(
                f"🗑️ Question `{id}` deleted.", ephemeral=True
            )
        except database.Question.DoesNotExist:
            await interaction.response.send_message(
                "❌ Question not found.", ephemeral=True
            )

    async def list_questions(self, interaction: discord.Interaction):
        renumber_display_order()

        def get_total_pages(page_size: int) -> int:
            total = database.Question.select().count()
            return math.ceil(total / page_size)

        async def populate_embed(embed: discord.Embed, page: int):
            embed.clear_fields()
            questions = (
                database.Question.select()
                .order_by(database.Question.display_order)
                .paginate(page, 10)
            )
            q_list = "\n".join(f"{q.display_order}. {q.question}" for q in questions)
            embed.add_field(name=f"Page {page}", value=q_list or "*No Questions Found*")
            return embed

        try:
            embed = discord.Embed(title="📋 Daily Questions")
            await paginate_embed(
                self.bot,
                interaction,
                embed,
                populate_embed,
                get_total_pages(10),
                page=1,
            )
        except Exception as e:
            _log.error(f"Error listing questions: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to list questions.", ephemeral=True
            )

    async def toggle_daily_question(self, interaction: discord.Interaction):
        try:
            bot_data = get_bot_data_for_server(str(interaction.guild.id))
            bot_data.daily_question_enabled = not bot_data.daily_question_enabled
            bot_data.save()
            status = "enabled" if bot_data.daily_question_enabled else "disabled"
            await interaction.response.send_message(
                f"✅ Daily questions {status}.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error toggling QOD: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to toggle QOD setting.", ephemeral=True
            )

    async def reset_usage(self, interaction: discord.Interaction):
        try:
            count = reset_question_usage()
            await interaction.response.send_message(
                f"✅ Reset usage for {count} questions.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error resetting usage: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to reset usage.", ephemeral=True
            )

    async def suggest_question(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))


async def setup(bot):
    await bot.add_cog(DailyQuestionCommands(bot))
    _log.info("✅ DailyQuestionCommands cog loaded.")
