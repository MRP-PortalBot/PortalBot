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
        self.upvote_button = discord.ui.button(
            label=f"👍 {self.upvote_count}",
            style=discord.ButtonStyle.green,
            custom_id="question_upvote",
        )
        self.upvote_button.callback = self.handle_upvote
        self.add_item(self.upvote_button)

        # Downvote Button
        self.downvote_button = discord.ui.button(
            label=f"👎 {self.downvote_count}",
            style=discord.ButtonStyle.red,
            custom_id="question_downvote",
        )
        self.downvote_button.callback = self.handle_downvote
        self.add_item(self.downvote_button)

        # Suggest a Question Button
        self.add_item(SuggestQuestionFromDQ(bot).suggest_question)

    async def handle_upvote(self, interaction: discord.Interaction):
        try:
            question = database.Question.get(display_order=self.question_id)
            question.upvotes += 1
            question.save()

            self.upvote_count = question.upvotes
            self.upvote_button.label = f"👍 {self.upvote_count}"
            await interaction.response.edit_message(view=self)
            _log.info(
                f"Upvote added by {interaction.user.display_name} for question ID {self.question_id}."
            )
        except Exception as e:
            _log.error(f"Error handling upvote: {e}", exc_info=True)

    async def handle_downvote(self, interaction: discord.Interaction):
        try:
            question = database.Question.get(display_order=self.question_id)
            question.downvotes += 1
            question.save()

            self.downvote_count = question.downvotes
            self.downvote_button.label = f"👎 {self.downvote_count}"
            await interaction.response.edit_message(view=self)
            _log.info(
                f"Downvote added by {interaction.user.display_name} for question ID {self.question_id}."
            )
        except Exception as e:
            _log.error(f"Error handling downvote: {e}", exc_info=True)


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

    @tasks.loop(hours=24)
    async def post_question(self):
        while True:
            try:
                database.ensure_database_connection()
                # First post at 10:00 AM CST
                await self.wait_until_time(10, 0)
                await self.send_daily_question()

                # Second post at 6:00 PM CST
                await self.wait_until_time(18, 0)
                await self.send_daily_question()
            except Exception as e:
                _log.error(f"Error in post_question task: {e}", exc_info=True)

    async def wait_until_time(self, hour, minute):
        """Waits until the next occurrence of the given hour and minute in CST."""
        now = datetime.now(pytz.timezone("America/Chicago"))
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time < now:
            target_time += timedelta(days=1)
        seconds_until_target = (target_time - now).total_seconds()
        _log.debug(f"Waiting {seconds_until_target} seconds until {target_time}.")
        await asyncio.sleep(seconds_until_target)

    async def send_daily_question(self):
        """Send a daily question to the configured channel and store the question ID."""
        try:
            database.ensure_database_connection()
            bot_data = await get_cached_bot_data(self.guild.id)

            if not bot_data.daily_question_enabled:
                _log.info(
                    f"Daily questions are disabled for guild {bot_data.server_id}."
                )
                return

            # Get the channel to post the question
            send_channel = self.bot.get_channel(bot_data.daily_question_channel)

            if not send_channel:
                _log.error(
                    f"Daily question channel with ID {bot_data.daily_question_channel} not found."
                )
                return

            # Check if all questions have been used (i.e., usage is True)
            unused_questions_count = (
                database.Question.select()
                .where(database.Question.usage == False)
                .count()
            )
            if unused_questions_count == 0:
                database.Question.update(usage=False).execute()
                _log.info("All questions were used, resetting all to unused.")

            # Select a random unused question
            question: database.Question = (
                database.Question.select()
                .where(database.Question.usage == False)
                .order_by(fn.Rand())
                .limit(1)
                .get()
            )
            question.usage = True
            question.save()

            # Create and send the embed for the daily question
            embed = discord.Embed(
                title="❓ QUESTION OF THE DAY ❓",
                description=f"**{question.question}**",
                color=0xB10D9F,
            )
            embed.set_footer(text=f"Question ID: {question.display_order}")

            view = QuestionVoteView(self.bot, question.display_order)
            await send_channel.send(embed=embed, view=view)

            _log.info(
                f"Question ID {question.display_order} sent to channel {send_channel.name}."
            )

            # Update the last_question_posted to store the question's ID
            bot_data.last_question_posted = question.display_order
            bot_data.last_question_posted_time = datetime.now(
                pytz.timezone("America/Chicago")
            )
            bot_data.save()
        except database.Question.DoesNotExist:
            _log.error("Bot data or question not found in the database.")
        except Exception as e:
            _log.error(f"Error sending daily question: {e}", exc_info=True)

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        _log.debug("Bot is ready. Starting post_question loop.")

    @DQ.command()
    async def suggest(self, interaction: discord.Interaction):
        class SuggestModal(discord.ui.Modal, title="Suggest a Question"):
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
                    msg = await log_channel.send(
                        embed=embed, view=QuestionSuggestionManager()
                    )

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

        await interaction.response.send_modal(SuggestModal(self.bot))

    @DQ.command(
        name="post",
        description="Post a daily question by ID or repeat today's question.",
    )
    @checks.slash_is_bot_admin_2
    async def postq(self, interaction: discord.Interaction, id: int = None):
        """Post a daily question by ID or repeat today's question."""
        try:
            _log.info(f"{interaction.user} triggered the post command.")

            row_id = get_bot_data_id()
            _log.debug(f"Retrieved bot data row ID: {row_id}")

            # Fetch the bot data to get the last posted question's ID
            bot_data: database.BotData = (
                database.BotData.select().where(database.BotData.id == row_id).get()
            )

            # Determine which question ID to use
            if id is None:
                last_question_id = bot_data.last_question_posted
                if not last_question_id:
                    _log.warning("No last_question_posted found.")
                    await interaction.response.send_message("No recent question found.")
                    return
                question_id_to_post = last_question_id
            else:
                question_id_to_post = id

            # Fetch the question from the database using the determined ID
            question: database.Question = database.Question.get(
                database.Question.display_order == question_id_to_post
            )
            _log.info(
                f"Posting question ID: {question_id_to_post}, Question: {question.question}"
            )

            # Create and send the embed for the question
            embed = discord.Embed(
                title="❓ QUESTION OF THE DAY ❓",
                description=f"**{question.question}**",
                color=0xB10D9F,
            )
            embed.set_footer(text=f"Question ID: {question.display_order}")
            await interaction.response.send_message(
                embed=embed, view=SuggestQuestionFromDQ(self.bot)
            )
            _log.info(f"Sent the question to {interaction.user}.")

        except database.Question.DoesNotExist:
            _log.error(f"No question found for ID: {question_id_to_post}.")
            await interaction.response.send_message("Question not found.")
        except Exception as e:
            _log.error(f"Error in posting question: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while posting the question."
            )

    @DQ.command(description="Modify a question!")
    @checks.slash_is_bot_admin_2
    async def modify(self, interaction: discord.Interaction, id: int, question: str):
        try:
            q: database.Question = database.Question.get(
                database.Question.display_order == id
            )
            q.question = question
            q.save()
            _log.info(f"Question ID {id} modified by {interaction.user.display_name}.")
            await interaction.response.send_message(
                f"Question {id} '{q.question}' has been modified successfully."
            )
        except database.Question.DoesNotExist:
            _log.error(f"Attempted to modify non-existent question ID {id}.")
            await interaction.response.send_message(
                "ERROR: This question does not exist!"
            )
        except Exception as e:
            _log.error(f"Error modifying question: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while modifying the question."
            )

    @DQ.command(description="Add a question!")
    @checks.slash_is_bot_admin_2
    async def new(self, interaction: discord.Interaction, question: str):
        try:
            q = database.Question.create(question=question)
            q.save()
            _log.info(
                f"Question '{question}' added by {interaction.user.display_name}."
            )
            await interaction.response.send_message(
                f"Question '{question}' has been added successfully."
            )
        except database.IntegrityError:
            _log.error(f"Duplicate question detected: '{question}'")
            await interaction.response.send_message("That question is already taken!")
        except Exception as e:
            _log.error(f"Error adding new question: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while adding the question."
            )
        renumber_display_order()

    @DQ.command(description="Delete a question!")
    @checks.slash_is_bot_admin_2
    async def delete(self, interaction: discord.Interaction, id: int):
        try:
            q: database.Question = database.Question.get(
                database.Question.display_order == id
            )
            q.delete_instance()
            await interaction.response.send_message(
                f"Question {id} '{q.question}' has been deleted."
            )
            _log.info(f"Question ID {id} deleted by {interaction.user.display_name}.")
        except database.Question.DoesNotExist:
            _log.error(f"Attempted to delete non-existent question ID {id}.")
            await interaction.response.send_message("Question not found.")
        except Exception as e:
            _log.error(f"Error deleting question: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while deleting the question."
            )
        renumber_display_order()

    @DQ.command(description="List every question.")
    async def list(self, interaction: discord.Interaction, page: int = 1):
        """List all tags in the database"""
        renumber_display_order()

        def get_total_pages(page_size: int) -> int:
            total_questions = database.Question.select().count()
            return math.ceil(total_questions / page_size)

        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed in list command"""
            embed.clear_fields()
            questions = (
                database.Question.select()
                .order_by(database.Question.display_order)
                .paginate(page, 10)
            )
            if not questions.exists():
                embed.add_field(name="No Questions", value="No questions found.")
            else:
                q_list = "\n".join(
                    [f"{q.display_order}. {q.question}" for q in questions]
                )
                embed.add_field(name=f"Page {page}", value=q_list)

            return embed

        try:
            total_pages = get_total_pages(10)
            embed = discord.Embed(title="Question List")
            await paginate_embed(
                self.bot, interaction, embed, populate_embed, total_pages, page
            )
            _log.info(
                f"Sent question list to {interaction.user.display_name}, page {page}."
            )
        except Exception as e:
            _log.error(f"Error listing questions: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while listing questions."
            )

    @DQ.command(
        name="toggle-daily-question", description="Enable or disable daily questions."
    )
    @checks.slash_is_bot_admin_2
    async def toggle_daily_question(self, interaction: discord.Interaction):
        try:
            bot_data = await get_cached_bot_data(interaction.guild.id)

            # Toggle the state
            bot_data.daily_question_enabled = not bot_data.daily_question_enabled
            bot_data.save()

            state = "enabled" if bot_data.daily_question_enabled else "disabled"
            await interaction.response.send_message(
                f"Daily questions have been {state}.", ephemeral=True
            )
            _log.info(f"Daily questions {state} for guild {interaction.guild.id}.")
        except Exception as e:
            _log.error(f"Error toggling daily questions: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while toggling daily questions.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DailyCMD(bot))
