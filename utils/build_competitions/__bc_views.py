from __future__ import annotations
import discord
from utils.database import BuildSeason, BuildEntry
from .__bc_logic import record_vote

class VoteButton(discord.ui.Button):
    def __init__(self, season_id: int, entry_id: int, label: str):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.season_id = season_id
        self.entry_id = entry_id

    async def callback(self, interaction: discord.Interaction):
        msg = await record_vote(interaction, self.season_id, self.entry_id)
        await interaction.response.send_message(msg, ephemeral=True)

class BallotView(discord.ui.View):
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

async def make_ballot_view(season: BuildSeason) -> BallotView:
    view = BallotView(timeout=None)
    entries = list(BuildEntry.select().where(BuildEntry.season == season).order_by(BuildEntry.created_at))
    # Up to 25 buttons per message; paginate later if needed
    for e in entries[:25]:
        label = f"Vote #{e.id}"
        view.add_item(VoteButton(season.id, e.id, label))
    return view
