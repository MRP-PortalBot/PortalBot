# utils/level_system/__ls_commands.py

import discord
from discord.ext import commands
from discord import app_commands

from utils.database import __database as database
from utils.admin.admin_core.__admin_commands import has_admin_level
from utils.admin.bot_management.__bm_logic import config
from utils.helpers.__logging_module import get_log
from .__ls_logic import (
    create_and_order_roles,
    sync_tatsu_score_for_user,
    calculate_level,
    get_role_for_level,
)

from .__ls_views import LeaderboardView  # Add this import at the top

_log = get_log(__name__)


class LevelSystemCommands(commands.GroupCog, name="levels"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setup", description="Create and organize leveled roles for this server."
    )
    @has_admin_level(3)
    async def setup_roles(self, interaction: discord.Interaction):
        """Creates roles from the level chart and inserts them into the database."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        _log.info(
            f"{interaction.user} initiated level role setup in {guild.name} ({guild.id})"
        )

        try:
            await create_and_order_roles(guild)
            await interaction.response.send_message(
                "✅ Leveled roles have been set up."
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage roles.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Error setting up roles: {e}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "❌ An unexpected error occurred.", ephemeral=True
            )
            _log.exception(f"Unexpected error during setup in {guild.name}: {e}")

    @app_commands.command(
        name="sync_tatsu",
        description="Sync scores from Tatsu for all users (MRP guild only).",
    )
    async def sync_tatsu_scores(self, interaction: discord.Interaction):
        """Fetches current Tatsu XP and updates local ServerScores for all users."""
        await interaction.response.defer(ephemeral=True)

        MRPguild_id = config.get("MRP")
        if interaction.guild.id != MRPguild_id:
            await interaction.followup.send(
                "This command is restricted to the MRP guild.", ephemeral=True
            )
            return

        members = [m for m in interaction.guild.members if not m.bot]
        _log.info(
            f"Starting Tatsu sync for {len(members)} members in {interaction.guild.name}"
        )

        for member in members:
            await sync_tatsu_score_for_user(
                self.bot,
                guild_id=member.guild.id,
                user_id=member.id,
                user_name=member.name,
            )

        await interaction.followup.send("✅ Tatsu scores updated.", ephemeral=True)

    @app_commands.command(
        name="leaderboard",
        description="View the top XP earners in this server (paginated).",
    )
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        top_scores = (
            database.ServerScores.select()
            .where(database.ServerScores.ServerID == str(interaction.guild.id))
            .order_by(database.ServerScores.Score.desc())
        )

        entries = list(top_scores)
        if not entries:
            await interaction.followup.send("No users with XP found for this server.")
            return

        view = LeaderboardView(interaction, entries)
        view.update_buttons()

        await interaction.followup.send(embed=view.get_embed(), view=view)

    @app_commands.command(
        name="rank", description="Check your XP rank and level in this server."
    )
    @app_commands.describe(user="The member to check (defaults to you)")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()

        target = user or interaction.user

        # Get this user's score
        score_entry = database.ServerScores.get_or_none(
            (database.ServerScores.DiscordLongID == str(target.id))
            & (database.ServerScores.ServerID == str(interaction.guild.id))
        )

        if not score_entry:
            await interaction.followup.send(
                f"{target.display_name} has no XP recorded."
            )
            return

        # Calculate their rank
        all_scores = (
            database.ServerScores.select()
            .where(database.ServerScores.ServerID == str(interaction.guild.id))
            .order_by(database.ServerScores.Score.desc())
        )

        rank = 1
        for entry in all_scores:
            if entry.DiscordLongID == str(target.id):
                break
            rank += 1

        # Progress to next level
        current_level = score_entry.Level
        current_score = score_entry.Score
        _, progress, next_level_score = calculate_level(current_score)
        to_next = next_level_score - current_score

        embed = discord.Embed(
            title=f"📊 {target.display_name}'s Level Stats", color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=str(current_level))
        embed.add_field(name="XP", value=str(current_score))
        embed.add_field(name="Rank", value=f"#{rank}")
        embed.add_field(name="XP to Next Level", value=str(to_next))

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="audit_roles",
        description="Recheck and fix level roles for all server members.",
    )
    @has_admin_level(3)
    async def audit_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        bot_data = database.BotData.get_or_none(
            database.BotData.server_id == str(guild.id)
        )
        if not bot_data or not bot_data.member_log:
            await interaction.followup.send(
                "⚠️ No member log channel configured in BotData."
            )
            return

        log_channel = guild.get_channel(int(bot_data.member_log))
        if not log_channel:
            await interaction.followup.send(
                "⚠️ Could not find the configured log channel."
            )
            return

        level_roles = database.LeveledRoles.select().where(
            database.LeveledRoles.ServerID == str(guild.id)
        )
        level_role_ids = {int(role.RoleID) for role in level_roles if role.RoleID}

        updated_count = 0

        for member in guild.members:
            if member.bot:
                continue

            score = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == str(member.id))
                & (database.ServerScores.ServerID == str(guild.id))
            )
            if not score:
                continue

            # Determine correct role
            correct_role = await get_role_for_level(score.Level, guild)
            current_roles = [r for r in member.roles if r.id in level_role_ids]

            needs_fix = False

            # Remove incorrect roles
            to_remove = [
                r
                for r in current_roles
                if correct_role is None or r.id != correct_role.id
            ]
            if to_remove:
                await member.remove_roles(*to_remove)
                needs_fix = True

            # Add correct role if not present
            if correct_role and correct_role not in member.roles:
                await member.add_roles(correct_role)
                needs_fix = True

            if needs_fix:
                updated_count += 1
                embed = discord.Embed(
                    title="🔧 Leveled Role Adjusted",
                    description=(
                        f"**User:** {member.mention} (`{member.name}`)\n"
                        f"**Level:** {score.Level}\n"
                        f"**Assigned Role:** {correct_role.mention if correct_role else '❌ None'}"
                    ),
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.set_footer(text=f"User ID: {member.id}")
                embed.set_thumbnail(url=member.display_avatar.url)

                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    _log.warning(f"Cannot send audit log to #{log_channel.name}")

        await interaction.followup.send(
            f"✅ Audit complete. {updated_count} member(s) had level roles fixed."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelSystemCommands(bot))
    _log.info("🛠️ LevelSystemCommands slash group loaded.")
