import discord
from discord.ext import commands
from discord import app_commands
from core import database
from core.logging_module import get_log

_log = get_log(__name__)
leveled_roles_log = get_log("leveled_roles", console=False)


class LeveledRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        leveled_roles_log.info("LeveledRoles cog initialized.")

    def with_db_connection(func):
        """Decorator to ensure database connection is open/closed properly."""

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
        Assigns the appropriate role to a user based on their new level.
        Removes any previous leveled role they had to ensure they only have one leveled role.
        """
        try:
            leveled_roles_log.info(
                f"Checking roles for {member.display_name} (Level {new_level})."
            )
            leveled_roles = database.LeveledRoles.select().where(
                database.LeveledRoles.ServerID == str(guild_id)
            )

            role_to_assign = None
            for role_entry in leveled_roles:
                if new_level >= role_entry.LevelThreshold:
                    role_to_assign = role_entry

            if role_to_assign:
                discord_role = discord.utils.get(
                    member.guild.roles, id=int(role_to_assign.RoleID)
                )

                # Remove all other leveled roles before adding the new one
                await self.remove_previous_leveled_roles(member, guild_id)

                if discord_role and discord_role not in member.roles:
                    await member.add_roles(discord_role)
                    leveled_roles_log.info(
                        f"Assigned {discord_role.name} to {member.display_name} for reaching Level {new_level}."
                    )
                    await member.send(
                        f"🎉 Congratulations {member.mention}, you've been promoted to **{discord_role.name}**!"
                    )
                else:
                    leveled_roles_log.warning(
                        f"Role {role_to_assign.RoleName} either not found or already assigned to {member.display_name}."
                    )
            else:
                leveled_roles_log.info(
                    f"No role found for Level {new_level} for {member.display_name}."
                )

        except Exception as e:
            leveled_roles_log.error(
                f"Error assigning role to {member.display_name}: {e}"
            )

    async def remove_previous_leveled_roles(
        self, member: discord.Member, guild_id: int
    ):
        """
        Removes any previously assigned leveled roles from the user to ensure they only have one leveled role at a time.
        """
        try:
            leveled_roles = database.LeveledRoles.select().where(
                database.LeveledRoles.ServerID == str(guild_id)
            )
            for role_entry in leveled_roles:
                discord_role = discord.utils.get(
                    member.guild.roles, id=int(role_entry.RoleID)
                )
                if discord_role in member.roles:
                    await member.remove_roles(discord_role)
                    leveled_roles_log.info(
                        f"Removed {discord_role.name} from {member.display_name}."
                    )
        except Exception as e:
            leveled_roles_log.error(
                f"Error removing previous leveled roles for {member.display_name}: {e}"
            )

    @with_db_connection
    @app_commands.command(
        name="set_level_role",
        description="Sets a level threshold for a role in the current server.",
    )
    async def set_level_role(
        self, interaction: discord.Interaction, role: discord.Role, level_threshold: int
    ):
        guild_id = interaction.guild_id
        leveled_roles_log.info(
            f"Setting role {role.name} for level {level_threshold} in guild {guild_id}."
        )

        try:
            role_entry, created = database.LeveledRoles.get_or_create(
                RoleID=str(role.id),
                ServerID=str(guild_id),
                defaults={"RoleName": role.name, "LevelThreshold": level_threshold},
            )

            if not created:
                role_entry.LevelThreshold = level_threshold
                role_entry.RoleName = role.name
                role_entry.save()

            await interaction.response.send_message(
                f"Role **{role.name}** has been set for level **{level_threshold}**."
            )
            leveled_roles_log.info(
                f"Role {role.name} successfully set for level {level_threshold}."
            )

        except Exception as e:
            leveled_roles_log.error(
                f"Error setting role {role.name} for level {level_threshold}: {e}"
            )
            await interaction.response.send_message(
                f"An error occurred while setting the role.", ephemeral=True
            )

    @with_db_connection
    @app_commands.command(
        name="remove_level_role",
        description="Removes a leveled role in the current server.",
    )
    async def remove_level_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        guild_id = interaction.guild_id
        leveled_roles_log.info(
            f"Removing role {role.name} from level system in guild {guild_id}."
        )

        try:
            role_entry = database.LeveledRoles.get_or_none(
                database.LeveledRoles.RoleID == str(role.id),
                database.LeveledRoles.ServerID == str(guild_id),
            )

            if role_entry:
                role_entry.delete_instance()
                await interaction.response.send_message(
                    f"Role **{role.name}** has been removed from the level system."
                )
                leveled_roles_log.info(f"Role {role.name} removed from level system.")
            else:
                await interaction.response.send_message(
                    f"Role **{role.name}** was not found in the level system."
                )
                leveled_roles_log.warning(
                    f"Role {role.name} not found in level system."
                )

        except Exception as e:
            leveled_roles_log.error(
                f"Error removing role {role.name} from level system: {e}"
            )
            await interaction.response.send_message(
                f"An error occurred while removing the role.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listener that checks if a user's level has changed and assigns the correct role based on the new level.
        """
        if message.author.bot:
            return  # Ignore bot messages

        member = message.author
        guild_id = message.guild.id
        leveled_roles_log.info(
            f"Checking level for user {member.display_name} in guild {guild_id}."
        )

        try:
            score_entry = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == str(member.id))
                & (database.ServerScores.ServerID == str(guild_id))
            )

            if score_entry:
                new_level = score_entry.Level
                leveled_roles_log.info(
                    f"{member.display_name} is at Level {new_level}. Checking for role assignment."
                )
                await self.assign_role_based_on_level(member, new_level, guild_id)
            else:
                leveled_roles_log.warning(
                    f"No score entry found for {member.display_name}."
                )

        except Exception as e:
            leveled_roles_log.error(
                f"Error in on_message level check for {member.display_name}: {e}"
            )


# Set up the cog
async def setup(bot):
    await bot.add_cog(LeveledRoles(bot))
