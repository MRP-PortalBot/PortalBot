import math
import discord
from discord import app_commands
from discord.ext import commands
from core import database, checks
from core.pagination import paginate_embed
from core.common import get_cached_bot_data
from core.logging_module import get_log

from .__dq_views import QuestionVoteView, SuggestModalNEW
from .__dq_logic import (
    send_daily_question,
    renumber_display_order,
    reset_question_usage,
)


_log = get_log(__name__)


class DailyQuestionCommands(commands.GroupCog, name="daily-question"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="post",
        description="Post a daily question by ID or repeat today's question.",
    )
    @checks.has_admin_level(2)
    async def post(self, interaction: discord.Interaction, id: str = None):
        bot_data = get_cached_bot_data(interaction.guild.id)
        if not bot_data:
            await interaction.response.send_message(
                "No bot data found.", ephemeral=True
            )
            return

        question_id = id or bot_data.last_question_posted
        if not question_id:
            await interaction.response.send_message(
                "No recent question found.", ephemeral=True
            )
            return

        await send_daily_question(self.bot, question_id)
        await interaction.response.send_message(
            f"Question `{question_id}` posted.", ephemeral=True
        )

    @app_commands.command(name="modify", description="Modify a question by ID.")
    @checks.has_admin_level(2)
    async def modify(self, interaction: discord.Interaction, id: str, question: str):
        try:
            q = database.Question.get(database.Question.display_order == id)
            q.question = question
            q.save()
            _log.info(f"Modified question {id}")
            await interaction.response.send_message(
                f"✅ Modified question {id}.", ephemeral=True
            )
        except database.Question.DoesNotExist:
            await interaction.response.send_message(
                "❌ Question not found.", ephemeral=True
            )

    @app_commands.command(name="new", description="Add a new daily question.")
    @checks.has_admin_level(2)
    async def new(self, interaction: discord.Interaction, question: str):
        try:
            database.Question.create(question=question, usage="False")
            _log.info(f"Added question: {question}")
            renumber_display_order()
            await interaction.response.send_message(
                "✅ Question added.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error adding question: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to add question.", ephemeral=True
            )

    @app_commands.command(name="delete", description="Delete a question by ID.")
    @checks.has_admin_level(2)
    async def delete(self, interaction: discord.Interaction, id: str):
        try:
            q = database.Question.get(database.Question.display_order == id)
            q.delete_instance()
            renumber_display_order()
            await interaction.response.send_message(
                f"🗑️ Question `{id}` deleted.", ephemeral=True
            )
        except database.Question.DoesNotExist:
            await interaction.response.send_message(
                "❌ Question not found.", ephemeral=True
            )

    @app_commands.command(name="list", description="List all daily questions.")
    async def list(self, interaction: discord.Interaction, page: int = 1):
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
            if not questions.exists():
                embed.add_field(name="No Questions", value="None found.")
            else:
                q_list = "\n".join(
                    f"{q.display_order}. {q.question}" for q in questions
                )
                embed.add_field(name=f"Page {page}", value=q_list)
            return embed

        try:
            total_pages = get_total_pages(10)
            embed = discord.Embed(title="📋 Daily Questions")
            await paginate_embed(
                self.bot, interaction, embed, populate_embed, total_pages, page
            )
        except Exception as e:
            _log.error(f"Error listing questions: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to list questions.", ephemeral=True
            )

    @app_commands.command(
        name="toggle-daily-question",
        description="Enable or disable daily question posting.",
    )
    @checks.has_admin_level(2)
    async def toggle(self, interaction: discord.Interaction):
        try:
            bot_data = get_cached_bot_data(interaction.guild.id)
            bot_data.daily_question_enabled = not bot_data.daily_question_enabled
            bot_data.save()
            status = "enabled" if bot_data.daily_question_enabled else "disabled"
            _log.info(f"Daily questions {status} for {interaction.guild.id}")
            await interaction.response.send_message(
                f"✅ Daily questions {status}.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error toggling daily questions: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to toggle setting.", ephemeral=True
            )

    @app_commands.command(name="suggest", description="Suggest a new daily question.")
    async def suggest(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))

    @app_commands.command(
        name="reset-usage", description="Reset usage flag for all daily questions."
    )
    @checks.has_admin_level(2)
    async def reset_usage(self, interaction: discord.Interaction):
        try:
            count = reset_question_usage()
            _log.info(f"Reset usage for {count} questions.")
            await interaction.response.send_message(
                f"✅ Reset usage for {count} questions.", ephemeral=True
            )
        except Exception as e:
            _log.error(f"Error resetting question usage: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Failed to reset question usage.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DailyQuestionCommands(bot))
    _log.info("✅ DailyQuestionCommands cog loaded.")
