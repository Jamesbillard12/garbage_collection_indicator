from symtable import Class

import neopixel
import board
import time
from src.handle_schedule import load_schedule
from datetime import datetime, timedelta
import atexit
import logging
import json
from threading import Thread, Lock

def format_schedule(schedule):
    return json.dumps(schedule, indent=4) if isinstance(schedule, dict) else str(schedule)

logger = logging.getLogger(__name__)
# LED Strip Configuration
NUM_LEDS = 48  # Total number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_GARBAGE = (50, 0, 90)  # Garbage
COLOR_ORGANIC = (0, 128, 0)  # Compost
COLOR_RECYCLING = (0, 0, 255)  # Recycling
COLOR_HOLIDAY = (255, 0, 0)  # Holiday
COLOR_RED = (255, 0, 0)
COLOR_NO = (255, 165, 0)  # No collection
COLOR_OFF = (0, 0, 0)

# Set up the LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

class AnimationManager:
    def __init__(self):
        self.lock = Lock()
        self.current_animation = ''
        self.params = {}

    def set_animation(self, name, params=None):
        """function to switch the current animation"""
        logger.info('CURRENT_ANIMATION:', name, "PARAMS:", params)
        with self.lock:
            self.current_animation = name
            self.params = params if params else {}

    def get_animation(self):
        """function to get the current animation"""
        with self.lock:
            return self.current_animation, self.params

animation_manager = AnimationManager()

# Ensure LEDs are turned off when the program exits
def turn_off_leds():
    logger.info("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()

# Register the turn_off_leds function to run on exit
atexit.register(turn_off_leds)

def pulsate_white(steps=50, interval=0.05):
    """
    Make the LEDs pulsate white with a smooth breathing effect.

    Args:
        steps (int): The number of steps for the fade-in and fade-out. Default is 50.
        interval (float): The time (in seconds) between each brightness step. Default is 0.05.
    """
    logger.info("Starting pulsating white effect.")

    try:
        while True:  # Continue until the stop_event is set
            # Fade in: Gradually increase brightness to white
            current, params = animation_manager.get_animation()
            if current != 'pulsate_white':
                return

            for step in range(steps + 1):
                brightness = max(step / steps, 0.2)
                white = (int(255 * brightness), int(255 * brightness), int(255 * brightness))  # Scale white color
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)

            # Fade out: Gradually decrease brightness to off
            for step in range(steps, -1, -1):
                brightness = max(step / steps, 0.2)
                white = (int(255 * brightness), int(255 * brightness), int(255 * brightness))  # Scale white color
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)
    except Exception as e:
        logger.error(f"Pulsating white effect failed: {e}")

def blink_red_and_turn_off(blink_count=5, blink_interval=0.5):
    """
    Make all LEDs blink red a specified number of times and then shut off.

    Args:
        blink_count (int): The number of times to blink red. Default is 5.
        blink_interval (float): The time (in seconds) between turning on and off. Default is 0.5 seconds.
    """
    logger.info(f"Blinking all LEDs red {blink_count} times, then turning them off.")

    # Blink red
    for _ in range(blink_count):
        current, params = animation_manager.get_animation()
        if current != 'blink_red_and_turn_off':
            return
        # Turn all LEDs red
        pixels.fill(COLOR_RED)
        pixels.show()
        time.sleep(blink_interval)

        # Turn all LEDs off
        pixels.fill(COLOR_OFF)
        pixels.show()
        time.sleep(blink_interval)

    # Ensure LEDs are off after blinking
    logger.info("Turning off all LEDs after blinking.")
    turn_off_leds()

def set_leds(garbage_on, organics_on, recycling_on):
    """
    Set LED colors based on collection status for groups of 8 LEDs.
    """
    logger.info(f"Setting LEDs: Garbage={garbage_on}, Organics={organics_on}, Recycling={recycling_on}")

    # Group configurations
    garbage_color = COLOR_GARBAGE if garbage_on else COLOR_WHITE  # Garbage group
    organics_color = COLOR_ORGANIC if organics_on else COLOR_WHITE  # Organics group
    recycling_color = COLOR_RECYCLING if recycling_on else COLOR_WHITE  # Recycling group

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
    """
    Set all LEDs to solid red for a holiday.
    """
    logger.info("Setting LEDs to solid red for holiday.")
    pixels.fill(COLOR_HOLIDAY)
    pixels.show()

