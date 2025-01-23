import neopixel
import board
import time
from src.handle_schedule import load_schedule
from datetime import datetime, timedelta
import atexit
import logging
import json

def format_schedule(schedule):
    return json.dumps(schedule, indent=4) if isinstance(schedule, dict) else str(schedule)

logger = logging.getLogger(__name__)
# LED Strip Configuration
NUM_LEDS = 48  # Total number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_PURPLE = (50, 0, 90)  # Garbage
COLOR_GREEN = (0, 128, 0)  # Compost
COLOR_BLUE = (0, 0, 255)  # Recycling
COLOR_RED = (255, 0, 0)  # Holiday
COLOR_OFF = (0, 0, 0)

# Set up the LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# Helper Functions
def set_leds(garbage_on, organics_on, recycling_on):
    """Set LED colors based on collection status for groups of 8 LEDs."""
    logger.info(f"Setting LEDs: Garbage={garbage_on}, Organics={organics_on}, Recycling={recycling_on}")

    # Group configurations
    garbage_color = COLOR_PURPLE if garbage_on else COLOR_WHITE  # Garbage group
    organics_color = COLOR_GREEN if organics_on else COLOR_WHITE  # Organics group
    recycling_color = COLOR_BLUE if recycling_on else COLOR_WHITE  # Recycling group

    # Assign colors to groups of 8
    for i in range(8):
        pixels[i] = garbage_color  # First group (garbage)
        pixels[i + 8] = organics_color  # Second group (organics)
        pixels[i + 16] = recycling_color  # Third group (recycling)
        pixels[i + 24] = recycling_color  # Fourth group (mimics 3rd group)
        pixels[i + 32] = organics_color  # Fifth group (mimics 2nd group)
        pixels[i + 40] = garbage_color  # Sixth group (mimics 1st group)

    # Apply changes to the strip
    pixels.show()


def set_holiday_lights():
    """Set all LEDs to solid red for a holiday."""
    logger.info("Setting LEDs to solid red for holiday.")
    pixels.fill(COLOR_RED)
    pixels.show()


def fade_to_color(collections, target_color, steps=50, interval=0.05):
    """Turn all LEDs to their collection colors, include an all-lights-on phase, and cycle through fading."""
    logger.info(f"Cycling and fading LEDs to {target_color} for collections: {collections}")

    # Determine collection colors
    garbage_color = COLOR_PURPLE if "garbage" in collections else COLOR_OFF
    organics_color = COLOR_GREEN if "organics" in collections else COLOR_OFF
    recycling_color = COLOR_BLUE if "recycling" in collections else COLOR_OFF

    # Define the paired groups and their colors
    paired_groups = [
        {"groups": [0, 40], "color": garbage_color},  # Group 1 and 6
        {"groups": [8, 32], "color": organics_color},  # Group 2 and 5
        {"groups": [16, 24], "color": recycling_color},  # Group 3 and 4
    ]

    # Step 1: Turn all LEDs to their collection colors
    for pair in paired_groups:
        for group_start in pair["groups"]:
            for j in range(group_start, group_start + 8):
                pixels[j] = pair["color"]
    pixels.show()
    time.sleep(1)  # Hold collection colors for 1 second

    # Step 2: Start fading cycles
    while True:  # Infinite cycle
        # Phase 1: Turn all collection lights on
        for pair in paired_groups:
            for group_start in pair["groups"]:
                for j in range(group_start, group_start + 8):
                    pixels[j] = pair["color"]
        pixels.show()
        time.sleep(1)  # Hold all lights on for 1 second

        # Phase 2: Cycle through paired groups with fading
        for pair in paired_groups:
            # Perform fade to the target color for the current group
            for step in range(steps + 1):
                fade_in_ratio = step / steps  # Ratio for target color
                fade_out_ratio = 1 - fade_in_ratio  # Ratio for the group's color

                for group_start in pair["groups"]:
                    for j in range(group_start, group_start + 8):
                        # Calculate the blended color
                        r = int(pair["color"][0] * fade_out_ratio + target_color[0] * fade_in_ratio)
                        g = int(pair["color"][1] * fade_out_ratio + target_color[1] * fade_in_ratio)
                        b = int(pair["color"][2] * fade_out_ratio + target_color[2] * fade_in_ratio)
                        pixels[j] = (r, g, b)

                # Apply changes to the strip
                pixels.show()
                time.sleep(interval)

            # Reverse fade (from target color back to the collection color)
            for step in range(steps, -1, -1):
                fade_in_ratio = step / steps  # Ratio for target color
                fade_out_ratio = 1 - fade_in_ratio  # Ratio for the group's color

                for group_start in pair["groups"]:
                    for j in range(group_start, group_start + 8):
                        # Calculate the blended color
                        r = int(pair["color"][0] * fade_out_ratio + target_color[0] * fade_in_ratio)
                        g = int(pair["color"][1] * fade_out_ratio + target_color[1] * fade_in_ratio)
                        b = int(pair["color"][2] * fade_out_ratio + target_color[2] * fade_in_ratio)
                        pixels[j] = (r, g, b)

                # Apply changes to the strip
                pixels.show()
                time.sleep(interval)





