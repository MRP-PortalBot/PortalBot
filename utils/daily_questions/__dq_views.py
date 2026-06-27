# utils/MRP_Cogs/daily_questions/dq_views.py

import discord
from discord import ui
from datetime import datetime
from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from typing import Callable, Optional
import re

_log = get_log(__name__)

QUESTION_UPVOTE_CUSTOM_ID = "question_upvote"
QUESTION_DOWNVOTE_CUSTOM_ID = "question_downvote"
QUESTION_FOOTER_RE = re.compile(r"Question #(?P<question_id>\d+)")


# ──────────────── NEW: Daily QOD Manager Interface ──────────────── #
class DailyQuestionActionView(discord.ui.View):
    def __init__(
        self, callback_provider: Callable[[str], Callable], timeout: Optional[int] = 180
    ):
        super().__init__(timeout=timeout)
        self.callback_provider = callback_provider

        self.add_item(DQButton("📤 Post Question", "post"))
        self.add_item(DQButton("♻️ Repost Last", "repost"))
        self.add_item(DQButton("🆕 Add", "new"))
        self.add_item(DQButton("✏️ Modify", "modify"))
        self.add_item(DQButton("🗑️ Delete", "delete"))
        self.add_item(DQButton("📋 List", "list"))
        self.add_item(DQButton("🧪 Reset Usage", "reset-usage"))
        self.add_item(DQButton("🔁 Toggle QOD", "toggle"))
        self.add_item(DQButton("💡 Suggest", "suggest"))


