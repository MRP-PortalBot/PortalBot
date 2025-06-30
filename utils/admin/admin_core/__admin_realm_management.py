# utils/admin/__admin_realm_management.py

from typing import Literal
import datetime
import discord
from discord import app_commands, ui
from discord.ext import commands
from utils.database import __database as database
from utils.helpers.__checks import has_admin_level, slash_check_MRP
from utils.helpers.__logging_module import get_log
from utils.admin.bot_management.__bm_logic import get_cached_bot_data


_log = get_log(__name__)


def build_realm_application_modal(bot):
    class RealmApplicationModal(ui.Modal, title="Realm Application"):
        def __init__(self):
            super().__init__(timeout=None)
            self.bot = bot

            self.realm_name = ui.TextInput(label="Realm Name", required=True)
            self.emoji = ui.TextInput(label="Emoji", required=True)
            self.play_style = ui.TextInput(label="Play Style", required=True)
            self.gamemode = ui.TextInput(label="Game Mode", required=True)
            self.short_description = ui.TextInput(
                label="Short Description", required=True
            )
            self.long_description = ui.TextInput(
                label="Long Description", style=discord.TextStyle.long, required=True
            )
            self.application_process = ui.TextInput(
                label="Application Process", style=discord.TextStyle.long, required=True
            )
            self.admin_team = ui.TextInput(
                label="Admin Team", style=discord.TextStyle.long, required=True
            )
            self.member_count = ui.TextInput(label="Member Count", required=True)
            self.community_age = ui.TextInput(label="Community Age", required=True)
            self.world_age = ui.TextInput(label="World Age", required=True)
            self.reset_schedule = ui.TextInput(label="Reset Schedule", required=True)
            self.foreseeable_future = ui.TextInput(
                label="Foreseeable Future", style=discord.TextStyle.long, required=True
            )
            self.realm_addons = ui.TextInput(
                label="Realm Addons", style=discord.TextStyle.long, required=True
            )
            self.pvp = ui.TextInput(label="PvP Enabled?", required=True)
            self.percent_player_sleep = ui.TextInput(
                label="Percent Player Sleep", required=True
            )

        async def on_submit(self, interaction: discord.Interaction):
            bot_data = get_cached_bot_data(interaction.guild.id)
            try:
                _log.info(
                    f"Realm application submitted by {interaction.user.display_name} for '{self.realm_name.value}'"
                )
                await self.save_application(interaction)
                embed = self.build_embed(interaction.user)
                log_channel = self.bot.get_channel(bot_data.realm_channel_response)
                admin_role = interaction.guild.get_role(bot_data.admin_role)
                await log_channel.send(content=admin_role.mention, embed=embed)

                await interaction.response.send_message(
                    "✅ Realm application submitted successfully!", ephemeral=True
                )
            except Exception as e:
                _log.exception(f"Error submitting application: {e}")
                await interaction.response.send_message(
                    "An error occurred while submitting your application.",
                    ephemeral=True,
                )

        async def save_application(self, interaction: discord.Interaction):
            try:
                database.RealmApplications.create(
                    discord_id=interaction.user.id,
                    discord_name=interaction.user.display_name,
                    realm_name=self.realm_name.value,
                    emoji=self.emoji.value,
                    play_style=self.play_style.value,
                    gamemode=self.gamemode.value,
                    short_desc=self.short_description.value,
                    long_desc=self.long_description.value,
                    application_process=self.application_process.value,
                    admin_team=self.admin_team.value,
                    member_count=int(self.member_count.value),
                    community_age=self.community_age.value,
                    world_age=self.world_age.value,
                    reset_schedule=self.reset_schedule.value,
                    foreseeable_future=self.foreseeable_future.value,
                    realm_addons=self.realm_addons.value,
                    pvp=self.pvp.value,
                    percent_player_sleep=self.percent_player_sleep.value,
                    approval=False,
                )
            except Exception as e:
                _log.exception(f"Error saving application to database: {e}")

        def build_embed(self, user: discord.Member):
            embed = discord.Embed(
                title="Realm Application",
                description=f"**Realm Owner:** {user.mention}",
                color=discord.Color.blurple(),
            )
            embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(name="Realm Name", value=self.realm_name.value, inline=True)
            embed.add_field(name="Emoji", value=self.emoji.value, inline=True)
            embed.add_field(name="Play Style", value=self.play_style.value, inline=True)
            embed.add_field(name="Game Mode", value=self.gamemode.value, inline=True)
            embed.add_field(
                name="Short Description",
                value=self.short_description.value,
                inline=False,
            )
            embed.add_field(
                name="Long Description", value=self.long_description.value, inline=False
            )
            embed.add_field(
                name="Application Process",
                value=self.application_process.value,
                inline=False,
            )
            embed.add_field(
                name="Admin Team", value=self.admin_team.value, inline=False
            )
            embed.add_field(
                name="Member Count", value=self.member_count.value, inline=True
            )
            embed.add_field(
                name="Community Age", value=self.community_age.value, inline=True
            )
            embed.add_field(name="World Age", value=self.world_age.value, inline=True)
            embed.add_field(
                name="Reset Schedule", value=self.reset_schedule.value, inline=True
            )
            embed.add_field(
                name="Foreseeable Future",
                value=self.foreseeable_future.value,
                inline=False,
            )
            embed.add_field(
                name="Realm Addons", value=self.realm_addons.value, inline=False
            )
            embed.add_field(name="PvP Enabled?", value=self.pvp.value, inline=True)
            embed.add_field(
                name="Percent Player Sleep",
                value=self.percent_player_sleep.value,
                inline=True,
            )
            embed.add_field(
                name="Reaction Codes",
                value="💚 Approve\n💛 More Info Needed\n❤️ Reject",
                inline=False,
            )
            embed.set_footer(
                text=f"Submitted on {datetime.datetime.now().strftime('%Y-%m-%d')}"
            )
            return embed

    return RealmApplicationModal()


