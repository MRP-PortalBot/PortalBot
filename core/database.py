import logging
import os
from peewee import (
    AutoField,
    Model,
    IntegerField,
    TextField,
    SqliteDatabase,
    TextField,
    BooleanField,
    TimestampField,
    MySQLDatabase,
    OperationalError,
    ForeignKeyField,
)
from playhouse.shortcuts import ReconnectMixin
from flask import Flask
from dotenv import load_dotenv
import json

from core.logging_module import get_log
from core.decorators import cache_updated

# Load environment variables
load_dotenv()

# Set up logging
_log = get_log(__name__)

# Load database configurations from environment variables
try:
    DB_IP = os.getenv(
        "database_ip", "localhost"
    )  # Default to localhost if not provided
    DB_Port = os.getenv("database_port", "3306")  # Default MySQL port
    DB_user = os.getenv("database_username")
    DB_password = os.getenv("database_password")
    DB_Database = os.getenv("database_schema")

    if not all([DB_IP, DB_Port, DB_user, DB_password, DB_Database]):
        raise ValueError("One or more required environment variables are missing.")
except Exception as e:
    _log.error(f"Error loading environment variables: {e}")
    raise SystemExit(e)  # Exit the program if environment variables are missing

# Set up MySQL database connection
try:
    db = MySQLDatabase(
        DB_Database, user=DB_user, password=DB_password, host=DB_IP, port=int(DB_Port)
    )
    # Uncomment below if using a pooled database connection
    # db = PooledMySQLDatabase(DB_Database, user=DB_user, password=DB_password, host=DB_IP, port=int(DB_Port), max_connections=32, stale_timeout=300,)
except Exception as e:
    _log.error(f"Error connecting to the database: {e}")
    raise SystemExit(e)  # Exit the program if the database connection fails


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


try:
    db = ReconnectMySQLDatabase(
        DB_Database, user=DB_user, password=DB_password, host=DB_IP, port=int(DB_Port)
    )
except Exception as e:
    _log.error(f"Error connecting to the database: {e}")
    raise SystemExit(e)  # Exit the program if the database connection fails


def ensure_database_connection():
    try:
        if db.is_closed():
            db.connect(reuse_if_open=True)
    except OperationalError as e:
        _log.error(f"Error connecting to the database: {e}")
        raise


# Define function to iterate through tables and create them if necessary
def iter_table(model_dict):
    """Iterates through a dictionary of tables, confirming they exist and creating them if necessary."""
    for key, model in model_dict.items():
        try:
            if not db.table_exists(model):
                db.connect(reuse_if_open=True)
                db.create_tables([model])
                _log.debug(f"Created table '{key}'")
        except Exception as e:
            _log.error(f"Error creating table {key}: {e}")
        finally:
            if not db.is_closed():
                db.close()


class BaseModel(Model):
    """Base Model class used for creating new tables."""

    class Meta:
        database = db


