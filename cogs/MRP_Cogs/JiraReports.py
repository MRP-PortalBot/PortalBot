import discord
import logging
from discord.ext import commands
import json
import datetime
from datetime import timedelta, datetime
from jira import JIRA

options = {"server": "https://bugs.mojang.com"}
jira = JIRA(options)

class SkeletonCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bugsearch(self, ctx, *, query = None):
        x = query.upper()
        if query == None:
            await ctx.send("Hey that's not fair, you didn't give me a query!")

        if x.startswith("MCPE-"):
            for issue in jira.search_issues(f'issueKey = {query}'):
                x = issue.fields.created
                x, nonehere = x.split("T")
                y, m, d = x.split("-")

                #if issue == None or issue == "" or issue == " ": 
                    #await ctx.send("No results!")
                    #return
                try:
                    e = discord.Embed(title = f"ISSUE: {issue.key}", description = f"Issue Title: {issue.fields.summary}", color = 0x42f5e9)
                    e.add_field(name = "Basic Information:", value = f"```autohotkey\nIssue Reporter: {issue.fields.reporter.name}\nState: {issue.fields.status}\nIssue State: {issue.fields.customfield_10500.value}\nConfirmation Status: {issue.fields.issuetype}\nCreated At: {m}/{d}/{y}\nSummery: {issue.fields.issuetype.description}```")
                    e.add_field(name = f"Details:" ,value = f"```autohotkey\nDescription: {issue.fields.description}\n```\n**ISSUE LINK:** {issue.permalink()}```", inline = False)
                    await ctx.send(embed = e)
                except:
                    e = discord.Embed(title = f"ISSUE: {issue.key}", description = f"Issue Title: {issue.fields.summary}", color = 0x42f5e9)
                    e.add_field(name = "Information:", value = f"```bash\n$I wasn't able to show you the results due to the character limit, but here's a link!\n```\n**LINK:** {issue.permalink()}")
                    await ctx.send(embed = e)



        else:
            for issue in jira.search_issues(f'text ~ "{query}"'):
                x = issue.fields.created
                x, nonehere = x.split("T")
                y, m, d = x.split("-")
                #if issue == None or issue == "" or issue == " ": 
                    #await ctx.send("No results!")
                    #return
                try:
                    e = discord.Embed(title = f"ISSUE: {issue.key}", description = f"Issue Title: {issue.fields.summary}", color = 0x42f5e9)
                    e.add_field(name = "Basic Information:", value = f"```autohotkey\nIssue Reporter: {issue.fields.reporter.name}\nState: {issue.fields.status}\nIssue State: {issue.fields.customfield_10500.value}\nConfirmation Status: {issue.fields.issuetype}\nCreated At: {m}/{d}/{y}\nSummery: {issue.fields.issuetype.description}```")
                    e.add_field(name = f"Details:" ,value = f"```autohotkey\nDescription: {issue.fields.description}\n```\n**ISSUE LINK:** {issue.permalink()}", inline = False)
                    await ctx.send(embed = e)
                except:
                    e = discord.Embed(title = f"ISSUE: {issue.key}", description = f"Issue Title: {issue.fields.summary}", color = 0x42f5e9)
                    e.add_field(name = "Information:", value = f"```bash\n$I wasn't able to show you the results due to the character limit, but here's a link!\n```\n**LINK:** {issue.permalink()}")
                    await ctx.send(embed = e)





def setup(bot):
    bot.add_cog(SkeletonCMD(bot))
