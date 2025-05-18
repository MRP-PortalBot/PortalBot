# utils/admin/__operator_commands.py

from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from core.logging_module import get_log
from core.checks import slash_is_realm_op

_log = get_log(__name__)


class OperatorCommands(commands.GroupCog, name="operator"):
    def __init__(self, bot):
        self.bot = bot
        _log.info("OperatorCommands group loaded.")

    @app_commands.command(
        name="manage_operators", description="Manage your realm admins here."
    )
    @app_commands.describe(
        action="Whether to add or remove a Realm OP Role",
        user="The user to add or remove the role from",
        role="The role to add or remove from the user. (Must be a Realm OP role & YOU MUST HAVE THE ROLE)",
    )
    @slash_is_realm_op
    async def manage_operators(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove"],
        user: discord.Member,
        *,
        role: discord.Role,
    ):
        try:
            _log.info(
                f"{interaction.user} initiated manage_operators: action={action}, user={user}, role={role}"
            )

            if "OP" not in role.name:
                _log.warning(f"Role '{role}' is not an OP role.")
                await interaction.response.send_message(
                    "This role is not a Realm role. Please contact an Admin if you believe this is a mistake.",
                    ephemeral=True,
                )
                return

            if role not in interaction.user.roles:
                _log.warning(f"{interaction.user} lacks role '{role}'.")
                await interaction.response.send_message(
                    f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!",
                    ephemeral=True,
                )
                return

            if role.id == 683430456490065959:
                _log.warning(f"{interaction.user} attempted to grant Realm OP role.")
                await interaction.response.send_message(
                    "You are not allowed to give out the `Realm OP` role.",
                    ephemeral=True,
                )
                return

            if action == "add":
                await user.add_roles(role)
                _log.info(f"Added {role} to {user} by {interaction.user}")
                embed = discord.Embed(
                    title="Realm Operator Command",
                    description=f"{user.mention} now has {role.mention}!\nPlease remember you require Spider Sniper or above in order to get the Realm OP role!",
                    color=0x4287F5,
                )
                await interaction.response.send_message(embed=embed)
                await user.send(
                    f"Hello, you have been given OP privileges for {str(role)} in the Minecraft Realm Portal. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules."
                )
            else:
                await user.remove_roles(role)
                _log.info(f"Removed {role} from {user} by {interaction.user}")
                embed = discord.Embed(
                    title="Realm Operator Command",
                    description=f"**Operator** {interaction.user.mention} removed {role.mention} from {user.name}",
                    color=0x4287F5,
                )
                await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            _log.error("Missing permissions to manage roles.")
            await interaction.response.send_message(
                "I do not have permission to manage roles. Please check my permissions and try again.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            _log.error(f"HTTP Exception: {e}")
            await interaction.response.send_message(
                "An error occurred while managing the role. Please try again later.",
                ephemeral=True,
            )
        except Exception as e:
            _log.exception(f"Unexpected error in manage_operators: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please contact an administrator.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(OperatorCommands(bot))
    _log.info("✅ OperatorCommands loaded.")
