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


def owns_realm_channel():
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel.category_id != 587627871216861244:
            return False

        # Check for permit level 3 or above
        database.db.connect(reuse_if_open=True)
        query = database.Administrators.select().where(
            (database.Administrators.TierLevel >= 3) & (database.Administrators.discordID == interaction.user.id)
        )
        result = query.exists()
        database.db.close()

        if result:
            return True

        # Extract the channel from the interaction
        channel = interaction.channel

        # Extract the realm name from the channel name (removing '-emoji')
        realm_name = channel.name.rsplit('-', 1)[0]

        # Construct the role name
        role_name = f"{realm_name} OP"

        # Check if the user has the role
        member = interaction.guild.get_member(interaction.user.id)
        has_role = any(role.name == role_name for role in member.roles)

        if not has_role:
            return False

        return True

    return app_commands.check(predicate)

slash_owns_realm_channel = owns_realm_channel()