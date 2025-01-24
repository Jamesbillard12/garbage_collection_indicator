from typing import Dict, List, Optional, Tuple
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Frame

# Load environment variables
load_dotenv()

@dataclass
class CalendarEvent:
    type: str
    left: int
    top: int

class RecologyCalendarScraper:
    BASE_URL = "https://www.recology.com/recology-king-county/shoreline/collection-calendar/"
    CELL_WIDTH = 62
    CELL_HEIGHT = 62
    TOP_OFFSET = 2

    def __init__(self):
        self.address = os.environ.get("address")
        if not self.address:
            raise ValueError("Address not found in environment variables")

    def setup_page(self) -> Tuple[Page, Frame]:
        """Initialize and setup the browser page and iframe."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Navigate and setup page
            page.goto(self.BASE_URL)
            page.wait_for_selector("#row-input-0")
            page.fill("#row-input-0", self.address)
            page.click("#rCbtn-search")

            # Handle iframe
            page.wait_for_selector("iframe#recollect-frame")
            iframe = page.frame(name="recollect")
            if not iframe:
                raise ValueError("Iframe not found")

            iframe.wait_for_selector("table.fc-border-separate")
            return page, iframe

    def extract_calendar_data(self, iframe: Frame) -> Tuple[BeautifulSoup, List, datetime]:
        """Extract calendar data from the iframe."""
        content = iframe.content()
        soup = BeautifulSoup(content, "html.parser")

        calendar_table = soup.find("table", class_="fc-border-separate")
        if not calendar_table:
            raise ValueError("Calendar table not found")

        cells = calendar_table.find_all("td", {"data-date": True})
        current_date = datetime.now()

        return soup, cells, current_date

    def initialize_dates_dict(self, cells: List, current_date: datetime) -> Dict:
        """Initialize the dates dictionary for the current month."""
        dates = {}
        for cell in cells:
            data_date = cell["data-date"]
            date_obj = datetime.strptime(data_date, "%Y-%m-%d")
            if date_obj.month == current_date.month and date_obj.year == current_date.year:
                dates[data_date] = {"collections": []}
        return dates

    def extract_events(self, soup: BeautifulSoup) -> List[CalendarEvent]:
        """Extract collection events from the calendar."""
        event_divs = soup.find_all("div", id=re.compile(r"^rCevt-"))
        events = []

        for event in event_divs:
            event_type = event.get("id").split("-")[1]
            event_styles = event.get("style", "")

            left_match = re.search(r"left: (\d+)", event_styles)
            top_match = re.search(r"top: (\d+)", event_styles)

            if left_match and top_match:
                events.append(CalendarEvent(
                    type=event_type,
                    left=int(left_match.group(1)),
                    top=int(top_match.group(1))
                ))

        return events

    def calculate_cell_position(self, event: CalendarEvent) -> Tuple[int, int]:
        """Calculate the cell position for an event."""
        adjusted_top = event.top - self.TOP_OFFSET
        event_row = adjusted_top // self.CELL_HEIGHT
        event_col = event.left // self.CELL_WIDTH
        return event_row, event_col

    def scrape_calendar(self) -> Dict:
        """Main method to scrape the calendar data."""
        try:
            # Setup page and get initial data
            page, iframe = self.setup_page()
            soup, cells, current_date = self.extract_calendar_data(iframe)

            # Initialize data structures
            dates = self.initialize_dates_dict(cells, current_date)
            events = self.extract_events(soup)

            # Process events
            for event in events:
                event_row, event_col = self.calculate_cell_position(event)
                cell_index = event_row * 7 + event_col

                if 0 <= cell_index < len(cells):
                    data_date = cells[cell_index]["data-date"]
                    if data_date in dates:
                        if event.type not in dates[data_date]["collections"]:
                            dates[data_date]["collections"].append(event.type)

            return dates

        except Exception as e:
            print(f"Error scraping calendar: {str(e)}")
            return {}
        finally:
            if 'page' in locals():
                page.context.browser.close()