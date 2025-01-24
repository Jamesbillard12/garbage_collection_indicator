# ----------------------------
# Imports
# ----------------------------

import json
from pathlib import Path
import logging

# ----------------------------
# Configuration and Constants
# ----------------------------

# Logger configuration
logger = logging.getLogger(__name__)

SCHEDULE_FILE = Path("collection_schedule.json")  # Path to the schedule file

# ----------------------------
# Functions
# ----------------------------

def save_schedule(data):
    """
    Save the collection schedule to a JSON file.

    Args:
        data (dict): The collection schedule data to save.
    """
    logger.info('SAVING DATA', data)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_schedule():
    """
    Load the collection schedule from a JSON file.

    Returns:
        dict: The collection schedule data. Returns an empty dictionary
              if the file does not exist.
    """
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {}