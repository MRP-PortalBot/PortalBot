from logging import exception
import discord
from discord.ext import commands
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from core.common import load_config
config, _ = load_config()
i = 1
time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
import logging
logger = logging.getLogger(__name__)

# -------------------------------------------------------

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

sheet = client.open(
    "Minecraft Realm Portal Channel Application (Responses)").sheet1

sheet2 = client.open("MRPCommunityRealmApp").sheet1
# -------------------------------------------------------

def check_MRP():
    def predicate(ctx):
        return ctx.message.guild.id == 587495640502763521 or ctx.message.guild.id == 448488274562908170
    return commands.check(predicate)


def check_MGP():
    def predicate(ctx):
        return ctx.message.guild.id == 192052103017922567 or ctx.message.guild.id == 448488274562908170
    return commands.check(predicate)

def convert(time):
    try:
        return int(time[:-1]) * time_convert[time[-1]]
    except:
        return time


class RealmCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("RealmCMD: Cog Loaded!")

    @commands.command()
    @check_MRP()
    @commands.has_permissions(manage_roles=True)
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

        #Realm OP Role
        role = await guild.create_role(name=realm + " OP", color=color, mentionable=True)
        RoleCreate = "DONE"

        #category = discord.utils.get(guild.categories, name = "Realm Channels List Test")

        #Channel Create
        category = discord.utils.get(guild.categories, name="🎮 Realms & Servers")
        channel = await category.create_text_channel(realm + "-" + emoji)

        #Welcome Message
        welcomeEM = discord.Embed(title = "Welcome to the MRP!", description = f"{role.mention} **Welcome to the MRP!** \n Your channel has been created and you should have gotten a DM regarding some stuff about your channel! \n If you have any questions, feel free to DM an Admin or a Moderator!", color = 0x4c594b)
        await channel.send(embed = welcomeEM)
        await channel.edit(topic="The newest Realm on the Minecraft Realm Portal, Check it out and chat with the owners for more Realm information. \n \n ]]Realm: Survival Multiplayer[[")
        ChannelCreate = "DONE"

        #Role
        await user.add_roles(role)
        RoleGiven = "DONE"

        #Channel Permissions
        perms = channel.overwrites_for(role)
        perms.manage_channels = True
        perms.manage_webhooks = True
        perms.manage_messages = True
        await channel.set_permissions(role, overwrite=perms, reason="Created New Realm! (RealmOP)")

        Muted = discord.utils.get(ctx.guild.roles, name="muted")
        permsM = channel.overwrites_for(Muted)
        permsM.read_messages = False
        permsM.send_messages = False
        await channel.set_permissions(Muted, overwrite=permsM, reason="Created New Realm! (Muted)")

        # This try statement is here incase we are testing this in the testing server as this channel does not appear in that server!
        if ctx.guild.id == 587495640502763521:
            channelrr = guild.get_channel(683454087206928435)
            print(channelrr)
            await channelrr.send(role.mention + "\n **Please agree to the rules to gain access to the Realm Owner Chats!**")
            perms12 = channelrr.overwrites_for(role)
            perms12.read_messages = True
            await channelrr.set_permissions(role, overwrite=perms12, reason="Created New Realm!")

        ChannelPermissions = "DONE"
        #await channel.set_permissions(Muted, overwrite=permsM)
        DMStatus = "FAILED"
        embed = discord.Embed(title="Congrats On Your New Realm Channel!",description="Your new channel: <#" + str(channel.id) + ">", color=0x42f5bc)
        embed.add_field(name="Information", value="Enjoy your new channel. Use this channel to advertise your realm, and engage the community. The more active a channel the more likely people will be to stop by and check you out. You have moderation privileges in your channel. You can change the description, pin messages, and delete messages. You now have access to the Realm Owner Chats. Before they will be fully unlocked you will need to agree to the rules in #realm-op-rules. If you would like to add an OP to your team, in your channel type: \n```>addOP @newOP @reamlrole``` \n", inline = True)
        embed.add_field(name="Realm Information Embed",value="In order to have your Realm listed in #realm-channels-info, please do not remove the ]]Realm: Survival Multiplayer[[ portion of your channel description. Feel free to edit this in the following way ]]Anything You Want To Show Up After Your Realm Name: Short Description Of Your Realm[[. ", inline = True)
        embed.add_field(name="Questions", value="Thanks for joining the Portal, and if you have any questions contact an Admin or a Moderator!", inline = True)
        embed.set_thumbnail(url = user.avatar_url)
        try:
            await user.send(embed=embed)
            DMStatus = "DONE"            

        finally:
            embed = discord.Embed(title="Realm Channel Output", description="Realm Requested by: " + author.mention, color=0x38ebeb)
            embed.add_field(name="**Console Logs**", value="**Role Created:** " + RoleCreate + " -> " + role.mention + "\n**Channel Created:** " + ChannelCreate +" -> <#" + str(channel.id) + ">\n**Role Given:** " + RoleGiven + "\n**Channel Permissions:** " + ChannelPermissions + "\n**DMStatus:** " + DMStatus)
            embed.set_footer(text = "The command has finished all of its tasks")
            embed.set_thumbnail(url = user.avatar_url)
            await ctx.send(embed=embed)

    @newrealm.error
    async def newrealm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Uh oh, looks like I can't execute this command because you don't have permissions!")

        if isinstance(error, commands.TooManyArguments):
            await ctx.send("You sent too many arguments! Did you use quotes for realm names over 2 words?")

        if isinstance(error, commands.CheckFailure):
            await ctx.send("This Command was not designed for this server!")

        elif isinstance(error, commands.BadArgument):
            await ctx.send("You didn't include all of the arguments!")
        
        else:
            raise error

    @commands.command()
    @check_MRP()
    async def checkin2(self, ctx):
        # 28
        em = discord.Embed(
            title="Realm Checkin", description="Please react with your Realm Emoji to checkin for the month!\n======================================================")
        em.add_field(name="Page 1/2", value="77th Combine - 🚜\n"
                     "Accelerated Survival - 🌎\n"
                     "Altered Reality - ⚜️\n"
                     "Aurafall - 💀\n"
                     "Bigbraincraft - 🧠\n"
                     "Biomecraft - 🌄\n"
                     "Bovinia - 👑\n"
                     "Brokerock - 💎\n"
                     "Coastal Craft - ☸️\n"
                     "Codename Electrify - ⚡️\n"
                     "Crimson Isles - 🍂\n"
                     "Dragons Keep - 🐲\n"
                     "Evercraft - ⏳\n"
                     "Evilcraft - 👹\n"
                     )

        msg = await ctx.send(embed=em)
        reactions = ['🚜', '🌎', '⚜️', '💀', '🧠', '🌄',
                     '👑', '💎', '☸️', '⚡', '🍂', '🐲', '⏳', '👹']
        for emoji in reactions:
            await msg.add_reaction(emoji)
            time.sleep(3)
        # Part2
        em = discord.Embed(
            title="Realm Checkin", description="Please react with your Realm Emoji to checkin for the month!\n======================================================")
        em.add_field(name="Page 2/2", value="Fortressworld - 🐉\n"
                     "Fresh Start - 🍃\n"
                     "Genesis - 🌱\n"
                     "Hals Crafters - 🌞\n"
                     "Industrious Inc - 🏭\n"
                     "Kingdoms Realm - 🏰\n"
                     "Mistical Darkness - 🌑\n"
                     "Oakridge - 🌳\n"
                     "Phantom Smp - 👻\n"
                     "Rage Craft Room - 😡\n"
                     "Slownerd Bedrock Paradise - 🐢\n"
                     "Tiny World - 🔬\n"
                     "World Traveling - 🛸\n"
                     "Xencraft - 🌹\n"
                     "Guest OP - 👀"
                     )
        msg = await ctx.send(embed=em)
        reactions = ['🐉', '🍃', '🌱', '🌞', '🏭', '🏰', '🌑',
                     '🌳', '👻', '😡', '🐢', '🔬', '🛸', '🌹', '👀']
        for emoji in reactions:
            await msg.add_reaction(emoji)
            time.sleep(3)

    @commands.command()
    @check_MRP()
    async def applyrealm(self, ctx):
        # Prior defines
        timestamp = datetime.now()
        channel2 = ctx.message.channel
        author = ctx.message.author
        channel = await ctx.author.create_dm()
        guild = ctx.message.guild
        responseChannel = self.bot.get_channel(config['realmChannelResponse'])
        admin = discord.utils.get(
            ctx.guild.roles, name="Admin")

        # Elgibilty Checks
        '''
    Channel Check
    '''
        if channel2.name != "bot-spam":
            await ctx.channel.purge(limit=1)
            noGoAway = discord.Embed(title="Woah Woah Woah, Slow Down There Buddy!",
                                     description="Please switch to #bot-spam! This command is not allowed to be used here.", color=0xfc0b03)
            await ctx.send(embed=noGoAway, delete_after=6)
            return

        '''
    Level Check
    '''
        JustSpawnedCheck = discord.utils.get(
            ctx.guild.roles, name="Just Spawned")
        SpiderSniperCheck = discord.utils.get(
            ctx.guild.roles, name="Spider Sniper")
        if JustSpawnedCheck in author.roles or SpiderSniperCheck in author.roles:
            noGoAway = discord.Embed(title="Woah Woah Woah, Slow Down There Buddy!",
                                     description="I appreciate you trying to apply towards a new channel here but you must have the `Zombie Slayer` role or have surpassed this role! \n*Please try again when you have reached this role.*", color=0xfc0b03)
            await ctx.send(embed=noGoAway)
            return

        await ctx.send("Please check your DMs!")

        # Answer Check
        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user

        # Questions
        introem = discord.Embed(title="Realm Channel Application", description="Hello! Please make sure you fill every question with a good amount of detail and if at any point you feel like you made a mistake, you will see a cancel reaction at the end. Then you can come back and re-answer your questions! \n**Questions will start in 5 seconds.**", color=0x42f5f5)
        await channel.send(embed=introem)
        time.sleep(5)
        await channel.send("Your Community's name?")
        answer1 = await self.bot.wait_for('message', check=check)

        await channel.send("Realm or Server?")
        answer2 = await self.bot.wait_for('message', check=check)

        await channel.send("Emoji you want to use?")
        answer3 = await self.bot.wait_for('message', check=check)

        await channel.send("Short description for the Realm list?")
        answer4 = await self.bot.wait_for('message', check=check)

        await channel.send("Long description for your channel description?")
        answer5 = await self.bot.wait_for('message', check=check)

        await channel.send("What is your application proccess for your community?")
        answer6 = await self.bot.wait_for('message', check=check)

        await channel.send("How many members does your community have?")
        answer7 = await self.bot.wait_for('message', check=check)

        await channel.send("How long has your community been active?")
        answer8 = await self.bot.wait_for('message', check=check)

        await channel.send("How long has your current Minecraft World been active?")
        answer9 = await self.bot.wait_for('message', check=check)

        await channel.send("How often do you reset your World?")
        answer10 = await self.bot.wait_for('message', check=check)

        await channel.send("Will your Realm/Server have the ability to continue for the foreseeable future?")
        answer11 = await self.bot.wait_for('message', check=check)

        await channel.send("List the members of your OP team, and how long each has been an OP.")
        answer12 = await self.bot.wait_for('message', check=check)

        message = await channel.send("**That's it!**\n\nReady to submit?\n✅ - SUBMIT\n❌ - CANCEL\n*You have 300 seconds to react, otherwise the application will automatically cancel. ")
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check2)

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")

        else:
            if str(reaction.emoji) == "✅":
                await ctx.send("Standby...")
                await message.delete()
            else:
                await ctx.send("Ended Application...")
                await message.delete()
                return

        submittime = timestamp.strftime("%m/%d/%Y %H:%M:%S")
        entryID = (int(sheet.acell('A3').value)+1)
        print(entryID)
        owner = (author.name + '#' + author.discriminator)
        #

        # Spreadsheet Data
        row = [entryID, answer1.content, answer2.content, answer3.content, str(owner), answer4.content,
               answer5.content, answer6.content, answer7.content, answer8.content, answer9.content, answer10.content, answer11.content, answer12.content,submittime]
        sheet.insert_row(row, 3, value_input_option='USER_ENTERED')

        # Actual Embed with Responses
        embed = discord.Embed(title="Realm Application", description="__**Realm Owner:**__\n" +
                              author.mention + "\n============================================", color=0xb10d9f)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png")
        embed.add_field(name="__**Realm Name**__",
                        value=str(answer1.content), inline=True)
        embed.add_field(name="__**Realm or Server?**__",
                        value=str(answer2.content), inline=True)
        embed.add_field(name="__**Emoji**__",
                        value=str(answer3.content), inline=True)
        embed.add_field(name="__**Short Description**__",
                        value=str(answer4.content), inline=False)
        embed.add_field(name="__**Long Description**__",
                        value=str(answer5.content), inline=False)
        embed.add_field(name="__**Application Process**__",
                        value=str(answer6.content), inline=False)
        embed.add_field(name="__**Current Member Count**__",
                        value=str(answer7.content), inline=True)
        embed.add_field(name="__**Age of Community**__",
                        value=str(answer8.content), inline=True)
        embed.add_field(name="__**Age of Current World**__",
                        value=str(answer9.content), inline=True)
        embed.add_field(name="__**How often do you reset**__",
                        value=str(answer10.content), inline=True)
        embed.add_field(name="__**Will your Realm/Server have the ability to continue for the foreseeable future?**__",
                        value=str(answer11.content), inline=True)
        embed.add_field(name="__**Members of the OP Team, and How long they have been an OP**__",
                        value=str(answer12.content), inline=False)
        embed.add_field(name="__**Reaction Codes**__",
                        value="Please react with the following codes to show your thoughts on this applicant.", inline=False)
        embed.add_field(name="----💚----", value="Approved", inline=True)
        embed.add_field(name="----💛----",
                        value="More Time in Server", inline=True)
        embed.add_field(name="----❤️----", value="Rejected", inline=True)
        embed.set_footer(text="Realm Application #" + str(entryID) + " | " + submittime)
        await responseChannel.send(admin.mention)
        msg = await responseChannel.send(embed=embed)

        # Reaction Appending
        reactions = ['💚', '💛', '❤️']
        for emoji in reactions:
            await msg.add_reaction(emoji)

        # Confirmation
        response = discord.Embed(
            title="Success!", description="I have sent in your application, you will hear back if you have passed!", color=0x03fc28)
        await channel.send(embed=response)

    @applyrealm.error
    async def applyrealm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Uh oh, looks like I can't execute this command because you don't have permissions!")

        if isinstance(error, commands.TooManyArguments):
            await ctx.send("You sent too many arguments! Did you use quotes for realm names over 2 words?")

        if isinstance(error, commands.CheckFailure):
            await ctx.send("This Command was not designed for this server!")

        else:
            raise error 
    
    @commands.command()
    @check_MRP()
    async def applymrpcr(self ,ctx):
        timestamp = datetime.now()
        channel2 = ctx.message.channel
        author = ctx.message.author
        channel = await ctx.author.create_dm()
        guild = ctx.message.guild
        responseChannel = self.bot.get_channel(config['realmApplyResponse'])

        # Elgibilty Checks
        '''
    Channel Check
    '''
        if channel2.name != "bot-spam":
            await ctx.channel.purge(limit=1)
            noGoAway = discord.Embed(title="Woah Woah Woah, Slow Down There Buddy!",
                                     description="Please switch to #bot-spam! This command is not allowed to be used here.", color=0xfc0b03)
            await ctx.send(embed=noGoAway, delete_after=6)
            return

        '''
    Level Check
    '''
        JustSpawnedCheck = discord.utils.get(
            ctx.guild.roles, name="Just Spawned")
        SpiderSniperCheck = discord.utils.get(
            ctx.guild.roles, name="Spider Sniper")
        if JustSpawnedCheck in author.roles or SpiderSniperCheck in author.roles:
            noGoAway = discord.Embed(title="Woah Woah Woah, Slow Down There Buddy!",
                                     description="I appreciate you trying to apply towards MRPCR here but you must have the `Zombie Slayer` role or have surpassed this role! \n*Please try again when you have reached this role.*", color=0xfc0b03)
            await ctx.send(embed=noGoAway)
            return

        await ctx.send("Please check your DMs!")

        # Answer Check
        def check(m):
            return m.content is not None and m.channel == channel and m.author is not self.bot.user
        
        intro = discord.Embed(title="MRPCR Realm Application", description="Hello! Please make sure you fill every question with a good amount of detail and if at any point you feel like you made a mistake, you will see a cancel reaction at the end. Then you can come back and re-answer your questions! \n**Questions will start in 5 seconds.**", color=0x42f5f5)
        await channel.send(embed=intro)
        time.sleep(5)

        answer1 = str(author.name) + "#" + str(author.discriminator)
        answer2 = str(author.id)

        await channel.send("Gamertag:")
        answer3 = await self.bot.wait_for('message', check=check)

        await channel.send("Age:")
        answer4= await self.bot.wait_for('message', check=check)

        await channel.send("Tell us about yourself and what you love about Minecraft.")
        answer5 = await self.bot.wait_for('message', check=check)

        message = await channel.send("**That's it!**\n\nReady to submit?\n✅ - SUBMIT\n❌ - CANCEL\n*You have 300 seconds to react, otherwise the application will automatically cancel.* ")
        reactions = ['✅', '❌']
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check2(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check2)

        except asyncio.TimeoutError:
            await channel.send("Looks like you didn't react in time, please try again later!")

        else:
            if str(reaction.emoji) == "✅":
                await ctx.send("Standby...")
                await message.delete()
            else:
                await ctx.send("Ended Application...")
                await message.delete()
                return

        submittime = str(timestamp.strftime(r"%x"))

        # Spreadsheet Data
        row = [answer1.content, answer2.content, answer3.content, answer4.content, answer5.content,submittime]
        sheet2.insert_row(row, 2)

        # Actual Embed with Responses
        embed = discord.Embed(title="New MRPCR Application!", description="Response turned in by: " +
                              author.mention, color=0x03fc28)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/588034623993413662/588413853667426315/Portal_Design.png")
        embed.add_field(name="__**Discord Name:**__",value=str(answer1.content), inline=True)
        embed.add_field(name="__**Gamertag:**__",value=str(answer2.content), inline=True)
        embed.add_field(name="__**Age:**__", value=str(answer3.content), inline=False)
        embed.add_field(name="__**Tell us about yourself and what you love about Minecraft.**__", value=str(answer4.content), inline=False)
        embed.add_field(name = "__**Timestamp:**__", value = str(timestamp.strftime(r"%x")))

        embed.add_field(name="__**Reaction Codes**__",value="Please react with the following codes to show your thoughts on this applicant.", inline=False)
        embed.add_field(name="----💚----", value="Approved", inline=True)
        embed.add_field(name="----💛----",value="More Time in Server", inline=True)
        embed.add_field(name="----❤️----", value="Rejected", inline=True)
        embed.set_footer(text="Realm Application | " + submittime)
        msg = await responseChannel.send(embed=embed)

        # Reaction Appending
        reactions = ['💚', '💛', '❤️']
        for emoji in reactions:
            await msg.add_reaction(emoji)

        # Confirmation
        response = discord.Embed(
            title="Success!", description="I have sent in your application, you will hear back if you have passed!", color=0x03fc28)
        await channel.send(embed=response)




def setup(bot):
    bot.add_cog(RealmCMD(bot))
