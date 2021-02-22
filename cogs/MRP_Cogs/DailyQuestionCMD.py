import discord
from discord.ext import commands
from datetime import datetime
import random
import threading
import asyncio
from core import database, common
from core.common import load_config
config, _ = load_config()
import math
from discord.ext import tasks
# Counts current lines in a file.

import logging

logger = logging.getLogger(__name__)
def LineCount():
    file = open("DailyQuestions.txt", "r")
    line_count = 0
    for line in file:
        if line != "\n":
            line_count += 1
    file.close()
    print(line_count)

async def getQuestion(ctx):
    limit = int(database.Question.select().count())
    print(str(limit) + "| getQuestion")
    Rnum = random.randint(1 , limit)
    print(str(Rnum))
    database.db.connect(reuse_if_open=True)
    q: database.Question = database.Question.select().where(database.Question.id == Rnum).get()
    print(q.id)
    if q.usage == False or q.usage == "False":
        q.usage = True
        q.save()
        embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓", description=f"**{q.question}**", color = 0xb10d9f)
        embed.set_footer(text = f"Question ID: {q.id}")
        await ctx.send(embed=embed)
        return True
    else:
        return False
       

async def mainTask(self):
    while True:
        d = datetime.utcnow()
        if d.hour == 17 or d.hour == "17":
            guild = self.bot.get_guild(config['ServerID'])
            channel = guild.get_channel(config['GeneralChannel'])
            limit = int(database.Question.select().count())
            print(limit)
            Rnum = random.randint(1 , limit)
            try:
                database.db.connect(reuse_if_open=True)
                try:
                    q: database.Question = database.Question.select().where(database.Question.id == Rnum).get()
                    embed = discord.Embed(title="❓ QUESTION OF THE DAY ❓", description=f"**{q.question}**", color = 0xb10d9f)
                    await channel.send(embed=embed)
        
                finally:
                    database.db.close()

            finally:
                database.db.close()
        await asyncio.sleep(3600)




class DailyCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("DailyQuestionsCMD: Cog Loaded!")

    def get_by_index(self, index):
        for i, t in enumerate(database.Question.select()):
            if i+1 == index:
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
                        q: database.Question = database.Question.create(question=question, usage = False)
                        q.save()
                    except database.IntegrityError:
                        await channel.send("ERROR: That question is already taken!")
                    finally:
                        database.db.close()

                    embed = discord.Embed(title="Suggestion Approved", description="<@" + str(
                        payload.user_id) + "> has approved a suggestion! ", color=0x31f505)
                    embed.add_field(name="Question Approved",
                                    value="Question: " + str(question))
                    await channel.send(embed=embed)
                    reactions = ['✅', '❌']
                    for emoji in reactions:
                        await msg.clear_reaction(emoji)

                elif str(payload.emoji) == "❌":
                    embed2 = discord.Embed(title="Suggestion Denied", description="<@" + str(
                        payload.user_id) + "> has denied a suggestion! ", color=0xf50505)
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

    # Lists all current questions in the textfile.

    @commands.command()
    async def listq(self, ctx):
        with open('DailyQuestions.txt', 'r') as file:
            author = ctx.message.author
            msg = file.read(984).strip()
            while len(msg) > 0:
                em = discord.Embed(title="Current Recorded Questions",
                                   description="Requested by: " + author.mention, color=0xb10d9f)
                em.add_field(name="Questions:", value=msg)
                await ctx.send(embed=em)
                msg = file.read(1024).strip()

    # Suggests a question and sends it to the moderators.
    @commands.command()
    async def suggestq(self, ctx, *, question):
        author = ctx.message.author
        channel = ctx.message.channel
        guild = ctx.message.guild
        DMChannel = await ctx.author.create_dm()
        if channel.name == "bot-spam":
            print(channel)

            def check(m):
                return m.content is not None and m.channel == channel and m.author is not self.bot.user

            await channel.send("Are you sure you want to submit this question for approval? \n**Warning:** You will be subjected to a warn/mute if your suggestion is deemed inappropriate!")
            message = await channel.send("**Steps to either submit or cancel:**\n\nReaction Key:\n✅ - SUBMIT\n❌ - CANCEL\n*You have 60 seconds to react, otherwise the application will automaically cancel.* ")
            reactions = ['✅', '❌']
            for emoji in reactions:
                await message.add_reaction(emoji)

            def check2(reaction, user):
                return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check2)
                if str(reaction.emoji) == "❌":
                    await message.delete()
                    await ctx.send("Okay, I didn't send your suggestion...")
                    return
                else:
                    await message.delete()
                    msga = await ctx.send("Standby, sending your suggestion. ")
                    channels = await self.bot.fetch_channel(config['questionSuggestChannel'])
                    embed = discord.Embed(title="Daily Question Suggestion", description=str(
                        author.name) + " suggested a question in <#" + str(channel.id) + ">", color=0xfcba03)
                    embed.add_field(name="Suggestion:", value=str(question))
                    # QuestionSuggestQ.txt
                    file = open("QuestionSuggestQ.txt", "r")
                    line_count = 0
                    for line in file:
                        if line != "\n":
                            line_count += 1
                    file.close()
                    lc = line_count + 1
                    embed.add_field(name="Approving/Denial Command",
                                    value="\n✅ - Approve \n❌ - Reject")
                    embed.add_field(name="Developer Payload",
                                    value=str(lc) + " | " + str(question))
                    timestamp = datetime.now()
                    embed.set_footer(text=guild.name + " | Date: " +
                                    str(timestamp.strftime(r"%x")))
                    msg = await channels.send(embed=embed)
                    with open("QuestionSuggestQ.txt", "a") as f:
                        f.write(str(lc) + " - " + question + "\n")
                    reactions = ['✅', '❌']
                    for emoji in reactions:
                        await msg.add_reaction(emoji)
                    await msga.edit(content="I have sent your question! \nPlease wait for an admin to approve it. ")
                    for emoji in reactions:
                        await message.clear_reaction(emoji)
            except asyncio.TimeoutError:
                await channel.send("Looks like you didn't react in time, please try again later!")
        else:
            await ctx.channel.purge(limit=1)
            embed = discord.Embed(
                title="Woah Slow Down!", description="This command is locked to <#588728994661138494>!\nI also sent your command in your DM's so all you have to do is just copy it and send it in the right channel!", color=0xb10d9f)
            msg = await ctx.send(embed=embed, delete_after=6)
            await DMChannel.send("Here is your command! \nPlease send it in #bot-spam!")
            await DMChannel.send(">suggestq " + str(question))


    

    @commands.command(aliases=['q', 'dailyq'])
    async def _q(self, ctx):
        """Activate a question"""
        limit = int(database.Question.select().count())
        q: database.Question = database.Question.select().where(database.Question.usage == True).count()
        print(f"{str(limit)}: limit\n{str(q)}: true count")
        if limit == q:
            query = database.Question.select().where(database.Question.usage == True)
            for question in query:
                question.usage = False
                question.save()
        await getQuestion(ctx)

    @commands.command(aliases=['mq'])
    @commands.has_any_role('Bot Manager', 'Moderator')
    async def modq(self, ctx, id, *, question):
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

    
    @commands.command(aliases=['nq', 'newquestion'])
    @commands.has_any_role('Bot Manager', 'Moderator')
    async def newq(self, ctx, *, question):
        """Add a question!"""
        try:
            database.db.connect(reuse_if_open=True)
            q: database.Question = database.Question.create(
                question=question)
            q.save()
            await ctx.send(f"{q.question} has been added successfully.")
        except database.IntegrityError:
            await ctx.send("That question is already taken!")
        finally:
            database.db.close()


    @commands.command(aliases=['delq', 'dq'])
    @commands.has_any_role("Bot Manager", "Moderator")
    async def deleteq(self, ctx, id):
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

    @commands.command(aliases=['lq'])
    async def listq(self, ctx, page=1):
        """List all tags in the database"""
        def get_end(page_size: int):
            database.db.connect(reuse_if_open=True)
            q: int = database.Question.select().count()
            return math.ceil(q/10)

        async def populate_embed(embed: discord.Embed, page: int):
            """Used to populate the embed in listtag command"""
            q_list = ""
            embed.clear_fields()
            database.db.connect(reuse_if_open=True)
            if database.Question.select().count() == 0:
                q_list = "No questions found"
            for i, q in enumerate(database.Question.select().paginate(page, 10)):
                q_list += f"{i+1+(10*(page-1))}. {q.question}\n"
            embed.add_field(name=f"Page {page}", value=q_list)
            database.db.close()
            return embed

        embed = discord.Embed(title="Tag List")
        embed = await common.paginate_embed(self.bot, ctx, embed, populate_embed, get_end(10), page=page)

    @commands.command()
    async def startTask(self, ctx):
        self.bot.loop.create_task(mainTask(self))
        await ctx.send("Done!")
        

def setup(bot):
    bot.add_cog(DailyCMD(bot))
