import discord
from discord import app_commands
from discord.ext import commands
from tatsu.wrapper import ApiWrapper
from core import database
from core.common import load_config

config, _ = load_config()

# Initialize the API wrapper with your Tatsu API key
wrapper = ApiWrapper(key="EeQlkBOyMi-wpTarZ98XYjS2pZscJ2TNf")

class TatsuScoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_and_store_scores(self, MRPguild_id: int, user_id: int, user_name: str):
        try:
            # Fetch the user's ranking from Tatsu
            result = await wrapper.get_member_ranking(MRPguild_id, user_id)

            # Access relevant fields such as user rank and score
            user_rank = result.rank
            user_score = result.score

            # Check if the user exists in the ServerScores table for this guild
            score_entry = database.ServerScores.get_or_none(
                (database.ServerScores.DiscordLongID == str(user_id)) & 
                (database.ServerScores.ServerID == str(MRPguild_id))
            )

            if score_entry:
                # Update the user's score in the ServerScores table
                score_entry.Score = user_score
                score_entry.DiscordName = user_name
                score_entry.save()
            else:
                # User not found in the ServerScores, create a new entry
                new_score_entry = database.ServerScores.create(
                    DiscordName=str(user_name),
                    DiscordLongID=str(user_id),
                    ServerID=str(MRPguild_id),
                    Score=user_score
                )
                new_score_entry.save()
                print(f"User {user_name} (ID: {user_id}) added to ServerScores with score {user_score}.")

        except Exception as e:
            print(f"Error fetching Tatsu score for user {user_id}: {e}")

    @app_commands.command(name="update_scores")
    async def update_all_scores(self, interaction: discord.Interaction):
        """
        Command to update all user scores in the current guild from Tatsu API.
        """
        guild = interaction.guild
        MRPguild = self.bot.get_guild(config['MRP'])
        print (str(MRPguild))

        if MRPguild is None:
            await interaction.response.send_message("MRP guild not found. Please check if the bot is in the correct guild and that the ID is valid.")
            return

        user_list = guild.members  # Fetch all members in the guild
        mrp_user_list = MRPguild.members

        await interaction.response.send_message(f"Updating scores for {len(mrp_user_list)} members in {MRPguild.name}...")

        for user in mrp_user_list:
            user_id = user.id
            user_name = user.display_name
            await self.fetch_and_store_scores(MRPguild.id, user_id, user_name)

        await interaction.followup.send(f"Scores updated for {len(user_list)} members.")

# Adding the cog to the bot
async def setup(bot):
    await bot.add_cog(TatsuScoreCog(bot))
