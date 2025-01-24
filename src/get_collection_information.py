# ----------------------------
# Imports
# ----------------------------

# Standard library imports
import os
import re
from datetime import datetime, timedelta

# Third-party imports
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ----------------------------
# Load Environment Variables
# ----------------------------

load_dotenv()

# ----------------------------
# Constants
# ----------------------------

URL = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
ADDRESS = os.environ["address"]
IFRAME_NAME = "recollect"
CELL_WIDTH = 62  # Adjusted for padding or spacing around cells
CELL_HEIGHT = 62  # Adjusted for padding or spacing around cells


# ----------------------------
# Main Function
# ----------------------------

def scrape_with_playwright():
    """
    Scrapes the Recology Shoreline Collection Calendar using Playwright
    and BeautifulSoup to retrieve collection schedules grouped by week.

    Returns:
        dict: A dictionary with week start dates as keys and collection
              information grouped by day.
    """
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the collection calendar page
            page.goto(URL)
            page.wait_for_selector("#row-input-0")

            # Enter the address and initiate the search
            page.fill("#row-input-0", ADDRESS)
            page.click("#rCbtn-search")
            page.wait_for_selector(f"iframe#{IFRAME_NAME}")

            # Switch to the iframe containing the calendar
            iframe = page.frame(name=IFRAME_NAME)
            if not iframe:
                print("Iframe not found")
                return None

            # Wait for the calendar table to load
            iframe.wait_for_selector("table.fc-border-separate")
            content = iframe.content()

            # Parse the iframe content with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            calendar_table = soup.find("table", class_="fc-border-separate")
            if not calendar_table:
                print("Calendar table not found")
                return None

            # ----------------------------
            # Extract Dates and Collections
            # ----------------------------

            dates = {}
            current_month = datetime.now().month
            current_year = datetime.now().year

            # Find all table cells with dates
            cells = calendar_table.find_all("td", {"data-date": True})
            for cell in cells:
                data_date = cell["data-date"]
                date_obj = datetime.strptime(data_date, "%Y-%m-%d")
                if date_obj.month == current_month and date_obj.year == current_year:
                    dates[data_date] = {"collections": []}

            # Extract collection events
            event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))
            events = []
            for event in event_divs:
                event_id = event.get("id")
                event_type = event_id.split("-")[1]  # Extract collection type
                event_styles = event.get("style", "")
                left_match = re.search(r"left: (\d+)", event_styles)
                top_match = re.search(r"top: (\d+)", event_styles)
                if left_match and top_match:
                    events.append({
                        "type": event_type,
                        "left": int(left_match.group(1)),
                        "top": int(top_match.group(1)),
                    })

            # Match event divs to table cells by inferred positions
            for event in events:
                adjusted_left = event["left"]
                adjusted_top = event["top"] - 2

                event_row = adjusted_top // CELL_HEIGHT
                event_col = adjusted_left // CELL_WIDTH

                cell_index = event_row * 7 + event_col  # Assuming 7 columns (days of the week)
                if 0 <= cell_index < len(cells):
                    data_date = cells[cell_index]["data-date"]
                    if data_date in dates:
                        if event["type"] not in dates[data_date]["collections"]:
                            dates[data_date]["collections"].append(event["type"])

            # ----------------------------
            # Group Dates into Weeks
            # ----------------------------

            weeks = {}
            for date_str, info in dates.items():
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                week_start = date_obj - timedelta(days=date_obj.weekday())  # Start of the week (Monday)
                week_start_str = week_start.strftime("%Y-%m-%d")

                if week_start_str not in weeks:
                    weeks[week_start_str] = []

                weeks[week_start_str].append({"date": date_str, "collections": info["collections"]})

            # Remove dates not in the current month
            for week_start in list(weeks.keys()):
                weeks[week_start] = [
                    day for day in weeks[week_start]
                    if datetime.strptime(day["date"], "%Y-%m-%d").month == current_month
                ]
                if not weeks[week_start]:  # Remove empty weeks
                    del weeks[week_start]

            # ----------------------------
            # Print Results (Optional)
            # ----------------------------

            for week_start, days in weeks.items():
                print(f"Week of {week_start}:")
                for day in days:
                    collections = ", ".join(day["collections"]) if day["collections"] else "No collections"
                    print(f"  Date: {day['date']}, Collections: {collections}")

            return weeks

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            # Ensure the browser is closed
            browser.close()
