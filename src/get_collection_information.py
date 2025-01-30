from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

def group_by_week(collection_data):
    """
    Organizes the collection data into weeks where each week starts on a Monday.

    :param collection_data: A dictionary where keys are dates (YYYY-MM-DD)
                            and values are lists of collection types.
    :return: A dictionary grouped by week start dates.
    """
    sorted_dates = sorted(collection_data.keys(), key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
    weeks = {}

    for date_str in sorted_dates:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        week_start = date_obj - timedelta(days=date_obj.weekday())  # Get Monday of the week
        week_start_str = week_start.strftime("%Y-%m-%d")

        if week_start_str not in weeks:
            weeks[week_start_str] = []

        weeks[week_start_str].append({
            "date": date_str,
            "collections": collection_data[date_str]
        })

    return weeks

def scrape_with_playwright():
    url = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    address = os.getenv("address")  # Use os.getenv to prevent crashes

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Run in headless mode
        context = browser.new_context()
        page = context.new_page()

        # Open the Recology Shoreline Collection Calendar page
        page.goto(url)

        # Wait for the address input field to load
        page.wait_for_selector("#row-input-0")

        # Enter the address
        page.fill("#row-input-0", address)

        # Click the search button (it's an <a> tag)
        page.click("#rCbtn-search")

        # Wait for the iframe to load after the search
        page.wait_for_selector("iframe#recollect-frame")

        # Switch to the iframe
        iframe = page.frame(name="recollect")
        if not iframe:
            print("Iframe not found")
            return

        # Wait for the calendar and events to fully load
        iframe.wait_for_selector("table.fc-border-separate", timeout=10000)
        iframe.wait_for_selector("div[id^='rCevt-']", timeout=10000)

        # Extract calendar data using Playwright
        calendar_data = iframe.evaluate('''() => {
            let result = {};
            document.querySelectorAll("td[data-date]").forEach(td => {
                let date = td.getAttribute("data-date");
                let events = Array.from(document.querySelectorAll("div[id^='rCevt-']"))  
                                  .filter(div => div.closest("td") === td)  // Only match inside this cell
                                  .map(div => div.id.split('-')[1]);  

                result[date] = events.length > 0 ? [...new Set(events)] : [];
            });
            return result;
        }''')

        # Organize data into weeks
        grouped_weeks = group_by_week(calendar_data)

        # Log the grouped results
        for week_start, days in grouped_weeks.items():
            logger.info(f"Week of {week_start}:")
            for day in days:
                collections_str = ", ".join(day["collections"]) if day["collections"] else "No collections"
                logger.info(f"  Date: {day['date']}, Collections: {collections_str}")

        browser.close()
        return grouped_weeks