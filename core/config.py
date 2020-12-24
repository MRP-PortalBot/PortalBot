from pathlib import Path
import json
def load_config():
  config_file = Path("botconfig.json")
  config_file.touch(exist_ok=True)
  if config_file.read_text() == "":
    config_file.write_text("{}")
  with config_file.open("r") as f:
    config = json.load(f)
  return config, config_file

def prompt_config(msg, key):
  config, config_file = load_config()
  if key not in config:
    config[key] = input(msg)
    with config_file.open("w+") as f:
      json.dump(config, f, indent=4)