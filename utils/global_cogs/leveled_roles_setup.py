import discord
from discord.ext import commands
from discord import app_commands

from core import database
from core.logging_module import get_log

_log = get_log(__name__)


class LeveledRolesCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        _log.info("LeveledRolesCMD Cog initialized")

    async def create_and_order_roles(self, guild: discord.Guild):
        """
        Creates roles based on level data, assigns colors, and reorders them.
        Also inserts them into the database if not already present.
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

        _log.info(f"Starting leveled role setup for guild: {guild.name} ({guild.id})")

        existing_roles = {role.name: role for role in guild.roles}
        created_roles = []

        try:
            for level, role_name, hex_color in roles_data:
                role_color = discord.Color(int(hex_color, 16))
                role = existing_roles.get(role_name)

                if not role:
                    _log.info(f"Creating role '{role_name}' with color #{hex_color}")
                    role = await guild.create_role(name=role_name, color=role_color)
                elif role.color != role_color:
                    _log.info(f"Updating role color for '{role_name}' to #{hex_color}")
                    await role.edit(color=role_color)

                created_roles.append((role, level))

                # Save role to database
                database.LeveledRoles.get_or_create(
                    RoleID=role.id,
                    ServerID=str(guild.id),
                    defaults={"RoleName": role_name, "LevelThreshold": level},
                )
                _log.debug(f"Role '{role_name}' synced to DB with Level {level}")

            # Reorder roles based on level
            sorted_roles = sorted(created_roles, key=lambda item: item[1])
            position_map = {
                role: index for index, (role, _) in enumerate(sorted_roles, start=1)
            }

            _log.info(f"Reordering roles in {guild.name}")
            await guild.edit_role_positions(positions=position_map)

        except discord.Forbidden:
            _log.error(f"Missing permissions to modify roles in {guild.name}")
            raise
        except discord.HTTPException as e:
            _log.error(f"HTTP error while modifying roles: {e}")
            raise
        except Exception as e:
            _log.error(f"Unexpected error in role setup: {e}")
            raise
        finally:
            _log.info(f"Completed leveled role setup for {guild.name}")

    @app_commands.command(
        name="setup_roles", description="Create and order leveled roles."
    )
    async def setup_roles_command(self, interaction: discord.Interaction):
        """Command handler to trigger leveled role setup in a guild."""
        guild = interaction.guild
        if not guild:
            _log.warning("setup_roles command called outside of a guild.")
            await interaction.response.send_message(
                "This command must be used in a server."
            )
            return

        try:
            _log.info(
                f"{interaction.user} started role setup in {guild.name} ({guild.id})"
            )
            await self.create_and_order_roles(guild)
            await interaction.response.send_message(
                "✅ Leveled roles have been set up."
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to manage roles."
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Error setting up roles: {e}")
        except Exception as e:
            await interaction.response.send_message("An unexpected error occurred.")
            _log.exception(f"Unexpected error during role setup in {guild.name}: {e}")


async def setup(bot):
    await bot.add_cog(LeveledRolesCMD(bot))
    _log.info("LeveledRolesCMD Cog loaded.")
