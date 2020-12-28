import discord
from discord.ext import commands
from discord.ext.commands.core import command
from core import database, common
import asyncio
import logging

from discord.ext import commands

logger = logging.getLogger(__name__)


class Tags(commands.Cog):
    """Commands related to our dynamic tag system."""

    def __init__(self, bot):
        logger.info("Tags: Cog Loaded!")
        self.bot = bot

    @commands.command(aliases=['t'])
    async def tag(self, ctx, tag_name):
        """Activate a tag"""
        try:
            database.db.connect(reuse_if_open=True)
            try: # tried selecting with or and with (statement) | (statement), led to nothing, so this.
                tag_name = int(tag_name)
                tag: database.Tag = database.Tag.select().where(
                    database.Tag.id == tag_name).get()
            except ValueError:
                tag: database.Tag = database.Tag.select().where(
                    database.Tag.tag_name == tag_name).get()
            embed = discord.Embed(title=tag.embed_title, description=tag.text)
            await ctx.send(embed=embed)
        except database.DoesNotExist:
            await ctx.send("Tag not found, please try again.")
        finally:
            database.db.close()

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
            await ctx.send(f"Tag {tag.tag_name} has been modified successfully.")
        except database.DoesNotExist:
            try:
                database.db.connect(reuse_if_open=True)
                tag: database.Tag = database.Tag.create(
                    tag_name=name, embed_title=title, text=text)
                tag.save()
                await ctx.send(f"Tag {tag.tag_name} has been created successfully.")
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

    @commands.command(aliases=['ltag'])
    async def listtag(self, ctx, page=1):
        """List all tags in the database"""
        def get_beginning(self, page_size: int):
            database.db.connect(reuse_if_open=True)
            tags: int = database.Tag.select().count()
            return tags/page_size + tags % page_size

        async def populate_embed(self, embed: discord.Embed, page: int):
            """Used to populate the embed in listtag command"""
            tag_list = ""
            embed.clear_fields()
            database.db.connect(reuse_if_open=True)
            if database.Tag.select().count() == 0:
                tag_list = "No tags found"
            for tag in database.Tag.select().order_by(database.Tag.id).paginate(page, 10):
                tag_list += f"{tag.id}. {tag.tag_name}\n"
            embed.add_field(name=f"Page {page}", value=tag_list)
            database.db.close()
            return embed

        embed = discord.Embed(title="Tag List")
        embed = await common.paginate_embed(self.bot, ctx, embed, populate_embed, get_beginning(10), page=page)


def setup(bot):
    bot.add_cog(Tags(bot))
