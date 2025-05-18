import discord
from discord.ext import commands
from discord import app_commands
from core import database
from core.logging_module import get_log
import functools

_log = get_log(__name__)
leveled_roles_log = get_log("leveled_roles", console=False)


class LeveledRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        leveled_roles_log.info("LeveledRoles cog initialized.")

    def with_db_connection(func):
        """Decorator to ensure database connection is open/closed properly."""

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                if database.db.is_closed():
                    database.db.connect(reuse_if_open=True)
                    leveled_roles_log.debug("Database connection opened.")
                result = await func(self, *args, **kwargs)
                return result
            except Exception as e:
                leveled_roles_log.error(f"Database operation failed: {e}")
            finally:
                if not database.db.is_closed():
                    database.db.close()
                    leveled_roles_log.debug("Database connection closed.")

        return wrapper

    @with_db_connection
    async def assign_role_based_on_level(
        self, member: discord.Member, new_level: int, guild_id: int
    ):
        """
        Assigns the appropriate leveled role based on user level.
        Only one leveled role is allowed at a time.
        """
        try:
            leveled_roles_log.info(
                f"Checking roles for {member.display_name} (Level {new_level})."
            )
            leveled_roles = (
                database.LeveledRoles.select()
                .where(database.LeveledRoles.ServerID == str(guild_id))
                .order_by(database.LeveledRoles.LevelThreshold.desc())
            )

            role_to_assign = None
            for role_entry in leveled_roles:
                if new_level >= role_entry.LevelThreshold:
                    role_to_assign = role_entry
                    break

            if role_to_assign:
                discord_role = discord.utils.get(
                    member.guild.roles, id=int(role_to_assign.RoleID)
                )
                leveled_roles_log.debug(
                    f"Intended role: {discord_role} | Current roles: {[r.name for r in member.roles]}"
                )

                await self.remove_previous_leveled_roles(
                    member, guild_id, keep_role=discord_role
                )

                if discord_role and discord_role not in member.roles:
                    leveled_roles_log.info(
                        f"Assigning {discord_role.name} to {member.display_name} for reaching Level {new_level}."
                    )
                    await member.add_roles(discord_role)
                    await member.send(
                        f"🎉 Congratulations {member.mention}, you've been promoted to **{discord_role.name}**!"
                    )
                else:
                    leveled_roles_log.info(
                        f"Role {discord_role.name if discord_role else 'None'} is already assigned or doesn't exist."
                    )
            else:
                leveled_roles_log.info(f"No leveled role found for Level {new_level}.")
        except Exception as e:
            leveled_roles_log.error(
                f"Error assigning role to {member.display_name}: {e}"
            )

    @with_db_connection
    async def remove_previous_leveled_roles(
        self, member: discord.Member, guild_id: int, keep_role: discord.Role = None
    ):
        """
        Removes all leveled roles from a member except the one they should keep.
        """
        try:
            leveled_roles = database.LeveledRoles.select().where(
                database.LeveledRoles.ServerID == str(guild_id)
            )

            for role_entry in leveled_roles:
                discord_role = discord.utils.get(
                    member.guild.roles, id=int(role_entry.RoleID)
                )
                if (
                    discord_role
                    and discord_role in member.roles
                    and discord_role != keep_role
                ):
                    await member.remove_roles(discord_role)
                    leveled_roles_log.info(
                        f"Removed role {discord_role.name} from {member.display_name}."
                    )
        except Exception as e:
            leveled_roles_log.error(
                f"Error removing roles for {member.display_name}: {e}"
            )

    @with_db_connection
    @app_commands.command(
        name="set_level_role",
        description="Set a level threshold for a role in this server.",
    )
    async def set_level_role(
        self, interaction: discord.Interaction, role: discord.Role, level_threshold: int
    ):
        guild_id = interaction.guild_id
        leveled_roles_log.info(
            f"Setting role {role.name} for level {level_threshold} in guild {guild_id}."
        )

        try:
            entry, created = database.LeveledRoles.get_or_create(
                RoleID=str(role.id),
                ServerID=str(guild_id),
                defaults={"RoleName": role.name, "LevelThreshold": level_threshold},
            )

            if not created:
                entry.LevelThreshold = level_threshold
                entry.RoleName = role.name
                entry.save()

            await interaction.response.send_message(
                f"✅ Role **{role.name}** set for level **{level_threshold}**."
            )
        except Exception as e:
            leveled_roles_log.error(f"Error setting leveled role: {e}")
            await interaction.response.send_message(
                "❌ Failed to set leveled role.", ephemeral=True
            )

    @with_db_connection
    @app_commands.command(
        name="remove_level_role", description="Remove a leveled role from this server."
    )
    async def remove_level_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        guild_id = interaction.guild_id
        leveled_roles_log.info(
            f"Removing role {role.name} from leveled system in guild {guild_id}."
        )

        try:
            entry = database.LeveledRoles.get_or_none(
                database.LeveledRoles.RoleID == str(role.id),
                database.LeveledRoles.ServerID == str(guild_id),
            )

            if entry:
                entry.delete_instance()
                await interaction.response.send_message(
                    f"✅ Role **{role.name}** removed from the level system."
                )
            else:
                await interaction.response.send_message(
                    f"⚠️ Role **{role.name}** not found in the level system."
                )
        except Exception as e:
            leveled_roles_log.error(f"Error removing leveled role: {e}")
            await interaction.response.send_message(
                "❌ Failed to remove leveled role.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listens for messages and checks if the user leveled up,
        then assigns them a role if needed.
        """
        if message.author.bot or not message.guild:
            return

        member = message.author
        guild_id = message.guild.id

        try:
            score = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == str(member.id))
                & (database.ServerScores.ServerID == str(guild_id))
            )

            if score:
                leveled_roles_log.info(
                    f"{member.display_name} is at Level {score.Level}. Checking for role assignment."
                )
                await self.assign_role_based_on_level(member, score.Level, guild_id)
            else:
                leveled_roles_log.warning(
                    f"No score entry found for {member.display_name} in guild {guild_id}."
                )
        except Exception as e:
            leveled_roles_log.error(f"Error during level check in on_message: {e}")


async def setup(bot):
    await bot.add_cog(LeveledRoles(bot))
    _log.info("LeveledRoles cog has been set up.")
