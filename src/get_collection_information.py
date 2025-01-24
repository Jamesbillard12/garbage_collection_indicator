# ----------------------------
# Imports
# ----------------------------

import os
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ----------------------------
# Configuration
# ----------------------------

# Load environment variables
load_dotenv()

# ----------------------------
# Main Function
# ----------------------------

def scrape_with_playwright():
    """
    Main function to scrape the Recology collection calendar using Playwright.
    """
    url = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    address = os.environ["address"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the calendar page and retrieve iframe content
            _navigate_to_calendar_page(page, url, address)
            iframe_content = _get_iframe_content(page)

            # Extract data and process it
            dates = _extract_calendar_dates(iframe_content)
            events = _extract_collection_events(iframe_content)
            _map_events_to_dates(events, dates)
            weeks = _group_dates_into_weeks(dates)

            # Print and return results
            _print_weeks(weeks)
            return weeks
        finally:
            browser.close()

# ----------------------------
# Helper Functions
# ----------------------------

def _navigate_to_calendar_page(page, url, address):
    """
    Navigate to the collection calendar page and enter the address.
    """
    page.goto(url)
    page.wait_for_selector("#row-input-0")
    page.fill("#row-input-0", address)
    page.click("#rCbtn-search")
    page.wait_for_selector("iframe#recollect-frame")

def _get_iframe_content(page):
    """
    Retrieve the content of the iframe containing the calendar.
    """
    iframe = page.frame(name="recollect")
    if not iframe:
        raise Exception("Iframe not found")
    iframe.wait_for_selector("table.fc-border-separate")
    return iframe.content()

# ----------------------------
# Data Extraction Functions
# ----------------------------

def _extract_calendar_dates(content):
    """
    Extract dates from the calendar table.
    """
    soup = BeautifulSoup(content, "html.parser")
    calendar_table = soup.find("table", class_="fc-border-separate")
    if not calendar_table:
        raise Exception("Calendar table not found")

    current_month = datetime.now().month
    current_year = datetime.now().year
    dates = {}

    cells = calendar_table.find_all("td", {"data-date": True})
    for cell in cells:
        data_date = cell["data-date"]
        date_obj = datetime.strptime(data_date, "%Y-%m-%d")
        if date_obj.month == current_month and date_obj.year == current_year:
            dates[data_date] = {"collections": []}

    return dates

def _extract_collection_events(content):
    """
    Extract collection events from the iframe content.
    """
    soup = BeautifulSoup(content, "html.parser")
    event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))
    events = []

    for event in event_divs:
        event_id = event.get("id")
        event_type = event_id.split("-")[1]  # Extract type (e.g., garbage, recycling)
        event_styles = event.get("style", "")
        event_left = _extract_css_value(event_styles, "left")
        event_top = _extract_css_value(event_styles, "top")
        if event_left is not None and event_top is not None:
            events.append({
                "type": event_type,
                "left": event_left,
                "top": event_top,
            })

    return events

def _extract_css_value(style, property_name):
    """
    Extract numerical value of a CSS property from a style string.
    """
    match = re.search(fr"{property_name}: (\d+)", style)
    return int(match.group(1)) if match else None

# ----------------------------
# Data Mapping and Grouping
# ----------------------------

def _map_events_to_dates(events, dates):
    """
    Map collection events to their corresponding dates.
    """
    cell_width, cell_height = 62, 62  # Adjusted for spacing
    cells = list(dates.keys())

    for event in events:
        adjusted_left = event["left"]
        adjusted_top = event["top"] - 2
        event_row = adjusted_top // cell_height
        event_col = adjusted_left // cell_width
        cell_index = event_row * 7 + event_col  # Assuming 7 columns (days of the week)

        if 0 <= cell_index < len(cells):
            data_date = cells[cell_index]
            if event["type"] not in dates[data_date]["collections"]:
                dates[data_date]["collections"].append(event["type"])

def _group_dates_into_weeks(dates):
    """
    Group dates into weeks.
    """
    current_month = datetime.now().month
    weeks = {}

    for date_str, info in dates.items():
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        week_start = date_obj - timedelta(days=date_obj.weekday())  # Get start of the week
        week_start_str = week_start.strftime("%Y-%m-%d")

        if week_start_str not in weeks:
            weeks[week_start_str] = []

        weeks[week_start_str].append({"date": date_str, "collections": info["collections"]})

    # Remove weeks with no dates in the current month
    weeks = {
        week_start: [
            day for day in days if datetime.strptime(day["date"], "%Y-%m-%d").month == current_month
        ]
        for week_start, days in weeks.items()
    }
    return {k: v for k, v in weeks.items() if v}

# ----------------------------
# Output Functions
# ----------------------------

def _print_weeks(weeks):
    """
    Print the grouped weeks and their collection events.
    """
    for week_start, days in weeks.items():
        print(f"Week of {week_start}:")
        for day in days:
            collections = ", ".join(day["collections"]) if day["collections"] else "No collections"
            print(f"  Date: {day['date']}, Collections: {collections}")
