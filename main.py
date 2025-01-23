from src.get_collection_information import scrape_with_playwright
from src.handle_schedule import save_schedule
from src.led_configuration import update_leds_today
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def run_process():
    logger.info('running process')
    today = datetime.now().day
    last_day_of_month = (datetime.now() + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    if today == 1 or today == last_day_of_month.day:
        # Run scraping at the beginning and end of the month
        logger.info('scraping recology site for collection dates')
        collections = scrape_with_playwright()
        save_schedule(collections)
        update_leds_today()
    else:
        # Update LEDs daily
        logger.info('running leds')
        update_leds_today()
    


if __name__ == '__main__':
    run_process()
