from src.get_collection_information import scrape_with_playwright
from src.handle_schedule import save_schedule
from src.led_configuration import update_leds_today
import logging
from datetime import datetime, timedelta
import time
import threading

logger = logging.getLogger(__name__)

def run_process():
    logger.info('Running process')
    today = datetime.now().day
    last_day_of_month = (datetime.now() + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    if today == 1 or today == last_day_of_month.day:
        # Run scraping at the beginning and end of the month
        logger.info('Scraping recology site for collection dates')
        collections = scrape_with_playwright()
        save_schedule(collections)
        update_leds_today()
    else:
        # Update LEDs daily
        logger.info('Running LEDs')
        update_leds_today()

def schedule_daily_run(hour=6, minute=0):
    """Schedule the process to run daily at a specific time."""
    def run_at_scheduled_time():
        while True:
            now = datetime.now()
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the scheduled time has already passed for today, schedule it for tomorrow
            if now > scheduled_time:
                scheduled_time += timedelta(days=1)

            # Calculate the wait time in seconds
            wait_time = (scheduled_time - now).total_seconds()
            logger.info(f"Next run scheduled at: {scheduled_time}. Waiting for {wait_time} seconds.")

            # Wait until the scheduled time
            time.sleep(wait_time)

            # Run the process
            run_process()

    # Start the scheduling in a separate thread
    scheduler_thread = threading.Thread(target=run_at_scheduled_time, daemon=True)
    scheduler_thread.start()

if __name__ == '__main__':
    logger.info("Starting LED scheduling program...")

    # Run the process immediately once on start
    run_process()

    # Schedule the daily run
    schedule_daily_run(hour=6, minute=0)  # Schedule to run at 6:00 AM daily

    # Keep the program running
    while True:
        time.sleep(1)
