# utils/MRP_Cogs/daily_questions/dq_views.py

import discord
from discord import ui
from core import database
from core.logging_module import get_log

_log = get_log(__name__)


class QuestionVoteView(discord.ui.View):
    def __init__(self, bot, question_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.question_id = question_id

        question = database.Question.get(display_order=question_id)
        self.upvote_count = question.upvotes
        self.downvote_count = question.downvotes

        self.upvote_button = discord.ui.Button(
            label=f"👍 {self.upvote_count}",
            style=discord.ButtonStyle.green,
            custom_id="question_upvote",
        )
        self.upvote_button.callback = self.handle_upvote
        self.add_item(self.upvote_button)

        self.downvote_button = discord.ui.Button(
            label=f"👎 {self.downvote_count}",
            style=discord.ButtonStyle.red,
            custom_id="question_downvote",
        )
        self.downvote_button.callback = self.handle_downvote
        self.add_item(self.downvote_button)

    async def handle_upvote(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            question = database.Question.get(display_order=self.question_id)
            vote, created = database.QuestionVote.get_or_create(
                question=question, user_id=user_id, defaults={"vote_type": "up"}
            )

            if not created:
                if vote.vote_type == "up":
                    vote.delete_instance()
                    question.upvotes = max(0, question.upvotes - 1)
                else:
                    vote.vote_type = "up"
                    vote.save()
                    question.downvotes = max(0, question.downvotes - 1)
                    question.upvotes += 1
            else:
                question.upvotes += 1

            question.save()
            self._update_labels(question)
            await interaction.response.edit_message(view=self)

        except Exception as e:
            _log.error(f"Error handling upvote: {e}", exc_info=True)

    async def handle_downvote(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            question = database.Question.get(display_order=self.question_id)
            vote, created = database.QuestionVote.get_or_create(
                question=question, user_id=user_id, defaults={"vote_type": "down"}
            )

            if not created:
                if vote.vote_type == "down":
                    vote.delete_instance()
                    question.downvotes = max(0, question.downvotes - 1)
                else:
                    vote.vote_type = "down"
                    vote.save()
                    question.upvotes = max(0, question.upvotes - 1)
                    question.downvotes += 1
            else:
                question.downvotes += 1

            question.save()
            self._update_labels(question)
            await interaction.response.edit_message(view=self)

        except Exception as e:
            _log.error(f"Error handling downvote: {e}", exc_info=True)

    def _update_labels(self, question):
        self.upvote_button.label = f"👍 {question.upvotes}"
        self.downvote_button.label = f"👎 {question.downvotes}"


class DisabledQuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Add Question",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="persistent_view:qsm_add_question",
        disabled=True,
    )
    async def add_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        pass

    @discord.ui.button(
        label="Discard Question",
        style=discord.ButtonStyle.red,
        emoji="❌",
        custom_id="persistent_view:qsm_discard_question",
        disabled=True,
    )
    async def discard_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        pass


class QuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Add Question",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="persistent_view:qsm_add_question",
    )
    async def add_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            q = database.QuestionSuggestionQueue.get(
                database.QuestionSuggestionQueue.message_id == interaction.message.id
            )
            new_q = database.Question.create(question=q.question, usage="False")
            q.delete_instance()

            embed = discord.Embed(
                title="Question Suggestion",
                description="This question has been added to the database!",
                color=discord.Color.green(),
            )
            embed.add_field(name="Question", value=q.question)
            embed.add_field(name="Added By", value=interaction.user.mention)
            embed.set_footer(text=f"Question ID: {new_q.display_order}")
            await interaction.message.edit(
                embed=embed, view=DisabledQuestionSuggestionManager()
            )

            await interaction.response.send_message("Added.", ephemeral=True)
        except Exception as e:
            _log.exception("Error adding suggested question: %s", e)
            await interaction.response.send_message("Error occurred.", ephemeral=True)

    @discord.ui.button(
        label="Discard Question",
        style=discord.ButtonStyle.red,
        emoji="❌",
        custom_id="persistent_view:qsm_discard_question",
    )
    async def discard_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            q = database.QuestionSuggestionQueue.get(
                database.QuestionSuggestionQueue.message_id == interaction.message.id
            )
            q.delete_instance()

            embed = discord.Embed(
                title="Question Suggestion",
                description="This question has been discarded.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Question", value=q.question)
            embed.add_field(name="Discarded By", value=interaction.user.mention)
            embed.set_footer(text=f"Question ID: {q.id}")
            await interaction.message.edit(
                embed=embed, view=DisabledQuestionSuggestionManager()
            )

            await interaction.response.send_message("Discarded.", ephemeral=True)
        except Exception as e:
            _log.exception("Error discarding question: %s", e)
            await interaction.response.send_message("Error occurred.", ephemeral=True)


class SuggestModalNEW(discord.ui.Modal, title="Suggest a Question"):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    short_description = ui.TextInput(
        label="Daily Question", style=discord.TextStyle.long, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            embed = discord.Embed(
                title="Question Suggestion",
                description=f"Requested by {interaction.user.mention}",
                color=0x18C927,
            )
            embed.add_field(name="Question", value=self.short_description.value)

            log_channel = await self.bot.fetch_channel(777987716008509490)
            msg = await log_channel.send(embed=embed, view=QuestionSuggestionManager())

            database.QuestionSuggestionQueue.create(
                question=self.short_description.value,
                discord_id=interaction.user.id,
                message_id=msg.id,
            )

            await interaction.followup.send(
                "Thank you for your suggestion!", ephemeral=True
            )
        except Exception as e:
            _log.exception("Error in SuggestModalNEW: %s", e)
            await interaction.followup.send("An error occurred.", ephemeral=True)


class SuggestQuestionFromDQ(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Suggest a Question!",
        style=discord.ButtonStyle.blurple,
        emoji="📝",
        custom_id="persistent_view:qsm_sug_question",
    )
    async def suggest_question(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))
