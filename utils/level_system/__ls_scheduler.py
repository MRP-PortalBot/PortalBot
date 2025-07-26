import discord
import datetime
from discord.ext import tasks, commands
from utils.database import __database as database
from utils.level_system.__ls_logic import calculate_level, get_role_for_level
from utils.helpers.__logging_module import get_log

_log = get_log("level_system.scheduler")


class LevelAuditScheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_task.start()

    def cog_unload(self):
        self.audit_task.cancel()

    @tasks.loop(hours=24)
    async def audit_task(self):
        now = datetime.datetime.utcnow()
        if now.weekday() != 0:  # Only run on Mondays (0 = Monday)
            return

        for guild in self.bot.guilds:
            bot_data = database.BotData.get_or_none(
                database.BotData.server_id == str(guild.id)
            )
            if (
                not bot_data
                or not bot_data.member_log
                or not bot_data.enable_weekly_audit
            ):
                continue

            log_channel = guild.get_channel(int(bot_data.member_log))
            if not log_channel:
                continue

            try:
                level_roles = database.LeveledRoles.select().where(
                    database.LeveledRoles.ServerID == str(guild.id)
                )
                level_role_ids = {int(r.RoleID) for r in level_roles if r.RoleID}

                updated = 0

                for member in guild.members:
                    if member.bot:
                        continue

                    score = database.ServerScores.get_or_none(
                        (database.ServerScores.DiscordLongID == str(member.id))
                        & (database.ServerScores.ServerID == str(guild.id))
                    )
                    if not score:
                        continue

                    correct_role = await get_role_for_level(score.Level, guild)
                    current_roles = [r for r in member.roles if r.id in level_role_ids]

                    to_remove = [
                        r
                        for r in current_roles
                        if correct_role is None or r.id != correct_role.id
                    ]
                    needs_fix = bool(
                        to_remove or (correct_role and correct_role not in member.roles)
                    )

                    if needs_fix:
                        if to_remove:
                            await member.remove_roles(*to_remove)
                        if correct_role and correct_role not in member.roles:
                            await member.add_roles(correct_role)

                        updated += 1

                        embed = discord.Embed(
                            title="🔄 Weekly Level Role Sync",
                            description=(
                                f"**User:** {member.mention} (`{member.name}`)\n"
                                f"**Level:** {score.Level}\n"
                                f"**Assigned Role:** {correct_role.mention if correct_role else '❌ None'}"
                            ),
                            color=discord.Color.teal(),
                            timestamp=discord.utils.utcnow(),
                        )
                        embed.set_footer(text=f"User ID: {member.id}")
                        embed.set_thumbnail(url=member.display_avatar.url)

                        await log_channel.send(embed=embed)

                if updated:
                    _log.info(f"{guild.name}: {updated} member roles updated.")

            except Exception as e:
                _log.error(f"Audit failed in guild {guild.name}: {e}", exc_info=True)

    @audit_task.before_loop
    async def before_audit(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelAuditScheduler(bot))
    _log.info("📅 Weekly level audit scheduler loaded.")
