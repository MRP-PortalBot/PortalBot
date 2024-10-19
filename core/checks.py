import os
import re
import discord
import logging
from discord import app_commands
from discord.ext import commands
from core import database
from peewee import (
    DoesNotExist,
    OperationalError,
)

# Setup logger
_log = logging.getLogger(__name__)


# Predicate for command checks based on the admin level
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
            _log.debug(
                f"Checking admin level for user {user_id} with required level {level}"
            )
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
            _log.error(f"Database connection error while checking admin level: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed.")

    return inner


# Create various admin-level check decorators for both command and slash commands
is_bot_Admin_1 = commands.check(predicate_LV(1))
is_bot_Admin_2 = commands.check(predicate_LV(2))
is_bot_Admin_3 = commands.check(predicate_LV(3))
is_bot_Admin_4 = commands.check(predicate_LV(4))

slash_is_bot_admin_1 = app_commands.check(predicate_LV(1))
slash_is_bot_admin_2 = app_commands.check(predicate_LV(2))
slash_is_bot_admin_3 = app_commands.check(predicate_LV(3))
slash_is_bot_admin_4 = app_commands.check(predicate_LV(4))


# Predicate for owning a realm channel
def owns_realm_channel(category_id=587627871216861244):
    def predicate(interaction: discord.Interaction) -> bool:
        _log.debug(f"Checking if user {interaction.user.id} owns realm channel.")
        if interaction.channel.category_id != category_id:
            _log.info(f"User {interaction.user.id} is not in the correct category.")
            return False

        try:
            database.db.connect(reuse_if_open=True)
            _log.debug(f"Checking admin privileges for user {interaction.user.id}")
            # Check if the user has a level 3 or above admin tier
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= 1)
                & (database.Administrators.discordID == interaction.user.id)
            )
            if query.exists():
                _log.info(f"User {interaction.user.id} has admin privileges.")
                return True
        except OperationalError as e:
            _log.error(f"Database connection error: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed.")

        # Extract the realm name from the channel name (removing '-emoji')
        try:
            realm_name = interaction.channel.name.rsplit("-", 1)[0]
            role_name = f"{realm_name} OP"

            # Check if the user has the appropriate role
            member = interaction.guild.get_member(interaction.user.id)
            if any(role.name == role_name for role in member.roles):
                _log.info(f"User {interaction.user.id} owns the realm {realm_name}.")
                return True
            else:
                _log.info(
                    f"User {interaction.user.id} does not own the realm {realm_name}."
                )
                return False
        except AttributeError as e:
            _log.error(
                f"Error checking role ownership for user {interaction.user.id}: {e}"
            )
            return False

    return app_commands.check(predicate)


# Create the decorator for checking realm channel ownership
slash_owns_realm_channel = owns_realm_channel()


# Predicate for owning a realm channel or having the Realm OP role
def is_realm_op():
    def predicate(interaction: discord.Interaction) -> bool:
        _log.debug(f"Checking if user {interaction.user.id} is a Realm OP.")

        try:
            # Attempt to connect to the database and check for admin privileges
            database.db.connect(reuse_if_open=True)
            _log.debug(f"Checking admin level for user {interaction.user.id}")
            query = database.Administrators.select().where(
                (database.Administrators.TierLevel >= 1)
                & (database.Administrators.discordID == interaction.user.id)
            )
            if query.exists():
                _log.info(f"User {interaction.user.id} has admin privileges.")
                return True
        except OperationalError as e:
            _log.error(f"Database connection error: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed.")

        # Check if the user has the "Realm OP" role or a role matching the realm name
        try:
            member = interaction.guild.get_member(interaction.user.id)
            if any(role.name == "Realm OP" for role in member.roles):
                _log.info(f"User {interaction.user.id} has the 'Realm OP' role.")
                return True
            else:
                _log.info(
                    f"User {interaction.user.id} does not have the 'Realm OP' role."
                )
                return False

        except AttributeError as e:
            _log.error(f"Error checking roles for user {interaction.user.id}: {e}")
            return False

    return app_commands.check(predicate)


# Create the decorator for checking realm channel ownership or admin level
slash_is_realm_op = is_realm_op()


def check_MRP():
    async def predicate(interaction: discord.Interaction) -> bool:
        return (
            interaction.guild.id == 587495640502763521
            or interaction.guild.id == 448488274562908170
        )

    return app_commands.check(predicate)


slash_check_MRP = check_MRP()
