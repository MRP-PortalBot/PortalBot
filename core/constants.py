import discord


DEFAULT_PREFIX = ">"


class ConsoleColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class EmbedColors:
    red = discord.Color.red()
    green = discord.Color.green()
    blue = discord.Color.blue()
    yellow = discord.Color.gold()
    default = discord.Color.blurple()


class BotAssets:
    error_png = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png"
    info_png = "https://icons.iconarchive.com/icons/custom-icon-design/flatastic-1/512/information-icon.png"


class Dev:
    TracebackChannel = 797193549992165456
    DefaultAdminID = 306070011028439041
