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
    def get_user_id(obj: Union[Context, Interaction]) -> int | None:
        if isinstance(obj, Context):
            return obj.author.id
        elif isinstance(obj, Interaction):
            return obj.user.id
        return None

    def check_permission(user_id: int) -> bool:
        try:
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
            _log.error(f"Database error during admin check: {e}")
            return False
        finally:
            if not database.db.is_closed():
                database.db.close()

    # The actual decorator to wrap the target function
    def decorator(func: Callable):
        # If it's a slash command, use app_commands.check
        if isinstance(func, app_commands.Command):
            return app_commands.check(lambda i: check_permission(get_user_id(i)))(func)

        # Otherwise, wrap and apply commands.check manually
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx_or_interaction = next(
                (arg for arg in args if isinstance(arg, (Context, Interaction))), None
            )

            if not ctx_or_interaction:
                _log.error("No Context or Interaction found in arguments.")
                return

            user_id = get_user_id(ctx_or_interaction)
            if user_id and check_permission(user_id):
                return await func(*args, **kwargs)

            _log.warning(f"Permission denied for {func.__name__} by user {user_id}")
            if isinstance(ctx_or_interaction, Context):
                await ctx_or_interaction.send(
                    "You do not have permission to use this command."
                )
            elif isinstance(ctx_or_interaction, Interaction):
                await ctx_or_interaction.response.send_message(
                    "You do not have permission to use this command.", ephemeral=True
                )

        # Apply check to the wrapped function
        return commands.check(lambda ctx: check_permission(get_user_id(ctx)))(wrapper)

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
