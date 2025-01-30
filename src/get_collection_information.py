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

        # Extract calendar table and event divs
        soup = BeautifulSoup(iframe.content(), "html.parser")

        # Extract all date cells with events
        dates = {}

        for td in soup.find_all("td", {"data-date": True}):
            data_date = td["data-date"]
            events = td.find_all("div", id=re.compile(r"^rCevt-"))

            # Extract collection types and remove duplicates
            collections = list(set(event["id"].split("-")[1] for event in events))

            # Store only non-empty days
            if collections:
                dates[data_date] = collections
            else:
                dates[data_date] = ["No collections"]

        # Log the results
        for date, collections in sorted(dates.items()):
            collections_str = ", ".join(collections)
            logger.info(f"Date: {date}, Collections: {collections_str}")

        browser.close()
        return dates
