import discord
from discord.ext import commands
from core import database
from core.common import get_cached_bot_data
from core.logging_module import get_log

# Setup logging
_log = get_log(__name__)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        log_channel = discord.utils.get(guild.channels, name="member-log")
        username = member.name
        longid = str(member.id)
        discordname = f"{username}#{member.discriminator}"

        _log.info(f"Member joined: {discordname} in guild: {guild.name}")

        try:
            # Connect to the database and fetch or create the user profile
            database.db.connect(reuse_if_open=True)

            profile, created = database.PortalbotProfile.get_or_create(
                DiscordLongID=longid, defaults={"DiscordName": discordname}
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

            # Log the message to the log channel, if available
            if log_channel:
                await log_channel.send(message)
            else:
                _log.warning(f"Log channel not found in guild: {guild.name}")

        except Exception as e:
            _log.error(f"Error processing join event for {discordname}: {e}")
            if log_channel:
                await log_channel.send(
                    f"An error occurred while processing {discordname}'s join event."
                )
        finally:
            if not database.db.is_closed():
                database.db.close()
                _log.debug("Database connection closed.")

        # Send a welcome message to the user
        await self.send_welcome_message(member)

async def send_welcome_message(self, member: discord.Member):
    try:
        # Retrieve cached bot data for the server
        bot_data = get_cached_bot_data(member.guild.id)
        if not bot_data:
            _log.warning(f"No cached bot data found for guild {member.guild.id}")
            return

        welcome_channel_id = bot_data.welcome_message_channel
        if not welcome_channel_id:
            _log.warning(f"No welcome message channel configured for guild {member.guild.id}")
            return

        # Get the welcome channel
        channel = member.guild.get_channel(welcome_channel_id)
        if not channel:
            _log.warning(f"Channel with ID {welcome_channel_id} not found in guild {member.guild.id}")
            return

        # Prepare welcome embed
        count = member.guild.member_count
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=f"**{str(member.display_name)}** is the **{str(count)}**th member!",
            color=0xB10D9F,
        )
        embed.add_field(
            name="Getting Started",
            value="Feel free to introduce yourself and check out the community!",
            inline=False,
        )

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        if member.guild.icon:
            embed.set_footer(
                text=f"Welcome to {member.guild.name}!", icon_url=member.guild.icon.url
            )

        # Send welcome message
        await channel.send(embed=embed)
        _log.info(f"Sent welcome message to {member.name} in guild {member.guild.name}.")
    except Exception as e:
        _log.error(f"Error sending welcome message to {member.name}: {e}", exc_info=True)


async def setup(bot):
    await bot.add_cog(Events(bot))
    _log.info("Events cog has been loaded.")
