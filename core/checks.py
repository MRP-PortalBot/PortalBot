"""
SETUP:
If you require a specific command to be protected, you can use the @is_botAdmin check or create your own one here!
"""

import os
import re

import discord
from discord import app_commands
from discord.ext import commands

from core import database


def predicate_LV(level):
    def inner(ctx) -> bool:
        database.db.connect(reuse_if_open=True)
        query = database.Administrators.select().where(
            (database.Administrators.TierLevel >= level) & (database.Administrators.discordID == ctx.author.id)
        )
        result = query.exists()
        database.db.close()
        return result
    return inner

is_botAdmin = commands.check(predicate_LV(1))
is_botAdmin2 = commands.check(predicate_LV(2))
is_botAdmin3 = commands.check(predicate_LV(3))
is_botAdmin4 = commands.check(predicate_LV(4))


def slash_predicate_LV(level):
    def predicate(interaction: discord.Interaction) -> bool:
        database.db.connect(reuse_if_open=True)
        query = database.Administrators.select().where(
            (database.Administrators.TierLevel >= level) & (database.Administrators.discordID == interaction.user.id)
        )
        result = query.exists()
        database.db.close()
        return result
    return app_commands.check(predicate)

slash_is_bot_admin = slash_predicate_LV(1)
slash_is_bot_admin_2 = slash_predicate_LV(2)
slash_is_bot_admin_3 = slash_predicate_LV(3)
slash_is_bot_admin_4 = slash_predicate_LV(4)