def handle_database_errors(func):
    """Decorator for handling database errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _log.error(f"Database error in {func.__name__}: {e}")

    return wrapper


class BotData(BaseModel):
    """
    BotData:
    Information used across the bot.
    """

    id = AutoField()  # Database Entry ID (ALWAYS QUERY 1)
    server_id = TextField(default=0)  # Server ID where the bot is active
    bot_id = TextField(default=0)  # Discord Bot ID
    bot_type = TextField(default="Stable")  # Bot type (e.g., "Stable", "Dev")
    pb_test_server_id = TextField(
        default=448488274562908170
    )  # Portal Bot Test Server ID
    prefix = TextField(default=">")  # Bot prefix
    admin_role = TextField(default=0)  # Admin role for the server
    persistent_views = BooleanField(
        default=False
    )  # Whether or not persistent views are enabled
    welcome_channel = TextField(default=0)  # Welcome Channel ID
    bannedlist_response_channel = TextField(
        default=0
    )  # Channel ID for blacklist responses
    daily_question_channel = TextField(default=0)  # Channel ID for daily questions
    question_suggest_channel = TextField(
        default=0
    )  # Channel ID for question suggestions
    bot_spam_channel = TextField(default=0)  # Channel ID for bot spam
    realm_channel_response = TextField(
        default=0
    )  # Channel ID for realm channel responses
    general_channel = TextField(default=0)  # General Channel ID
    mod_channel = TextField(default=0)  # MOderator Channel ID
    daily_question_enabled = BooleanField(default=True)
    last_question_posted = TextField(null=True)  # Last question that was posted
    last_question_posted_time = TimestampField()  # Last time a question was posted
    cooldown_time = IntegerField(default=120)  # Default is 120 seconds
    points_per_message = IntegerField(default=10)  # Default is 10 points
    blocked_channels = TextField(default="[]")  # New field to store blocked channel IDs
    rule_channel = TextField(default=0)
    rule_message_id = TextField(default=0)

    def get_blocked_channels(self):
        return json.loads(self.blocked_channels)

    def set_blocked_channels(self, channel_ids):
        self.blocked_channels = json.dumps(channel_ids)

    @cache_updated
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class Tag(BaseModel):
    """Stores our tags accessed by the tag command."""

    id = AutoField()  # Tag entry ID
    tag_name = TextField()  # Name of the tag
    embed_title = TextField()  # Title of the embed associated with the tag
    text = TextField()  # Tag text content


class Question(BaseModel):
    """Stores questions for DailyQ here."""

    id = AutoField()  # Question entry ID
    display_order = TextField()  # Display order
    question = TextField()  # The question text
    usage = BooleanField(default=False)  # Indicates if the question has been used
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)


class QuestionVote(BaseModel):
    question = ForeignKeyField(Question, backref="votes")
    user_id = TextField()  # Discord user ID as string
    vote_type = TextField()  # "up" or "down"


class QuestionSuggestionQueue(BaseModel):
    """Stores users who suggested questions for the bot."""

    id = AutoField()  # Suggestion entry ID
    discord_id = TextField()  # Discord ID of the user
    discord_name = TextField()  # Discord Name of the user
    question = TextField()  # Suggested question
    message_id = TextField()  # ID of the message containing the suggestion


class MRP_Blacklist_Data(BaseModel):
    """Stores Blacklist Data here."""

    entryid = AutoField()  # Database Entry ID for blacklist
    BanReporter = TextField()  # Who reported the ban
    DiscUsername = TextField()  # Discord username of the banned user
    DiscID = TextField()  # Discord ID of the banned user
    Gamertag = TextField()  # Gamertag of the banned user
    BannedFrom = TextField()  # Where the user is banned from
    KnownAlts = TextField()  # Known alternative accounts
    ReasonforBan = TextField()  # Reason for banning the user
    DateofIncident = TextField()  # Date of the incident
    TypeofBan = TextField()  # Type of ban imposed (e.g., temp, perm)
    DatetheBanEnds = TextField()  # Date when the ban ends (if applicable)


class PortalbotProfile(BaseModel):
    """Stores Profile Data here."""

    entryid = AutoField()  # Profile entry ID
    DiscordName = TextField()  # The Discord username
    DiscordLongID = TextField()  # The Discord user ID
    Timezone = TextField(default="None")  # The user's timezone
    XBOX = TextField(default="None")  # Xbox Gamertag
    Playstation = TextField(default="None")  # Playstation username
    Switch = TextField(default="None")  # Nintendo Switch username
    SwitchNNID = TextField(default="None")  # Nintendo Switch Nintendo Network ID
    RealmsJoined = TextField(default="None")  # Number of realms the user has joined
    RealmsAdmin = TextField(default="None")  # Whether the user is an admin of realms


class RealmApplications(BaseModel):
    """Stores users' realm applications."""

    entry_id = AutoField()  # Database Entry ID for the realm
    discord_id = TextField()  # Discord ID of the applicant
    discord_name = TextField()  # Discord name of the applicant
    realm_name = TextField()  # Realm name the user is applying to
    emoji = TextField()  # Emoji associated with the realm
    play_style = TextField()  # Play style (e.g., survival, creative)
    gamemode = TextField()  # Game mode (peaceful, easy, hard, hardcore)
    short_desc = TextField()  # Short description of the realm
    long_desc = TextField()  # Long description of the realm
    application_process = TextField()  # Application process details
    admin_team = TextField()  # List of realm administrators
    member_count = IntegerField()  # Current member count of the realm
    community_age = TextField()  # Age of the community
    world_age = TextField()  # Age of the world in the realm
    reset_schedule = TextField()  # Realm reset schedule
    foreseeable_future = TextField()  # Future plans for the realm
    realm_addons = TextField()  # Addons or mods associated with the realm
    pvp = TextField()  # PvP enabled or not
    percent_player_sleep = TextField()  # Percent of players for sleep
    timestamp = TimestampField()  # Timestamp of the application
    approval = BooleanField()  # Approved or Denied


