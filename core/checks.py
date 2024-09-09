import os
import re

import discord
from discord import app_commands
from discord.ext import commands

from core import database

# Predicate for command checks based on the admin level
def predicate_LV(level):
    def inner(ctx) -> bool:
        try:
            database.db.connect(reuse_if_open=True)
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= level) & (database.Administrators.discordID == ctx.author.id)
            )
            return query.exists()
        finally:
            database.db.close()
    return inner

# Create various admin-level check decorators
is_botAdmin = commands.check(predicate_LV(1))
is_botAdmin2 = commands.check(predicate_LV(2))
is_botAdmin3 = commands.check(predicate_LV(3))
is_botAdmin4 = commands.check(predicate_LV(4))

# Predicate for slash command checks based on the admin level
def slash_predicate_LV(level):
    def predicate(interaction: discord.Interaction) -> bool:
        try:
            database.db.connect(reuse_if_open=True)
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= level) & (database.Administrators.discordID == interaction.user.id)
            )
            return query.exists()
        finally:
            database.db.close()
    return app_commands.check(predicate)

# Create various slash command admin-level check decorators
slash_is_bot_admin = slash_predicate_LV(1)
slash_is_bot_admin_2 = slash_predicate_LV(2)
slash_is_bot_admin_3 = slash_predicate_LV(3)
slash_is_bot_admin_4 = slash_predicate_LV(4)

# Predicate for owning a realm channel
def owns_realm_channel(category_id=587627871216861244):
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel.category_id != category_id:
            return False
        
        try:
            database.db.connect(reuse_if_open=True)
            # Check if the user has a level 3 or above admin tier
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= 3) & (database.Administrators.discordID == interaction.user.id)
            )
            if query.exists():
                return True
        finally:
            database.db.close()

        # Extract the realm name from the channel name (removing '-emoji')
        realm_name = interaction.channel.name.rsplit('-', 1)[0]
        role_name = f"{realm_name} OP"

        # Check if the user has the appropriate role
        member = interaction.guild.get_member(interaction.user.id)
        return any(role.name == role_name for role in member.roles)

    return app_commands.check(predicate)

# Create the decorator for checking realm channel ownership
slash_owns_realm_channel = owns_realm_channel()

