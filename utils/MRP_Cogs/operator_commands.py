import logging
from datetime import datetime
from typing import Literal

import discord
from discord import CategoryChannel, app_commands
from discord.ext import commands

from core.logging_module import get_log

_log = get_log(__name__)


def solve(s):
    a = s.split(' ')
    for i in range(len(a)):
        a[i] = a[i].capitalize()
    return ' '.join(a)


class OperatorCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        action="Whether to add or remove a Realm OP Role",
        user="The user to add or remove the role from",
        role="The role to add or remove from the user. (Must be a Realm OP role & YOU MUST HAVE THE ROLE)"
    )
    @app_commands.checks.has_role("Realm OP")
    async def manage_operators(self, interaction: discord.Interaction, action: Literal["add", "remove"],
                               user: discord.Member, *, role: discord.Role):
        if "OP" in role.name:
            if role not in interaction.user.roles:
                return await interaction.response.send_message(
                    f"You don't have the role '{str(role)}'. Please contact an Admin if you are having trouble!")
            elif role.id == 683430456490065959:
                return await interaction.response.send_message("You are not allowed to give out the `Realm OP` role.")
            else:
                if action == "add":
                    await user.add_roles(role)
                    embed = discord.Embed(title="Realm Operator Command",
                                          description=user.mention + " now has " + role.mention +
                                                      "!\nPlease remember you require Spider Sniper or above in order to get the Realm OP role!",
                                          color=0x4287f5)
                    await user.send(
                        f"Hello, you have been given OP privileges for {str(role)} in the Minecraft Realm Portal. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules.")
                else:
                    await user.remove_roles(role)
                    embed = discord.Embed(title="Realm Operator Command",
                                          description="**Operator** " + user.mention + " removed " + role.mention + " from " + user.name,
                                          color=0x4287f5)
                await interaction.followup.send(embed=embed)

        else:
            await interaction.response.send_message(
                "This role is not a Realm role. Please contact an Admin if you believe this is a mistake.")


async def setup(bot):
    await bot.add_cog(OperatorCMD(bot))
