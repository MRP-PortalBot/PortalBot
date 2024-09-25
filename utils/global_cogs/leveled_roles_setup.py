import discord
from discord.ext import commands
from discord import app_commands
from core import database  # Assuming you have the database set up for leveled roles

class LeveledRolesCMD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_and_order_roles(self, guild: discord.Guild):
        roles_data = [
            (1, "Just Spawned", "2eb0aa"),
			(2, "Chicken Plucker", "2eb0a5"),
			(3, "Cow Milker", "2fafa0"),
			(4, "Zombie Slayer", "30af9b"),
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
			(80, "Ender Dragon Conqueror", "1919dc")
        ]

        # Iterate over the roles and create them if they don't exist
        created_roles = []
        for level, role_name, hex_color in roles_data:
            # Convert hex to RGB
            role_color = discord.Color(int(hex_color, 16))

            # Check if the role already exists
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                # Create the role if it doesn't exist
                role = await guild.create_role(name=role_name, color=role_color)
                created_roles.append(role)
            else:
                # Update the role color if it exists
                await role.edit(color=role_color)
                created_roles.append(role)

            # Add the role to the leveled roles database
            database.LeveledRoles.get_or_create(
                RoleID=role.id,
                LevelThreshold=level,
                ServerID=guild.id,
                defaults={'RoleName': role_name}
            )

        # Reorder roles: Highest level at the top, Just Spawned at the bottom
        # Reverse sort by level
        sorted_roles = sorted(created_roles, key=lambda r: [r.name, r.position], reverse=True)
        await guild.edit_role_positions(positions={r: i + 1 for i, r in enumerate(sorted_roles)})

    @app_commands.command(name="setup_roles", description="Create and order leveled roles.")
    async def setup_roles_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This command must be run in a server.")
            return

        await self.create_and_order_roles(guild)
        await interaction.response.send_message("Leveled roles have been set up and ordered.")

# Set up the cog
async def setup(bot):
    await bot.add_cog(LeveledRolesCMD(bot))
