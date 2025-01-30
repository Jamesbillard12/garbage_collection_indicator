# ----------------------------
# Imports
# ----------------------------

import atexit
import json
import logging
import math
import time
from datetime import datetime, timedelta
from threading import Thread, Lock

import board
import neopixel

from src.handle_schedule import load_schedule

# ----------------------------
# Configuration and Constants
# ----------------------------

# Initialize logger
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

# ----------------------------
# Utility Functions
# ----------------------------

def format_schedule(schedule):
    """
    Format the schedule as a JSON string.

    Args:
        schedule (dict): Schedule data.

    Returns:
        str: Formatted schedule string.
    """
    return json.dumps(schedule, indent=4) if isinstance(schedule, dict) else str(schedule)


def turn_off_leds():
    """
    Turn off all LEDs by setting their color to off.
    """
    logger.info("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()


# Ensure LEDs are turned off when the program exits
atexit.register(turn_off_leds)

# ----------------------------
# Animation Manager Class
# ----------------------------

class AnimationManager:
    """
    Manages the current LED animation and its parameters.
    """
    def __init__(self):
        self.lock = Lock()
        self.current_animation = ''
        self.params = {}

    def set_animation(self, name, params=None):
        """
        Set the current animation.

        Args:
            name (str): Name of the animation.
            params (dict): Parameters for the animation.
        """
        logger.info(f'CURRENT_ANIMATION: {name}, PARAMS: {params}')
        with self.lock:
            self.current_animation = name
            self.params = params if params else {}

    def get_animation(self):
        """
        Get the current animation and its parameters.

        Returns:
            tuple: Current animation name and parameters.
        """
        with self.lock:
            return self.current_animation, self.params


# Initialize animation manager
animation_manager = AnimationManager()

# ----------------------------
# Animation Functions
# ----------------------------

def pulsate_white(steps=50, interval=0.05):
    """
    Make the LEDs pulsate white with a smooth breathing effect.
    """
    logger.info("Starting pulsating white effect.")
    try:
        while True:
            current, params = animation_manager.get_animation()
            if current != 'pulsate_white':
                return

            # Fade in and fade out
            for step in range(steps + 1):
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))
                white = (int(255 * brightness),) * 3
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)

            for step in range(steps, -1, -1):
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))
                white = (int(255 * brightness),) * 3
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)
    except Exception as e:
        logger.error(f"Pulsating white effect failed: {e}")


def blink_red_and_turn_off(blink_count=5, blink_interval=0.5):
    """
    Make all LEDs blink red a specified number of times and then turn them off.
    """
    logger.info(f"Blinking all LEDs red {blink_count} times, then turning them off.")
    for _ in range(blink_count):
        current, params = animation_manager.get_animation()
        if current != 'blink_red_and_turn_off':
            return

        pixels.fill(COLOR_RED)
        pixels.show()
        time.sleep(blink_interval)

        pixels.fill(COLOR_OFF)
        pixels.show()
        time.sleep(blink_interval)

    animation_manager.set_animation('')


def set_leds(garbage_on, organics_on, recycling_on):
    """
    Set LED colors based on collection status for groups of 8 LEDs.
    """
    logger.info(f"Setting LEDs: Garbage={garbage_on}, Organics={organics_on}, Recycling={recycling_on}")
    garbage_color = COLOR_GARBAGE if garbage_on else COLOR_WHITE
    organics_color = COLOR_ORGANIC if organics_on else COLOR_WHITE
    recycling_color = COLOR_RECYCLING if recycling_on else COLOR_WHITE

    for i in range(8):
        pixels[i] = garbage_color
        pixels[i + 8] = organics_color
        pixels[i + 16] = recycling_color
        pixels[i + 24] = recycling_color
        pixels[i + 32] = organics_color
        pixels[i + 40] = garbage_color

    pixels.show()


def set_holiday_lights():
    """
    Set all LEDs to solid red for a holiday.
    """
    logger.info("Setting LEDs to solid red for holiday.")
    pixels.fill(COLOR_HOLIDAY)
    pixels.show()


def fade_to_color(collections, BASE_COLOR, steps=100, interval=0.02, hold_time=5):
    """
    Fade LEDs between base color and collection colors.

    Args:
        collections (list): Types of collections (e.g., garbage, recycling).
        BASE_COLOR (tuple): RGB color to fade to.
        steps (int): Number of steps for fading. Default is 100.
        interval (float): Time between each step. Default is 0.02 seconds.
        hold_time (int): Duration to hold the collection colors. Default is 5 seconds.
    """
    try:
        while True:
            current, params = animation_manager.get_animation()
            if current != 'fade_to_color':
                return
            if not params or "fade_state" not in params:
                return

            logger.info(f"Starting at {BASE_COLOR}, fading LEDs to collection colors, holding, and cycling back.")
            garbage_color = COLOR_GARBAGE if "garbage" in collections else COLOR_NO
            organics_color = COLOR_ORGANIC if "organics" in collections else COLOR_NO
            recycling_color = COLOR_RECYCLING if "recycling" in collections else COLOR_NO

            paired_groups = [
                {"groups": [0, 40], "color": garbage_color},
                {"groups": [8, 32], "color": organics_color},
                {"groups": [16, 24], "color": recycling_color},
            ]

            pixels.fill(BASE_COLOR)
            pixels.show()
            time.sleep(1)

            for pair in paired_groups:
                for step in range(steps + 1):
                    fade_in_ratio = step / steps
                    fade_out_ratio = 1 - fade_in_ratio

                    for group_start in pair["groups"]:
                        for j in range(group_start, group_start + 8):
                            r = int(BASE_COLOR[0] * fade_out_ratio + pair["color"][0] * fade_in_ratio)
                            g = int(BASE_COLOR[1] * fade_out_ratio + pair["color"][1] * fade_in_ratio)
                            b = int(BASE_COLOR[2] * fade_out_ratio + pair["color"][2] * fade_in_ratio)
                            pixels[j] = (r, g, b)

                    pixels.show()
                    time.sleep(interval)

            time.sleep(hold_time)

            for step in range(steps + 1):
                fade_in_ratio = step / steps
                fade_out_ratio = 1 - fade_in_ratio

                for pair in paired_groups:
                    for group_start in pair["groups"]:
                        for j in range(group_start, group_start + 8):
                            r = int(pair["color"][0] * fade_out_ratio + BASE_COLOR[0] * fade_in_ratio)
                            g = int(pair["color"][1] * fade_out_ratio + BASE_COLOR[1] * fade_in_ratio)
                            b = int(pair["color"][2] * fade_out_ratio + BASE_COLOR[2] * fade_in_ratio)
                            pixels[j] = (r, g, b)

                pixels.show()
                time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Fade to color interrupted. Turning off LEDs.")
        animation_manager.set_animation('')

