import discord
from discord.ext import commands
from core import database
from core.common import load_config
from core.logging_module import get_log

# Load configuration and setup logging
config, _ = load_config()
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
        guild_id = member.guild.id
        channel = None
        embed = None
        _log.info(
            f"Preparing to send welcome message to {member.name} in guild {member.guild.name} (ID: {guild_id})"
        )

        if guild_id == 587495640502763521:  # Example Guild 1
            channel = member.guild.get_channel(588813558486269956)
            count = member.guild.member_count
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"**{str(member.display_name)}** is the **{str(count)}**th member!",
                color=0xB10D9F,
            )
            embed.add_field(
                name="Looking for a Realm?",
                value="Check out the Realm list in <#588070315117117440>!",
                inline=False,
            )

        elif guild_id == 192052103017922567:  # Example Guild 2
            channel = member.guild.get_channel(796115065622626326)
            count = member.guild.member_count
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"**{str(member.display_name)}** is ready to game!",
                color=0xFFCE41,
            )
            embed.add_field(
                name="Want to see more channels?",
                value="Check out the Game list in <#796114173514743928>, and react to a game to join the channel!",
                inline=False,
            )

        elif guild_id == 448488274562908170:  # Another Guild
            _log.info(
                f"No specific welcome message set for guild {member.guild.name} (ID: {guild_id})"
            )
            return

        if channel and embed:
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            if member.guild.icon:
                embed.set_footer(
                    text="Join the MRP Community Realm!", icon_url=member.guild.icon.url
                )
            await channel.send(embed=embed)
            _log.info(
                f"Sent welcome message to {member.name} in guild {member.guild.name}."
            )
        else:
            _log.warning(
                f"Unable to send welcome message for {member.name}: Channel or embed not defined."
            )


async def setup(bot):
    await bot.add_cog(Events(bot))
    _log.info("Events cog has been loaded.")