def update_leds_today():
    """Update LEDs based on the upcoming schedule, with special handling for today and tomorrow."""
    schedule = load_schedule()
    logger.info(f"Schedule: {format_schedule(schedule)}")  # Debugging logger.info to ensure schedule is loaded

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    upcoming_collection = None  # Store the first collection after today and tomorrow
    today_or_tomorrow_handled = False  # Flag to check if today/tomorrow was handled

    # Iterate through the schedule
    for week_key, daily_schedules in schedule.items():
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            # Case 1: Holiday today
            if "holiday" in daily_schedule["collections"] and date_obj == today:
                logger.info(f"Holiday detected on {date_obj}. Checking next day's collections...")

                # Check if garbage or other collection is scheduled for tomorrow
                for next_schedule in daily_schedules:
                    next_date = datetime.strptime(next_schedule["date"], "%Y-%m-%d").date()
                    if next_date == tomorrow and len(next_schedule["collections"]) > 0:
                        logger.info(f"Holiday today with collection tomorrow: {next_schedule['collections']}")
                        fade_to_color(next_schedule["collections"], COLOR_RED, steps=100, interval=0.02)  # Cycle and fade to red
                        return

                # No collection tomorrow, just show solid red
                logger.info(f"Holiday today with no collection tomorrow. Setting solid red.")
                set_holiday_lights()
                return

            # Case 2: Today's collections
            if date_obj == today and len(daily_schedule["collections"]) > 0:
                logger.info(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                fade_to_color(daily_schedule["collections"], COLOR_WHITE, steps=100, interval=0.02)  # Cycle and fade to white
                today_or_tomorrow_handled = True

            # Case 3: Tomorrow's collections (no holiday logic)
            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                logger.info(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                fade_to_color(daily_schedule["collections"], COLOR_WHITE, steps=100, interval=0.02)  # Cycle and fade to white
                today_or_tomorrow_handled = True

            # Case 4: Future collections (after today and tomorrow)
            elif date_obj > tomorrow and len(daily_schedule["collections"]) > 0 and upcoming_collection is None:
                upcoming_collection = daily_schedule["collections"]
                logger.info(f"First upcoming collection after tomorrow: {upcoming_collection}")
                break  # Stop looking once the first collection is found

        if upcoming_collection:
            break  # Exit the outer loop if we've found the first collection

    # Case 5: No today/tomorrow collections, show the first future collection
    if not today_or_tomorrow_handled and upcoming_collection:
        logger.info(f"Setting LEDs for the first upcoming collection: {upcoming_collection}")
        set_leds(
            "garbage" in upcoming_collection,
            "organics" in upcoming_collection,
            "recycling" in upcoming_collection,
        )
    elif not today_or_tomorrow_handled:
        # Case 6: No collections at all
        logger.info("No collections found for today, tomorrow, or the rest of the week. Keeping LEDs as-is.")


# Ensure LEDs are turned off when the program exits
def turn_off_leds():
    logger.info("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()

# Register the turn_off_leds function to run on exit
atexit.register(turn_off_leds)
