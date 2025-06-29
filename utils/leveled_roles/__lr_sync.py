import discord
from discord.ext import commands
from discord import app_commands

from utils.helpers.__logging_module import get_log
from utils.leveled_roles.__lr_logic import sync_tatsu_score_for_user
from utils.core_features.__common import config

_log = get_log(__name__)

class LeveledRolesSync(commands.GroupCog, name="levels"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="update_scores", description="Sync scores from Tatsu for all users (MRP guild only).")
    async def update_scores(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        MRPguild_id = config["MRP"]
        if interaction.guild.id != MRPguild_id:
            await interaction.followup.send("This command is restricted to the MRP guild.", ephemeral=True)
            return

        members = [m for m in interaction.guild.members if not m.bot]

        _log.info(f"Starting Tatsu sync for {len(members)} members in {interaction.guild.name}")

        for member in members:
            await sync_tatsu_score_for_user(self.bot, member.guild.id, member.id, member.name)

        await interaction.followup.send("✅ Tatsu scores updated.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeveledRolesSync(bot))
    _log.info("📊 Tatsu score sync command loaded.")
