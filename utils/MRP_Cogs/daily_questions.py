import asyncio
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands, ui
from discord.ext import commands, tasks
from peewee import fn

from core import database, common
from core.checks import slash_is_bot_admin_2
from core.common import load_config, QuestionSuggestionManager, get_bot_data_id
from core.logging_module import get_log
from main import PortalBot

config, _ = load_config()
import math

# Counts current lines in a file.


_log = get_log(__name__)


def LineCount():
    file = open("DailyQuestions.txt", "r")
    line_count = 0
    for line in file:
        if line != "\n":
            line_count += 1
    file.close()
    print(line_count)


async def get_question(self):
    send_channel = self.bot.get_channel(config['dqchannel'])
    limit = int(database.Question.select().count())
    print(str(limit) + "| getQuestion")
    database.db.connect(reuse_if_open=True)
    posted = 0
    while (posted < 1):
        Rnum = random.randint(1, limit)
        print(str(Rnum))
        q: database.Question = database.Question.select().where(
            database.Question.id == Rnum).get()
        print(q.id)
        if q.usage is False or q.usage == "False":
            q.usage = True
            q.save()
            posted = 2
            print(posted)
            embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓",
                                  description=f"**{q.question}**",
                                  color=0xb10d9f)
            embed.set_footer(text=f"Question ID: {q.id}")
            await send_channel.send(embed=embed)
        else:
            posted = 0
            print(posted)


class DailyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    DQ = app_commands.Group(
        name="daily-question",
        description="Configure the daily-question settings.",
    )

    def get_by_index(self, index):
        for i, t in enumerate(database.Question.select()):
            if i + 1 == index:
                return t

    @tasks.loop(hours=24)
    async def post_question(self):
        row_id = get_bot_data_id()
        q: database.BotData = database.BotData.select().where(database.BotData.id == row_id).get()
        send_channel = self.bot.get_channel(q.daily_question_channel)
        last_time_posted = q.last_question_posted

        # Check if it's been 24 hours since the last question was posted
        if datetime.now() - last_time_posted >= timedelta(hours=24):
            question: database.Question = database.Question.select().where(
                database.Question.usage == False
            ).order_by(fn.Random()).limit(1).get()
            question.usage = True
            question.save()
            embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓",
                                  description=f"**{question.question}**",
                                  color=0xb10d9f)
            embed.set_footer(text=f"Question ID: {question.id}")
            await send_channel.send(embed=embed)

            # Update the last_question_posted time
            q.last_question_posted = datetime.now()
            q.save()

    @DQ.command()
    async def suggest(self, interaction: discord.Interaction):
        class SuggestModal(discord.ui.Modal, title="Suggest a Question"):
            def __init__(self, bot: PortalBot):
                super().__init__(timeout=None)
                self.bot = bot

            short_description = ui.TextInput(
                label="Daily Question",
                style=discord.TextStyle.long,
                required=True
            )

            async def on_submit(self, interaction: discord.Interaction):
                row_id = get_bot_data_id()
                q: database.BotData = database.BotData.select().where(database.BotData.id == row_id).get()
                await interaction.response.defer(thinking=True)
                embed = discord.Embed(title="Question Suggestion",
                                      description=f"Requested by {interaction.user.mention}", color=0x18c927)
                embed.add_field(name="Question:", value=f"{self.short_description.value}")
                log_channel = await self.bot.fetch_channel(777987716008509490)
                msg = await log_channel.send(embed=embed, view=QuestionSuggestionManager())
                q: database.QuestionSuggestionQueue = database.QuestionSuggestionQueue.create(
                    question=self.short_description.value,
                    discord_id=interaction.user.id,
                    message_id=msg.id,
                )
                q.save()

                await interaction.followup.send("Thank you for your suggestion!")
        await interaction.response.send_modal(SuggestModal(self.bot))

    @DQ.command(
        name="repeat",
        description="Repeat a daily question by id number",
    )
    @slash_is_bot_admin_2()
    async def repeatq(self, interaction: discord.Interaction, number: int):
        """Activate a question"""
        q: database.Question = database.Question.select().where(
            database.Question.id == number).get()
        embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓",
                              description=f"**{q.question}**",
                              color=0xb10d9f)
        embed.set_footer(text=f"Question ID: {q.id}")
        await interaction.response.send_message(embed=embed)

    """@DQ.command(name="use", description="Use a question")
    async def _activate(self, interaction: discord.Interaction):
        limit = int(database.Question.select().count())
        q: database.Question = database.Question.select().where(
            database.Question.usage == True).count()
        print(f"{str(limit)}: limit\n{str(q)}: true count")
        if limit == q:
            query = database.Question.select().where(
                database.Question.usage == True)
            for question in query:
                question.usage = False
                question.save()
        await get_question(self)"""

    @DQ.command(description="Modify a question!")
    @slash_is_bot_admin_2()
    async def modify(self, interaction: discord.Interaction, id: int, question: str):
        """Modify a question!"""
        try:
            if id != None:
                database.db.connect(reuse_if_open=True)
                q: database.Question = database.Question.select().where(
                    database.Question.id == id).get()
                q.question = question
                q.save()
                await interaction.response.send_message(f"{q.question} has been modified successfully.")
        except database.DoesNotExist:
            await interaction.response.send_message("ERROR: This question does not exist!")
        finally:
            database.db.close()

    @DQ.command(description="Add a question!")
    @slash_is_bot_admin_2()
    async def new(self, interaction: discord.Interaction, question: str):
        """Add a question!"""
        try:
            database.db.connect(reuse_if_open=True)
            q: database.Question = database.Question.create(question=question)
            q.save()
            await interaction.response.send_message(f"{q.question} has been added successfully.")
        except database.IntegrityError:
            await interaction.response.send_message("That question is already taken!")
        finally:
            database.db.close()

    @DQ.command(description="Delete a question!")
    @slash_is_bot_admin_2()
    async def delete(self, interaction: discord.Interaction, id: int):
        """Delete a tag"""
        try:
            database.db.connect(reuse_if_open=True)
            q: database.Question = database.Question.select().where(
                database.Question.id == id).get()
            q.delete_instance()
            await interaction.response.send_message(f"{q.question} has been deleted.")
        except database.DoesNotExist:
            await interaction.response.send_message("Question not found, please try again.")
        finally:
            database.db.close()

    @DQ.command(description="List every question.")
    async def list(self, interaction: discord.Interaction, page: int=1):
        """List all tags in the database"""

        def get_end(page_size: int):
            database.db.connect(reuse_if_open=True)
            q: int = database.Question.select().count()
            return math.ceil(q / 10)

        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed in listtag command"""
            q_list = ""
            embed.clear_fields()
            database.db.connect(reuse_if_open=True)
            if database.Question.select().count() == 0:
                q_list = "No questions found"
            for i, q in enumerate(database.Question.select().paginate(
                    page, 10)):
                q_list += f"{i + 1 + (10 * (page - 1))}. {q.question}\n"
            embed.add_field(name=f"Page {page}", value=q_list)
            database.db.close()
            return embed

        embed = discord.Embed(title="Tag List")
        embed = await common.paginate_embed(self.bot,
                                            interaction,
                                            embed,
                                            populate_embed,
                                            get_end(10),
                                            page=page)


async def setup(bot):
    await bot.add_cog(DailyCMD(bot))
