from __future__ import annotations
import logging
import os

class ColourFormatter(logging.Formatter):
    """Formatter for console logging with colors."""
    
    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),   # Grey
        (logging.INFO, "\x1b[34;1m"),    # Blue
        (logging.WARNING, "\x1b[33;1m"), # Yellow
        (logging.ERROR, "\x1b[31m"),     # Red
        (logging.CRITICAL, "\x1b[41m"),  # Background Red
    ]

    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])

        # Format exception text in red
        if record.exc_info:
            record.exc_text = f"\x1b[31m{formatter.formatException(record.exc_info)}\x1b[0m"

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

        # File Handler without colour for persistent logs
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/{name}.log")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
