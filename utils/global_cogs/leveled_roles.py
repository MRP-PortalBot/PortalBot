import discord
from discord.ext import commands
from discord import app_commands
from core import database
from core.logging_module import get_log

_log = get_log(__name__)


class LeveledRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def with_db_connection(func):
        """Decorator to manage database connection open/close."""

        async def wrapper(self, *args, **kwargs):
            if database.db.is_closed():
                database.db.connect(reuse_if_open=True)
            try:
                return await func(self, *args, **kwargs)
            finally:
                if not database.db.is_closed():
                    database.db.close()

        return wrapper

    @with_db_connection
    async def assign_role_based_on_level(
        self, member: discord.Member, new_level: int, guild_id: int
    ):
        """
        Assigns the appropriate role to a user based on their new level.
        """
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

            if discord_role and discord_role not in member.roles:
                try:
                    await member.add_roles(discord_role)
                    _log.info(
                        f"Assigned {discord_role.name} to {member.display_name} (Level {new_level})."
                    )
                    await member.send(
                        f"Congratulations {member.mention}, you've been promoted to **{discord_role.name}**!"
                    )
                except Exception as e:
                    _log.error(f"Error assigning role: {e}")
            else:
                _log.warning(
                    f"Role {role_to_assign.RoleName} not found or already assigned."
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

    @with_db_connection
    @app_commands.command(
        name="remove_level_role",
        description="Removes a leveled role in the current server.",
    )
    async def remove_level_role(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        guild_id = interaction.guild_id

        role_entry = database.LeveledRoles.get_or_none(
            database.LeveledRoles.RoleID == str(role.id),
            database.LeveledRoles.ServerID == str(guild_id),
        )
        if role_entry:
            role_entry.delete_instance()
            await interaction.response.send_message(
                f"Role **{role.name}** has been removed from the level system."
            )
        else:
            await interaction.response.send_message(
                f"Role **{role.name}** was not found in the level system."
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

        score_entry = database.ServerScores.get_or_none(
            (database.ServerScores.DiscordLongID == str(member.id))
            & (database.ServerScores.ServerID == str(guild_id))
        )

        if score_entry:
            new_level = score_entry.Level
            await self.assign_role_based_on_level(member, new_level, guild_id)


# Set up the cog
async def setup(bot):
    await bot.add_cog(LeveledRoles(bot))
