import os
import json
import datetime
from dotenv import load_dotenv
from peewee import (
    AutoField,
    Model,
    IntegerField,
    TextField,
    BooleanField,
    DateTimeField,
    MySQLDatabase,
    OperationalError,
    ForeignKeyField,
    DateField,
)
from playhouse.shortcuts import ReconnectMixin
from utils.helpers.__logging_module import get_log

# --------------------------------------------------------------------
# Environment + DB connection
# --------------------------------------------------------------------
load_dotenv()
_log = get_log(__name__)

try:
    DB_IP = os.getenv("database_ip", "localhost")
    DB_Port = int(os.getenv("database_port", "3306"))
    DB_user = os.getenv("database_username")
    DB_password = os.getenv("database_password")
    DB_Database = os.getenv("database_schema")
    if not all([DB_IP, DB_Port, DB_user, DB_password, DB_Database]):
        raise ValueError("One or more required environment variables are missing.")
except Exception as e:
    _log.error(f"Error loading environment variables: {e}")
    raise SystemExit(e)


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    def _initialize_connection(self, conn):
        super()._initialize_connection(conn)
        cursor = conn.cursor()
        try:
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
        finally:
            cursor.close()


try:
    db = ReconnectMySQLDatabase(
        DB_Database,
        user=DB_user,
        password=DB_password,
        host=DB_IP,
        port=DB_Port,
        charset="utf8mb4",
        use_unicode=True,
    )
except Exception as e:
    _log.error(f"Error connecting to the database: {e}")
    raise SystemExit(e)


def ensure_database_connection():
    try:
        if db.is_closed():
            db.connect(reuse_if_open=True)
    except OperationalError as e:
        _log.error(f"Error connecting to the database: {e}")
        raise


class BaseModel(Model):
    class Meta:
        database = db


# --------------------------------------------------------------------
# MODELS
# --------------------------------------------------------------------


class BotData(BaseModel):
    id = AutoField()
    server_name = TextField(default="0")
    server_desc = TextField(default="0")
    server_invite = TextField(default="0")
    other_info_1_title = TextField(default="Additional Info")
    other_info_1_text = TextField(default="")
    other_info_2_title = TextField(default="More Information")
    other_info_2_text = TextField(default="")
    server_id = TextField(default="0")
    bot_id = TextField(default="0")
    bot_type = TextField(default="Stable")
    pb_test_server_id = TextField(default="448488274562908170")
    prefix = TextField(default=">")
    admin_role = TextField(default="0")
    persistent_views = BooleanField(default=False)
    welcome_channel = TextField(default="0")
    bannedlist_response_channel = TextField(default="0")
    daily_question_channel = TextField(default="0")
    question_suggest_channel = TextField(default="0")
    bot_spam_channel = TextField(default="0")
    realm_channel_response = TextField(default="0")
    general_channel = TextField(default="0")
    mod_channel = TextField(default="0")
    message_log = TextField(default="0")
    member_log = TextField(default="0")
    server_log = TextField(default="0")
    daily_question_enabled = BooleanField(default=True)
    last_question_posted = TextField(null=True)
    last_question_posted_time = DateTimeField(null=True)
    cooldown_time = IntegerField(default=120)
    points_per_message = IntegerField(default=10)
    blocked_channels = TextField(default="[]")
    rule_channel = TextField(default="0")
    rule_message_id = TextField(default="0")
    enable_weekly_audit = BooleanField(default=True)
    monthly_checkin_channel = TextField(default="587673548160630804")
    last_realm_checkin_posted_month = TextField(null=True)

    def get_blocked_channels(self):
        return json.loads(self.blocked_channels)

    def set_blocked_channels(self, channel_ids):
        self.blocked_channels = json.dumps(channel_ids)


class Tag(BaseModel):
    id = AutoField()
    tag_name = TextField()
    embed_title = TextField()
    text = TextField()


class Question(BaseModel):
    id = AutoField()
    display_order = TextField()
    question = TextField()
    usage = BooleanField(default=False)
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)


class Daily_Question_Log(BaseModel):
    id = AutoField()
    log_date = DateField(unique=True)  # YYYY-MM-DD (no time part)
    question = ForeignKeyField(Question, backref="qod_logs", on_delete="CASCADE")
    posted_at = DateTimeField()  # exact datetime (in CST)


