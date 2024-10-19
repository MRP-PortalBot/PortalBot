from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from core import database
from core.checks import slash_is_bot_admin_3, slash_check_MRP
from core.logging_module import get_log

_log = get_log(__name__)


def return_applyfornewrealm_modal(
    bot,
    realm_name: str,
    type_of_realm: str,
    emoji: str,
    member_count: str,
    community_duration: str,
    world_duration: str,
    reset_schedule: str,
):
    class ApplyForNewRealmForm(ui.Modal, title="Realm Application"):
        def __init__(self):
            super().__init__(timeout=None)
            self.bot = bot
            self.realm_name = realm_name
            self.type_of_realm = type_of_realm
            self.emoji = emoji
            self.member_count = member_count
            self.community_duration = community_duration
            self.world_duration = world_duration
            self.reset_schedule = reset_schedule

            # Define form inputs
            self.short_description = ui.TextInput(
                label="Short Description",
                style=discord.TextStyle.short,
                placeholder="Short description of the realm",
                required=True,
            )

            self.long_description = ui.TextInput(
                label="Long Description",
                style=discord.TextStyle.long,
                placeholder="Long description of the realm",
                required=True,
            )

            self.application_process = ui.TextInput(
                label="Application Process",
                style=discord.TextStyle.long,
                placeholder="Application process for the realm",
                required=True,
            )

            self.foreseeable_future = ui.TextInput(
                label="Foreseeable Future",
                style=discord.TextStyle.long,
                placeholder="Will your Realm/Server have the ability to continue for the foreseeable future?",
                required=True,
            )

            self.admin_team = ui.TextInput(
                label="Admin Team",
                style=discord.TextStyle.long,
                placeholder="Who is on your admin team and how long have they been with you?",
                required=True,
            )

        async def on_submit(self, interaction: discord.Interaction):
            try:
                await self.save_realm_application(interaction)
                embed = self.create_application_embed(
                    interaction.user, interaction.guild
                )
                log_channel = self.bot.get_channel(config["realmChannelResponse"])
                admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

                # Send embed to the log channel
                await log_channel.send(content=admin_role.mention, embed=embed)

                # Confirmation response to the user
                await interaction.response.send_message(
                    "Realm application submitted successfully!", ephemeral=True
                )

            except Exception as e:
                _log.error(f"Error submitting realm application: {e}")
                await interaction.response.send_message(
                    "An error occurred while submitting your application.",
                    ephemeral=True,
                )

        async def save_realm_application(self, interaction: discord.Interaction):
            """Save the realm application to the database."""
            q = database.RealmApplications.create(
                discord_id=interaction.user.id,
                realm_name=self.realm_name,
                type_of_realm=self.type_of_realm,
                emoji=self.emoji,
                member_count=self.member_count,
                realm_age=self.community_duration,
                world_age=self.world_duration,
                reset_schedule=self.reset_schedule,
                short_desc=self.short_description.value,
                long_desc=self.long_description.value,
                application_process=self.application_process.value,
                foreseeable_future=self.foreseeable_future.value,
                admin_team=self.admin_team.value,
            )
            q.save()

        def create_application_embed(self, user, guild):
            """Create the embed message for the application."""
            embed = discord.Embed(
                title="Realm Application",
                description=f"__**Realm Owner:**__\n{user.mention}\n============================================",
                color=0xB10D9F,
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png"
            )
            embed.add_field(
                name="__**Realm Name**__", value=self.realm_name, inline=True
            )
            embed.add_field(
                name="__**Realm or Server?**__", value=self.type_of_realm, inline=True
            )
            embed.add_field(name="__**Emoji**__", value=self.emoji, inline=True)
            embed.add_field(
                name="__**Short Description**__",
                value=self.short_description.value,
                inline=False,
            )
            embed.add_field(
                name="__**Long Description**__",
                value=self.long_description.value,
                inline=False,
            )
            embed.add_field(
                name="__**Application Process**__",
                value=self.application_process.value,
                inline=False,
            )
            embed.add_field(
                name="__**Current Member Count**__",
                value=self.member_count,
                inline=True,
            )
            embed.add_field(
                name="__**Age of Community**__",
                value=self.community_duration,
                inline=True,
            )
            embed.add_field(
                name="__**Age of Current World**__",
                value=self.world_duration,
                inline=True,
            )
            embed.add_field(
                name="__**Reset Schedule**__", value=self.reset_schedule, inline=True
            )
            embed.add_field(
                name="__**Foreseeable Future**__",
                value=self.foreseeable_future.value,
                inline=True,
            )
            embed.add_field(
                name="__**Admin Team**__", value=self.admin_team.value, inline=False
            )
            embed.add_field(
                name="__**Reaction Codes**__",
                value="React with 💚 for Approved, 💛 for More Time, ❤️ for Rejected",
                inline=False,
            )
            embed.set_footer(
                text=f"Realm Application #{self.realm_name} | Submitted on {datetime.now().strftime('%Y-%m-%d')}"
            )
            return embed

    return ApplyForNewRealmForm()


class RealmCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    RC = app_commands.Group(
        name="Realm Channel", description="Realm/Server channel commands."
    )

    @RC.command(
        name="Create Realm Channel",
        description="Create a new realm via an application.",
    )
    @app_commands.describe(
        app_number="Application number that corresponds with the realm you're trying to create."
    )
    @slash_is_bot_admin_3
    async def create_realm(self, interaction: discord.Interaction, app_number: int):
        await interaction.response.defer(thinking=True)
        # Status set to null
        role_create = "FALSE"
        channel_create = "FALSE"
        role_given = "FALSE"
        channel_permissions = "FALSE"
        DMStatus = "FALSE"
        author = interaction.user
        guild = interaction.guild
        channel = interaction.channel
        color = discord.Colour(0x3498DB)

        q: database.RealmApplications = database.RealmApplications.select().where(
            database.RealmApplications.id == app_number
        )
        if not q.exists():
            return await interaction.followup.send(
                content="That application does not exist."
            )
        else:
            q = q.get()

        # Realm OP Role
        role = await guild.create_role(
            name=f"{q.realm_name} OP", color=color, mentionable=True
        )
        role_create = "DONE"

        # category = discord.utils.get(guild.categories, name = "Realm Channels List Test")

        # Channel Create
        category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")
        channel = await category.create_text_channel(q.realm_name + "-" + q.emoji)

        # Welcome Message
        welcomeEM = discord.Embed(
            title="Welcome to the MRP!",
            description=f"{role.mention} **Welcome to the MRP!** \n Your channel has been created and you should have gotten a DM regarding some stuff about your channel! \n If you have any questions, feel free to DM an Admin or a Moderator!",
            color=0x4C594B,
        )
        await channel.send(embed=welcomeEM)
        await channel.edit(
            topic="The newest Realm on the Minecraft Realm Portal, Check it out and chat with the owners for more Realm information. \n \n ]]Realm: Survival Multiplayer[["
        )
        channel_create = "DONE"

        # Role
        user = await interaction.guild.fetch_member(q.discord_id)
        await user.add_roles(role)
        role_given = "DONE"

        # Channel Permissions
        perms = channel.overwrites_for(role)
        perms.manage_channels = True
        perms.manage_webhooks = True
        perms.manage_messages = True
        await channel.set_permissions(
            role, overwrite=perms, reason="Created New Realm! (RealmOP)"
        )

        Muted = discord.utils.get(interaction.guild.roles, name="muted")
        permsM = channel.overwrites_for(Muted)
        permsM.read_messages = False
        permsM.send_messages = False
        await channel.set_permissions(
            Muted, overwrite=permsM, reason="Created New Realm! (Muted)"
        )

        # This try statement is here incase we are testing this in the testing server as this channel does not appear in that server!
        if interaction.guild.id == 587495640502763521:
            channelrr = guild.get_channel(683454087206928435)
            await channelrr.send(
                role.mention
                + "\n **Please agree to the rules to gain access to the Realm Owner Chats!**"
            )
            perms12 = channelrr.overwrites_for(role)
            perms12.read_messages = True
            await channelrr.set_permissions(
                role, overwrite=perms12, reason="Created New Realm!"
            )

        channel_permissions = "DONE"
        # await channel.set_permissions(Muted, overwrite=permsM)
        DMStatus = "FAILED"
        embed = discord.Embed(
            title="Congrats On Your New Realm Channel!",
            description="Your new channel: <#" + str(channel.id) + ">",
            color=0x42F5BC,
        )
        embed.add_field(
            name="Information",
            value="Enjoy your new channel. Use this channel to advertise your realm, and engage the community. The more active a channel the more likely people will be to stop by and check you out. You have moderation privileges in your channel. You can change the description, pin messages, and delete messages. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules. If you would like to add an OP to your team, in your channel type: \n```>addOP @newOP @reamlrole``` \n",
            inline=True,
        )
        embed.add_field(
            name="Realm Information Embed",
            value="In order to have your Realm listed in #realm-channels-info, please do not remove the ]]Realm: Survival Multiplayer[[ portion of your channel description. Feel free to edit this in the following way ]]Anything You Want To Show Up After Your Realm Name: Short Description Of Your Realm[[. ",
            inline=True,
        )
        embed.add_field(
            name="Questions",
            value="Thanks for joining the Portal, and if you have any questions contact an Admin or a Moderator!",
            inline=True,
        )
        embed.set_thumbnail(url=user.avatar.url)
        try:
            await user.send(embed=embed)
            DMStatus = "DONE"

        finally:
            embed = discord.Embed(
                title="Realm Channel Output",
                description="Realm Requested by: " + author.mention,
                color=0x38EBEB,
            )
            embed.add_field(
                name="**Console Logs**",
                value="**Role Created:** "
                + role_create
                + " -> "
                + role.mention
                + "\n**Channel Created:** "
                + channel_create
                + " -> <#"
                + str(channel.id)
                + ">\n**Role Given:** "
                + role_given
                + "\n**Channel Permissions:** "
                + channel_permissions
                + "\n**DMStatus:** "
                + DMStatus,
            )
            embed.set_footer(text="The command has finished all of its tasks")
            embed.set_thumbnail(url=user.avatar.url)
            await interaction.followup.send(embed=embed)

    @RC.command()
    @slash_check_MRP
    @slash_is_bot_admin_3
    async def newrealm2(self, ctx, realm, emoji, user: discord.Member):
        # Status set to null
        RoleCreate = "FALSE"
        ChannelCreate = "FALSE"
        RoleGiven = "FALSE"
        ChannelPermissions = "FALSE"
        DMStatus = "FALSE"
        author = ctx.message.author
        guild = ctx.message.guild
        channel = ctx.message.channel
        color = discord.Colour(0x3498DB)

        # Realm OP Role
        role = await guild.create_role(
            name=realm + " OP", color=color, mentionable=True
        )
        RoleCreate = "DONE"

        # category = discord.utils.get(guild.categories, name = "Realm Channels List Test")

        # Channel Create
        category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")
        channel = await category.create_text_channel(realm + "-" + emoji)

        # Welcome Message
        welcomeEM = discord.Embed(
            title="Welcome to the MRP!",
            description=f"{role.mention} **Welcome to the MRP!** \n Your channel has been created and you should have gotten a DM regarding some stuff about your channel! \n If you have any questions, feel free to DM an Admin or a Moderator!",
            color=0x4C594B,
        )
        await channel.send(embed=welcomeEM)
        await channel.edit(
            topic="The newest Realm on the Minecraft Realm Portal, Check it out and chat with the owners for more Realm information. \n \n ]]Realm: Survival Multiplayer[["
        )
        ChannelCreate = "DONE"

        # Role
        await user.add_roles(role)
        RoleGiven = "DONE"

        # Channel Permissions
        perms = channel.overwrites_for(role)
        perms.manage_channels = True
        perms.manage_webhooks = True
        perms.manage_messages = True
        await channel.set_permissions(
            role, overwrite=perms, reason="Created New Realm! (RealmOP)"
        )

        Muted = discord.utils.get(ctx.guild.roles, name="muted")
        permsM = channel.overwrites_for(Muted)
        permsM.read_messages = False
        permsM.send_messages = False
        await channel.set_permissions(
            Muted, overwrite=permsM, reason="Created New Realm! (Muted)"
        )

        # This try statement is here incase we are testing this in the testing server as this channel does not appear in that server!
        if ctx.guild.id == 587495640502763521:
            channelrr = guild.get_channel(683454087206928435)
            await channelrr.send(
                role.mention
                + "\n **Please agree to the rules to gain access to the Realm Owner Chats!**"
            )
            perms12 = channelrr.overwrites_for(role)
            perms12.read_messages = True
            await channelrr.set_permissions(
                role, overwrite=perms12, reason="Created New Realm!"
            )

        ChannelPermissions = "DONE"
        # await channel.set_permissions(Muted, overwrite=permsM)
        DMStatus = "FAILED"
        embed = discord.Embed(
            title="Congrats On Your New Realm Channel!",
            description="Your new channel: <#" + str(channel.id) + ">",
            color=0x42F5BC,
        )
        embed.add_field(
            name="Information",
            value="Enjoy your new channel. Use this channel to advertise your realm, and engage the community. The more active a channel the more likely people will be to stop by and check you out. You have moderation privileges in your channel. You can change the description, pin messages, and delete messages. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules. If you would like to add an OP to your team, in your channel type: \n```>addOP @newOP @reamlrole``` \n",
            inline=True,
        )
        embed.add_field(
            name="Realm Information Embed",
            value="In order to have your Realm listed in #realm-channels-info, please do not remove the ]]Realm: Survival Multiplayer[[ portion of your channel description. Feel free to edit this in the following way ]]Anything You Want To Show Up After Your Realm Name: Short Description Of Your Realm[[. ",
            inline=True,
        )
        embed.add_field(
            name="Questions",
            value="Thanks for joining the Portal, and if you have any questions contact an Admin or a Moderator!",
            inline=True,
        )
        embed.set_thumbnail(url=user.avatar.url)
        try:
            await user.send(embed=embed)
            DMStatus = "DONE"

        finally:
            embed = discord.Embed(
                title="Realm Channel Output",
                description="Realm Requested by: " + author.mention,
                color=0x38EBEB,
            )
            embed.add_field(
                name="**Console Logs**",
                value="**Role Created:** "
                + RoleCreate
                + " -> "
                + role.mention
                + "\n**Channel Created:** "
                + ChannelCreate
                + " -> <#"
                + str(channel.id)
                + ">\n**Role Given:** "
                + RoleGiven
                + "\n**Channel Permissions:** "
                + ChannelPermissions
                + "\n**DMStatus:** "
                + DMStatus,
            )
            embed.set_footer(text="The command has finished all of its tasks")
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)

    @app_commands.command(
        description="Looking to get your channel here? Apply for it here!"
    )
    @app_commands.describe(
        realm_name="The name of your realm",
        emoji="The emoji you want to represent your realm",
        type_of_realm="The type of realm you are applying for",
        member_count="The amount of members you have in your realm",
        community_duration="How long your realm has been around",
        world_duration="How long your current world has been around",
        reset_schedule="How often your world resets",
    )
    async def apply_for_a_realm(
        self,
        interaction: discord.Interaction,
        realm_name: str,
        emoji: str,
        type_of_realm: Literal["realm", "server"],
        member_count: int,
        community_duration: str,
        world_duration: str,
        reset_schedule: str,
    ):
        author = interaction.user
        JustSpawnedCheck = discord.utils.get(
            interaction.guild.roles, name="Just Spawned"
        )
        ChickenPluckerCheck = discord.utils.get(
            interaction.guild.roles, name="Chicken Plucker"
        )
        if JustSpawnedCheck in author.roles or ChickenPluckerCheck in author.roles:
            embed = discord.Embed(
                title="Not Enough Experience",
                description="`Zombie Slayer`+ is required to apply for a realm.",
                color=0xFC0B03,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        view = return_applyfornewrealm_modal(
            self.bot,
            realm_name,
            type_of_realm,
            emoji,
            str(member_count),
            community_duration,
            world_duration,
            reset_schedule,
        )
        await interaction.response.send_modal(view=view)


async def setup(bot):
    await bot.add_cog(RealmCMD(bot))
