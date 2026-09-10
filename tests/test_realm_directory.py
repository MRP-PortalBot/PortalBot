"""Offline directory checks: python -m unittest discover -s tests."""
import importlib
import logging
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord

# Import models without loading deployment credentials or connecting to MySQL.
with patch.dict(os.environ, {
    "database_username": "test", "database_password": "test",
    "database_schema": "test", "database_ip": "localhost", "database_port": "3306",
}), patch("dotenv.load_dotenv"), patch.dict(sys.modules, {
    "utils.helpers.__logging_module": SimpleNamespace(get_log=logging.getLogger),
}):
    directory = importlib.import_module("utils.realm_profiles.__rp_directory")
    database = importlib.import_module("utils.database.__database")
    with patch.dict(sys.modules, {
        "utils.realm_profiles.__rp_logic": SimpleNamespace(
            create_realm_channel_link_view=None, generate_realm_profile_card=None,
            save_image_from_url=None, _parse_world_start_date=None,
        ),
    }):
        views = importlib.import_module("utils.realm_profiles.__rp_views")


def profile(name, channel_id=1, **changes):
    values = dict(entry_id=channel_id, realm_name=name, emoji="🌍", short_desc="Survival",
                  channel_id=str(channel_id), archived=False, community_type="",
                  application_status="Not specified")
    values.update(changes)
    return SimpleNamespace(**values)


class Message:
    def __init__(self, embed, author=42):
        self.embeds = [embed]
        self.author = SimpleNamespace(id=author)
        self.edits = 0
        self.deleted = False

    async def edit(self, *, embed, **kwargs):
        self.embeds = [embed]
        self.edits += 1

    async def delete(self):
        self.deleted = True


class Channel:
    def __init__(self, messages=()):
        self.messages = list(messages)

    async def history(self, **kwargs):
        for message in self.messages:
            if not message.deleted:
                yield message

    async def send(self, *, embed, **kwargs):
        self.messages.append(Message(embed))


class DirectoryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.channels = {i: SimpleNamespace(category_id=directory.REALMS_CATEGORY_ID)
                         for i in range(1, 10)}

    def embeds(self, profiles):
        return directory.directory_embeds(profiles, self.channels)

    def test_eligibility_order_and_defaults(self):
        self.channels[4].category_id = 123
        entries = self.embeds([
            profile("zebra"), profile("Alpha", 2), profile("Archived", 3, archived=True),
            profile("Wrong category", 4), profile("Missing", 99),
            profile("Invalid", channel_id="invalid"),
        ])
        self.assertEqual([e.title for e in entries[1:]], ["🌍 Alpha", "🌍 zebra"])
        self.assertEqual([f.name for f in entries[1].fields], ["Applications", "Channel"])
        self.assertEqual(entries[1].fields[0].value, "Not specified")

    def test_status_type_and_limits(self):
        for status in directory.APPLICATION_STATUSES:
            entry = self.embeds([profile("X" * 300, short_desc="x" * 5000,
                                        application_status=status, community_type="Server")])[1]
            self.assertEqual(entry.fields[0].value, "Server")
            self.assertEqual(entry.fields[1].value, status)
            self.assertLessEqual(len(entry.title), 256)
            self.assertLessEqual(len(entry.description), 4096)
            self.assertLessEqual(len(entry), 6000)

    async def test_restart_noop_and_legacy_protection(self):
        legacy = Message(discord.Embed(title="Old directory"))
        foreign = Message(self.embeds([])[0], author=77)
        channel = Channel([legacy, foreign])
        desired = self.embeds([profile("Alpha")])
        await directory.reconcile_messages(channel, 42, desired)
        self.assertEqual(len(channel.messages), 4)
        await directory.reconcile_messages(channel, 42, desired)
        self.assertEqual(len(channel.messages), 4)
        self.assertTrue(all(m.edits == 0 for m in channel.messages))
        await directory.reconcile_messages(channel, 42, self.embeds([]))
        self.assertFalse(legacy.deleted)
        self.assertFalse(foreign.deleted)
        self.assertTrue(channel.messages[-1].deleted)

    async def test_add_rename_remove_and_manual_deletion(self):
        channel = Channel()
        await directory.reconcile_messages(channel, 42, self.embeds([profile("Zulu")]))
        await directory.reconcile_messages(channel, 42, self.embeds([profile("Zulu"), profile("Alpha", 2)]))
        self.assertEqual([m.embeds[0].title for m in channel.messages[1:]], ["🌍 Alpha", "🌍 Zulu"])
        channel.messages[1].deleted = True
        await directory.reconcile_messages(channel, 42, self.embeds([profile("Beta"), profile("Alpha", 2)]))
        active = [m for m in channel.messages if not m.deleted]
        self.assertEqual([m.embeds[0].title for m in active[1:]], ["🌍 Alpha", "🌍 Beta"])
        await directory.reconcile_messages(channel, 42, self.embeds([profile("Beta")]))
        active = [m for m in channel.messages if not m.deleted]
        self.assertEqual(len(active), 2)
        self.assertEqual(active[1].embeds[0].title, "🌍 Beta")

    async def test_description_edit_changes_only_its_entry(self):
        channel = Channel()
        await directory.reconcile_messages(channel, 42, self.embeds([profile("Alpha"), profile("Beta", 2)]))
        await directory.reconcile_messages(channel, 42, self.embeds([
            profile("Alpha", short_desc="Updated"), profile("Beta", 2)]))
        self.assertEqual([m.edits for m in channel.messages], [0, 1, 0])

    async def test_dropdown_defaults_and_permission_recheck(self):
        user = SimpleNamespace(id=5)
        realm = profile("Alpha")
        view = views.ProfileSectionView(user, realm, "Identity")
        self.assertEqual([o.value for o in view.children[0].options], ["blank", "Realm", "Server"])
        self.assertTrue(view.children[0].options[0].default)
        application_view = views.ProfileSectionView(user, realm, "Apply")
        self.assertTrue(application_view.children[0].options[-1].default)
        interaction = SimpleNamespace(user=user, response=SimpleNamespace(send_message=AsyncMock()))
        with patch.object(views.RealmProfile, "get_or_none", return_value=realm), patch.object(
            views, "_user_can_manage_realm", return_value=True
        ):
            self.assertTrue(await view.interaction_check(interaction))
            realm.archived = True
            self.assertFalse(await view.interaction_check(interaction))
            realm.archived = False
            interaction.user = SimpleNamespace(id=6)
            self.assertFalse(await view.interaction_check(interaction))

    async def test_dropdown_save_requests_sync(self):
        realm = profile("Alpha")
        user = SimpleNamespace(id=5)
        view = views.ProfileSectionView(user, realm, "Apply")
        selector = view.children[0]
        selector._values = ["Closed"]
        interaction = SimpleNamespace(user=user,
            response=SimpleNamespace(edit_message=AsyncMock()),
            client=SimpleNamespace(dispatch=MagicMock()))
        with patch.object(views.RealmProfile, "update") as update, patch.object(
            views.RealmProfile, "get_by_id", return_value=realm
        ):
            await selector.callback(interaction)
            self.assertEqual(list(update.call_args.args[0].values()), ["Closed"])
            update.return_value.where.return_value.execute.assert_called_once()
        interaction.client.dispatch.assert_called_once_with("realm_profile_updated")

    def test_schema_additions_are_restart_safe(self):
        columns = {"realmprofile": {"last_checkin_at", "checkin"},
                   "botdata": {"monthly_checkin_channel", "last_realm_checkin_posted_month"}}
        statements = []
        def execute(sql):
            statements.append(sql)
            if sql.startswith("ALTER TABLE"):
                columns[sql.split()[2]].add(sql.split()[5])
        db = SimpleNamespace(
            get_columns=lambda table: [SimpleNamespace(name=n) for n in columns[table]],
            execute_sql=execute,
        )
        with patch.object(database, "db", db):
            database.ensure_schema_columns()
            database.ensure_schema_columns()
        alters = [s for s in statements if s.startswith("ALTER")]
        self.assertEqual(len(alters), 2)
        self.assertIn("community_type", columns["realmprofile"])
        self.assertIn("application_status", columns["realmprofile"])


if __name__ == "__main__":
    unittest.main()
