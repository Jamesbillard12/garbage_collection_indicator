from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import os
import logging

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)


def scrape_with_playwright():
    url = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    address = os.getenv("address")  # Use os.getenv to handle missing values gracefully

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set headless=False for debugging
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

        # Get the iframe content
        iframe = page.frame(name="recollect")
        if not iframe:
            print("Iframe not found")
            return

        # Wait for the calendar to load inside the iframe
        iframe.wait_for_selector("table.fc-border-separate")

        # Extract page source
        content = iframe.content()
        soup = BeautifulSoup(content, "html.parser")

        # Extract all calendar date cells
        cells = soup.find_all("td", {"data-date": True})
        dates = {cell["data-date"]: {"collections": []} for cell in cells}

        # Extract collection events
        event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))
        for event in event_divs:
            event_type = event["id"].split("-")[1]  # e.g., "garbage", "recycling"

            # Find the closest parent that aligns with the calendar
            parent_td = event.find_parent("td", {"data-date": True})
            if parent_td:
                data_date = parent_td["data-date"]
                if data_date in dates:
                    dates[data_date]["collections"].append(event_type)

        # If events are still not inside TDs, infer positions based on ordering
        if not any(dates[d]["collections"] for d in dates):
            all_dates = list(dates.keys())  # Ordered list of date strings

            # Extract event elements and align them sequentially to the date order
            for i, event in enumerate(event_divs):
                event_type = event["id"].split("-")[1]
                if i < len(all_dates):  # Ensure index is within bounds
                    dates[all_dates[i]]["collections"].append(event_type)

        # Log and return data
        for date, info in dates.items():
            collections_str = ", ".join(info["collections"]) if info["collections"] else "No collections"
            logger.info(f"Date: {date}, Collections: {collections_str}")

        browser.close()
        return dates
