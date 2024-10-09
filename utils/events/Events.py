import discord
from discord.ext import commands
from core import database
from core.common import load_config
from core.logging_module import get_log

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

        try:
            # Connect to the database and fetch or create the user profile
            database.db.connect(reuse_if_open=True)

            profile, created = database.PortalbotProfile.get_or_create(
                DiscordLongID=longid, defaults={"DiscordName": discordname}
            )

            if created:
                message = (
                    f"{profile.DiscordName}'s Profile has been created successfully."
                )
            else:
                profile.DiscordName = discordname
                profile.save()
                message = (
                    f"{profile.DiscordName}'s Profile has been updated successfully."
                )

            if log_channel:
                await log_channel.send(message)
            _log.info(message)

        except Exception as e:
            _log.error(f"Error processing join event for {member.name}: {e}")
            if log_channel:
                await log_channel.send(
                    f"An error occurred while processing {member.name}'s join event."
                )
        finally:
            if not database.db.is_closed():
                database.db.close()

        # Send a welcome message based on the guild
        await self.send_welcome_message(member)

    async def send_welcome_message(self, member: discord.Member):
        guild_id = member.guild.id
        channel = None
        embed = None

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

        elif (
            guild_id == 448488274562908170
        ):  # Another Guild (handle differently if needed)
            _log.info(f"Unhandled join event for guild: {member.guild.name}")

        # Send the welcome message if a channel and embed are ready
        if channel and embed:
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(
                text="Join the MRP Community Realm!", icon_url=member.guild.icon.url
            )
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
