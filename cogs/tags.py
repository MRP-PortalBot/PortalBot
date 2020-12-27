import discord
from discord.ext import commands
from discord.ext.commands.core import command
from core import database
import asyncio
import logging

from discord.ext import commands

logger = logging.getLogger(__name__)

# TODO: Convert messages to embeds
class Tags(commands.Cog):
    """Commands related to our dynamic tag system."""

    def __init__(self, bot):
        logger.info("Tags: Cog Loaded!")
        self.bot = bot

    # TODO: Catch for when no tags.
    def populate_embed(self, embed: discord.Embed, page: int):
        """Used to populate the embed in listtag command"""
        tag_list = ""
        embed.clear_fields()
        for tag in database.Tag.select().order_by(database.Tag.id).paginate(page, 10):
            tag_list += f"- {tag.tag_name}\n"
        embed.add_field(name=f"Page {page}", value=tag_list)
        return embed, page

    @commands.command(aliases=['t'])
    async def tag(self, ctx, tag_id):
        """Activate a tag"""
        try:
            database.db.connect(reuse_if_open=True)
            tag: database.Tag = database.Tag.select().where(
                database.Tag.tag_name == tag_id).get()
            await ctx.send(tag.text)
        except database.DoesNotExist:
            await ctx.send("Tag not found, please try again.")
        finally:
            database.db.close()

    # TODO: Add user feedback
    @commands.command(aliases=['newtag', 'ntag', 'mtag'])
    @commands.has_any_role('Bot Manager', 'Moderator')
    async def modtag(self, ctx, name, title, *, text):
        """Modify a tag, or create a new one if it doesn't exist."""
        try:
            database.db.connect(reuse_if_open=True)
            tag: database.Tag = database.Tag.select().where(
                database.Tag.tag_name == name).get()
            tag.text = text
            tag.embed_title = title
            tag.save()
        except database.DoesNotExist:
            try:
                database.db.connect(reuse_if_open=True)
                tag: database.Tag = database.Tag.create(
                    tag_name=name, embed_title=title, text=text)
                tag.save()
            except database.IntegrityError:
                await ctx.send("That tag name is already taken!")
        finally:
            database.db.close()

    @commands.command(aliases=['deltag', 'dtag'])
    @commands.has_any_role("Bot Manager", "Moderator")
    async def deletetag(self, ctx, name):
        """Delete a tag"""
        try:
            database.db.connect(reuse_if_open=True)
            tag: database.Tag = database.Tag.select().where(
                database.Tag.tag_name == name).get()
            tag.delete_instance()
            await ctx.send(f"{tag.tag_name} has been deleted.")
        except database.DoesNotExist:
            await ctx.send("Tag not found, please try again.")
        finally:
            database.db.close()

    # TODO: Catch for beginning of list, and end of list
    # TODO: Create a wrapper for easy pagination of embeds
    @commands.command(aliases=['ltag'])
    async def listtag(self, ctx, page=1):
        """List all tags in the database"""
        async def check_reaction(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]
        embed = discord.Embed(title="Tag List")
        embed, page = self.populate_embed(embed, page)
        message = await ctx.send(embed=embed)
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check_reaction)
                if user == self.bot.user:
                    continue
                if str(reaction.emoji) == "▶️":
                    embed, page = await self.populate_embed(embed, page)
                    await message.remove_reaction(reaction, user)
                    await message.edit(embed=embed)
                elif str(reaction.emoji) == "◀️" and page > 2:
                    await message.remove_reaction(reaction, user)
                    embed, page = await self.populate_embed(embed, page-2)
                    await message.edit(embed=embed)
            except asyncio.TimeoutError:  # ends loop after timeout.
                await message.clear_reactions()
                break


def setup(bot):
    bot.add_cog(Tags(bot))