class QuestionVote(BaseModel):
    question = ForeignKeyField(Question, backref="votes", on_delete="CASCADE")
    user_id = TextField()
    vote_type = TextField()  # "up" or "down"


class QuestionSuggestionQueue(BaseModel):
    id = AutoField()
    discord_id = TextField()
    discord_name = TextField()
    question = TextField()
    message_id = TextField()


class MRP_Blacklist_Data(BaseModel):
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
    entryid = AutoField()
    DiscordName = TextField()
    DiscordLongID = TextField()
    Timezone = TextField(default="None")
    XBOX = TextField(default="None")
    Playstation = TextField(default="None")
    Switch = TextField(default="None")
    SwitchNNID = TextField(default="None")
    RealmsJoined = TextField(default="None")
    RealmsAdmin = TextField(default="None")


class RealmApplications(BaseModel):
    entry_id = AutoField()
    discord_id = TextField()
    discord_name = TextField()
    realm_name = TextField()
    emoji = TextField()
    play_style = TextField()
    gamemode = TextField()
    short_desc = TextField()
    long_desc = TextField()
    application_process = TextField()
    admin_team = TextField()
    member_count = IntegerField()
    community_age = TextField()
    world_start_date = DateField(null=True)
    reset_schedule = TextField()
    foreseeable_future = TextField()
    realm_addons = TextField()
    pvp = TextField()
    percent_player_sleep = TextField()
    timestamp = DateTimeField(null=True)
    approval = BooleanField()


class RealmProfile(BaseModel):
    entry_id = AutoField()
    discord_id = TextField()
    discord_name = TextField()
    realm_name = TextField()
    emoji = TextField()
    logo_url = TextField()
    banner_url = TextField()
    play_style = TextField()
    gamemode = TextField()
    short_desc = TextField()
    long_desc = TextField()
    application_process = TextField()
    admin_team = TextField()
    members = TextField()
    member_count = IntegerField()
    community_age = TextField()
    world_start_date = DateField(null=True)
    reset_schedule = TextField()
    foreseeable_future = TextField()
    realm_addons = TextField()
    pvp = TextField()
    percent_player_sleep = TextField()
    portal_invite = TextField()
    op_role_id = TextField(default="0")
    channel_id = TextField(default="0")
    checkin = BooleanField(default=False)
    last_checkin_at = DateTimeField(null=True)
    archived = BooleanField()


class RealmCheckIn(BaseModel):
    id = AutoField()
    realm = ForeignKeyField(RealmProfile, backref="monthly_checkins", on_delete="CASCADE")
    guild_id = TextField(index=True)
    checkin_month = TextField(index=True)
    checked_in_by_id = TextField(null=True)
    checked_in_by_name = TextField(null=True)
    method = TextField(default="reaction")
    message_id = TextField(null=True)
    checked_in_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        indexes = ((("realm", "guild_id", "checkin_month"), True),)


class Administrators(BaseModel):
    id = AutoField()
    discordID = TextField(unique=True)
    discord_name = TextField()
    TierLevel = IntegerField(default=1)


class ServerScores(BaseModel):
    ScoreID = AutoField()
    DiscordName = TextField()
    DiscordLongID = TextField()
    ServerID = TextField()
    Score = IntegerField()
    Level = IntegerField(default=0)
    Progress = IntegerField(default=0)
    LastMessageTimestamp = DateTimeField(default=0)
    TatsuXP = IntegerField(default=0)


class LeveledRoles(BaseModel):
    id = AutoField()
    RoleName = TextField()
    RoleID = TextField()
    ServerID = TextField()
    LevelThreshold = IntegerField()


class Reminder(BaseModel):
    id = AutoField()
    user_id = TextField()
    message_link = TextField()
    remind_at = DateTimeField(null=True)


class Rule(BaseModel):
    guild_id = TextField()
    category = TextField()
    number = IntegerField()
    text = TextField()


# ---------------------- Build Competition (Community Vote) ----------------------


class BuildConfig(BaseModel):
    id = AutoField()
    guild_id = TextField(index=True, unique=True)

    # existing
    announce_channel_id = TextField(null=True)  # e.g. #build-competition-announcements
    submission_forum_id = TextField(null=True)  # central forum channel id

    # NEW
    announce_role_id = TextField(
        null=True
    )  # role to ping (reaction role grants/removes this)
    rules_channel_id = TextField(null=True)  # where /build post-rules posted
    discussion_channel_id = TextField(null=True)  # #build-competition-discussion
    reaction_message_id = TextField(null=True)  # message id of the reaction-role post


