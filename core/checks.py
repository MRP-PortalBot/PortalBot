import os
import re
import discord
from discord import app_commands
from discord.ext import commands
from core import database
from peewee import (
    DoesNotExist,
    OperationalError,
)  # Add exception handling for peewee database errors

# Predicate for command checks based on the admin level
import logging
from discord import app_commands
from discord.ext import commands
from peewee import OperationalError
from core import database

_log = logging.getLogger(__name__)


def predicate_LV(level):
    """Unified predicate for both command and slash-command admin level checks."""

    def inner(ctx_or_interaction) -> bool:
        user_id = (
            ctx_or_interaction.author.id
            if isinstance(ctx_or_interaction, commands.Context)
            else ctx_or_interaction.user.id
        )
        try:
            database.db.connect(reuse_if_open=True)
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= level)
                & (database.Administrators.discordID == user_id)
            )
            if query.exists():
                _log.info(f"User {user_id} has sufficient admin level {level} access.")
                return True
            else:
                _log.warning(
                    f"User {user_id} does not have sufficient admin level {level} access."
                )
                return False
        except OperationalError as e:
            _log.error(f"Database connection error: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed.")

    return inner


# Create various admin-level check decorators for both command and slash commands
is_bot_Admin = commands.check(predicate_LV(1))
is_bot_Admin_2 = commands.check(predicate_LV(2))
is_bot_Admin_3 = commands.check(predicate_LV(3))
is_bot_Admin_4 = commands.check(predicate_LV(4))

slash_is_bot_admin = app_commands.check(predicate_LV(1))
slash_is_bot_admin_2 = app_commands.check(predicate_LV(2))
slash_is_bot_admin_3 = app_commands.check(predicate_LV(3))
slash_is_bot_admin_4 = app_commands.check(predicate_LV(4))


# Predicate for owning a realm channel
def owns_realm_channel(category_id=587627871216861244):
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel.category_id != category_id:
            return False

        try:
            database.db.connect(reuse_if_open=True)
            # Check if the user has a level 3 or above admin tier
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= 3)
                & (database.Administrators.discordID == interaction.user.id)
            )
            if query.exists():
                return True
        except OperationalError as e:
            # Log or handle database connection issues
            print(f"Database connection error: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()

        # Extract the realm name from the channel name (removing '-emoji')
        try:
            realm_name = interaction.channel.name.rsplit("-", 1)[0]
            role_name = f"{realm_name} OP"

            # Check if the user has the appropriate role
            member = interaction.guild.get_member(interaction.user.id)
            return any(role.name == role_name for role in member.roles)
        except AttributeError as e:
            # Handle cases where the user has no roles or channel name doesn't match expected format
            print(f"Error checking role ownership: {e}")
            return False

    return app_commands.check(predicate)


# Create the decorator for checking realm channel ownership
slash_owns_realm_channel = owns_realm_channel()
