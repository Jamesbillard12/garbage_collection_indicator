from pathlib import Path
import json

SCHEDULE_FILE = Path("collection_schedule.json")

def save_schedule(data):
    """Save the collection schedule to a JSON file."""
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_schedule():
    """Load the collection schedule from a JSON file."""
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {}