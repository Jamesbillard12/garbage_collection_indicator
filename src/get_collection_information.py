from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import os
from datetime import datetime, timedelta
import logging

load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)


def scrape_with_playwright():
    url = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    address = os.getenv("address")  # Use os.getenv to prevent crashes

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Use headless=True for headless mode
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
            logger.error("Iframe not found")
            return

        # Wait for the calendar to load inside the iframe
        iframe.wait_for_selector("table.fc-border-separate")

        # Get the iframe content
        content = iframe.content()
        soup = BeautifulSoup(content, "html.parser")

        # Locate the table with the class 'fc-border-separate'
        calendar_table = soup.find("table", class_="fc-border-separate")
        if not calendar_table:
            logger.error("Calendar table not found")
            return

        # Extract all table rows, ensuring we skip the first row (header row)
        rows = calendar_table.find_all("tr")[1:]  # Skip <thead> (Days of the Week)

        # Extract all date-containing cells (td[data-date])
        cells = [td for row in rows for td in row.find_all("td", {"data-date": True})]

        # Ensure cells are sorted correctly by date
        sorted_cells = sorted(cells, key=lambda td: td["data-date"])

        # Extract dates dictionary
        dates = {cell["data-date"]: {"collections": []} for cell in sorted_cells}

        # Extract collection event divs
        event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))

        # Assume each row height is ~62px, and subtract the <thead> height (28px)
        row_height = 62
        thead_height = 28

        # Compute estimated Y positions for each date cell
        cell_positions = {}
        for i, cell in enumerate(sorted_cells):
            cell_positions[cell["data-date"]] = (i // 7) * row_height + thead_height  # Calculate Y position

        # Match event divs to table cells dynamically
        for event in event_divs:
            event_id = event.get("id")
            event_type = event_id.split("-")[1]  # Extract type (e.g., garbage, recycling)
            event_styles = event.get("style", "")
            event_top_match = re.search(r"top: (\d+)", event_styles)

            if event_top_match:
                event_top = int(event_top_match.group(1)) - thead_height  # Adjust for <thead> height

                # Find the closest matching `td[data-date]` based on vertical position
                closest_date = min(cell_positions, key=lambda date: abs(cell_positions[date] - event_top))

                # Assign the event to the correct date
                if event_type not in dates[closest_date]["collections"]:
                    dates[closest_date]["collections"].append(event_type)

        # Group dates into weeks
        weeks = {}
        for date_str, info in dates.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            week_start = date_obj - timedelta(days=date_obj.weekday())  # Get the start of the week (Monday)
            week_start_str = week_start.strftime("%Y-%m-%d")

            if week_start_str not in weeks:
                weeks[week_start_str] = []

            weeks[week_start_str].append({"date": date_str, "collections": info["collections"]})

        # Log the results
        for week_start, days in weeks.items():
            logger.info(f"Week of {week_start}:")
            for day in days:
                collections = ", ".join(day["collections"]) if day["collections"] else "No collections"
                logger.info(f"  Date: {day['date']}, Collections: {collections}")

        browser.close()
        return weeks