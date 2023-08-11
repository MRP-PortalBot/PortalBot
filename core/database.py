import logging
import os
from peewee import AutoField, Model, IntegerField, TextField, SqliteDatabase, BigIntegerField, BooleanField, TimestampField, \
    MySQLDatabase
from flask import Flask
from dotenv import load_dotenv

from core.logging_module import get_log

load_dotenv()

DB_IP = os.getenv('database_ip')
DB_Port = os.getenv('database_port')
DB_user = os.getenv('database_username')
DB_password = os.getenv('database_password')
DB_Database = os.getenv('database_schema')

# db = SqliteDatabase("data.db", pragmas={'foreign_keys': 1})
db = MySQLDatabase(DB_Database, user=DB_user, password=DB_password,host=DB_IP, port=int(DB_Port))

_log = get_log(__name__)


def iter_table(model_dict):
    """Iterates through a dictionary of tables, confirming they exist and creating them if necessary."""
    for key in model_dict:
        if not db.table_exists(key):
            db.connect(reuse_if_open=True)
            db.create_tables([model_dict[key]])
            _log.debug(f"Created table '{key}'")
            db.close()


class BaseModel(Model):
    """Base Model class used for creating new tables."""

    class Meta:
        database = db


class BotData(BaseModel):
    """
    BotData:
    Information used across the bot.

    `id`: AutoField()
    Database Entry ID (ALWAYS QUERY 1)

    `last_question_posted`: DateTimeField()
    Last time a question was posted

    `persistent_views`: BooleanField()
    Whether or not persistent views are enabled

    `prefix`: TextField()
    Bot prefix

    `blacklist_response_channel`: BigIntegerField()
    Channel ID for blacklist responses

    `question_suggest_channel`: BigIntegerField()
    Channel ID for question suggestions

    `bot_spam_channel`: BigIntegerField()
    Channel ID for bot spam

    `realm_channel_response`: BigIntegerField()
    Channel ID for realm channel responses

    `bot_type`: TextField()
    Bot type

    `other_bot_id`: BigIntegerField()
    Other bot ID

    `bot_id`: BigIntegerField()
    Bot ID

    `server_id`: BigIntegerField()
    Server ID
    """
    id = AutoField()
    last_question_posted = TextField(null=True)
    persistent_views = BooleanField(default=False)
    prefix = TextField(default=">")
    blacklist_response_channel = BigIntegerField(default=0)
    daily_question_channel = BigIntegerField(default=0)
    question_suggest_channel = BigIntegerField(default=0)
    bot_spam_channel = BigIntegerField(default=0)
    realm_channel_response = BigIntegerField(default=0)
    bot_type = TextField(default="Stable")
    other_bot_id = BigIntegerField(default=0)
    bot_id = BigIntegerField(default=0)
    server_id = BigIntegerField(default=0)



class Tag(BaseModel):
    """Stores our tags accessed by the tag command."""
    id = AutoField()
    tag_name = TextField()
    embed_title = TextField()
    text = TextField()


class Question(BaseModel):
    """Stores Questions for DailyQ here"""
    id = AutoField()
    question = TextField()
    usage = TextField(default=False)


class MRP_Blacklist_Data(BaseModel):
    """Stores Blacklist Data here"""
    entryid = AutoField()
    BanReporter = TextField()
    DiscUsername = TextField()
    DiscID = TextField()
    Gamertag = TextField()
    BannedFrom = TextField()
    KnownAlts = TextField()
    ReasonforBan = TextField()
    DateofIncident = TextField()
    TypeofBan = TextField()
    DatetheBanEnds = TextField()


class PortalbotProfile(BaseModel):
    """Stores Profile Data here"""
    entryid = AutoField()
    DiscordName = TextField()
    DiscordLongID = TextField()
    Timezone = TextField(default="None")
    XBOX = TextField(default="None")
    Playstation = TextField(default="None")
    Switch = TextField(default="None")
    PokemonGo = TextField(default="None")
    Chessdotcom = TextField(default="None")


class RealmProfile(BaseModel):
    """Stores Realm Profile Data here"""
    entryid = AutoField()
    RealmName = TextField()
    RealmEmoji = TextField()
    RealmLongDesc = TextField()
    RealmShortDesc = TextField()
    Realmaddons = TextField()
    WorldAge = TextField()
    PVP = TextField()
    OnePlayerSleep = TextField()
    RealmStyle = TextField()
    Gamemode = TextField()


class Administrators(BaseModel):
    """
    Administrators:
    List of users who are whitelisted on the bot.

    `id`: AutoField()
    Database Entry

    `discordID`: BigIntegerField()
    Discord ID

    `TierLevel`: IntegerField()
    TIER LEVEL

    1 - Bot Manager\n
    2 - Admin\n
    3 - Sudo Admin\n
    4 - Owner
    """

    id = AutoField()
    discordID = BigIntegerField(unique=True)
    TierLevel = IntegerField(default=1)


class QuestionSuggestionQueue(BaseModel):
    """
    QuestionSuggestionQueue:
    List of users who have suggested questions for the bot.

    `id`: AutoField()
    Database Entry

    `discord_id`: BigIntegerField()
    Discord ID

    `question`: TextField()
    Question

    `message_id`: BigIntegerField()
    Message ID
    """

    id = AutoField()
    discord_id = BigIntegerField()
    question = TextField()
    message_id = BigIntegerField()


class RealmApplications(BaseModel):
    """
    RealmApplications:
    List of users who have applied for a realm and their application details.

    `id`: AutoField()
    Database Entry

    `discord_id`: BigIntegerField()
    Discord ID

    `realm_name`: TextField()
    Realm Name

    `type_of_realm`: TextField()
    Realm Type

    `emoji`: TextField()
    Realm Emoji

    `short_desc`: TextField()
    Realm Short Description

    `long_desc`: TextField()
    Realm Long Description

    `application_process`: TextField()
    Realm Application Process

    `member_count`: IntegerField()
    Realm Member Count

    `realm_age`: TextField()
    Realm Age

    `world_age`: TextField()
    Realm World Age

    `reset_schedule`: TextField()
    Realm Reset Schedule

    `foreseeable_future`: TextField()
    Realm Foreseeable Future

    `admin_team`: TextField()
    Realm Admin Team
    """
    id = AutoField()
    discord_id = BigIntegerField()
    discord_name = TextField()
    realm_name = TextField()
    type_of_realm = TextField()
    emoji = TextField()
    short_desc = TextField()
    long_desc = TextField()
    application_process = TextField()
    member_count = TextField()
    realm_age = TextField()
    world_age = TextField()
    reset_schedule = TextField()
    foreseeable_future = TextField()
    admin_team = TextField()
    timestamp = TimestampField()


app = Flask(__name__)


# This hook ensures that a connection is opened to handle any queries
# generated by the request.
@app.before_request
def _db_connect():
    db.connect()


# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


tables = {
    "tag": Tag,
    "questions": Question,
    "blacklist": MRP_Blacklist_Data,
    "profile": PortalbotProfile,
    "realmprofile": RealmProfile,
    "administrators": Administrators,
    "questionsuggestionqueue": QuestionSuggestionQueue,
    "realmapplications": RealmApplications,
    "botdata": BotData
}
iter_table(tables)
