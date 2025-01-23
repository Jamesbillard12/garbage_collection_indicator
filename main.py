import logging
import time
from datetime import datetime, timedelta
from src.get_collection_information import scrape_with_playwright
from src.handle_schedule import save_schedule, load_schedule
from src.led_configuration import update_leds_today, blink_red_and_turn_off, pulsate_white
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def is_beginning_or_end_of_month():
    """Check if today is the beginning or end of the month."""
    today = datetime.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    return today == first_day or today == last_day

def has_valid_collections(collections):
    """Check if the collections data contains any non-empty collections."""
    for week_key, daily_schedules in collections.items():
        for daily_schedule in daily_schedules:
            if len(daily_schedule.get("collections", [])) > 0:
                return True  # Found valid collections
    return False  # No valid collections found

def fetch_and_update_leds():
    """
    Fetch the collection data, save it, and update the LEDs.
    Re-fetch if no valid data is found.
    """
    threading.Thread(target=pulsate_white, daemon=True)
    try:
        logger.info("Fetching collection data on application start...")
        collections = scrape_with_playwright()
        save_schedule(collections)

        # Validate the fetched data
        if has_valid_collections(collections):
            logger.info("Valid collections found. Updating LEDs...")
            update_leds_today()
        else:
            logger.warning("No valid collections found on initial fetch. Re-fetching data...")
            collections = scrape_with_playwright()
            save_schedule(collections)

            # Validate again after re-fetching
            if has_valid_collections(collections):
                logger.info("Valid collections found after re-fetching. Updating LEDs...")
                update_leds_today()
            else:
                logger.error("No valid collections found even after re-fetching. Turning off LEDs as a fallback.")
                blink_red_and_turn_off()
    except Exception as e:
        logger.error(f"Failed to fetch or update LEDs: {e}")
        blink_red_and_turn_off()  # Turn off LEDs on failure

def load_or_fetch_schedule_and_update_leds():
    """
    Load the schedule or fetch new data if:
    - It's the beginning or end of the month.
    - No valid data is found in the loaded schedule.
    """
    try:
        if is_beginning_or_end_of_month():
            logger.info("It's the beginning or end of the month. Fetching new collection data...")
            collections = scrape_with_playwright()
            save_schedule(collections)
        else:
            logger.info("Loading existing schedule data...")
            collections = load_schedule()

        # Validate the data (loaded or fetched)
        if has_valid_collections(collections):
            logger.info("Valid collections found. Updating LEDs...")
            update_leds_today()
        else:
            logger.warning("No valid collections found in loaded schedule. Re-fetching data...")
            collections = scrape_with_playwright()
            save_schedule(collections)

            # Validate again after re-fetching
            if has_valid_collections(collections):
                logger.info("Valid collections found after re-fetching. Updating LEDs...")
                update_leds_today()
            else:
                logger.error("No valid collections found even after re-fetching. Turning off LEDs as a fallback.")
                blink_red_and_turn_off()
    except Exception as e:
        logger.error(f"Failed to load, fetch, or update LEDs: {e}")
        blink_red_and_turn_off()  # Turn off LEDs on failure

def schedule_daily_run(hour=6, minute=0):
    """
    Schedule the process to run daily at a specific time.
    """
    def run_at_scheduled_time():
        while True:
            now = datetime.now()
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the scheduled time has already passed today, set it for tomorrow
            if now > scheduled_time:
                scheduled_time += timedelta(days=1)

            # Calculate the wait time in seconds
            wait_time = (scheduled_time - now).total_seconds()
            logger.info(f"Next run scheduled at: {scheduled_time}. Waiting for {wait_time} seconds.")

            # Wait until the scheduled time
            time.sleep(wait_time)

            # Run the process at the scheduled time
            load_or_fetch_schedule_and_update_leds()

    # Run the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_at_scheduled_time, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    logger.info("Starting Garbage Collection Indicator...")

    # Schedule the daily run at 6:00 AM
    schedule_daily_run(hour=6, minute=0)

    # Run fetch and update process immediately on startup
    fetch_and_update_leds()

    # Keep the application running
    while True:
        time.sleep(1)