def fade_to_color(collections, BASE_COLOR, steps=100, interval=0.02, hold_time=5):

    try:
        while True:  # Infinite cycle
            current, params = animation_manager.get_animation()
            if current != 'fade_to_color':
                return
            if not params or "fade_state" not in params:
                return

            fade_state = params.fade_state
            collections = fade_state.collections
            BASE_COLOR = fade_state.base_color
            steps = fade_state.steps
            interval = fade_state.interval
            hold_time =5

            """
                Start at the base color, fade each group to its collection color, then fade all back to the base color.
                """
            logger.info(
                f"Starting at {BASE_COLOR}, fading LEDs to collection colors, holding, and cycling back to {BASE_COLOR}.")

            # Determine collection colors
            garbage_color = COLOR_GARBAGE if "garbage" in collections else COLOR_NO
            organics_color = COLOR_ORGANIC if "organics" in collections else COLOR_NO
            recycling_color = COLOR_RECYCLING if "recycling" in collections else COLOR_NO

            # Define the paired groups and their colors
            paired_groups = [
                {"groups": [0, 40], "color": garbage_color},  # Group 1 and 6
                {"groups": [8, 32], "color": organics_color},  # Group 2 and 5
                {"groups": [16, 24], "color": recycling_color},  # Group 3 and 4
            ]
            # Step 1: Start with all LEDs set to the base color
            pixels.fill(BASE_COLOR)
            pixels.show()
            time.sleep(1)  # Pause at base color

            # Step 2: Sequentially fade each group to its collection color
            for pair in paired_groups:
                for step in range(steps + 1):
                    fade_in_ratio = step / steps  # Ratio for collection color
                    fade_out_ratio = 1 - fade_in_ratio  # Ratio for base color

                    for group_start in pair["groups"]:
                        for j in range(group_start, group_start + 8):
                            # Calculate the blended color
                            r = int(BASE_COLOR[0] * fade_out_ratio + pair["color"][0] * fade_in_ratio)
                            g = int(BASE_COLOR[1] * fade_out_ratio + pair["color"][1] * fade_in_ratio)
                            b = int(BASE_COLOR[2] * fade_out_ratio + pair["color"][2] * fade_in_ratio)
                            pixels[j] = (r, g, b)

                    # Apply changes to the strip
                    pixels.show()
                    time.sleep(interval)

            # Step 3: Hold all collection colors for the specified time
            time.sleep(hold_time)

            # Step 4: Fade all LEDs back to the base color
            for step in range(steps + 1):
                fade_in_ratio = step / steps  # Ratio for base color
                fade_out_ratio = 1 - fade_in_ratio  # Ratio for collection color

                for pair in paired_groups:
                    for group_start in pair["groups"]:
                        for j in range(group_start, group_start + 8):
                            # Calculate the blended color
                            r = int(pair["color"][0] * fade_out_ratio + BASE_COLOR[0] * fade_in_ratio)
                            g = int(pair["color"][1] * fade_out_ratio + BASE_COLOR[1] * fade_in_ratio)
                            b = int(pair["color"][2] * fade_out_ratio + BASE_COLOR[2] * fade_in_ratio)
                            pixels[j] = (r, g, b)

                # Apply changes to the strip
                pixels.show()
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Fade to color interrupted. Turning off LEDs.")
        turn_off_leds()

def update_leds_today():
    """
    Update LEDs based on the upcoming schedule, with special handling for today and tomorrow.
    """
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
                        animation_manager.set_animation(
                            'fade_to_color',
                            {
                                "fade_state": {
                                    "collections": next_schedule["collections"],
                                     "base_color": COLOR_HOLIDAY,
                                     "steps": 100,
                                     "interval": 0.02
                                }
                            }
                        )
                        return

                # No collection tomorrow, just show solid red
                logger.info(f"Holiday today with no collection tomorrow. Setting solid red.")
                animation_manager.set_animation("set_holiday_lights", {})
                return

            # Case 2: Today's collections
            if True:
                logger.info(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                animation_manager.set_animation(
                    'fade_to_color',
                    {
                        "fade_state": {
                            "collections": daily_schedule["collections"],
                            "base_color": COLOR_WHITE,
                            "steps": 100,
                            "interval": 0.02
                        }
                    }
                ) # Cycle and fade to white
                today_or_tomorrow_handled = True

            # Case 3: Tomorrow's collections (no holiday logic)
            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                logger.info(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                animation_manager.set_animation(
                    'fade_to_color',
                    {
                        "fade_state": {
                            "collections": daily_schedule["collections"],
                            "base_color": COLOR_WHITE,
                            "steps": 100,
                            "interval": 0.02
                        }
                    }
                )  # Cycle and fade to white
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
        animation_manager.set_animation('set_leds', {
            "collection_state": {
                "garbage_on": "garbage" in upcoming_collection,
                 "organics_on": "organics" in upcoming_collection,
                 "recycling_on": "recycling" in upcoming_collection
            }
        })
    elif not today_or_tomorrow_handled:
        # Case 6: No collections at all
        logger.info("No collections found for today, tomorrow, or the rest of the week. Keeping LEDs as-is.")

def run_animations():
    """main loop to manage animations"""
    while True:
        name, params = animation_manager.get_animation()
        if name == 'pulsate_white':
            pulsate_white()
        elif name == 'blink_red_and_turn_off':
            blink_red_and_turn_off()
        elif name == 'set_leds':
            collection_state = params.get(
                'collection_state',
                {
                    "garbage_on": False,
                    "organics_on": False,
                    "recycling_on": False,
                })
            set_leds(
                collection_state["garbage_on"],
                collection_state["organics_on"],
                collection_state["recycling_on"]
            )
        elif name == "set_holiday_lights":
            set_holiday_lights()
        elif name == "fade_to_color":
            fade_state = params.get(
                'fade_state',
                {
                    "collections": [],
                    "base_color": (255, 255, 255),
                    "steps": 100,
                    "interval": 0.02
                }
            )
            fade_to_color(
                fade_state["collections"],
                fade_state["base_color"],
                fade_state["steps"],
                fade_state["interval"]
            )
        else:
            turn_off_leds()

animation_thread = Thread(target=run_animations, daemon=True)
animation_thread.start()

update_leds_today_thread = Thread(target=update_leds_today, daemon=True)
