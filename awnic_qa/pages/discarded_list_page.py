"""
The Discarded Tickets list - /tickets/discarded.

It has its own five columns, so it has its own page object (not TicketListPage).

A restored ticket stays on this list with a "Restored" badge and no action menu, and it
still shows the number it was discarded under.
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class DiscardedListPage(BasePage):
    # The columns this list shows.
    EXPECTED_COLUMNS = [
        "Reference number",
        "Sender",
        "Discard Reason",
        "AI Confidence",
        "Date & Time",
    ]

    HEADING = (By.TAG_NAME, "h1")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    COLUMN_HEADERS = (By.CSS_SELECTOR, "table thead th")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder*='sender']")
    CONFIDENCE_FILTER = (
        By.XPATH,
        "//button[contains(normalize-space(),'AI Confidence')]",
    )

    # ---------------- Actions ----------------

    def wait_until_loaded(self):
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text):
        self.type_into(self.SEARCH_INPUT, text)

    def open_confidence_filter(self):
        self.click(self.CONFIDENCE_FILTER)

    def select_confidence(self, level):
        self.open_confidence_filter()
        self.click_button(level)

    def open_row_menu(self, row_index):
        """
        Opens a row's action menu (where "Restore as ..." is). Uses self.click() because
        notification toasts can cover the button.
        """
        self.click(
            (
                By.XPATH,
                f"(//table/tbody/tr)[{row_index + 1}]//button[@aria-label='Row actions']",
            )
        )

    def click_restore_as(self, reference_type):
        """Clicks "Restore as Enquiry" / "Restore as Complaint" in the open row menu."""
        self.click(
            (
                By.XPATH,
                f"//*[@role='menu']//*[normalize-space()='Restore as {reference_type}']",
            )
        )

    def wait_for_row_count(self, expected):
        self.wait_for_count(self.TABLE_ROWS, expected)

    # ---------------- Checks ----------------

    def get_heading(self):
        return self.wait_visible(self.HEADING).text

    def get_row_count(self):
        return self.count(self.TABLE_ROWS)

    def get_column_headers(self):
        headers = []
        for header in self.texts_of(self.COLUMN_HEADERS):
            if header:
                headers.append(header)
        return headers

    def get_reference_numbers(self):
        """The reference number on each row (the FIRST column on this list)."""
        numbers = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                numbers.append(cells[0].text.strip().split("\n")[0].strip())
        return numbers

    def get_search_placeholder(self):
        """The search box's hint text."""
        return self.driver.find_element(*self.SEARCH_INPUT).get_attribute("placeholder")

    def any_row_is_badged_restored(self):
        """True if the word "restored" appears in any row."""
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            if "restored" in row.text.lower():
                return True
        return False

    def row_is_badged_restored(self, row_index):
        """True when this row's reference cell has the "Restored" badge."""
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_index]
        cells = row.find_elements(By.TAG_NAME, "td")
        if not cells:
            return False
        badges = cells[0].find_elements(By.XPATH, ".//span[normalize-space()='Restored']")
        return bool(badges)

    def row_has_action_menu(self, row_index):
        """A restored row has no action menu."""
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_index]
        menu_buttons = row.find_elements(By.CSS_SELECTOR, "button[aria-label='Row actions']")
        return len(menu_buttons) > 0

    def get_open_menu_labels(self):
        """The options in the open row menu, e.g. "Restore as Enquiry"."""
        found = self.texts_of(
            (
                By.CSS_SELECTOR,
                "[role='menu'] [role='menuitem'], [role='menu'] button",
            )
        )
        labels = []
        for text in found:
            if text:
                labels.append(text)
        return labels

    def is_empty_state_displayed(self):
        return self.exists((By.XPATH, "//td[contains(normalize-space(.),'No ')]"))
