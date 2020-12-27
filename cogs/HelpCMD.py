import discord
from discord.ext import commands
from datetime import datetime
import core.common


class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Help Command
    @commands.group(invoke_without_command=True)
    async def help(self, ctx):
        author = ctx.message.author
        guild = ctx.message.guild
        role = discord.utils.find(
            lambda r: r.name == 'Realm OP', ctx.message.guild.roles)
        if role in author.roles:
            embed = discord.Embed(
                title="Help", description="Commands are listed here for further help!", color=0xb10d9f)
            embed.add_field(name="=============================",
                            value="============================")
            embed.set_thumbnail(url=guild.icon_url)
            await ctx.send(embed=embed)

            embed1 = discord.Embed(title="Realm Channel Configuration \n",
                                   description="**OP Roles** \n *Add's or removes your realms OP role from someone!* \n **Usage:** >addOP/>removeOP (mention:user) (mention:OP Role) \n \n", inline=False, color=0xb10d9f)
            await ctx.send(embed=embed1)

            embed2 = discord.Embed(
                title="Misc Commands \n", description="**Ping** \n *Check's API Latency!* \n **Usage:** >ping \n \n **Uptime** \n *Check's how long the bot has been up!* \n **Usage:** >uptime \n", color=0xb10d9f)
            await ctx.send(embed=embed2)

            embed2 = discord.Embed(title="Blacklist Commands \n", description="**Blacklist** \n *Start's the Blacklist Process!* \n **Usage:** >blacklist \n \n **~~Blacklist Logs~~** \n *~~Gives every user that was blacklisted!~~* \n ~~**Usage:** >blogs~~ \n \n **Blacklist Search** \n *Check's for a specific user in the blacklist logs!* \n **Usage:** >bsearch \n \n **Gamertag Search** \n *Searches the Portal's database for a gamertag or a user!* \n *Usage:* >gtsearch \n", color=0xb10d9f)
            await ctx.send(embed=embed2)

            embed2 = discord.Embed(title="Nickname Commands \n", description="**AddEmoji** \n *Add's a realm's emoji to your nickname!* \n **Usage:** >addemoji #channel \n \n **RemoveNickname** \n *Removes your nickname!* \n **Usage:** >rememoji \n \n **Gamertag** \n *Add's your gamertag to the database! (You can also add your gamertag to your nickname) \n *Usage:* >gtadd (GAMERTAG) \n", color=0xb10d9f)
            timestamp = datetime.now()
            embed2.set_footer(text=guild.name + " | Date: " +
                              str(timestamp.strftime(r"%x")))
            await ctx.send(embed=embed2)

        else:
            embed2 = discord.Embed(
                title="Misc Commands \n", description="**Ping** \n *Check's API Latency!* \n **Usage:** >ping \n \n **Uptime** \n *Check's how long the bot has been up!* \n **Usage:** >uptime \n", color=0xb10d9f)
            await ctx.send(embed=embed2)
            embed2 = discord.Embed(title="Nickname Commands \n", description="**AddEmoji** \n *Add's a realm's emoji to your nickname!* \n **Usage:** >addemoji #channel \n \n **RemoveNickname** \n *Removes your nickname!* \n **Usage:** >rememoji \n \n **Gamertag** \n *Add's your gamertag to the database! (You can also add your gamertag to your nickname) \n *Usage:* >gtadd (GAMERTAG)", color=0xb10d9f)
            embed2.set_thumbnail(url=guild.icon_url)
            timestamp = datetime.now()
            embed2.set_footer(text=guild.name + " | Date: " +
                              str(timestamp.strftime(r"%x")))
            await ctx.send(embed=embed2)

    @help.command(aliases=["Ping", "ping"])
    async def _ping(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**PING:** Checks the bot's latency! \nUsage: **>ping**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Uptime", "uptime"])
    async def _uptime(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**UPTIME:** Checks how long the bot has been up! \nUsage: **>uptime**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Addemoji", "addemoji"])
    async def _addemoji(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**ADDEMOJI:** Add's a certain realm emoji to your nickname! \nUsage: **>addemoji #channel**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Rememoji", "rememoji"])
    async def _rememoji(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**REMEMOJI:** Reverts your nickname back to your username! \nUsage: **>rememoji**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["gtadd", "GTadd", "Gamertag", "gamertag"])
    async def _gamertag(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**GAMERTAG:** Add's your gamertag so Realm OP's can easily find/contact you! \nUsage: **>gtadd (GAMERTAG)**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Say", "say"])
    async def _say(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**SAY:** Sends a message through the bot! \nUsage: **>say (message)**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Embed", "embed"])
    async def _embed(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**EMBED:** Sends an embed through the bot! \nUsage: **>embed (channel) (color) (title) | (bottom text)", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Nick", "nick"])
    async def _nick(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**NICK:** Changes a user's nickname! \nUsage: **>nick (user:mention/id) (#realmchannel)**", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["NewRealm", "newrealm", "Newrealm"])
    async def _newrealm(self, ctx):
        em = discord.Embed(title="Help Command", description="**NEWREALM:** Creates a new realm channel! \nUsage: **>newrealm ('Realm Name') (emoji) (owner:mention/id)** \n\n**NOTE:** Please use the **(' ')** for realms that have more then *2* words!", color=0xb10d9f)
        await ctx.send(embed=em)

    @help.command(aliases=["Addop", "AddOP", "addop"])
    async def _addOP(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**ADDOP:** Add's your channels Realm OP role to someone! \nUsage: **>addOP (mention:user)**", color=0xb10d9f)
        await ctx.send(ebed=em)

    @help.command(aliases=["Removeop", "RemoveOP", "removeop"])
    async def _removeOP(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**REMOVEOP:** Removes's your channels Realm OP role to someone! \nUsage: **>removeOP (mention:user)**", color=0xb10d9f)
        await ctx.send(ebed=em)

    @help.command(aliases=["Blacklist", "blacklist"])
    async def _blacklist(self, ctx):
        em = discord.Embed(title="Help Command", description="**Blacklist:** Starts the Blacklist Process! \nUsage: **>blacklist** \n**NOTE:** The Blacklist Process will take place in your DM's so make sure the bot can DM you!", color=0xb10d9f)
        await ctx.send(ebed=em)

    @help.command(aliases=["Addq", "addq"])
    async def _addq(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**Add Question:** Add's a question to the database! \nUsage: **>addq (question)**", color=0xb10d9f)
        await ctx.send(ebed=em)

    @help.command(aliases=["Removeq", "removeq"])
    async def _removeq(self, ctx):
        em = discord.Embed(
            title="Help Command", description="**Remove Question:** Removes a question from the database! \nUsage: **>removeq (number)**", color=0xb10d9f)
        await ctx.send(ebed=em)

    @commands.command()
    @commands.has_role("Moderator")
    async def mhelp(self, ctx):
        guild = ctx.message.guild
        author = ctx.message.author
        logfile = open("commandlog.txt", "a")
        logfile.write(str(author.name) + " used MHELP \n")
        logfile.close()
        embedm = discord.Embed(title="Administrative Commands", description="**Say** \n *Sends a message through the bot!* \n **Usage:** >say (message) \n \n **Embed** \n *Sends an embed!* \n **Usage:** >embed (channel) (color) (Title) **|** (Bottom Text) \n \n **DM** \n *DM's a user!* \n **Usage:** >DM (user) (message) \n \n **Nick** \n *Add's an emoji to the users nickname!* \n **Usage:** >nick (user:mention/id) (#realmchannel) \n \n **New Realm!** \n *Creates a realm channel, roles, and overrides!* \n **Usage:** >newrealm ('Realm Name') (emoji) (owner:mention/id) \n\n**DailyQ** \n *Sends a random daily question!* \n **Usage:** >dailyq \n \n **Question Appender/Remover** \n *Modifies or adds a question!* \n **Usage:** >addq/>removeq (question or question number) \n \n **ListQ** \n *Lists all the questions in the database!* \n **Usage:** >listq", color=0xb10d9f)
        embedm.set_thumbnail(url=guild.icon_url)
        timestamp = datetime.now()
        embedm.set_footer(text=guild.name + " | Date: " +
                          str(timestamp.strftime(r"%x")))
        await ctx.send(embed=embedm)

    @commands.command()
    async def info(self, ctx):
        config, _ = core.common.load_config()
        guild = ctx.message.guild
        em = discord.Embed(
            title="PortalBot Info", description="Hello. I am PortalBot, a `Discord.py` powered bot!", color=0xffd700)
        em.add_field(name="PortalBot Owner:", value="SpaceRanger#0001")
        em.add_field(name="Python Version: ", value="3.8.6")
        em.add_field(name="Discord.py Version:", value="1.5.1")
        em.add_field(name="PortalBot Version:", value="1.3")
        em.add_field(name="Help Command:",
                     value=f"Prefix: **{config['prefix']}** | Help Command: **{config['prefix']}help** *or* **{config['prefix']}help (command)**")
        em.set_thumbnail(url=guild.icon_url)
        timestamp = datetime.now()
        em.set_footer(text=guild.name + " | Date: " +
                      str(timestamp.strftime(r"%x")))
        await ctx.send(embed=em)


# nick clear DM newrealm

def setup(bot):
    bot.add_cog(HelpCMD(bot))
