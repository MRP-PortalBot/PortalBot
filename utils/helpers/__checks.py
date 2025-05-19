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

from utils.database import __database

_log = logging.getLogger(__name__)

# Constants for server/category IDs
TEST_SERVER_ID = 587495640502763521
PORTAL_SERVER_ID = 448488274562908170
REALM_CATEGORY_ID = 587627871216861244


def has_admin_level(required_level: int):
    """
    Decorator to check if a user has the required admin level.
    Works with both message and slash command contexts.
    """

    def get_user_id(obj: Union[Context, Interaction]) -> int | None:
        if isinstance(obj, Context):
            return obj.author.id
        elif isinstance(obj, Interaction):
            return obj.user.id
        return None

    def check_permission(user_id: int) -> bool:
        """Check if the given user ID has the required admin tier."""
        try:
            __database.db.connect(reuse_if_open=True)
            result = (
                __database.Administrators.select()
                .where(
                    (__database.Administrators.TierLevel >= required_level)
                    & (
                        __database.Administrators.discordID == str(user_id)
                    )  # IDs now stored as strings
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
            if not __database.db.is_closed():
                __database.db.close()

    def decorator(func: Callable):
        """Actual decorator logic"""
        if isinstance(func, app_commands.Command):
            return app_commands.check(lambda i: check_permission(get_user_id(i)))(func)

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

        return commands.check(lambda ctx: check_permission(get_user_id(ctx)))(wrapper)

    return decorator


def owns_realm_channel(category_id=REALM_CATEGORY_ID):
    """
    Check if a user owns the realm channel they are currently in.
    This is based on the role name matching channel name pattern.
    """

    def predicate(interaction: discord.Interaction) -> bool:
        _log.debug(f"Checking if user {interaction.user.id} owns realm channel.")
        if interaction.channel.category_id != category_id:
            _log.info(f"User {interaction.user.id} is not in the correct category.")
            return False

        try:
            __database.db.connect(reuse_if_open=True)
            query = __database.Administrators.select().where(
                (__database.Administrators.TierLevel >= 1)
                & (__database.Administrators.discordID == str(interaction.user.id))
            )
            if query.exists():
                _log.info(f"User {interaction.user.id} has admin privileges.")
                return True
        except OperationalError as e:
            _log.error(f"Database connection error: {e}")
            return False
        finally:
            if not __database.db.is_closed():
                __database.db.close()
                _log.debug("Database connection closed.")

        try:
            realm_name = interaction.channel.name.rsplit("-", 1)[0]
            role_name = f"{realm_name} OP"
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


slash_owns_realm_channel = owns_realm_channel()


def is_realm_op():
    """
    Check if a user is a Realm OP either by role or admin privileges.
    Used for managing realm-level permissions.
    """

    def predicate(interaction: discord.Interaction) -> bool:
        _log.debug(f"Checking if user {interaction.user.id} is a Realm OP.")

        try:
            __database.db.connect(reuse_if_open=True)
            query = __database.Administrators.select().where(
                (__database.Administrators.TierLevel >= 1)
                & (__database.Administrators.discordID == str(interaction.user.id))
            )
            if query.exists():
                _log.info(f"User {interaction.user.id} has admin privileges.")
                return True
        except OperationalError as e:
            _log.error(f"Database connection error: {e}")
            return False
        finally:
            if not __database.db.is_closed():
                __database.db.close()
                _log.debug("Database connection closed.")

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


slash_is_realm_op = is_realm_op()


def check_MRP():
    """
    Check that a command is only allowed in the TEST or PORTAL server.
    """

    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.guild.id in {TEST_SERVER_ID, PORTAL_SERVER_ID}

    return app_commands.check(predicate)


slash_check_MRP = check_MRP()
