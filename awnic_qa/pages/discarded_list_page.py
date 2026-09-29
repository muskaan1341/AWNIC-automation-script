"""
The Discarded Tickets queue (/tickets/discarded).

This is a DIFFERENT table from the Enquiries / Complaints list, with only five columns of
its own, so it gets its own page object. Reusing TicketListPage's 18-column expectations
here is the commonest way to fail this screen for the wrong reason.

A RESTORED ticket STAYS on this list for the record, badged "Restored", with its restore
action removed. So a non-empty list does not mean everything on it is still junk - and a
restored row deliberately shows the number it was DISCARDED under, not its new one.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class DiscardedListPage(BasePage):
    #: The columns this screen renders - deliberately NOT the ticket list's set.
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

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text: str) -> None:
        self.type_into(self.SEARCH_INPUT, text)

    def open_confidence_filter(self) -> None:
        self.click(self.CONFIDENCE_FILTER)

    def select_confidence(self, level: str) -> None:
        self.open_confidence_filter()
        self.click_button(level)

    def open_row_menu(self, row_index: int) -> None:
        """Opens a row's action menu, which is where "Restore as …" lives."""
        self.driver.find_elements(*self.TABLE_ROWS)[row_index].find_element(
            By.CSS_SELECTOR, "button[aria-label='Row actions']"
        ).click()

    def click_restore_as(self, reference_type: str) -> None:
        """Picks "Restore as Enquiry" / "Restore as Complaint" from an open row menu."""
        self.click(
            (
                By.XPATH,
                f"//*[@role='menu']//*[normalize-space()='Restore as {reference_type}']",
            )
        )

    def wait_for_row_count(self, expected: int) -> None:
        self.wait_for_count(self.TABLE_ROWS, expected)

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self) -> str:
        return self.wait_visible(self.HEADING).text

    def get_row_count(self) -> int:
        return self.count(self.TABLE_ROWS)

    def get_column_headers(self) -> list[str]:
        return [header for header in self.texts_of(self.COLUMN_HEADERS) if header]

    def get_reference_numbers(self) -> list[str]:
        """The reference number in each row (the FIRST column on this screen)."""
        numbers: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                numbers.append(cells[0].text.strip().split("\n")[0].strip())
        return numbers

    def get_search_placeholder(self) -> str:
        """The search hint - it tells the tester which fields the search actually covers."""
        return self.driver.find_element(*self.SEARCH_INPUT).get_attribute("placeholder")

    def any_row_is_badged_restored(self) -> bool:
        return any(
            "restored" in row.text.lower()
            for row in self.driver.find_elements(*self.TABLE_ROWS)
        )

    def row_is_badged_restored(self, row_index: int) -> bool:
        """
        True when THIS row carries the "Restored" badge beside its reference number.

        any_row_is_badged_restored() matches the word anywhere in any row - a subject line or
        discard reason containing "restored" satisfies it. This reads the badge itself: a
        <span> reading exactly "Restored" in the reference cell, which
        DiscardedTicketListClient renders only when the ticket has left the Discarded type.
        """
        cells = self.driver.find_elements(*self.TABLE_ROWS)[row_index].find_elements(
            By.TAG_NAME, "td"
        )
        return bool(cells) and bool(
            cells[0].find_elements(By.XPATH, ".//span[normalize-space()='Restored']")
        )

    def row_has_action_menu(self, row_index: int) -> bool:
        """A restored row has no action menu at all, because restoring no longer applies."""
        return (
            len(
                self.driver.find_elements(*self.TABLE_ROWS)[row_index].find_elements(
                    By.CSS_SELECTOR, "button[aria-label='Row actions']"
                )
            )
            > 0
        )

    def get_open_menu_labels(self) -> list[str]:
        """The options offered inside an open row menu, e.g. "Restore as Enquiry"."""
        found = self.texts_of(
            (
                By.CSS_SELECTOR,
                "[role='menu'] [role='menuitem'], [role='menu'] button",
            )
        )
        return [text for text in found if text]

    def is_empty_state_displayed(self) -> bool:
        return self.exists((By.XPATH, "//td[contains(normalize-space(.),'No ')]"))