# ----------------------------
# Schedule Functions
# ----------------------------

def update_leds_today():
    """
    Update LEDs based on the upcoming schedule, with special handling for today and tomorrow.
    """
    schedule = load_schedule()
    logger.info(f"Schedule: {format_schedule(schedule)}")
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    upcoming_collection = None
    today_or_tomorrow_handled = False

    for week_key, daily_schedules in schedule.items():
        logger.info('Daily Schedule:', daily_schedules)
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            # Case 1: Holiday today
            if "holiday" in daily_schedule["collections"] and date_obj == today:
                logger.info(f"Holiday detected on {date_obj}. Checking tomorrow's collections...")
                for next_schedule in daily_schedules:
                    next_date = datetime.strptime(next_schedule["date"], "%Y-%m-%d").date()
                    if next_date == tomorrow and len(next_schedule["collections"]) > 0:
                        logger.info(f"Holiday today, collections tomorrow: {next_schedule['collections']}")
                        animation_manager.set_animation(
                            'fade_to_color',
                            {
                                "fade_state": {
                                    "collections": next_schedule["collections"],
                                    "base_color": COLOR_HOLIDAY,
                                    "steps": 100,
                                    "interval": 0.02,
                                }
                            }
                        )
                        return

                logger.info("Holiday today with no collections tomorrow. Setting holiday lights.")
                animation_manager.set_animation("set_holiday_lights", {})
                return

            # Case 2: Collections today
            if date_obj == today and len(daily_schedule["collections"]) > 0:
                logger.info(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                animation_manager.set_animation(
                    'fade_to_color',
                    {
                        "fade_state": {
                            "collections": daily_schedule["collections"],
                            "base_color": COLOR_WHITE,
                            "steps": 100,
                            "interval": 0.02,
                        }
                    }
                )
                today_or_tomorrow_handled = True

            # Case 3: Collections tomorrow
            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                logger.info(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                animation_manager.set_animation(
                    'fade_to_color',
                    {
                        "fade_state": {
                            "collections": daily_schedule["collections"],
                            "base_color": COLOR_WHITE,
                            "steps": 100,
                            "interval": 0.02,
                        }
                    }
                )
                today_or_tomorrow_handled = True

            # Case 4: First upcoming collection
            elif date_obj > tomorrow and len(daily_schedule["collections"]) > 0 and upcoming_collection is None:
                upcoming_collection = daily_schedule["collections"]
                logger.info(f"First upcoming collection after tomorrow: {upcoming_collection}")
                break

        if upcoming_collection:
            break

    # Case 5: No collections today/tomorrow, show future collection
    if not today_or_tomorrow_handled and upcoming_collection:
        logger.info(f"Setting LEDs for the first upcoming collection: {upcoming_collection}")
        animation_manager.set_animation(
            'set_leds',
            {
                "collection_state": {
                    "garbage_on": "garbage" in upcoming_collection,
                    "organics_on": "organics" in upcoming_collection,
                    "recycling_on": "recycling" in upcoming_collection,
                }
            }
        )
    elif not today_or_tomorrow_handled:
        # Case 6: No collections at all
        logger.info("No collections found for today, tomorrow, or the rest of the week. Turning off LEDs.")

# ----------------------------
# Main Animation Loop
# ----------------------------

def run_animations():
    """
    Main loop to manage animations.
    """
    while True:
        name, params = animation_manager.get_animation()
        if name == 'pulsate_white':
            pulsate_white()
        elif name == 'blink_red_and_turn_off':
            blink_red_and_turn_off()
        elif name == 'set_leds':
            collection_state = params.get(
                'collection_state',
                {"garbage_on": False, "organics_on": False, "recycling_on": False},
            )
            set_leds(
                collection_state["garbage_on"],
                collection_state["organics_on"],
                collection_state["recycling_on"],
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
                    "interval": 0.02,
                }
            )
            fade_to_color(
                fade_state["collections"],
                fade_state["base_color"],
                fade_state["steps"],
                fade_state["interval"],
            )
        else:
            turn_off_leds()

# ----------------------------
# Threads and Startup
# ----------------------------

# Start animation thread
animation_thread = Thread(target=run_animations, daemon=True)
animation_thread.start()

# Start update LEDs thread
update_leds_today_thread = Thread(target=update_leds_today, daemon=True)
update_leds_today_thread.start()
