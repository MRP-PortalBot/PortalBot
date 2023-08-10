import asyncio
import random
from datetime import datetime

import discord
from discord import app_commands, ui
from discord.ext import commands

from core import database, common
from core.common import load_config
from core.logging_module import get_log
from main import PortalBot

config, _ = load_config()
import math
# Counts current lines in a file.


_log = get_log(__name__)
_log.info("Starting PortalBot...")


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

    # Waits for either the approval or denial on a question suggestion
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id:
            if payload.channel_id == config['questionSuggestChannel']:
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                embed = msg.embeds[0]
                contentval = embed.fields[2].value
                linec, question = contentval.split(" | ")
                if str(payload.emoji) == "✅":
                    try:
                        database.db.connect(reuse_if_open=True)
                        q: database.Question = database.Question.create(
                            question=question, usage=False)
                        q.save()
                    except database.IntegrityError:
                        await channel.send(
                            "ERROR: That question is already taken!")
                    finally:
                        database.db.close()

                    embed = discord.Embed(title="Suggestion Approved",
                                          description="<@" +
                                          str(payload.user_id) +
                                          "> has approved a suggestion! ",
                                          color=0x31f505)
                    embed.add_field(name="Question Approved",
                                    value="Question: " + str(question))
                    await channel.send(embed=embed)
                    reactions = ['✅', '❌']
                    for emoji in reactions:
                        await msg.clear_reaction(emoji)

                elif str(payload.emoji) == "❌":
                    embed2 = discord.Embed(title="Suggestion Denied",
                                           description="<@" +
                                           str(payload.user_id) +
                                           "> has denied a suggestion! ",
                                           color=0xf50505)
                    embed.add_field(name="Question Denied",
                                    value="Question: " + str(question))
                    await channel.send(embed=embed2)
                    reactions = ['✅', '❌']
                    for emoji in reactions:
                        await msg.clear_reaction(emoji)
                else:
                    return
            else:
                return
        else:
            return

    # Suggests a question and sends it to the moderators.
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
                await interaction.response.defer()
                await interaction.followup.send("Thank you for your suggestion!")

    @DQ.command(
        name="repeat",
        description="Repeat a daily question by id number",
    )
    @discord.ext.commands.has_any_role("Moderator")
    async def repeatq(self, interaction: discord.Interaction, number):
        """Activate a question"""
        q: database.Question = database.Question.select().where(
            database.Question.id == number).get()
        embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓",
                              description=f"**{q.question}**",
                              color=0xb10d9f)
        embed.set_footer(text=f"Question ID: {q.id}")
        await ctx.respond(embed=embed)

    @DQ.command(name="use", description="Use a question")
    async def _activate(self, interaction: discord.Interaction):
        """Activate a question"""
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
        await get_question(self)

    @DQ.command(description="Modify a question!")
    @commands.has_any_role('Bot Manager', 'Moderator')
    async def _modify(self, interaction: discord.Interaction, id, *, question):
        """Modify a question!"""
        try:
            if id != None:
                database.db.connect(reuse_if_open=True)
                q: database.Question = database.Question.select().where(
                    database.Question.id == id).get()
                q.question = question
                q.save()
                await ctx.send(f"{q.question} has been modified successfully.")
        except database.DoesNotExist:
            await ctx.send("ERROR: This question does not exist!")
        finally:
            database.db.close()

    @DQ.command(description="Add a question!")
    @commands.has_any_role('Bot Manager', 'Moderator')
    async def _new(self, interaction: discord.Interaction, *, question):
        """Add a question!"""
        try:
            database.db.connect(reuse_if_open=True)
            q: database.Question = database.Question.create(question=question)
            q.save()
            await ctx.send(f"{q.question} has been added successfully.")
        except database.IntegrityError:
            await ctx.send("That question is already taken!")
        finally:
            database.db.close()

    @app_commands.command(description="Delete a question!")
    @commands.has_any_role("Bot Manager", "Moderator")
    async def _delete(self, interaction: discord.Interaction, id):
        """Delete a tag"""
        try:
            database.db.connect(reuse_if_open=True)
            q: database.Question = database.Question.select().where(
                database.Question.id == id).get()
            q.delete_instance()
            await ctx.send(f"{q.question} has been deleted.")
        except database.DoesNotExist:
            await ctx.send("Question not found, please try again.")
        finally:
            database.db.close()

    @DQ.command(description="List every question.")
    async def listq(self, interaction: discord.Interaction, page=1):
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
                q_list += f"{i+1+(10*(page-1))}. {q.question}\n"
            embed.add_field(name=f"Page {page}", value=q_list)
            database.db.close()
            return embed

        embed = discord.Embed(title="Tag List")
        embed = await common.paginate_embed(self.bot,
                                            ctx,
                                            embed,
                                            populate_embed,
                                            get_end(10),
                                            page=page)


def setup(bot):
    bot.add_cog(DailyCMD(bot))
