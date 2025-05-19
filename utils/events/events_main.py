import discord
from discord.ext import commands
from utils.database import __database
from admin.bot_management.__bm_logic import get_cached_bot_data

from utils.helpers.__logging_module import get_log

_log = get_log(__name__)


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        guild_id = str(guild.id)
        user_id = str(member.id)
        discordname = f"{member.name}#{member.discriminator}"

        log_channel = discord.utils.get(guild.channels, name="member-log")
        _log.info(f"Member joined: {discordname} in guild: {guild.name} ({guild_id})")

        try:
            __database.db.connect(reuse_if_open=True)

            profile, created = __database.PortalbotProfile.get_or_create(
                DiscordLongID=user_id, defaults={"DiscordName": discordname}
            )

            if created:
                message = (
                    f"{profile.DiscordName}'s profile has been created successfully."
                )
                _log.info(f"Profile created for {discordname}")
            else:
                profile.DiscordName = discordname
                profile.save()
                message = (
                    f"{profile.DiscordName}'s profile has been updated successfully."
                )
                _log.info(f"Profile updated for {discordname}")

            if log_channel:
                await log_channel.send(message)
            else:
                _log.warning(f"Log channel not found in guild: {guild.name}")

        except Exception as e:
            _log.error(
                f"Error processing join event for {discordname}: {e}", exc_info=True
            )
            if log_channel:
                await log_channel.send(
                    f"An error occurred while processing {discordname}'s join event."
                )
        finally:
            if not __database.db.is_closed():
                __database.db.close()
                _log.debug("Database connection closed.")

        await self.send_welcome_message(member)

    async def send_welcome_message(self, member: discord.Member):
        try:
            guild = member.guild
            guild_id = str(guild.id)
            bot_data = get_cached_bot_data(guild_id)

            if not bot_data:
                _log.warning(f"No cached bot data found for guild {guild_id}")
                return

            welcome_channel_id = bot_data.welcome_channel
            if not welcome_channel_id:
                _log.warning(
                    f"No welcome message channel configured for guild {guild_id}"
                )
                return

            channel = guild.get_channel(int(welcome_channel_id))
            if not channel:
                _log.warning(
                    f"Channel with ID {welcome_channel_id} not found in guild {guild_id}"
                )
                return

            count = guild.member_count
            embed = discord.Embed(
                title=f"Welcome to {guild.name}!",
                description=f"**{member.mention}** is the **{count}** member!",
                color=0xB10D9F,
            )
            embed.add_field(
                name="Getting Started",
                value="Feel free to introduce yourself and check out the community!",
                inline=False,
            )

            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            if guild.icon:
                embed.set_footer(
                    text=f"Welcome to {guild.name}!", icon_url=guild.icon.url
                )

            await channel.send(embed=embed)
            _log.info(f"Sent welcome message to {member.name} in guild {guild.name}.")

        except Exception as e:
            _log.error(
                f"Error sending welcome message to {member.name}: {e}", exc_info=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
    _log.info("✅ Events cog loaded.")
