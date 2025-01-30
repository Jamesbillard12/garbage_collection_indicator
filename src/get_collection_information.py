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

        # Constants based on computed styles
        row_height = 55  # Each week row is 55px tall
        event_stack_height = 16  # Each event within a day increases top by 16px
        first_event_top = 31  # The first event in a week starts at 31px

        # Mapping of `left` positions to days of the week (Sunday-starting)
        day_mapping = {
            4: 0,    # Sunday (Estimate)
            74: 1,   # Monday
            144: 2,  # Tuesday (Estimate)
            214: 3,  # Wednesday
            284: 4,  # Thursday
            354: 5,  # Friday (Estimate)
            424: 6   # Saturday (Estimate)
        }

        # Match event divs to table cells dynamically
        for event in event_divs:
            event_id = event.get("id")
            event_type = event_id.split("-")[1]  # Extract type (e.g., garbage, recycling)
            event_styles = event.get("style", "")

            # Extract `top` and `left` positions
            event_top_match = re.search(r"top: (\d+)px", event_styles)
            event_left_match = re.search(r"left: (\d+)px", event_styles)

            if event_top_match and event_left_match:
                event_top = int(event_top_match.group(1))
                event_left = int(event_left_match.group(1))

                # Determine the week based on `top`
                week_index = (event_top - first_event_top) // row_height  # Row in the calendar

                # Find the correct day using `left`
                closest_day = min(day_mapping.keys(), key=lambda x: abs(x - event_left))
                day_index = day_mapping[closest_day]  # Convert `left` to day of the week (Sunday start)

                # Get Sunday of each week
                week_start_dates = sorted(set(dates.keys()))[::7]  # Get Sundays for each week
                if 0 <= week_index < len(week_start_dates):
                    week_start = week_start_dates[week_index]

                    # Compute the correct date for this event
                    event_date_obj = datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=day_index)
                    event_date = event_date_obj.strftime("%Y-%m-%d")

                    # Assign the event to the correct date
                    if event_date in dates and event_type not in dates[event_date]["collections"]:
                        dates[event_date]["collections"].append(event_type)

        # Fix week grouping and remove empty first week
        weeks = {}

        for date_str, info in sorted(dates.items()):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            # Get the correct Sunday start for this week
            week_start = date_obj - timedelta(days=date_obj.weekday() + 1)  # Adjust for Sunday-based weeks
            week_start_str = week_start.strftime("%Y-%m-%d")

            # Ensure this Sunday exists in the dictionary
            if week_start_str not in weeks:
                weeks[week_start_str] = []

            # Handle holiday shifts
            if "holiday" in info["collections"]:
                # Move collection to the next day
                new_date_obj = date_obj + timedelta(days=1)
                new_date_str = new_date_obj.strftime("%Y-%m-%d")

                if new_date_str not in weeks:
                    weeks[new_date_str] = []

                weeks[new_date_str].append({
                    "date": new_date_str,
                    "collections": [c for c in info["collections"] if c != "holiday"]
                })
            else:
                # Add to the correct week
                weeks[week_start_str].append({
                    "date": date_str,
                    "collections": info["collections"]
                })

        # **Remove empty first week if it has no collections**
        first_week = min(weeks.keys())  # Get the first recorded week
        if all(len(day["collections"]) == 0 for day in weeks[first_week]):
            del weeks[first_week]  # Remove the week if it's empty

        # Log the results
        logger.info(f"Final Weekly Schedule: {weeks}")

        browser.close()
        return weeks