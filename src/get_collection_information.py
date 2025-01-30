from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
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
        browser = p.chromium.launch(headless=False)  # Set headless=False for debugging
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

        # Wait for events to load inside the iframe
        iframe.wait_for_selector("div[id^='rCevt-']", timeout=5000)

        # Extract calendar data using Playwright's JS execution
        calendar_data = iframe.evaluate('''() => {
            let result = {};
            document.querySelectorAll("td[data-date]").forEach(td => {
                let date = td.getAttribute("data-date");
                let events = Array.from(td.querySelectorAll("div[id^='rCevt-']"))
                                  .map(div => div.id.split('-')[1]);  // Extract event type

                result[date] = events.length > 0 ? [...new Set(events)] : ["No collections"];
            });
            return result;
        }''')

        # Log and return data
        for date, collections in sorted(calendar_data.items()):
            collections_str = ", ".join(collections)
            logger.info(f"Date: {date}, Collections: {collections_str}")

        browser.close()
        return calendar_data
