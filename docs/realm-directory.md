# Realm directory

On bot startup, the existing schema updater adds `community_type` and
`application_status` to `realmprofile`. Existing types stay blank; application
status starts as `Not specified`. New profiles use the same defaults.

Owners use `/realm-profile edit` → **Directory Info** to choose **Realm** or
**Server**, and **Open**, **Waitlist**, **Closed**, or **Not specified**.
Each dropdown saves immediately. The existing realm OP permission check applies.
Descriptions, names, and emojis still use their existing edit sections.

The directory posts in channel `588070315117117440`. It includes non-archived
profiles with a text channel in category `587627871216861244`. Active profiles
are the bot's approved-community records: approval creates/reactivates a profile,
and archiving deactivates it. The historical application name is not joined to
the profile, because owners can rename their community after approval.

Entries are text-only embeds with a common accent color. A header identifies
all communities as Bedrock. Blank types are omitted. Closed applications remain
listed. Entries are sorted by case-insensitive community name.

Profile edits, approvals, and archives trigger a refresh. A five-minute sweep
also catches external database edits and repairs manually deleted directory
messages. Category moves/deletions trigger a refresh. Discord errors are logged
and retried on the next sweep.

The bot needs View Channel, Read Message History, Send Messages, and Embed Links
in the destination channel. It reads channel history to recover its entries on
restart. Only messages authored by this bot with the exact directory footer
`PortalBot realm directory · v1` are managed; old messages are left for manual
removal. Do not reuse that footer for other bot messages.

Alphabetical positions are reused on additions, renames, and removals. This keeps
the directory ordered without reposting every entry, but a message link points
to a directory position rather than permanently identifying one community.
Unchanged entries are not edited, and messages suppress mentions.

Deploy the updated code and restart the existing bot to run the migration and
publish the directory. No manual SQL is needed. Run only one bot instance against
this directory. This change does not start or restart a deployed bot itself.

Offline checks (requires discord.py, peewee, and python-dotenv):

```shell
python -m unittest discover -s tests -v
```
