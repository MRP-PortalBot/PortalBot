# utils/leveled_roles/__lr_logic.py

import aiohttp

import os
import discord
from tatsu.wrapper import ApiWrapper

from utils.database import __database as database
from utils.helpers.__logging_module import get_log
from utils.core_features.__common import calculate_level

_log = get_log(__name__)
wrapper = ApiWrapper(os.getenv("tatsu_api_key"))


async def create_and_order_roles(guild: discord.Guild):
    """
    Creates, colors, and orders leveled roles for the guild,
    inserting any missing roles into the database.
    """
    roles_data = [
        (1, "Just Spawned", "2eb0aa"),
        (2, "Chicken Plucker", "2eb0a5"),
        (3, "Zombie Slayer", "2fafa0"),
        (4, "Cow Milker", "30af9b"),
        (5, "Pig Rider", "30ae96"),
        (6, "Sheep Shearer", "31ae91"),
        (7, "Creeper Crater", "32ad8c"),
        (8, "Rabbit Bouncer", "32ad87"),
        (9, "Cat Napper", "33ac82"),
        (10, "Axolotl Bucketer", "34ab7d"),
        (11, "Horse Jumper", "34b371"),
        (12, "Ocelot Sneaker", "33bb64"),
        (13, "Wolf Master", "32c458"),
        (14, "Spider Sniper", "31cc4b"),
        (15, "Villager Trader", "30d53f"),
        (16, "Wandering Trader Tracker", "30dd32"),
        (17, "Skeleton Breaker", "2fe526"),
        (18, "Donkey Drifter", "2eee19"),
        (19, "Mule Maker", "2df60d"),
        (20, "Parrot Perch", "2cff00"),
        (21, "Bee Keeper", "3dff00"),
        (22, "Fox Befriender", "4fff00"),
        (23, "Bat Whisperer", "61ff00"),
        (24, "Salmon Snapper", "73ff00"),
        (25, "Cod Swimmer", "85ff00"),
        (26, "Tropical Fish Catcher", "96ff00"),
        (27, "Squid Seeker", "a8ff00"),
        (28, "Pufferfish Dodger", "baff00"),
        (29, "Drowned Skewer", "ccff00"),
        (30, "Dolphin Diver", "deff00"),
        (31, "Glow Squid Seeker", "e1f800"),
        (32, "Frog Hopper", "e4f000"),
        (33, "Tadpole Trainer", "e7e800"),
        (34, "Turtle Tamer", "ebe000"),
        (35, "Camel Cruiser", "eed800"),
        (36, "Goat Herder", "f1d100"),
        (37, "Phantom Fader", "f5c900"),
        (38, "Sniffer Finder", "f8c100"),
        (39, "Llama Target", "fbb900"),
        (40, "Trader Llama Leader", "ffb100"),
        (41, "Mooshroom Harvester", "ffa900"),
        (42, "Panda Snuggler", "ffa000"),
        (43, "Polar Bear Avoider", "ff9700"),
        (44, "Skeleton Horse Reaper", "ff8e00"),
        (45, "Iron Golem Creator", "ff8500"),
        (46, "Zombified Piglin Silencer", "ff7d00"),
        (47, "Snow Golem Chiller", "ff7400"),
        (48, "Husk Hitter", "ff6b00"),
        (49, "Cave Spider Curer", "ff6200"),
        (50, "Enderman Eluder", "ff5900"),
        (51, "Pillager Puncher", "f95100"),
        (52, "Ravager Raider", "f24800"),
        (53, "Evoker Evader", "ec3f00"),
        (54, "Vindicator Vanisher", "e53600"),
        (55, "Vex Vanquisher", "de2d00"),
        (56, "Hoglin Charger", "d82400"),
        (57, "Piglin Pal", "d11b00"),
        (58, "Piglin Brute Brawler", "cb1200"),
        (59, "Blaze Battler", "c40900"),
        (60, "Ghast Assassin", "bd0000"),
        (61, "Magma Cube Destroyer", "bb0216"),
        (62, "Strider Walker", "b8052c"),
        (63, "Zoglin Charger", "b50742"),
        (64, "Witch Watcher", "b20a58"),
        (65, "Silverfish Stomper", "af0c6e"),
        (66, "Slime Divider", "ad0f84"),
        (67, "Guardian Basher", "aa119a"),
        (68, "Elder Guardian Sinker", "a714b0"),
        (69, "Shulker Dodger", "a416c6"),
        (70, "Endermite Masher", "a119dc"),
        (71, "Zombie Villager Snatcher", "9419dc"),
        (72, "Allay Ally", "8619dc"),
        (73, "Armadillo Defender", "7919dc"),
        (74, "Breeze Blaster", "6b19dc"),
        (75, "Bogged Swampwalker", "5d19dc"),
        (76, "Stray Slicer", "5019dc"),
        (77, "Warden Whisperer", "4219dc"),
        (78, "Wither Skeleton Beheader", "3519dc"),
        (79, "Wither Warrior", "2719dc"),
        (80, "Ender Dragon Conqueror", "1919dc"),
    ]

    existing_roles = {role.name: role for role in guild.roles}
    created_roles = []

    for level, role_name, hex_color in roles_data:
        role_color = discord.Color(int(hex_color, 16))
        role = existing_roles.get(role_name)

        if not role:
            _log.info(f"Creating role '{role_name}' with color #{hex_color}")
            role = await guild.create_role(name=role_name, color=role_color)
        elif role.color.value != role_color.value:
            _log.info(f"Updating color for '{role_name}' to #{hex_color}")
            await role.edit(color=role_color)

        created_roles.append((role, level))

        database.LeveledRoles.get_or_create(
            RoleID=role.id,
            ServerID=str(guild.id),
            defaults={"RoleName": role_name, "LevelThreshold": level},
        )

    # Reorder roles
    sorted_roles = sorted(created_roles, key=lambda r: r[1])
    await guild.edit_role_positions(
        positions={r: i + 1 for i, (r, _) in enumerate(sorted_roles)}
    )

    _log.info(f"Leveled roles created and ordered in {guild.name}.")


