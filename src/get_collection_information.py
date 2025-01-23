from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import os
from datetime import datetime, timedelta

load_dotenv()

def scrape_with_playwright():
    url = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    address = os.environ["address"]

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
            print("Iframe not found")
            return

        # Wait for the calendar to load inside the iframe
        iframe.wait_for_selector("table.fc-border-separate")

        # Get the iframe content
        content = iframe.content()
        soup = BeautifulSoup(content, "html.parser")

        # Locate the table with the class 'fc-border-separate'
        calendar_table = soup.find("table", class_="fc-border-separate")
        if not calendar_table:
            print("Calendar table not found")
            return

        # Extract all table cells with data-date
        dates = {}
        cells = calendar_table.find_all("td", {"data-date": True})
        current_month = datetime.now().month
        current_year = datetime.now().year

        for cell in cells:
            data_date = cell["data-date"]
            date_obj = datetime.strptime(data_date, "%Y-%m-%d")
            if date_obj.month == current_month and date_obj.year == current_year:
                dates[data_date] = {"collections": []}

        # Extract collection event divs
        event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))
        events = []
        for event in event_divs:
            event_id = event.get("id")
            event_type = event_id.split("-")[1]  # Extract type (e.g., garbage, recycling)
            event_styles = event.get("style", "")
            event_left_match = re.search(r"left: (\d+)", event_styles)
            event_top_match = re.search(r"top: (\d+)", event_styles)
            if event_left_match and event_top_match:
                events.append({
                    "type": event_type,
                    "left": int(event_left_match.group(1)),
                    "top": int(event_top_match.group(1)),
                })

        # Match event divs to table cells by inferred positions
        cell_width = 62  # Adjusted for padding or spacing around cells
        cell_height = 62  # Adjusted for padding or spacing around cells

        for event in events:
            # Adjust for potential offsets due to spacing
            adjusted_left = event["left"]
            adjusted_top = event["top"] - 2

            event_row = adjusted_top // cell_height
            event_col = adjusted_left // cell_width

            # Get the corresponding cell by row and column
            cell_index = event_row * 7 + event_col  # Assuming 7 columns (days of the week)
            if 0 <= cell_index < len(cells):
                data_date = cells[cell_index]["data-date"]
                if data_date in dates:
                    if event["type"] not in dates[data_date]["collections"]:
                        dates[data_date]["collections"].append(event["type"])

        # Group dates into weeks
        weeks = {}
        for date_str, info in dates.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            week_start = date_obj - timedelta(days=date_obj.weekday())  # Get the start of the week (Monday)
            week_start_str = week_start.strftime("%Y-%m-%d")

            if week_start_str not in weeks:
                weeks[week_start_str] = []

            weeks[week_start_str].append({"date": date_str, "collections": info["collections"]})

        # Adjust weeks to include only the current month's dates
        for week_start in list(weeks.keys()):
            weeks[week_start] = [
                day for day in weeks[week_start]
                if datetime.strptime(day["date"], "%Y-%m-%d").month == current_month
            ]
            if not weeks[week_start]:  # Remove empty weeks
                del weeks[week_start]

        # Print the results
        for week_start, days in weeks.items():
            print(f"Week of {week_start}:")
            for day in days:
                collections = ", ".join(day["collections"]) if day["collections"] else "No collections"
                print(f"  Date: {day['date']}, Collections: {collections}")

        browser.close()
        return weeks