class RealmProfile(BaseModel):
    """Stores Realm Profile Data here."""

    entry_id = AutoField()  # Database Entry ID for the realm
    discord_id = TextField()  # Discord ID of the applicant
    discord_name = TextField()  # Discord name of the applicant
    realm_name = TextField()  # Realm name the user is applying to
    emoji = TextField()  # Emoji associated with the realm
    logo_url = TextField()  # Logo associated with the realm
    banner_url = TextField()  # Banner associated with the realm
    play_style = TextField()  # Play style (e.g., survival, creative)
    gamemode = TextField()  # Game mode (peaceful, easy, hard, hardcore)
    short_desc = TextField()  # Short description of the realm
    long_desc = TextField()  # Long description of the realm
    application_process = TextField()  # Application process details
    admin_team = TextField()  # List of realm administrators
    members = TextField()  # List of members
    member_count = IntegerField()  # Current member count of the realm
    community_age = TextField()  # Age of the community
    world_age = TextField()  # Age of the world in the realm
    reset_schedule = TextField()  # Realm reset schedule
    foreseeable_future = TextField()  # Future plans for the realm
    realm_addons = TextField()  # Addons or mods associated with the realm
    pvp = TextField()  # PvP enabled or not
    percent_player_sleep = TextField()  # Percent of players for sleep
    portal_invite = TextField()  # Invite to the portal specific to each realm
    checkin = BooleanField()  # Has the realm checked in this month?
    archived = BooleanField()  # Is the realm archived?


class Administrators(BaseModel):
    """
    Administrators:
    List of users whitelisted on the bot.
    """

    id = AutoField()  # Admin entry ID
    discordID = TextField(unique=True)  # Discord ID of the administrator
    discord_name = TextField()  # Discord Name of the administrator
    TierLevel = IntegerField(default=1)  # Admin tier level (1-4)


class ServerScores(BaseModel):
    """Stores the score for each user in different servers."""

    ScoreID = AutoField()  # Unique ID for each score entry
    DiscordName = TextField()  # User's Discord name
    DiscordLongID = TextField()  # Discord user ID (foreign key to PortalbotProfile)
    ServerID = TextField()  # Server ID where the score was achieved
    Score = IntegerField()  # Score in the particular server
    Level = IntegerField(default=0)  # Current level of the user
    Progress = IntegerField(default=0)  # Progress toward the next level


class LeveledRoles(BaseModel):
    """Stores the roles and level thresholds for each server."""

    id = AutoField()  # Unique ID for each role entry
    RoleName = TextField()  # Name of the role
    RoleID = TextField()  # Discord Role ID for role assignment
    ServerID = TextField()  # Server ID where the role is applicable
    LevelThreshold = IntegerField()  # Level required to achieve the role


class Reminder(BaseModel):
    """Stores reminders for users."""

    id = AutoField()  # Unique ID for each reminder
    user_id = TextField()  # Discord user ID of the user who set the reminder
    message_link = TextField()  # Link to the message to remind the user about
    remind_at = TimestampField()  # When to send the reminder


class Rule(BaseModel):
    guild_id = TextField()
    category = TextField()
    number = IntegerField()
    text = TextField()


# Flask app initialization
app = Flask(__name__)


# Flask database hooks
@app.before_request
def _db_connect():
    try:
        if db.is_closed():
            db.connect()
    except Exception as e:
        _log.error(f"Error connecting to the database before request: {e}")


@app.teardown_request
def _db_close(exc):
    try:
        if not db.is_closed():
            db.close()
    except Exception as e:
        _log.error(f"Error closing the database after request: {e}")


tables = {
    "tag": Tag,
    "questions": Question,
    "questionvote": QuestionVote,
    "questionsuggestionqueue": QuestionSuggestionQueue,
    "blacklist": MRP_Blacklist_Data,
    "profile": PortalbotProfile,
    "realmprofile": RealmProfile,
    "serverscores": ServerScores,
    "leveledroles": LeveledRoles,
    "administrators": Administrators,
    "realmapplications": RealmApplications,
    "botdata": BotData,
    "reminders": Reminder,
    "rules": Rule,
}

# Call the table creation function
if __name__ == "__main__":
    try:
        iter_table(tables)
    except Exception as e:
        _log.error(f"Error during table creation: {e}")
        raise SystemExit(e)
