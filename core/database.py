import logging
import os
from peewee import *
from discord.enums import ExpireBehavior
from peewee import AutoField, ForeignKeyField, Model, IntegerField, PrimaryKeyField, TextField, SqliteDatabase, DoesNotExist, DateTimeField, UUIDField, IntegrityError
from playhouse.shortcuts import model_to_dict, dict_to_model  # these can be used to convert an item to or from json http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#model_to_dict
from playhouse.sqlite_ext import RowIDField
from datetime import datetime
from peewee import MySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from flask import Flask

#from dotenv import load_dotenv
#load_dotenv()

#DB_IP = os.getenv("DB_IP")
#print(DB_IP)
#DB_Port = os.getenv("DB_PORT")
#print(DB_Port)
#DB_user = os.getenv("DB_USER")
#print(DB_user)
#DB_password = os.getenv("DB_PASSWORD")
#print(DB_password)
#DB_Database = os.getenv("DB_DATABASE")
#print(DB_Database)

db = SqliteDatabase("data.db", pragmas={'foreign_keys': 1})
#db = MySQLDatabase(DB_Database, user=DB_user, password=DB_password,host=DB_IP, port=int(DB_Port))
logger = logging.getLogger(__name__)

def iter_table(model_dict):
    """Iterates through a dictionary of tables, confirming they exist and creating them if necessary."""
    for key in model_dict:
        if not db.table_exists(key):
            db.connect(reuse_if_open=True)
            db.create_tables([model_dict[key]])
            logger.debug(f"Created table '{key}'")
            db.close()

class BaseModel(Model):
    """Base Model class used for creating new tables."""
    class Meta:
        database = db

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

tables = {"tag": Tag, "questions": Question, "blacklist": MRP_Blacklist_Data, "profile": PortalbotProfile, "realmprofile": RealmProfile}
iter_table(tables)
