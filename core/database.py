import logging

from discord.enums import ExpireBehavior
from peewee import AutoField, ForeignKeyField, Model, IntegerField, PrimaryKeyField, TextField, SqliteDatabase, DoesNotExist, DateTimeField, UUIDField, IntegrityError
from playhouse.shortcuts import model_to_dict, dict_to_model  # these can be used to convert an item to or from json http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#model_to_dict
from playhouse.sqlite_ext import RowIDField
from datetime import datetime

db = SqliteDatabase("data.db", pragmas={'foreign_keys': 1})
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
    id = PrimaryKeyField()
    tag_name = TextField(unique=True)
    embed_title = TextField()
    text = TextField()

class Question(BaseModel):
    """Stores Questions for DailyQ here"""
    id = AutoField()
    question = TextField()

class Blacklist(BaseModel):
    """Stores Questions for DailyQ here"""
    entryid = AutoField()
    discordUsername = TextField()
    discordID = TextField()
    Gamertag = TextField()
    BannedRealm = TextField()
    Alts = TextField()
    BanReason = TextField()
    IncidentDate = TextField()
    BanType = TextField()
    ExpireBan = TextField()

class Profile(BaseModel):
    """Stores Questions for DailyQ here"""
    entryid = AutoField()
    discordName = TextField()
    discordID = TextField()
    timezone = TextField()
    xboxID = TextField()
    playstationID = TextField()
    switchID = TextField()
    pokemonGOID = TextField()
    chessID = TextField()



tables = {"tag": Tag, "questions": Question, "blacklist": Blacklist, "profile": Profile}
iter_table(tables)
