import neopixel
import board
import time
from src.handle_schedule import load_schedule
from datetime import datetime, timedelta

# LED Strip Configuration
NUM_LEDS = 24  # Number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

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
    """Set LED colors based on collection status for groups of 8 LEDs."""
    print(f"Setting LEDs: Garbage={garbage_on}, Organics={organics_on}, Recycling={recycling_on}")  # Debugging

    # Group configurations
    garbage_color = COLOR_PURPLE if garbage_on else COLOR_OFF  # Garbage group
    organics_color = COLOR_GREEN if organics_on else COLOR_OFF  # Organics group
    recycling_color = COLOR_BLUE if recycling_on else COLOR_OFF  # Recycling group

    # Assign colors to groups of 8
    for i in range(8):
        pixels[i] = garbage_color  # First group (garbage)
        pixels[i + 8] = organics_color  # Second group (organics)
        pixels[i + 16] = recycling_color  # Third group (recycling)

    # Apply changes to the strip
    pixels.show()


def blink_leds(daily_schedule, times=3, interval=0.5):
    """Blink each group of LEDs sequentially."""
    print(f"Blinking LEDs for: {daily_schedule['collections']}")

    # Determine the colors for each group
    garbage_color = COLOR_PURPLE if "garbage" in daily_schedule["collections"] else COLOR_OFF
    organics_color = COLOR_GREEN if "organics" in daily_schedule["collections"] else COLOR_OFF
    recycling_color = COLOR_BLUE if "recycling" in daily_schedule["collections"] else COLOR_OFF

    for _ in range(times):
        # Blink the garbage group (LEDs 0–7)
        for i in range(8):
            pixels[i] = garbage_color
        pixels.show()
        time.sleep(interval)
        for i in range(8):
            pixels[i] = COLOR_OFF  # Turn off garbage group
        pixels.show()

        # Blink the organics group (LEDs 8–15)
        for i in range(8, 16):
            pixels[i] = organics_color
        pixels.show()
        time.sleep(interval)
        for i in range(8, 16):
            pixels[i] = COLOR_OFF  # Turn off organics group
        pixels.show()

        # Blink the recycling group (LEDs 16–23)
        for i in range(16, 24):
            pixels[i] = recycling_color
        pixels.show()
        time.sleep(interval)
        for i in range(16, 24):
            pixels[i] = COLOR_OFF  # Turn off recycling group
        pixels.show()

        # Optional: Short pause between full cycles
        time.sleep(interval)



def update_leds_today():
    """Update LEDs based on today's and tomorrow's schedule."""
    schedule = load_schedule()
    print("Schedule:", schedule)  # Debugging print to ensure schedule is loaded

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Iterate through the schedule
    for week_key, daily_schedules in schedule.items():
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            if date_obj == today:
                # Set LEDs solid for today's collections
                print(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                set_leds(
                    "garbage" in daily_schedule["collections"],
                    "organics" in daily_schedule["collections"],
                    "recycling" in daily_schedule["collections"],
                )

            elif date_obj == tomorrow:
                # Blink LEDs for tomorrow's collections
                print(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                blink_leds(daily_schedule)

    # Turn off LEDs if no match for today or tomorrow
    pixels.fill(COLOR_OFF)
    pixels.show()
