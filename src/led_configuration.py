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


def fade_group(start_color, end_color, group_start, group_end, steps=50, delay=0.05):
    """
    Fades a specific group of LEDs from one color to another.

    Args:
        start_color (tuple): The starting RGB color (R, G, B).
        end_color (tuple): The ending RGB color (R, G, B).
        group_start (int): Start index of the LED group.
        group_end (int): End index (exclusive) of the LED group.
        steps (int): Number of steps for the transition.
        delay (float): Delay in seconds between each step.
    """
    # Extract RGB components
    start_r, start_g, start_b = start_color
    end_r, end_g, end_b = end_color

    # Calculate step size for each color component
    step_r = (end_r - start_r) / steps
    step_g = (end_g - start_g) / steps
    step_b = (end_b - start_b) / steps

    # Fade over the specified number of steps
    for step in range(steps + 1):
        # Calculate current color
        current_r = int(start_r + step * step_r)
        current_g = int(start_g + step * step_g)
        current_b = int(start_b + step * step_b)

        # Update the specified group of LEDs
        for i in range(group_start, group_end):
            pixels[i] = (current_r, current_g, current_b)
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
    """Update LEDs based on today's and tomorrow's schedule."""
    schedule = load_schedule()
    print("Schedule:", schedule)  # Debugging print to ensure schedule is loaded

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Iterate through the schedule
    for week_key, daily_schedules in schedule.items():
        for daily_schedule in daily_schedules:
            date_obj = datetime.strptime(daily_schedule["date"], "%Y-%m-%d").date()

            if date_obj == today and len(daily_schedule["collections"]) > 0:
                # Set LEDs solid for today's collections
                print(f"Today's collections ({date_obj}): {daily_schedule['collections']}")
                set_leds(
                    "garbage" in daily_schedule["collections"],
                    "organics" in daily_schedule["collections"],
                    "recycling" in daily_schedule["collections"],
                )

            elif date_obj == tomorrow and len(daily_schedule["collections"]) > 0:
                # Blink LEDs for tomorrow's collections
                print(f"Tomorrow's collections ({date_obj}): {daily_schedule['collections']}")
                fade_leds(daily_schedule, steps=100, interval=0.02)


    # Turn off LEDs if no match for today or tomorrow
    pixels.fill(COLOR_OFF)
    pixels.show()