async def sync_tatsu_score_for_user(bot, guild_id: int, user_id: int, user_name: str):
    """
    Syncs a user's Tatsu XP and level from the API and updates their ServerScore entry
    if the values have changed.
    """
    stats = await get_tatsu_score(user_id, guild_id)
    if not stats:
        return  # API failed or user not found

    score = stats["score"]
    level = stats["level"]

    existing = database.ServerScores.get_or_none(
        (database.ServerScores.ServerID == str(guild_id))
        & (database.ServerScores.DiscordLongID == str(user_id))
    )

    if existing:
        # Skip update if the score is unchanged
        if existing.total_xp == score:
            return

        existing.total_xp = score
        existing.level = level
        existing.username = user_name
        existing.save()
    else:
        database.ServerScores.create(
            ServerID=str(guild_id),
            DiscordLongID=str(user_id),
            username=user_name,
            total_xp=score,
            level=level,
        )


# utils/leveled_roles/__lr_logic.py


async def get_tatsu_score(user_id: int, guild_id: int) -> dict | None:
    """
    Fetch Tatsu XP and level for a specific user from the Tatsu API.
    Returns a dictionary with 'score' and 'level', or None if the request fails.
    """
    try:
        stats = await wrapper.get_user_stats(str(user_id), str(guild_id))
        return {
            "score": stats.get("score", 0),
            "level": stats.get("level", 0),
        }
    except Exception as e:
        _log.warning(f"Failed to fetch Tatsu stats for {user_id}: {e}")
        return None


async def get_role_for_level(level: int, guild: discord.Guild) -> discord.Role | None:
    try:
        entry = database.LeveledRoles.get_or_none(
            (database.LeveledRoles.LevelThreshold == level)
            & (database.LeveledRoles.ServerID == str(guild.id))
        )
        if entry:
            return discord.utils.get(guild.roles, id=int(entry.RoleID))  # ← FIXED HERE
    except Exception as e:
        _log.error(f"Error retrieving role for level {level}: {e}")
    return None