class AdminRealmManagement(commands.GroupCog, name="realm"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="apply",
        description="Apply for a realm channel (realm owners only).",
    )
    async def apply_for_realm(self, interaction: discord.Interaction):
        modal = build_realm_application_modal(self.bot)
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="approve_realm",
        description="Approve a submitted realm application and create its channel and role.",
    )
    @app_commands.describe(
        app_number="Application number that corresponds with the realm you're approving."
    )
    @has_admin_level(3)
    async def approve_realm(self, interaction: discord.Interaction, app_number: int):
        await interaction.response.defer(thinking=True)
        bot_data = get_cached_bot_data(interaction.guild.id)
        guild = interaction.guild
        author = interaction.user

        # Fetch application
        try:
            q: database.RealmApplications = (
                database.RealmApplications.select()
                .where(database.RealmApplications.id == app_number)
                .get()
            )
        except database.RealmApplications.DoesNotExist:
            return await interaction.followup.send(
                "❌ Application not found with that ID.", ephemeral=True
            )

        # Status tracking
        log = {
            "RoleCreated": "❌",
            "ChannelCreated": "❌",
            "RoleAssigned": "❌",
            "PermissionsSet": "❌",
            "DMStatus": "❌",
        }

        try:
            # Create role
            role = await guild.create_role(
                name=f"{q.realm_name} OP", color=discord.Color.blue(), mentionable=True
            )
            log["RoleCreated"] = "✅"

            # Create channel
            category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")
            channel = await category.create_text_channel(f"{q.realm_name}-{q.emoji}")
            log["ChannelCreated"] = "✅"

            # Send welcome message
            welcome_embed = discord.Embed(
                title="Welcome to the MRP!",
                description=f"{role.mention} Welcome to the Portal! You should receive a DM with more info shortly.",
                color=0x4C594B,
            )
            await channel.send(embed=welcome_embed)
            await channel.edit(
                topic="The newest Realm on the Minecraft Realm Portal. ]]Realm: Survival Multiplayer[["
            )

            # Assign role
            user = await guild.fetch_member(q.discord_id)
            await user.add_roles(role)
            log["RoleAssigned"] = "✅"

            # Channel permissions
            perms = channel.overwrites_for(role)
            perms.manage_channels = True
            perms.manage_webhooks = True
            perms.manage_messages = True
            await channel.set_permissions(role, overwrite=perms)

            muted = discord.utils.get(guild.roles, name="muted")
            if muted:
                perms_muted = channel.overwrites_for(muted)
                perms_muted.read_messages = False
                perms_muted.send_messages = False
                await channel.set_permissions(muted, overwrite=perms_muted)

            log["PermissionsSet"] = "✅"

            # Realm OP chat unlock
            if guild.id == 587495640502763521:
                op_rules = guild.get_channel(683454087206928435)
                if op_rules:
                    await op_rules.send(
                        f"{role.mention}\nPlease agree to the rules to access Realm OP channels."
                    )
                    perms_rules = op_rules.overwrites_for(role)
                    perms_rules.read_messages = True
                    await op_rules.set_permissions(role, overwrite=perms_rules)

            # DM user
            dm_embed = discord.Embed(
                title="Congrats On Your New Realm Channel!",
                description=f"Your new channel: <#{channel.id}>",
                color=0x42F5BC,
            )
            dm_embed.add_field(
                name="Information",
                value=(
                    "You now have moderation privileges in your realm channel. "
                    "You can update the topic, manage messages, and add OPs using `/operator manage_operators`.\n\n"
                    "To update your realm listing, keep ]]Realm: XYZ[[ in your topic."
                ),
                inline=False,
            )
            await user.send(embed=dm_embed)
            log["DMStatus"] = "✅"

        except Exception as e:
            _log.error(f"Failed to complete realm approval: {e}", exc_info=True)

        finally:
            summary = discord.Embed(
                title="Realm Approval Summary",
                description=f"Approved by: {author.mention}\nApplication ID: {app_number}",
                color=discord.Color.green(),
            )
            for k, v in log.items():
                summary.add_field(name=k, value=v)
            summary.set_footer(text="Command completed.")
            await interaction.followup.send(embed=summary)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminRealmManagement(bot))
    _log.info("✅ AdminRealmManagement loaded.")
