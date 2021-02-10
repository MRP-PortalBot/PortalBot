# Things that are in beta release, after beta period cog will move to its respected file.
import discord
from discord.ext import commands
import time
import logging

logger = logging.getLogger(__name__)
# Used for solving text or capitalizing letters.


def solve(s):
    a = s.split(' ')
    for i in range(len(a)):
        a[i] = a[i].capitalize()
    return ' '.join(a)


class BetaCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Beta: Cog Loaded!")

    @commands.command()
    async def testinginfo(self, ctx):
        a = "Turtle"
        guild = ctx.message.guild
        channel = ctx.message.channel
        emoji = "🐢"
        x = 1
        if x == 1:
            def check(m):
                return m.channel == channel and m.author != self.bot.user
            await channel.send("Getting Embed Configuration...")
            time.sleep(1)
            await channel.send("**EXAMPLE:** \n" + a + "`Realm` *<- Question 1's Response* \n`Enhanced Vanilla, Survival, Cheats are on` *<- Question 2's Response*")
            await channel.send("Everything that is in `Code Blocks` will change based on what you respond!")

            await channel.send("1: `Is this a Realm, Server, or Other`")
            typer1 = await self.bot.wait_for('message', check=check)

            await channel.send("2: What would you like appended to the end of your Realm Name?")
            typer2 = await self.bot.wait_for('message', check=check)

            message = await channel.fetch_message(786391628461375499)

            typesrealm = typer1.content

            # This is the user input
            user_input = {'field name': "***" + a + " " + typesrealm + "***",
                          'field value': typer2.content + "\nChannel - <#" + str(channel.id) + ">" + "\nEmoji - " + emoji}

            # Getting the embed and converting it to a dict
            embed = message.embeds[0]
            embed_dict = embed.to_dict()

            for field in embed_dict['fields']:
                if field['name'] == user_input['field name']:
                    field['value'] = user_input['field value']

            # Converting the embed to a `discord.Embed` obj
            edited_embed = discord.Embed.from_dict(embed_dict)

            # Editing the message
            await message.edit(embed=edited_embed)


def setup(bot):
    bot.add_cog(BetaCMD(bot))
