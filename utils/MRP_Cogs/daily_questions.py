import math
from datetime import datetime, timedelta
import asyncio
import pytz

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from peewee import fn
from core import common, database, checks
from core.common import load_config, get_bot_data_id, SuggestQuestionFromDQ
from core.pagination import paginate_embed
from core.logging_module import get_log
from main import PortalBot


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


class DailyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_question.start()

    DQ = app_commands.Group(
        name="daily-question",
        description="Configure the daily-question settings.",
    )

    @tasks.loop(hours=24)  # This loop will be rescheduled manually
    async def post_question(self):
        while True:
            try:
                # Ensure database connection is open
                database.ensure_database_connection()

                # First post at 10:00 AM CST
                await self.wait_until_time(10, 0)  # Wait until 10:00 AM
                await self.send_daily_question()

                # Second post at 6:00 PM CST
                await self.wait_until_time(18, 0)  # Wait until 6:00 PM
                await self.send_daily_question()
            except Exception as e:
                _log.error(f"Error in post_question task: {e}")

    async def wait_until_time(self, hour, minute):
        """Waits until the next occurrence of the given hour and minute in CST."""
        now = datetime.now(pytz.timezone("America/Chicago"))
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target_time < now:
            target_time += timedelta(
                days=1
            )  # If the time has already passed today, schedule for tomorrow

        seconds_until_target = (target_time - now).total_seconds()
        await asyncio.sleep(seconds_until_target)

    async def send_daily_question(self):
        # Ensure database connection is open
        database.ensure_database_connection()

        """Send a daily question to the configured channel and store the question ID."""
        row_id = get_bot_data_id()
        q: database.BotData = (
            database.BotData.select().where(database.BotData.id == row_id).get()
        )
        send_channel = self.bot.get_channel(q.daily_question_channel)

        # Check if all questions have been used (i.e., usage is True)
        unused_questions_count = (
            database.Question.select().where(database.Question.usage == False).count()
        )

        if unused_questions_count == 0:
            # Reset all questions to unused (usage = False) if all have been used
            database.Question.update(usage=False).execute()
            _log.info("All questions were used, resetting all to unused.")

        # Now, select a random unused question
        question: database.Question = (
            database.Question.select()
            .where(database.Question.usage == False)
            .order_by(fn.Rand())
            .limit(1)
            .get()
        )

        # Mark the selected question as used
        question.usage = True
        question.save()

        # Create and send the embed for the daily question
        embed = discord.Embed(
            title="❓ QUESTION OF THE DAY ❓",
            description=f"**{question.question}**",
            color=0xB10D9F,
        )
        embed.set_footer(text=f"Question ID: {question.id}")
        await send_channel.send(embed=embed, view=SuggestQuestionFromDQ(self.bot))

        # Update the last_question_posted to store the question's ID
        # Update the last_question_posted_time to store the current time
        q.last_question_posted = question.id
        q.last_question_posted_time = datetime.now(pytz.timezone("America/Chicago"))
        q.save()

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()  # Ensure the bot is ready before starting the task

    @DQ.command()
    async def suggest(self, interaction: discord.Interaction):
        class SuggestModal(discord.ui.Modal, title="Suggest a Question"):
            def __init__(self, bot: PortalBot):
                super().__init__(timeout=None)
                self.bot = bot

            short_description = ui.TextInput(
                label="Daily Question", style=discord.TextStyle.long, required=True
            )

            async def on_submit(self, interaction: discord.Interaction):
                row_id = get_bot_data_id()
                q: database.BotData = database.BotData.get_by_id(row_id)
                await interaction.response.defer(thinking=True)
                embed = discord.Embed(
                    title="Question Suggestion",
                    description=f"Requested by {interaction.user.mention}",
                    color=0x18C927,
                )
                embed.add_field(
                    name="Question:", value=f"{self.short_description.value}"
                )
                log_channel = await self.bot.fetch_channel(777987716008509490)
                msg = await log_channel.send(
                    embed=embed, view=SuggestQuestionFromDQ(self.bot)
                )
                database.QuestionSuggestionQueue.create(
                    question=self.short_description.value,
                    discord_id=interaction.user.id,
                    message_id=msg.id,
                )

                await interaction.followup.send("Thank you for your suggestion!")

        await interaction.response.send_modal(SuggestModal(self.bot))

    @DQ.command(name="repeat", description="Repeat the most recent daily question.")
    @checks.slash_is_bot_admin_2
    async def repeatq(self, interaction: discord.Interaction):
        """Repeat the most recent daily question based on the last_question_posted."""
        try:
            _log.info(f"{interaction.user} triggered the repeat command.")

            row_id = get_bot_data_id()
            _log.debug(f"Retrieved bot data row ID: {row_id}")

            # Fetch the bot data to get the last posted question's ID
            bot_data: database.BotData = (
                database.BotData.select().where(database.BotData.id == row_id).get()
            )
            last_question_id = bot_data.last_question_posted
            _log.debug(f"Retrieved last_question_posted: {last_question_id}")

            if not last_question_id:
                _log.warning("No last_question_posted found.")
                await interaction.response.send_message("No recent question found.")
                return

            # Fetch the question from the database using the stored ID
            question: database.Question = database.Question.get_by_id(last_question_id)
            _log.info(
                f"Repeating question ID: {last_question_id}, Question: {question.question}"
            )

            # Create and send the embed for the repeated question
            embed = discord.Embed(
                title="❓ QUESTION OF THE DAY ❓",
                description=f"**{question.question}**",
                color=0xB10D9F,
            )
            embed.set_footer(text=f"Question ID: {question.id}")
            await interaction.response.send_message(embed=embed)
            _log.info(f"Sent the repeated question to {interaction.user}.")

        except database.DoesNotExist:
            _log.error(
                f"No question found for last_question_posted ID: {last_question_id}."
            )
            await interaction.response.send_message("Question not found.")
        except Exception as e:
            _log.error(f"Error in repeating question: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred while repeating the question."
            )

    @DQ.command(description="Modify a question!")
    @checks.slash_is_bot_admin_2
    async def modify(self, interaction: discord.Interaction, id: int, question: str):
        try:
            q: database.Question = database.Question.get_by_id(id)
            q.question = question
            q.save()
            await interaction.response.send_message(
                f"Question {id} has been modified successfully."
            )
        except database.DoesNotExist:
            await interaction.response.send_message(
                "ERROR: This question does not exist!"
            )
        except Exception as e:
            _log.error(f"Error modifying question: {e}")
            await interaction.response.send_message(
                "An error occurred while modifying the question."
            )

    @DQ.command(description="Add a question!")
    @checks.slash_is_bot_admin_2
    async def new(self, interaction: discord.Interaction, question: str):
        try:
            q = database.Question.create(question=question)
            q.save()
            await interaction.response.send_message(
                f"Question '{question}' has been added successfully."
            )
        except database.IntegrityError:
            await interaction.response.send_message("That question is already taken!")
        except Exception as e:
            _log.error(f"Error adding new question: {e}")
            await interaction.response.send_message(
                "An error occurred while adding the question."
            )

    @DQ.command(description="Delete a question!")
    @checks.slash_is_bot_admin_2
    async def delete(self, interaction: discord.Interaction, id: int):
        try:
            q: database.Question = database.Question.get_by_id(id)
            q.delete_instance()
            await interaction.response.send_message(
                f"Question {q.question} has been deleted."
            )
        except database.DoesNotExist:
            await interaction.response.send_message("Question not found.")
        except Exception as e:
            _log.error(f"Error deleting question: {e}")
            await interaction.response.send_message(
                "An error occurred while deleting the question."
            )

    @DQ.command(description="List every question.")
    async def list(self, interaction: discord.Interaction, page: int = 1):
        """List all tags in the database"""

        def get_total_pages(page_size: int) -> int:
            total_questions = database.Question.select().count()
            return math.ceil(total_questions / page_size)

        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed in listtag command"""
            embed.clear_fields()
            questions = database.Question.select().paginate(page, 10)
            if not questions.exists():
                embed.add_field(name="No Questions", value="No questions found.")
            else:
                q_list = "\n".join([f"{q.id}. {q.question}" for q in questions])
                embed.add_field(name=f"Page {page}", value=q_list)

            return embed

        total_pages = get_total_pages(10)
        embed = discord.Embed(title="Question List")
        await paginate_embed(
            self.bot, interaction, embed, populate_embed, total_pages, page
        )


async def setup(bot):
    await bot.add_cog(DailyCMD(bot))
