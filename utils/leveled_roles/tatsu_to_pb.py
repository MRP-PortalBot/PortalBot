import os
import discord
from discord import app_commands
from discord.ext import commands
from tatsu.wrapper import ApiWrapper
import asyncio  # Import asyncio for sleep function
from core import database
from core.common import load_config, calculate_level
from core.logging_module import get_log

_log = get_log(__name__)

config, _ = load_config()

# Initialize the API wrapper with your Tatsu API key
wrapper = ApiWrapper(os.getenv("tatsu_api_key"))


class TatsuScoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_and_store_scores(self, guild_id: int, user_id: int, user_name: str):
        try:
            # Fetch user's score and rank from Tatsu API
            result = await wrapper.get_member_ranking(guild_id, user_id)
            user_score = result.score
            user_rank = result.rank  # Not used but available

            # Check if this user already has a score entry
            score_entry = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == str(user_id))
                & (database.ServerScores.ServerID == str(guild_id))
            )

            if score_entry:
                # Update existing entry
                score_entry.Score = user_score
                score_entry.DiscordName = user_name
                score_entry.save()
                _log.info(f"Updated score for {user_name} to {user_score}.")
            else:
                # Create new score entry with default level/progress
                level, progress, next_level_score = calculate_level(user_score)

                database.ServerScores.create(
                    DiscordName=user_name,
                    DiscordLongID=str(user_id),
                    ServerID=str(guild_id),
                    Score=user_score,
                    Level=level,
                    Progress=next_level_score,
                )
                _log.info(
                    f"Created new score record for {user_name} (score: {user_score}, level: {level})."
                )

        except Exception as e:
            _log.error(
                f"Error fetching Tatsu score for user {user_id}: {e}", exc_info=True
            )

    @app_commands.command(
        name="update_scores", description="Sync user scores from Tatsu API."
    )
    async def update_all_scores(self, interaction: discord.Interaction):
        """
        Command to update all user scores in the configured MRP guild from Tatsu.
        """
        guild = interaction.guild
        MRPguild = self.bot.get_guild(config["MRP"])

        if MRPguild is None:
            await interaction.response.send_message(
                "MRP guild not found. Please check the bot is in the correct guild and that the ID is valid.",
                ephemeral=True,
            )
            _log.warning("MRP guild not found during Tatsu sync.")
            return

        mrp_user_list = MRPguild.members
        await interaction.response.send_message(
            f"Updating scores for {len(mrp_user_list)} members in {MRPguild.name}..."
        )

        for user in mrp_user_list:
            await self.fetch_and_store_scores(MRPguild.id, user.id, user.display_name)
            await asyncio.sleep(1.1)  # Delay to avoid hitting Tatsu rate limits

        await interaction.followup.send(
            f"✅ Scores updated for {len(mrp_user_list)} members."
        )
        _log.info(
            f"Completed Tatsu score update for {len(mrp_user_list)} users in {MRPguild.name}."
        )


# Cog setup
async def setup(bot):
    await bot.add_cog(TatsuScoreCog(bot))
