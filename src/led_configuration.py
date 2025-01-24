# ----------------------------
# Imports
# ----------------------------

# Standard library imports
import time
import logging
import json
import math
from datetime import datetime, timedelta
from threading import Thread, Lock
import atexit
import math


# Third-party imports
import neopixel
import board

# Local imports
from src.handle_schedule import load_schedule

# ----------------------------
# Configuration and Constants
# ----------------------------

# Logger configuration
logger = logging.getLogger(__name__)

# LED Strip Configuration
NUM_LEDS = 48  # Total number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

# LED Colors
COLOR_WHITE = (255, 255, 255)
COLOR_GARBAGE = (50, 0, 90)  # Garbage
COLOR_ORGANIC = (0, 128, 0)  # Compost
COLOR_RECYCLING = (0, 0, 255)  # Recycling
COLOR_HOLIDAY = (255, 0, 0)  # Holiday
COLOR_RED = (255, 0, 0)
COLOR_NO = (255, 165, 0)  # No collection
COLOR_OFF = (0, 0, 0)

# Initialize LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)


# ----------------------------
# Classes
# ----------------------------

class AnimationManager:
    """
    Manages the current LED animation and parameters.
    Thread-safe for concurrent access.
    """
    def __init__(self):
        self.lock = Lock()
        self.current_animation = ''
        self.params = {}

    def set_animation(self, name, params=None):
        """function to switch the current animation"""
        logger.info(f'CURRENT_ANIMATION: {name}, PARAMS: {params}')
        with self.lock:
            self.current_animation = name
            self.params = params if params else {}

    def get_animation(self):
        with self.lock:
            return self.current_animation, self.params


# Create a single instance of AnimationManager
animation_manager = AnimationManager()

# ----------------------------
# Utility Functions
# ----------------------------

def turn_off_leds():
    """
    Turns off all LEDs and ensures it's done on program exit.
    """
    logger.info("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()

# Register the function to run on exit
atexit.register(turn_off_leds)

def format_schedule(schedule):
    """
    Formats the schedule for logging or debugging.
    """
    return json.dumps(schedule, indent=4) if isinstance(schedule, dict) else str(schedule)

# ----------------------------
# Animation Functions
# ----------------------------

def pulsate_white(steps=50, interval=0.05):
    """Pulsates LEDs in a white breathing effect."""
    logger.info("Starting pulsating white effect.")
    try:
        while True:
            current, params = animation_manager.get_animation()
            if current != 'pulsate_white':
                return

            for step in range(steps + 1):
                # Use a sinusoidal function for smooth fading
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))  # Range: 0.2 to 1.0
                white = (int(255 * brightness), int(255 * brightness), int(255 * brightness))  # Scale white color
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)

            # Fade out: Gradually decrease brightness
            for step in range(steps, -1, -1):
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))  # Range: 0.2 to 1.0
                white = (int(255 * brightness), int(255 * brightness), int(255 * brightness))  # Scale white color
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)
    except Exception as e:
        logger.error(f"Pulsating white effect failed: {e}")


def blink_red_and_turn_off(blink_count=5, blink_interval=0.5):
    """Blinks LEDs red a specified number of times, then turns them off."""
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

    turn_off_leds()


def set_leds(garbage_on, organics_on, recycling_on):
    """
    Sets LED colors based on collection status for groups of LEDs.
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

def fade_to_color(collections, BASE_COLOR, steps=100, interval=0.02, hold_time=5):
    """
    Gradually fades LEDs to specified colors based on collections.
    """
    logger.info("Fading LEDs to collection colors.")
    try:
        while True:
            current, params = animation_manager.get_animation()
            if current != 'fade_to_color':
                return

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

    except KeyboardInterrupt:
        logger.info("Fade to color interrupted. Turning off LEDs.")
        turn_off_leds()

# ----------------------------
# Main Logic
# ----------------------------

def update_leds_today():
    """
    Updates LEDs based on today's and tomorrow's schedule.
    """
    schedule = load_schedule()
    logger.info(f"Schedule: {format_schedule(schedule)}")

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    upcoming_collection = None
    today_or_tomorrow_handled = False

    for week_key, daily_schedules in schedule.items():
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            if "holiday" in daily_schedule["collections"] and date_obj == today:
                for next_schedule in daily_schedules:
                    next_date = datetime.strptime(next_schedule["date"], "%Y-%m-%d").date()
                    if next_date == tomorrow and len(next_schedule["collections"]) > 0:
                        animation_manager.set_animation(
                            'fade_to_color',
                            {"fade_state": {"collections": next_schedule["collections"]}}
                        )
                        return

                animation_manager.set_animation("set_holiday_lights", {})
                return

            if date_obj == today and len(daily_schedule["collections"]) > 0:
                animation_manager.set_animation(
                    'fade_to_color',
                    {"fade_state": {"collections": daily_schedule["collections"]}}
                )
                today_or_tomorrow_handled = True

            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                animation_manager.set_animation(
                    'fade_to_color',
                    {"fade_state": {"collections": daily_schedule["collections"]}}
                )
                today_or_tomorrow_handled = True

            elif date_obj > tomorrow and len(daily_schedule["collections"]) > 0 and upcoming_collection is None:
                upcoming_collection = daily_schedule["collections"]

        if upcoming_collection:
            break

    if not today_or_tomorrow_handled and upcoming_collection:
        animation_manager.set_animation('set_leds', {
            "collection_state": {
                "garbage_on": "garbage" in upcoming_collection,
                "organics_on": "organics" in upcoming_collection,
                "recycling_on": "recycling" in upcoming_collection,
            }
        })

def run_animations():
    """Main loop for running animations."""
    while True:
        name, params = animation_manager.get_animation()
        if name == 'pulsate_white':
            pulsate_white()
        elif name == 'blink_red_and_turn_off':
            blink_red_and_turn_off()
        elif name == 'set_leds':
            set_leds(**params.get('collection_state', {}))
        elif name == 'fade_to_color':
            fade_to_color(**params.get('fade_state', {}))
        else:
            turn_off_leds()


# Start animation thread
animation_thread = Thread(target=run_animations, daemon=True)
animation_thread.start()

# Start schedule updater thread
update_leds_today_thread = Thread(target=update_leds_today, daemon=True)
update_leds_today_thread.start()
