import neopixel
import board
import time
from src.handle_schedule import load_schedule
from datetime import datetime, timedelta
import atexit

# LED Strip Configuration
NUM_LEDS = 24  # Number of LEDs in your strip
PIN = board.D10  # GPIO pin connected to the LED strip
BRIGHTNESS = 1  # Brightness (0.0 to 1.0)

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_PURPLE = (128, 0, 128)  # Garbage
COLOR_GREEN = (0, 255, 0)  # Organics
COLOR_BLUE = (0, 0, 255)  # Recycling
COLOR_RED = (255, 0, 0)  # Holiday
COLOR_OFF = (0, 0, 0)

# Set up the LED strip
pixels = neopixel.NeoPixel(PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# Helper Functions
def set_leds(garbage_on, organics_on, recycling_on):
    """Set LED colors based on collection status for groups of 8 LEDs."""
    print(f"Setting LEDs: Garbage={garbage_on}, Organics={organics_on}, Recycling={recycling_on}")

    # Group configurations
    garbage_color = COLOR_PURPLE if garbage_on else COLOR_WHITE  # Garbage group
    organics_color = COLOR_GREEN if organics_on else COLOR_WHITE  # Organics group
    recycling_color = COLOR_BLUE if recycling_on else COLOR_WHITE  # Recycling group

    # Assign colors to groups of 8
    for i in range(8):
        pixels[i] = garbage_color  # First group (garbage)
        pixels[i + 8] = organics_color  # Second group (organics)
        pixels[i + 16] = recycling_color  # Third group (recycling)

    # Apply changes to the strip
    pixels.show()


def set_holiday_lights():
    """Set all LEDs to solid red for a holiday."""
    print("Setting LEDs to solid red for holiday.")
    pixels.fill(COLOR_RED)
    pixels.show()


def fade_groups_cycling(daily_schedule, steps=50, delay=0.05):
    """Cycle fades where one group fades in while the others fade out in a continuous loop."""
    print(f"Cycling fade for LEDs with overlap for: {daily_schedule['collections']}")

    # Determine colors for each group
    garbage_color = COLOR_PURPLE if "garbage" in daily_schedule["collections"] else COLOR_WHITE
    organics_color = COLOR_GREEN if "organics" in daily_schedule["collections"] else COLOR_WHITE
    recycling_color = COLOR_BLUE if "recycling" in daily_schedule["collections"] else COLOR_WHITE

    # Define the groups and their colors
    groups = [
        {"start": 0, "end": 8, "color": garbage_color},
        {"start": 8, "end": 16, "color": organics_color},
        {"start": 16, "end": 24, "color": recycling_color},
    ]

    # Cycling fade logic
    while True:  # Infinite cycle
        for i, group in enumerate(groups):
            next_group = groups[(i + 1) % len(groups)]  # Get the next group in the sequence

            for step in range(steps + 1):
                fade_in_ratio = step / steps
                fade_out_ratio = 1 - fade_in_ratio

                # Fade out current group
                current_r = int(group["color"][0] * fade_out_ratio)
                current_g = int(group["color"][1] * fade_out_ratio)
                current_b = int(group["color"][2] * fade_out_ratio)
                for j in range(group["start"], group["end"]):
                    pixels[j] = (current_r, current_g, current_b)

                # Fade in next group
                next_r = int(next_group["color"][0] * fade_in_ratio)
                next_g = int(next_group["color"][1] * fade_in_ratio)
                next_b = int(next_group["color"][2] * fade_in_ratio)
                for j in range(next_group["start"], next_group["end"]):
                    pixels[j] = (next_r, next_g, next_b)

                # Apply the changes to all LEDs
                pixels.show()

                # Delay between steps
                time.sleep(delay)


def fade_leds(daily_schedule, steps=50, interval=0.05):
    """Fade LEDs for a schedule using the cycling fade_groups method."""
    fade_groups_cycling(daily_schedule, steps=steps, delay=interval)


def update_leds_today():
    """Update LEDs based on the upcoming schedule, with special handling for today and tomorrow."""
    schedule = load_schedule()
    print("Schedule:", schedule)  # Debugging print to ensure schedule is loaded

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    upcoming_collections = []  # Store collection types for the week
    today_or_tomorrow_handled = False  # Flag to check if today/tomorrow was handled

    # Iterate through the schedule
    for week_key, daily_schedules in schedule.items():
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            # Check for holidays
            if "holiday" in daily_schedule["collections"]:
                print(f"Holiday detected on {date_obj}. Turning lights solid red.")
                set_holiday_lights()
                return

            # Check for today's collections
            if date_obj == today and len(daily_schedule["collections"]) > 0:
                print(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                fade_leds(daily_schedule, steps=100, interval=0.02)  # Fade lights for today
                today_or_tomorrow_handled = True

            # Check for tomorrow's collections
            elif date_obj == tomorrow and len(daily_schedule["collections"]):
                print(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                fade_leds(daily_schedule, steps=100, interval=0.02)  # Fade lights for tomorrow
                today_or_tomorrow_handled = True

            # Collect all upcoming collections for the week (after today)
            elif date_obj > today and len(daily_schedule["collections"]):
                upcoming_collections.extend(daily_schedule["collections"])

    # If no today/tomorrow collections were handled, show solid lights for the week's upcoming collections
    if not today_or_tomorrow_handled and upcoming_collections:
        print(f"Upcoming collections this week: {set(upcoming_collections)}")
        set_leds(
            "garbage" in upcoming_collections,
            "organics" in upcoming_collections,
            "recycling" in upcoming_collections,
        )
    elif not today_or_tomorrow_handled:
        # No collections at all for the week
        print("No collections found for today, tomorrow, or the rest of the week. Keeping LEDs as-is.")

# Ensure LEDs are turned off when the program exits
def turn_off_leds():
    print("Turning off LEDs.")
    pixels.fill(COLOR_OFF)
    pixels.show()

# Register the turn_off_leds function to run on exit
atexit.register(turn_off_leds)
