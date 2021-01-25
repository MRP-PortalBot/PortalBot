import discord
import logging
from discord.ext import commands
import json
import datetime
from datetime import timedelta, datetime
from googleapiclient.http import MediaFileUpload
from googleapiclient import discovery
import httplib2
import auth
import logging

logger = logging.getLogger(__name__)

def getFileByteSize(filename):
    # Get file size in python
    from os import stat
    file_stats = stat(filename)
    print('File Size in Bytes is {}'.format(file_stats.st_size))
    return file_stats.st_size

def upload_file(drive_service, filename, mimetype, upload_filename, resumable=True, chunksize=262144):
    media = MediaFileUpload(filename, mimetype=mimetype, resumable=resumable, chunksize=chunksize)
    # Add all the writable properties you want the file to have in the body!
    body = {"name": upload_filename} 
    request = drive_service.files().create(body=body, media_body=media).execute()
    if getFileByteSize(filename) > chunksize:
        response = None
        while response is None:
            chunk = request.next_chunk()
            if chunk:
                status, response = chunk
                if status:
                    print("Uploaded %d%%." % int(status.progress() * 100))
    print("Upload Complete!")

class SkeletonCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Backup: Cog Loaded!")

    @commands.command()
    async def placeholder(self, ctx):
        return

    
def setup(bot):
    bot.add_cog(SkeletonCMD(bot))
