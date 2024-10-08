from __future__ import annotations
import logging
import os
from datetime import datetime
import discord # type: ignore
from discord.errors import ConnectionClosed # type: ignore


class ColourFormatter(logging.Formatter):
    """Formatter for console logging with colors."""

    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),  # Grey
        (logging.INFO, "\x1b[34;1m"),  # Blue
        (logging.WARNING, "\x1b[33;1m"),  # Yellow
        (logging.ERROR, "\x1b[31m"),  # Red
        (logging.CRITICAL, "\x1b[41m"),  # Background Red
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

        # Format exception text in red
        if record.exc_info:
            record.exc_text = (
                f"\x1b[31m{formatter.formatException(record.exc_info)}\x1b[0m"
            )

        return formatter.format(record)


def get_log(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Creates and configures a logger.

    Args:
        name (str): The name of the logger.
        level (int): Logging level. Defaults to DEBUG.

    Returns:
        logging.Logger: Configured logger object.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if logger already has handlers
    if not logger.hasHandlers():
        # Console Handler with ColourFormatter
        stream_formatter = ColourFormatter()
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

        # File Handler without colour for persistent logs, named by current date
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        # Determine the path for log storage (inside core/logs folder)
        log_dir = os.path.join("core", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Use the current date for the log file name
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(log_dir, f"{current_date}.log")

        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


class MyBot(discord.Client):
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
        Handles raw messages from the WebSocket.
        Catches ConnectionClosed errors and attempts to reconnect.
        """
        try:
            self.logger.debug(f"Socket message received: {message}")
            # Your message handling logic here

        except ConnectionClosed as e:
            self.logger.error(
                f"Connection closed: {e.code} - {e.reason}", exc_info=True
            )
            await self.handle_reconnect()

    async def handle_reconnect(self):
        """
        Attempts to reconnect after a WebSocket closure.
        """
        self.logger.info("Attempting to reconnect...")
        try:
            await self.connect()  # Reconnect logic here
            self.logger.info("Reconnected successfully.")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}", exc_info=True)

    async def on_error(self, event, *args, **kwargs):
        """
        Catches all unhandled errors in events and logs them.
        """
        self.logger.error(
            f"An error occurred during {event}: {args}, {kwargs}", exc_info=True
        )
