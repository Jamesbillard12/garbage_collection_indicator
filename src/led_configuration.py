import neopixel
import board
import time
from src.handle_schedule import load_schedule
from datetime import datetime, timedelta

# LED Strip Configuration
NUM_LEDS = 3  # Number of LEDs in your strip
PIN = board.D18  # GPIO pin connected to the LED strip
BRIGHTNESS = 0.5  # Brightness (0.0 to 1.0)

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_PURPLE = (128, 0, 128)  # Garbage
COLOR_GREEN = (0, 255, 0)  # Organics
COLOR_BLUE = (0, 0, 255)  # Recycling
COLOR_OFF = (0, 0, 0)

# Set up the LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# Helper Functions
def set_leds(garbage_on, organics_on, recycling_on):
    """Set LED colors based on collection status."""
    pixels[0] = COLOR_PURPLE if garbage_on else COLOR_WHITE
    pixels[1] = COLOR_GREEN if organics_on else COLOR_WHITE
    pixels[2] = COLOR_BLUE if recycling_on else COLOR_WHITE
    pixels.show()

def blink_leds(times=3, interval=0.5):
    """Blink LEDs sequentially."""
    for _ in range(times):
        for i in range(NUM_LEDS):
            pixels.fill(COLOR_OFF)  # Turn off all LEDs
            pixels[i] = pixels[i]  # Light up only the current LED
            pixels.show()
            time.sleep(interval)
        pixels.fill(COLOR_OFF)
        pixels.show()
        time.sleep(interval)

def update_leds_today():
    """Update LEDs based on today's and tomorrow's schedule."""
    schedule = load_schedule()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    for date_str, info in schedule.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        if date_obj == today:
            # Set LEDs solid for today's collections
            print(f"Today's collections: {info['collections']}")
            set_leds(
                "garbage" in info["collections"],
                "organics" in info["collections"],
                "recycling" in info["collections"],
            )

        elif date_obj == tomorrow:
            # Blink LEDs for tomorrow's collections
            print(f"Tomorrow's collections: {info['collections']}")
            blink_leds()

        else:
            # Turn off LEDs for other days
            pixels.fill(COLOR_OFF)
            pixels.show()