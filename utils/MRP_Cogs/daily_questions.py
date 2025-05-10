import math
from datetime import datetime, timedelta
import asyncio
import pytz
import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from peewee import fn
from core import database, checks
from core.common import load_config, get_cached_bot_data
from core.pagination import paginate_embed
from core.logging_module import get_log


config, _ = load_config()
_log = get_log(__name__)


def get_seconds_until(target_time):
    """Returns the number of seconds until the next occurrence of the target_time."""
    now = datetime.now(pytz.timezone("America/Chicago"))
    target = now.replace(
        hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0
    )
    if target < now:
        target += timedelta(
            days=1
        )  # If the target time is earlier today, move it to tomorrow
    return (target - now).total_seconds()


def renumber_display_order():
    try:
        database.ensure_database_connection()  # Ensure the database is connected
        questions = database.Question.select().order_by(database.Question.id)
        for new_order, question in enumerate(questions, start=1):
            question.display_order = new_order
            question.save()

        _log.info("Questions have been renumbered successfully by display order.")
    except Exception as e:
        _log.error(f"Error renumbering questions by display order: {e}", exc_info=True)


# Disabled View for questions that have been processed
class DisabledQuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

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


# Active View for managing question suggestions
class QuestionSuggestionManager(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

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
            new_question = database.Question.create(question=q.question, usage=False)
            q.delete_instance()
            _log.info(
                f"Question '{q.question}' added by {interaction.user.display_name}."
            )

            # Update embed and disable view
            embed = discord.Embed(
                title="Question Suggestion",
                description="This question has been added to the database!",
                color=discord.Color.green(),
            )
            embed.add_field(name="Question", value=q.question)
            embed.add_field(name="Added By", value=interaction.user.mention)
            embed.set_footer(text=f"Question ID: {new_question.display_order}")
            await interaction.message.edit(
                embed=embed, view=DisabledQuestionSuggestionManager()
            )

            await interaction.response.send_message(
                "Operation Complete.", ephemeral=True
            )
            renumber_display_order()
        except database.QuestionSuggestionQueue.DoesNotExist:
            _log.error("Question suggestion not found in the queue.")
            await interaction.response.send_message(
                "This question suggestion could not be found.", ephemeral=True
            )
        except Exception as e:
            _log.exception("Error adding question: %s", e)
            await interaction.response.send_message(
                "An error occurred.", ephemeral=True
            )

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
            _log.info(
                f"Question '{q.question}' discarded by {interaction.user.display_name}."
            )

            # Update embed and disable view
            embed = discord.Embed(
                title="Question Suggestion",
                description="This question has been discarded!",
                color=discord.Color.red(),
            )
            embed.add_field(name="Question", value=q.question)
            embed.add_field(name="Discarded By", value=interaction.user.mention)
            embed.set_footer(text=f"Question ID: {q.id}")
            await interaction.message.edit(
                embed=embed, view=DisabledQuestionSuggestionManager()
            )

            await interaction.response.send_message(
                "Operation Complete.", ephemeral=True
            )
        except Exception as e:
            _log.exception("Error discarding question: %s", e)
            await interaction.response.send_message(
                "An error occurred.", ephemeral=True
            )


# Modal for submitting a new question
class SuggestModalNEW(discord.ui.Modal, title="Suggest a Question"):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    short_description = ui.TextInput(
        label="Daily Question", style=discord.TextStyle.long, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()  # Defers the interaction to give more time

            # Create embed and log the question suggestion
            embed = discord.Embed(
                title="Question Suggestion",
                description=f"Requested by {interaction.user.mention}",
                color=0x18C927,
            )
            embed.add_field(name="Question", value=self.short_description.value)

            # Send the suggestion to the log channel
            log_channel = await self.bot.fetch_channel(777987716008509490)
            msg = await log_channel.send(embed=embed, view=QuestionSuggestionManager())

            # Save the question to the suggestion queue with the message ID
            q = database.QuestionSuggestionQueue.create(
                question=self.short_description.value,
                discord_id=interaction.user.id,
                message_id=msg.id,  # Now we have the actual message ID
            )
            _log.info(
                f"Question '{self.short_description.value}' suggested by {interaction.user.display_name}."
            )

            # Send the follow-up response
            await interaction.followup.send(
                "Thank you for your suggestion!", ephemeral=True
            )

        except Exception as e:
            _log.exception("Error submitting question: %s", e)
            try:
                await interaction.followup.send(
                    "An error occurred while submitting your suggestion.",
                    ephemeral=True,
                )
            except discord.errors.NotFound:
                _log.error(
                    "Interaction follow-up failed because the webhook was not found."
                )


class QuestionVoteView(discord.ui.View):
    def __init__(self, bot, question_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.question_id = question_id

        # Load the initial vote counts
        question = database.Question.get(display_order=question_id)
        self.upvote_count = question.upvotes
        self.downvote_count = question.downvotes

        # Upvote Button
        self.upvote_button = discord.ui.Button(
            label=f"👍 {self.upvote_count}",
            style=discord.ButtonStyle.green,
            custom_id="question_upvote",
        )
        self.upvote_button.callback = self.handle_upvote
        self.add_item(self.upvote_button)

        # Downvote Button
        self.downvote_button = discord.ui.Button(
            label=f"👎 {self.downvote_count}",
            style=discord.ButtonStyle.red,
            custom_id="question_downvote",
        )
        self.downvote_button.callback = self.handle_downvote
        self.add_item(self.downvote_button)

        # Suggest a Question Button
        self.suggest_question_button = discord.ui.Button(
            label="Suggest a Question!",
            style=discord.ButtonStyle.blurple,
            emoji="📝",
            custom_id="persistent_view:qsm_sug_question",
        )
        self.suggest_question_button.callback = self.handle_suggest_question
        self.add_item(self.suggest_question_button)

    async def handle_upvote(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        try:
            question = database.Question.get(display_order=self.question_id)
            vote, created = database.QuestionVote.get_or_create(
                question=question, user_id=user_id, defaults={"vote_type": "up"}
            )

            if not created:
                if vote.vote_type == "up":
                    # Toggle: remove existing upvote
                    vote.delete_instance()
                    question.upvotes = max(0, question.upvotes - 1)
                    _log.info(
                        f"{interaction.user.display_name} removed upvote on question {self.question_id}."
                    )
                else:
                    # Switch from downvote to upvote
                    vote.vote_type = "up"
                    vote.save()
                    question.downvotes = max(0, question.downvotes - 1)
                    question.upvotes += 1
                    _log.info(
                        f"{interaction.user.display_name} switched to upvote on question {self.question_id}."
                    )
            else:
                # New upvote
                question.upvotes += 1
                _log.info(
                    f"{interaction.user.display_name} upvoted question {self.question_id}."
                )

            question.save()

            self.upvote_count = question.upvotes
            self.downvote_count = question.downvotes
            self.upvote_button.label = f"👍 {self.upvote_count}"
            self.downvote_button.label = f"👎 {self.downvote_count}"

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
                    # Toggle: remove existing downvote
                    vote.delete_instance()
                    question.downvotes = max(0, question.downvotes - 1)
                    _log.info(
                        f"{interaction.user.display_name} removed downvote on question {self.question_id}."
                    )
                else:
                    # Switch from upvote to downvote
                    vote.vote_type = "down"
                    vote.save()
                    question.upvotes = max(0, question.upvotes - 1)
                    question.downvotes += 1
                    _log.info(
                        f"{interaction.user.display_name} switched to downvote on question {self.question_id}."
                    )
            else:
                # New downvote
                question.downvotes += 1
                _log.info(
                    f"{interaction.user.display_name} downvoted question {self.question_id}."
                )

            question.save()

            self.upvote_count = question.upvotes
            self.downvote_count = question.downvotes
            self.upvote_button.label = f"👍 {self.upvote_count}"
            self.downvote_button.label = f"👎 {self.downvote_count}"

            await interaction.response.edit_message(view=self)

        except Exception as e:
            _log.error(f"Error handling downvote: {e}", exc_info=True)

    async def handle_suggest_question(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestModalNEW(self.bot))


# View for users to submit a new question
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


class DailyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_question.start()
        _log.info("DailyCMD cog initialized and post_question task started.")

    DQ = app_commands.Group(
        name="daily-question", description="Configure the daily-question settings."
    )

    @tasks.loop(hours=1)
    async def post_question(self):
        _log.info("🕒 post_question loop ticked.")

        try:
            now = datetime.now(pytz.timezone("America/Chicago"))
            hour = now.hour
            minute = now.minute

            if 10 <= hour <= 10 and 0 <= minute <= 10:
                _log.info("⏰ Attempting 10:00 AM post.")
                question_id = await self.send_daily_question()

                for guild in self.bot.guilds:
                    bot_data = get_cached_bot_data(guild.id)
                    if bot_data:
                        bot_data.last_question_posted = question_id
                        bot_data.last_question_posted_time = datetime.now(
                            pytz.timezone("America/Chicago")
                        )
                        bot_data.save()
                        _log.info(f"✅ Saved last_question_posted for {guild.name}.")

            elif 18 <= hour <= 18 and 0 <= minute <= 10:
                _log.info("⏰ Attempting 6:00 PM repost.")
                for guild in self.bot.guilds:
                    bot_data = get_cached_bot_data(guild.id)
                    if bot_data and bot_data.last_question_posted:
                        await self.send_daily_question(bot_data.last_question_posted)
                    else:
                        _log.warning(
                            f"⚠️ No question to repost for {guild.name} ({guild.id})."
                        )

        except Exception as e:
            _log.error(f"Error in post_question task: {e}", exc_info=True)

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        _log.info("✅ Bot is ready. Starting post_question loop.")

    async def send_daily_question(self, question_id: str = None):
        try:
            database.ensure_database_connection()

            if question_id is None:
                unused_questions = database.Question.select().where(
                    database.Question.usage == "False"
                )
                if not unused_questions.exists():
                    database.Question.update(usage="False").execute()
                    _log.info("🔁 Reset all questions to unused.")

                question = (
                    database.Question.select()
                    .where(database.Question.usage == "False")
                    .order_by(fn.Rand())
                    .limit(1)
                    .get()
                )
                question.usage = "True"
                question.save()
            else:
                question = database.Question.get(
                    database.Question.display_order == question_id
                )

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

            for guild in self.bot.guilds:
                bot_data = get_cached_bot_data(guild.id)
                if not bot_data or not bot_data.daily_question_enabled:
                    _log.warning(f"🚫 Skipping {guild.name}: no bot data or disabled.")
                    continue

                send_channel = self.bot.get_channel(
                    int(bot_data.daily_question_channel)
                )
                if not send_channel:
                    _log.error(
                        f"❌ Channel ID {bot_data.daily_question_channel} not found in {guild.name}."
                    )
                    continue

                view = QuestionVoteView(self.bot, question.display_order)
                await send_channel.send(embed=embed, view=view)
                _log.info(
                    f"📤 Posted Q#{question.display_order} to {send_channel.name} in {guild.name}."
                )

            return question.display_order

        except database.Question.DoesNotExist:
            _log.error("❗ Question not found.")
        except Exception as e:
            _log.error(f"Error sending daily question: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(DailyCMD(bot))
    _log.info("✅ DailyCMD cog loaded.")