class BuildSeason(BaseModel):
    id = AutoField()
    guild_id = TextField(index=True)
    theme = TextField()

    # NEW
    theme_description = TextField(null=True)  # longer description shown on season post
    season_thread_id = TextField(null=True)  # the pinned season announcement thread id

    # existing timing/status
    submission_start = DateTimeField()
    submission_end = DateTimeField()
    voting_start = DateTimeField()
    voting_end = DateTimeField()
    status = TextField(default="scheduled")  # scheduled, submissions, voting, closed

    # other existing knobs
    max_images = IntegerField(default=5)
    anon_voting = BooleanField(default=True)
    min_account_days = IntegerField(default=0)
    min_server_messages = IntegerField(default=0)
    allow_multiple_entries = BooleanField(default=False)


class BuildEntry(BaseModel):
    id = AutoField()
    season = ForeignKeyField(BuildSeason, backref="entries", on_delete="CASCADE")
    user_id = TextField(index=True)
    message_id = TextField(null=True)  # first message in forum post
    thread_id = TextField(null=True)  # forum post id
    caption = TextField(null=True)
    image_urls = TextField()  # json array if you store them
    world_url = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)


class BuildVote(BaseModel):
    id = AutoField()
    season = ForeignKeyField(BuildSeason, backref="votes", on_delete="CASCADE")
    entry = ForeignKeyField(BuildEntry, backref="votes", on_delete="CASCADE")
    voter_id = TextField(index=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        indexes = ((("season", "voter_id"), True),)  # one vote per user per season


# --------------------------------------------------------------------
# Table creation on startup
# --------------------------------------------------------------------


def create_all_tables():
    """
    Create any missing tables in a single batch to satisfy FK constraints.
    Call this during bot startup.
    """
    ensure_database_connection()
    models_in_order = [
        # core
        Tag,
        Question,
        QuestionVote,
        QuestionSuggestionQueue,
        MRP_Blacklist_Data,
        PortalbotProfile,
        RealmApplications,
        RealmProfile,
        RealmCheckIn,
        Administrators,
        ServerScores,
        LeveledRoles,
        Reminder,
        Rule,
        BotData,
        # build comp (parents before children)
        BuildConfig,
        BuildSeason,
        BuildEntry,
        BuildVote,
    ]
    to_create = [m for m in models_in_order if not m.table_exists()]
    if to_create:
        db.create_tables(to_create)
        _log.info(
            "Created tables: %s", ", ".join(m._meta.table_name for m in to_create)
        )
    ensure_schema_columns()


def ensure_schema_columns():
    """
    Add columns introduced after a table already exists.

    Peewee's create_tables() is intentionally non-destructive and will not alter
    existing MySQL tables, so lightweight ALTER statements keep older
    deployments compatible when new model fields are added.
    """
    realm_profile_columns = {column.name for column in db.get_columns("realmprofile")}
    if "last_checkin_at" not in realm_profile_columns:
        db.execute_sql("ALTER TABLE realmprofile ADD COLUMN last_checkin_at DATETIME NULL")
        _log.info("Added missing realmprofile.last_checkin_at column.")

    if "checkin" not in realm_profile_columns:
        db.execute_sql(
            "ALTER TABLE realmprofile ADD COLUMN checkin BOOL NOT NULL DEFAULT 0"
        )
        _log.info("Added missing realmprofile.checkin column.")

    bot_data_columns = {column.name for column in db.get_columns("botdata")}
    if "monthly_checkin_channel" not in bot_data_columns:
        db.execute_sql(
            "ALTER TABLE botdata ADD COLUMN monthly_checkin_channel TEXT "
            "DEFAULT '587673548160630804'"
        )
        _log.info("Added missing botdata.monthly_checkin_channel column.")

    if "last_realm_checkin_posted_month" not in bot_data_columns:
        db.execute_sql(
            "ALTER TABLE botdata ADD COLUMN last_realm_checkin_posted_month TEXT NULL"
        )
        _log.info("Added missing botdata.last_realm_checkin_posted_month column.")


def init_database():
    """
    Public entrypoint for app startup.
    Ensures the DB is connected and tables are present.
    """
    create_all_tables()
    _log.info("Database initialized and tables verified.")


# Back-compat alias some code uses elsewhere
__database = db
