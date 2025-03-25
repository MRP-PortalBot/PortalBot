import os
import re
from typing import Callable, Union
from functools import wraps
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.ext.commands import Context
from peewee import OperationalError
import logging

from core import database

_log = logging.getLogger(__name__)

TEST_SERVER_ID = 587495640502763521
PORTAL_SERVER_ID = 448488274562908170
REALM_CATEGORY_ID = 587627871216861244


def has_admin_level(required_level: int):
    """
    Permission check decorator that supports both app_commands and regular commands.
    Can be applied to:
    - app_commands.command()
    - commands.command()
    - raw async def functions
    """

    def predicate(obj: Union[Context, Interaction]) -> bool:
        try:
            user_id = (
                obj.author.id
                if isinstance(obj, Context)
                else obj.user.id if isinstance(obj, Interaction) else None
            )

            if user_id is None:
                _log.error(f"has_admin_level: Unsupported object type {type(obj)}")
                return False

            database.db.connect(reuse_if_open=True)
            result = (
                database.Administrators.select()
                .where(
                    (database.Administrators.TierLevel >= required_level)
                    & (database.Administrators.discordID == user_id)
                )
                .exists()
            )

            _log.info(
                f"Admin check {'passed' if result else 'failed'} for user {user_id} (level {required_level})"
            )
            return result

        except OperationalError as e:
            _log.error(f"Database error in has_admin_level: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()

    def decorator(func: Callable):
        # Slash command style
        if isinstance(func, app_commands.Command):
            return app_commands.check(predicate)(func)

        # Prefix command style — return Command object
        if isinstance(func, commands.Command):
            return commands.check(predicate)(func)

        # Raw async function (fallback)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx_or_interaction = args[0]

            if predicate(ctx_or_interaction):
                return await func(*args, **kwargs)

            _log.warning(f"User failed permission check for: {func.__name__}")
            if isinstance(ctx_or_interaction, Context):
                await ctx_or_interaction.send(
                    "You do not have permission to use this command."
                )
            elif isinstance(ctx_or_interaction, Interaction):
                await ctx_or_interaction.response.send_message(
                    "You do not have permission to use this command.", ephemeral=True
                )

        return wrapper

    return decorator


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
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.guild.id in {TEST_SERVER_ID, 448488274562908170}

    return app_commands.check(predicate)


slash_check_MRP = check_MRP()
