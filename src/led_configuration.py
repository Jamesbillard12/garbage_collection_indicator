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


def fade_groups(daily_schedule, steps=50, delay=0.05):
    """Fade multiple LED groups with overlapping transitions."""
    print(f"Fading LEDs with overlap for: {daily_schedule['collections']}")

    # Determine colors for each group
    garbage_color = COLOR_PURPLE if "garbage" in daily_schedule["collections"] else COLOR_WHITE
    organics_color = COLOR_GREEN if "organics" in daily_schedule["collections"] else COLOR_WHITE
    recycling_color = COLOR_BLUE if "recycling" in daily_schedule["collections"] else COLOR_WHITE

    # Define the groups and their colors
    groups = [
        {"start": 0, "end": 8, "start_color": COLOR_OFF, "end_color": garbage_color},
        {"start": 8, "end": 16, "start_color": COLOR_OFF, "end_color": organics_color},
        {"start": 16, "end": 24, "start_color": COLOR_OFF, "end_color": recycling_color},
    ]

    # Extract RGB component deltas for each group
    for group in groups:
        start_r, start_g, start_b = group["start_color"]
        end_r, end_g, end_b = group["end_color"]
        group["step_r"] = (end_r - start_r) / steps
        group["step_g"] = (end_g - start_g) / steps
        group["step_b"] = (end_b - start_b) / steps

    # Perform overlapping fades
    for step in range(steps + 1):
        for group in groups:
            # Calculate current color for this group
            current_r = int(group["start_color"][0] + step * group["step_r"])
            current_g = int(group["start_color"][1] + step * group["step_g"])
            current_b = int(group["start_color"][2] + step * group["step_b"])

            # Update the LEDs in this group
            for i in range(group["start"], group["end"]):
                pixels[i] = (current_r, current_g, current_b)

        # Apply the changes to all LEDs
        pixels.show()

        # Delay between steps
        time.sleep(delay)



def fade_leds(daily_schedule, steps=50, interval=0.5):
    """Fade each group of LEDs sequentially."""
    print(f"Fading LEDs for: {daily_schedule['collections']}")

    # Determine colors for each group
    garbage_color = COLOR_PURPLE if "garbage" in daily_schedule["collections"] else COLOR_WHITE
    organics_color = COLOR_GREEN if "organics" in daily_schedule["collections"] else COLOR_WHITE
    recycling_color = COLOR_BLUE if "recycling" in daily_schedule["collections"] else COLOR_WHITE

    # Fade each group sequentially
    fade_group(COLOR_OFF, garbage_color, 0, 8, steps, interval)
    fade_group(garbage_color, COLOR_OFF, 0, 8, steps, interval)

    fade_group(COLOR_OFF, organics_color, 8, 16, steps, interval)
    fade_group(organics_color, COLOR_OFF, 8, 16, steps, interval)

    fade_group(COLOR_OFF, recycling_color, 16, 24, steps, interval)
    fade_group(recycling_color, COLOR_OFF, 16, 24, steps, interval)




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

            # Check for today's collections
            if date_obj == today and len(daily_schedule["collections"]) > 0:
                print(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                fade_leds(daily_schedule, steps=100, interval=0.02)  # Fade lights for today
                today_or_tomorrow_handled = True

            # Check for tomorrow's collections
            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                print(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                fade_leds(daily_schedule, steps=100, interval=0.02)  # Fade lights for tomorrow
                today_or_tomorrow_handled = True

            # Collect all upcoming collections for the week (after today)
            elif date_obj > today and len(daily_schedule["collections"]) > 0:
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
        print("No collections found for today, tomorrow, or the rest of the week. Turning off LEDs.")
        pixels.fill(COLOR_OFF)
        pixels.show()
