from pathlib import Path
from typing import Tuple
import json

def load_config() -> Tuple[dict, Path]:
  """Load data from the botconfig.json.\n
  Returns a tuple containing the data as a dict, and the file as a Path"""
  config_file = Path("botconfig.json")
  config_file.touch(exist_ok=True)
  if config_file.read_text() == "":
    config_file.write_text("{}")
  with config_file.open("r") as f:
    config = json.load(f)
  return config, config_file

def prompt_config(msg, key):
  """Ensure a value exists in the botconfig.json, if it doesn't prompt the bot owner to input via the console."""
  config, config_file = load_config()
  if key not in config:
    config[key] = input(msg)
    with config_file.open("w+") as f:
      json.dump(config, f, indent=4)