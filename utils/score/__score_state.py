import time
import json
from pathlib import Path

COOLDOWN_FILE = Path("data/score_cooldowns.json")


class CooldownTracker:
    def __init__(self):
        self.timestamps: dict[str, float] = {}
        self.load()

    def on_cooldown(self, user_id: str, cooldown_time: float) -> bool:
        now = time.time()
        last = self.timestamps.get(user_id, 0)
        return (now - last) < cooldown_time

    def set_timestamp(self, user_id: str):
        self.timestamps[user_id] = time.time()
        self.save()

    def time_remaining(self, user_id: str, cooldown_time: float) -> float:
        return max(0, cooldown_time - (time.time() - self.timestamps.get(user_id, 0)))

    def save(self):
        try:
            COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with COOLDOWN_FILE.open("w") as f:
                json.dump(self.timestamps, f)
        except Exception as e:
            print(f"[CooldownTracker] Failed to save cooldowns: {e}")

    def load(self):
        if COOLDOWN_FILE.exists():
            try:
                with COOLDOWN_FILE.open("r") as f:
                    self.timestamps = json.load(f)
            except Exception as e:
                print(f"[CooldownTracker] Failed to load cooldowns: {e}")
                self.timestamps = {}


# Global tracker instance
cooldowns = CooldownTracker()
