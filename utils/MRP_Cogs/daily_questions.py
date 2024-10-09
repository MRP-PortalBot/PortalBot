import math
from datetime import datetime, timedelta

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from peewee import fn
from core import common, database, checks
from core.common import load_config, get_bot_data_id, SuggestQuestionFromDQ
from core.pagination import paginate_embed
from core.common import load_config
from core.logging_module import get_log
from main import PortalBot

config, _ = load_config()
_log = get_log(__name__)


class DailyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    DQ = app_commands.Group(
        name="daily-question",
        description="Configure the daily-question settings.",
    )

    @tasks.loop(hours=24)
    async def post_question(self):
        row_id = get_bot_data_id()
        q: database.BotData = database.BotData.get_by_id(row_id)
        send_channel = self.bot.get_channel(q.daily_question_channel)
        last_time_posted = q.last_question_posted

        if datetime.now() - last_time_posted >= timedelta(hours=24):
            try:
                question: database.Question = (
                    database.Question.select()
                    .where(database.Question.usage == False)
                    .order_by(fn.Rand())
                    .get()
                )

                question.usage = True
                question.save()

                embed = discord.Embed(
                    title="❓ QUESTION OF THE DAY ❓",
                    description=f"**{question.question}**",
                    color=0xB10D9F,
                )
                embed.set_footer(text=f"Question ID: {question.id}")
                await send_channel.send(
                    embed=embed, view=SuggestQuestionFromDQ(self.bot)
                )

                q.last_question_posted = datetime.now()
                q.save()

            except database.DoesNotExist:
                _log.error("No questions available to post.")
                await send_channel.send("No new questions available for today.")
            except Exception as e:
                _log.error(f"Error in posting question: {e}")

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

    @DQ.command(name="repeat", description="Repeat a daily question by id number")
    @checks.slash_is_bot_admin_2
    async def repeatq(self, interaction: discord.Interaction, number: int):
        try:
            q: database.Question = database.Question.get_by_id(number)
            embed = discord.Embed(
                title="❓ QUESTION OF THE DAY ❓",
                description=f"**{q.question}**",
                color=0xB10D9F,
            )
            embed.set_footer(text=f"Question ID: {q.id}")
            await interaction.response.send_message(embed=embed)
        except database.DoesNotExist:
            await interaction.response.send_message("Question not found.")
        except Exception as e:
            _log.error(f"Error in repeating question: {e}")
            await interaction.response.send_message("An error occurred.")

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
