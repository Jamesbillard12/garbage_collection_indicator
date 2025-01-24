# Standard library imports
from datetime import datetime, timedelta
from symtable import Class
from threading import Thread, Lock
import atexit
import json
import logging
import math
import time

# Third-party imports
import board
import neopixel

# Local imports
from src.handle_schedule import load_schedule

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Constants and Configuration
# ============================================================================

# LED Strip Configuration
NUM_LEDS = 48  # Total number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

# Color definitions
COLOR_WHITE = (255, 255, 255)
COLOR_GARBAGE = (50, 0, 90)    # Garbage
COLOR_ORGANIC = (0, 128, 0)    # Compost
COLOR_RECYCLING = (0, 0, 255)  # Recycling
COLOR_HOLIDAY = (255, 0, 0)    # Holiday
COLOR_RED = (255, 0, 0)
COLOR_NO = (255, 165, 0)       # No collection
COLOR_OFF = (0, 0, 0)

# Initialize LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# ============================================================================
# Utility Functions
# ============================================================================

def format_schedule(schedule):
    """Format schedule data for logging."""
    return json.dumps(schedule, indent=4) if isinstance(schedule, dict) else str(schedule)

def turn_off_leds():
    """Turn off all LEDs."""
    logger.info("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()

# Register cleanup function
atexit.register(turn_off_leds)

# ============================================================================
# Animation Management
# ============================================================================

class AnimationManager:
    """Manages the current animation state and parameters."""

    def __init__(self):
        self.lock = Lock()
        self.current_animation = ''
        self.params = {}

    def set_animation(self, name, params=None):
        """Set the current animation and its parameters."""
        logger.info(f'CURRENT_ANIMATION: {name}, PARAMS: {params}')
        with self.lock:
            self.current_animation = name
            self.params = params if params else {}

    def get_animation(self):
        """Get the current animation and its parameters."""
        with self.lock:
            return self.current_animation, self.params

# Initialize animation manager
animation_manager = AnimationManager()

# ============================================================================
# Animation Functions
# ============================================================================

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
                # Use a sinusoidal function for smooth fading
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))
                white = (int(255 * brightness),) * 3  # Scale white color
                pixels.fill(white)
                pixels.show()
                time.sleep(interval)

            # Fade out: Gradually decrease brightness
            for step in range(steps, -1, -1):
                brightness = 0.2 + 0.8 * math.sin((math.pi / 2) * (step / steps))
                white = (int(255 * brightness),) * 3  # Scale white color
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
