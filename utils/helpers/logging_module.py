from __future__ import annotations
import logging
import os
from datetime import datetime
import discord
from discord.errors import ConnectionClosed
import sys


class ColourFormatter(logging.Formatter):
    """Formatter for console logging with ANSI color codes based on log level."""

    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),  # Grey background
        (logging.INFO, "\x1b[34;1m"),  # Blue
        (logging.WARNING, "\x1b[33;1m"),  # Yellow
        (logging.ERROR, "\x1b[31m"),  # Red
        (logging.CRITICAL, "\x1b[41m"),  # Red background
    ]

    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])

        # Format exception info in red
        if record.exc_info:
            formatted_exception = (
                f"\x1b[31m{formatter.formatException(record.exc_info)}\x1b[0m"
            )
            return f"{formatter.format(record)}\n{formatted_exception}"
        return formatter.format(record)


def get_log(
    name: str, level: int = logging.DEBUG, console: bool = True
) -> logging.Logger:
    """
    Creates and configures a logger for a given module or context.

    Args:
        name (str): The logger name (usually __name__).
        level (int): Logging level (default: DEBUG).
        console (bool): Whether to log to the console as well as file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        # Console handler with colored output
        if console:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(ColourFormatter())
            stream_handler.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)

        # Log directory logic
        special_dirs = {
            "server_score": "logs/server_score",
            "leveled_roles": "logs/leveled_roles",
        }
        log_dir = special_dirs.get(name, "logs/daily")
        os.makedirs(log_dir, exist_ok=True)

        # File handler for daily logs
        file_name = datetime.now().strftime("%Y-%m-%d.log")
        file_path = os.path.join(log_dir, file_name)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
            )
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger


# Set up global exception logging
_log = get_log(__name__)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    _log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


# Apply the global exception hook
sys.excepthook = handle_exception


class MyBot(discord.Client):
    """
    Custom Discord client that includes enhanced logging and error handling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_log("my_discord_bot")

    async def on_ready(self):
        self.logger.info(f"Bot is ready! Logged in as {self.user}")

    async def on_disconnect(self):
        self.logger.warning("The bot has disconnected.")

    async def on_resumed(self):
        self.logger.info("The bot has resumed.")

    async def on_socket_raw_receive(self, message):
        """
        Handles raw WebSocket messages. Logs message and handles reconnect attempts on errors.
        """
        try:
            self.logger.debug(f"Socket message received: {message}")
            # Additional processing can go here
        except ConnectionClosed as e:
            self.logger.error(
                f"Connection closed: {e.code} - {e.reason}", exc_info=True
            )
            await self.handle_reconnect()

    async def handle_reconnect(self):
        """
        Attempts to reconnect after a WebSocket disconnect.
        """
        self.logger.info("Attempting to reconnect...")
        try:
            await self.connect()
            self.logger.info("Reconnected successfully.")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}", exc_info=True)

    async def on_error(self, event, *args, **kwargs):
        """
        Logs uncaught exceptions in event listeners.
        """
        self.logger.error(
            f"An error occurred during {event}: {args}, {kwargs}", exc_info=True
        )
