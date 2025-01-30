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
    address = os.getenv("address")  # Use os.getenv to prevent crashes

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

        # Switch to the iframe
        iframe = page.frame(name="recollect")
        if not iframe:
            print("Iframe not found")
            return

        # Wait for the calendar to load inside the iframe
        iframe.wait_for_selector("table.fc-border-separate")

        # Extract all calendar date cells
        cells = iframe.query_selector_all("td[data-date]")
        dates = {cell.get_attribute("data-date"): {"collections": []} for cell in cells}

        # Extract event elements
        event_divs = iframe.query_selector_all("div[id^='rCevt-']")

        for event in event_divs:
            event_type = event.get_attribute("id").split("-")[1]  # e.g., "garbage", "recycling"

            # Get event's on-screen position
            event_box = event.bounding_box()
            if not event_box:
                continue  # Skip if bounding box is not available

            event_x, event_y = event_box["x"], event_box["y"]

            # Find the nearest td based on Y position
            closest_td = None
            min_distance = float("inf")

            for cell in cells:
                cell_box = cell.bounding_box()
                if not cell_box:
                    continue

                cell_x, cell_y = cell_box["x"], cell_box["y"]

                # Compute vertical distance
                distance = abs(event_y - cell_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_td = cell

            # If we found a match, assign the event to that date
            if closest_td:
                data_date = closest_td.get_attribute("data-date")
                if data_date in dates:
                    dates[data_date]["collections"].append(event_type)

        # Log and return data
        for date, info in dates.items():
            collections_str = ", ".join(info["collections"]) if info["collections"] else "No collections"
            logger.info(f"Date: {date}, Collections: {collections_str}")

        browser.close()
        return dates
