import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash import SlashCommand
from discord_slash import SlashContext
from discord_slash.utils import manage_commands
import time

class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            # Creates new SlashCommand instance to bot if bot doesn't have.
            bot.slash = SlashCommand(bot, override_type=True)
        self.bot = bot
        self.bot.slash.get_cog_commands(self)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)


    @cog_ext.cog_slash(name="say", description = "Iterates something as the bot!", guild_ids=[448488274562908170], options=[manage_commands.create_option(name = "phrase" , description = "Phrase to reiterate", option_type = 3, required = True)])
    async def say(self, ctx, phrase=None):
        #await ctx.channel.purge(limit=1)
        print(ctx)
        await ctx.send(content = phrase)

    @cog_ext.cog_slash(name="newrealm", description = "Creates a new realm!",guild_ids=[448488274562908170], options=[manage_commands.create_option(name = "realm" , description = "The Realm's Name", option_type = 3, required = True), manage_commands.create_option(name = "emoji" , description = "Realms Emoji", option_type = 3, required = True), manage_commands.create_option(name = "realm_owner" , description = "Realm's Owner", option_type = 6, required = True)])
    #@commands.command()
    #@commands.has_permissions(manage_roles=True)
    async def newrealm(self, ctx, realm, emoji,  user: discord.Member):
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
        role = await guild.create_role(name=realm + " OP", color=color, mentionable=True)
        RoleCreate = "DONE"
        #category = discord.utils.get(guild.categories, name = "Realm Channels List Test")
        category = discord.utils.get(
            guild.categories, name="🎮 Realms & Servers")
        channel = await category.create_text_channel(realm + "-" + emoji)
        await channel.send(role.mention + " **Welcome to the MRP!** \n Your channel has been created and you should have gotten a DM regarding some stuff about your channel! \n If you have any questions, feel free to DM an Admin or a Moderator! ")
        await channel.edit(topic="The newest Realm on the Minecraft Realm Portal, Check it out and chat with the owners for more Realm information. \n \n ]]Realm: Survival Multiplayer[[")
        ChannelCreate = "DONE"
        await user.add_roles(role)
        RoleGiven = "DONE"
        perms = channel.overwrites_for(role)
        perms.manage_channels = True
        perms.manage_webhooks = True
        perms.manage_messages = True
        await channel.set_permissions(role, overwrite=perms, reason="Created New Realm!")

        # This try statement is here incase we are testing this in the testing server as this channel does not appear in that server!
        try:
            channelrr = guild.get_channel(683454087206928435)
            await channelrr.send(role.mention + "\n **Please agree to the rules to gain access to the Realm Owner Chats!**")
            perms12 = channelrr.overwrites_for(role)
            perms12.read_messages = True
        finally:
            Muted = discord.utils.get(ctx.guild.roles, name="Muted")
            permsM = channel.overwrites_for(Muted)
            permsM.read_messages = False
            permsM.send_messages = False
            ChannelPermissions = "DONE"
            await channel.set_permissions(Muted, overwrite=permsM)
            try:
                embed = discord.Embed(title="Congrats On Your New Realm Channel!",
                                      description="Your new channel: <#" + channel.id + ">", color=0x42f5bc)
                embed.add_field(name="Information", value="Enjoy your new channel. Use this channel to advertise your realm, and engage the community. The more active a channel the more likely people will be to stop by and check you out. You have moderation privileges in your channel. You can change the description, pin messages, and delete messages. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules. If you would like to add an OP to your team, in your channel type: \n```>addOP @newOP @reamlrole``` \n")
                embed.add_field(name="Realm Information Embed",
                                value="In order to have your Realm listed in #realm-channels-info, please do not remove the ]]Realm: Survival Multiplayer[[ portion of your channel description. Feel free to edit this in the following way ]]Anything You Want To Show Up After Your Realm Name: Short Description Of Your Realm[[. ")
                embed.add_field(
                    name="Questions", value="Thanks for joining the Portal, and if you have any questions contact an Admin or a Moderator!")
                await user.send(embed=[embed])
            except:
                await ctx.send("Uh oh, something went wrong while trying to DM the Realm Owner. \n`Error: Discord Forbidden (User's Privacy Settings Prevented the DM Message)`")
                await ctx.send("DM Status: **FAILED**")
                DMStatus = "FAILED"
            else:
                DMStatus = "DONE"
            finally:
                await ctx.send("**The command has finished all of its tasks.**\n> *If there was an error with anything, you should see the status for that specific argument.*")
                time.sleep(2)
                # Variables:
                '''
        RoleCreate = "FALSE"
        ChannelCreate = "FALSE"
        RoleGiven = "FALSE"
        ChannelPermissions = "FALSE"
        DMStatus = "FALSE"
        '''
                embed = discord.Embed(
                    title="Realm Channel Output", description="Realm Requested by: " + author.mention, color=0x38ebeb)
                embed.add_field(name="**Console Logs**", value="**Role Created:** " + RoleCreate + " : " + role.mention + "\n**Channel Created:** " + ChannelCreate +
                                " : <#" + channel.id + ">\n**Role Given:** " + RoleGiven + "\n**Channel Permissions:** " + ChannelPermissions + "\n**DMStatus:** " + DMStatus)
                await ctx.send(embed=[embed])



def setup(bot):
    bot.add_cog(Slash(bot))