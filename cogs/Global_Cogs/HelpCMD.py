import discord
from discord.ext import commands
from datetime import datetime
import core.common
import logging

logger = logging.getLogger(__name__)

class HelpCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpCMD: Cog Loaded!")

    # Help Command
    @commands.command()
    async def help(self, ctx):
        author = ctx.message.author
        guild = ctx.message.guild
        RealmOP = discord.utils.find(lambda r: r.name == 'Realm OP', ctx.message.guild.roles)
        Moderator = discord.utils.find(lambda r: r.name == 'Moderator', ctx.message.guild.roles)

        embed = discord.Embed(title = "Help Commands", description = "Every PortalBot Command!", color = 0xffd700)
        embed.add_field(name = "Misc Commands", value = "[Misc Documentation](https://www.notion.so/Misc-Commands-ee70d925c3474749b6415a169f3b2ac4)")
        embed.add_field(name = "Profile/Gamertag Commands", value = '[Profile/Gamertag Documentation](https://www.notion.so/Profile-Gamertag-Commands-d5e0debd59fc4cb3a6a2bed5cbd3a39b)', inline = False)
        embed.add_field(name = "Music Commands", value = '[Music Documentation](https://www.notion.so/Music-Commands-e6e2ccd03b694ebe96bb130fda966656)', inline = False)
        embed.add_field(name = "Application Commands", value = '[Application Documentation](https://www.notion.so/Application-Commands-2aabe7f7bcac45feb788c2ad8092d908)')
        embed.add_field(name = "Dailyq Commands", value = '[Daily Question Documentation](https://www.notion.so/Daily-Question-Commands-5226b3c698c94593a72543efad24ad82)', inline = False)
        embed.add_field(name = "Bug Reporting", value = '[Bug Reporting Documentation](https://www.notion.so/Bug-Reporting-0e7ea86e881646a4984dbb9e7762329d)', inline = False)

    
        if RealmOP in author.roles:
            embed.add_field(name = "Realm OP Commands", value = '[Realm OP Documentation](https://www.notion.so/Realm-Operator-Commands-62e80e2232434407a2099f782c54189c)')
            embed.add_field(name = "Blacklist Commands", value = '[Blacklist Documentation](https://www.notion.so/Blacklist-Commands-5293a1765f014993b64fe53cacebb005)', inline = False)
            

        elif Moderator in author.roles:
            embed.add_field(name = "Moderation Commands", value = '[Moderation Documentation](https://www.notion.so/Blacklist-Commands-5293a1765f014993b64fe53cacebb005)', inline = False)
            
        else:
            pass

        await ctx.send(embed = embed)
            

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
