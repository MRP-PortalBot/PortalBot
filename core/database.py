import logging
from peewee import AutoField, ForeignKeyField, Model, IntegerField, PrimaryKeyField, TextField, SqliteDatabase, DoesNotExist, DateTimeField, UUIDField, IntegrityError
from playhouse.shortcuts import model_to_dict, dict_to_model  # these can be used to convert an item to or from json http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#model_to_dict
from datetime import datetime

db = SqliteDatabase("data.db", pragmas={'foreign_keys': 1})
logger = logging.getLogger(__name__)

def iter_table(model_dict):
    """Iterates through a dictionary of tables, confirming they exist and creating them if necessary."""
    for key in model_dict:
        if not db.table_exists(key):
            db.create_tables([model_dict[key]])
            logger.debug(f"Created table '{key}'")

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

tables = {"tag": Tag}

iter_table(tables)