class DQButton(discord.ui.Button):
    def __init__(self, label: str, action: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        view: DailyQuestionActionView = self.view  # type: ignore
        callback_func = view.callback_provider(self.action)

        if self.action == "new":
            await interaction.response.send_modal(
                QuestionInputModal(
                    "Add New Question", "Question Text", callback=callback_func
                )
            )
        elif self.action == "modify":
            await interaction.response.send_modal(
                IDAndQuestionInputModal(callback=callback_func)
            )
        elif self.action in {"delete", "post"}:
            await interaction.response.send_modal(
                QuestionIDInputModal(
                    "Enter Question ID", "Question ID", callback=callback_func
                )
            )
        elif self.action == "suggest":
            await callback_func(interaction)
        else:
            await callback_func(interaction)


class QuestionInputModal(discord.ui.Modal):
    def __init__(
        self, title: str, label: str, default: str = "", callback: Callable = None
    ):
        super().__init__(title=title)
        self.callback_func = callback
        self.input = ui.TextInput(
            label=label, default=default, max_length=400, required=True
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction, self.input.value)


class IDAndQuestionInputModal(discord.ui.Modal):
    def __init__(self, callback: Callable):
        super().__init__(title="Modify Question")
        self.callback_func = callback

        self.id_input = ui.TextInput(
            label="Question ID", placeholder="e.g., 5", required=True
        )
        self.question_input = ui.TextInput(
            label="New Question Text", style=discord.TextStyle.paragraph, required=True
        )

        self.add_item(self.id_input)
        self.add_item(self.question_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_func(
            interaction, self.id_input.value, self.question_input.value
        )


class QuestionIDInputModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, callback: Callable):
        super().__init__(title=title)
        self.callback_func = callback
        self.id_input = ui.TextInput(label=label, placeholder="e.g., 5", required=True)
        self.add_item(self.id_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_func(interaction, self.id_input.value)


# ──────────────── EXISTING COMPONENTS: UNCHANGED ──────────────── #


class QuestionVoteView(discord.ui.View):
    def __init__(self, bot, question_id=None, *, include_suggest: bool = True):
        super().__init__(timeout=None)
        self.bot = bot
        self.question_id = question_id

        question = None
        if question_id is not None:
            question = database.Question.get(display_order=question_id)

        self.upvote_count = question.upvotes if question else 0
        self.downvote_count = question.downvotes if question else 0

        self.upvote_button = discord.ui.Button(
            label=f"👍 {self.upvote_count}" if question else "👍",
            style=discord.ButtonStyle.green,
            custom_id=QUESTION_UPVOTE_CUSTOM_ID,
        )
        self.upvote_button.callback = self.handle_upvote
        self.add_item(self.upvote_button)

        self.downvote_button = discord.ui.Button(
            label=f"👎 {self.downvote_count}" if question else "👎",
            style=discord.ButtonStyle.red,
            custom_id=QUESTION_DOWNVOTE_CUSTOM_ID,
        )
        self.downvote_button.callback = self.handle_downvote
        self.add_item(self.downvote_button)

        if include_suggest:
            self.suggest_button = discord.ui.Button(
                label="Suggest a Question!",
                style=discord.ButtonStyle.blurple,
                emoji="📝",
                custom_id="persistent_view:qsm_sug_question",
            )
            self.suggest_button.callback = self.handle_suggest_question
            self.add_item(self.suggest_button)

    async def handle_upvote(self, interaction: discord.Interaction):
        await self._handle_vote(interaction, "up")

    async def handle_downvote(self, interaction: discord.Interaction):
        await self._handle_vote(interaction, "down")

    async def _handle_vote(self, interaction: discord.Interaction, vote_type: str):
        user_id = str(interaction.user.id)
        try:
            database.ensure_database_connection()
            question = self._get_question_from_interaction(interaction)
            vote, created = database.QuestionVote.get_or_create(
                question=question,
                user_id=user_id,
                defaults={"vote_type": vote_type},
            )

            if not created:
                if vote.vote_type == vote_type:
                    vote.delete_instance()
                    self._decrement_question_vote(question, vote_type)
                else:
                    old_vote_type = vote.vote_type
                    vote.vote_type = vote_type
                    vote.save()
                    self._decrement_question_vote(question, old_vote_type)
                    self._increment_question_vote(question, vote_type)
            else:
                self._increment_question_vote(question, vote_type)

            question.save()
            self._update_labels(question)
            await interaction.response.edit_message(view=self)

        except Exception as e:
            _log.error(f"Error handling {vote_type}vote: {e}", exc_info=True)
            await self._send_vote_error(interaction)

    def _get_question_from_interaction(self, interaction: discord.Interaction):
        question_id = self.question_id or self._question_id_from_message(interaction)
        if question_id is None:
            raise ValueError("Could not determine daily question id for vote.")
        return database.Question.get(display_order=str(question_id))

    def _question_id_from_message(self, interaction: discord.Interaction):
        message = interaction.message
        if not message or not message.embeds:
            return None

        footer_text = message.embeds[0].footer.text or ""
        match = QUESTION_FOOTER_RE.search(footer_text)
        return match.group("question_id") if match else None

    def _increment_question_vote(self, question, vote_type: str):
        if vote_type == "up":
            question.upvotes += 1
        else:
            question.downvotes += 1

    def _decrement_question_vote(self, question, vote_type: str):
        if vote_type == "up":
            question.upvotes = max(0, question.upvotes - 1)
        else:
            question.downvotes = max(0, question.downvotes - 1)

    async def _send_vote_error(self, interaction: discord.Interaction):
        message = "I couldn't record that vote. Please try again in a moment."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            pass

    async def handle_suggest_question(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))

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

# ──────────────── DAILY QUESTION EMBED ──────────────── #

def create_question_embed(question) -> discord.Embed:
    embed = discord.Embed(
        title="🌟❓Question of the Day❓🌟",
        description=f"## **{question.question}**",
        color=discord.Color.from_rgb(177, 13, 159),
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/788873229136560140/1298745739048124457/MC-QOD.png"
    )
    embed.add_field(
        name="🗣️ Discuss",
        value="We'd love to hear your thoughts! Share your response below and get to know the community better!",
        inline=False,
    )
    embed.add_field(
        name="💡 Tip",
        value="Remember, thoughtful answers help everyone learn something new!",
        inline=False,
    )
    embed.set_footer(
        text=f"Thank you for participating! • Question #{question.display_order}",
        icon_url="https://cdn.discordapp.com/attachments/788873229136560140/801180249748406272/Portal_Design.png",
    )
    embed.timestamp = datetime.now()
    return embed
