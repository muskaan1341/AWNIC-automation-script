"""
A ticket list screen - used for both the Enquiries and the Complaints list.
  /tickets/enquiries   heading "Enquiries Tickets",  button "Create Enquiry"
  /tickets/complaints  heading "Complaints Tickets", button "Create Complaint"
The Discarded list has different columns, so it has its own page (DiscardedListPage).

Good to know:
 1. The scope tabs (My Tickets / My Department / Organization Tickets) do not change the URL,
    so wait for the rows to change instead.
 2. A role with only one scope sees no tabs at all.
 3. "6 results" is split into several text pieces, so contains(text(),'result') does not work.
"""

import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage

# How many times to re-read the table if it redraws while we read it.
STALE_READ_ATTEMPTS = 3

# The filters in the Filter drawer, and the id of each one's dropdown.
FILTER_IDS = {
    "Priority": "filter-priority",
    "Status": "filter-status",
    "Department": "filter-department",
    "Source": "filter-source",
    "Type": "filter-inquiry_type",
    "Enquiry": "filter-enquiry",
    "Sub Enquiry": "filter-sub_enquiry",
    "Duplicate": "filter-duplicate",
    "SLA Status": "filter-sla_status",
}


class TicketListPage(BasePage):
    # The scope tabs the screen can show, in order.
    SCOPE_TABS = ["My Tickets", "My Department", "Organization Tickets"]

    HEADING = (By.TAG_NAME, "h1")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder^='Search']")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    COLUMN_HEADERS = (By.CSS_SELECTOR, "table thead th")
    LIST_VIEW_BUTTON = (By.XPATH, "//button[normalize-space()='List']")
    KANBAN_VIEW_BUTTON = (By.XPATH, "//button[normalize-space()='Kanban']")
    FILTER_BUTTON = (By.XPATH, "//button[normalize-space()='Filter']")
    FILTER_DRAWER = (By.CSS_SELECTOR, "div[role='dialog']")
    CHIPS = (By.XPATH, "//button[starts-with(@aria-label,'Remove ')]/..")
    CLEAR_ALL_CHIPS = (By.XPATH, "//button[normalize-space()='Clear all']")
    NEXT_PAGE = (By.CSS_SELECTOR, "button[aria-label='Next page']")
    PREVIOUS_PAGE = (By.CSS_SELECTOR, "button[aria-label='Previous page']")
    CURRENT_PAGE = (By.CSS_SELECTOR, "button[aria-current='page']")

    # Matches if ANY text piece contains "result" (see point 3 above).
    RESULT_COUNT = (By.XPATH, "//div[text()[contains(.,'result')]]")
    EMPTY_STATE = (
        By.XPATH,
        "//td[contains(text(),'No tickets yet') or contains(text(),'match your filters')]",
    )

    # ---------------- Actions ----------------

    def wait_until_loaded(self):
        """Waits until the table is shown."""
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text):
        """Types the search text and presses Enter (search only runs on Enter)."""
        self.type_into(self.SEARCH_INPUT, text)
        self.wait_visible(self.SEARCH_INPUT).send_keys(Keys.ENTER)

    def clear_search(self):
        """Empties the search box and presses Enter."""
        box = self.wait_visible(self.SEARCH_INPUT)
        self.clear_box(box)
        box.send_keys(Keys.ENTER)

    def click_create_button(self, label):
        self.click_button(label)

    def switch_to_kanban(self):
        self.click(self.KANBAN_VIEW_BUTTON)

    def switch_to_list(self):
        self.click(self.LIST_VIEW_BUTTON)

    def select_tab(self, label):
        """Selects a scope tab. The URL does not change, so wait on the rows afterwards."""
        self.click_button(label)

    def sort_by(self, column_name):
        self.click((By.XPATH, f"//th//button[normalize-space()='{column_name}']"))

    def open_first_row(self):
        """
        Opens the first row that can be opened and returns its reference number.

        Merged duplicates are shown as disabled rows ("cursor-not-allowed") that do nothing
        when clicked, so they are skipped. Openable rows have "cursor-pointer".
        """
        inert = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            classes = row.get_attribute("class") or ""
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                reference = cells[2].text.strip().split("\n")[0].strip()
            else:
                reference = "?"
            if "cursor-pointer" in classes:
                self.scroll_to_middle(row)
                row.click()
                return reference
            if "cursor-not-allowed" in classes:
                inert.append(reference)

        # Fail straight away with a clear message instead of waiting for a timeout.
        raise AssertionError(
            "No row on this list can be opened. Rows on screen: "
            f"{self.get_row_count()}; deliberately inert (merged duplicates): {inert or 'none'}. "
            "An inert row is correct product behaviour, so this means the list holds nothing "
            "else to open - seed an openable ticket, or narrow the list first."
        )

    def open_row(self, row_index):
        """Opens the ticket on one row (0 = the first)."""
        self.driver.find_elements(*self.TABLE_ROWS)[row_index].click()

    def open_row_menu(self, row_index):
        """Opens a row's "..." action menu (without opening the ticket)."""
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_index]
        row.find_element(By.CSS_SELECTOR, "button[aria-label^='Actions for']").click()

    # ---- filters ----

    def open_filter_drawer(self):
        self.click(self.FILTER_BUTTON)
        self.wait_visible(self.FILTER_DRAWER)

    @staticmethod
    def filter_dropdown(filter_label):
        field_id = FILTER_IDS.get(filter_label)
        if field_id is None:
            raise ValueError(
                f"No filter called '{filter_label}'. Known: {sorted(FILTER_IDS)}"
            )
        return (By.ID, field_id)

    def select_filter_value(self, filter_label, option_label):
        """Picks a value in one of the filter dropdowns."""
        self.choose_option(self.filter_dropdown(filter_label), option_label)

    def select_first_filter_value(self, filter_label):
        """Picks the first value in a filter dropdown and returns it."""
        return self.choose_first_option(self.filter_dropdown(filter_label))

    def filter_options(self, filter_label):
        """The values one filter dropdown offers."""
        return self.read_dropdown_options(self.filter_dropdown(filter_label))

    def visible_filter_names(self):
        """The names of the filters shown in the drawer."""
        names = []
        for name in FILTER_IDS:
            if self.exists(self.filter_dropdown(name)):
                names.append(name)
        return names

    def apply_filters(self):
        self.click_button("Apply Filter")
        self.wait_gone(self.FILTER_DRAWER)

    def reset_filters(self):
        self.click_button("Reset")

    def close_filter_drawer_without_applying(self):
        """
        Closes the drawer with its Close button. (Clicking the dark backdrop does not work:
        its centre is under the drawer, so the click is intercepted.)
        """
        self.click((By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']"))
        self.wait_gone(self.FILTER_DRAWER)

    def remove_chip(self, chip_label):
        self.click((By.CSS_SELECTOR, f"button[aria-label='Remove {chip_label} filter']"))

    def clear_all_filters(self):
        self.click(self.CLEAR_ALL_CHIPS)

    # ---- paging ----

    def go_to_next_page(self):
        self.click(self.NEXT_PAGE)

    def go_to_previous_page(self):
        self.click(self.PREVIOUS_PAGE)

    def set_page_size(self, size):
        self.choose_option((By.CSS_SELECTOR, "button[aria-label='Results per page']"), size)

    # ---- waits ----

    def wait_for_row_count(self, expected):
        self.wait_for_count(self.TABLE_ROWS, expected)

    def wait_for_rows_to_change(self, previous_references):
        """Waits until the rows are different from the ones captured earlier."""
        self.wait.until(lambda d: self.get_reference_numbers() != previous_references)

    def wait_for_empty_state(self):
        self.wait.until(lambda d: self.exists(self.EMPTY_STATE))

    # ---------------- Checks ----------------

    def get_heading(self):
        return self.wait_visible(self.HEADING).text

    def get_row_count(self):
        return self.count(self.TABLE_ROWS)

    def is_search_input_displayed(self):
        return self.exists(self.SEARCH_INPUT)

    def is_empty_state_displayed(self):
        return self.exists(self.EMPTY_STATE)

    def get_empty_state_text(self):
        return self.text_of(self.EMPTY_STATE)

    def get_column_headers(self):
        """All non-empty column headings, left to right."""
        headers = []
        for header in self.texts_of(self.COLUMN_HEADERS):
            if header:
                headers.append(header)
        return headers

    def get_reference_numbers(self):
        """
        The reference number on each row (3rd column, first line only - the cell can also
        show a "Duplicate"/"Merged" badge underneath).

        If the table redraws while we read it (a stale element), read it again.
        """
        for attempt in range(1, STALE_READ_ATTEMPTS + 1):
            try:
                numbers = []
                for row in self.driver.find_elements(*self.TABLE_ROWS):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        numbers.append(cells[2].text.strip().split("\n")[0].strip())
                return numbers
            except StaleElementReferenceException:
                if attempt == STALE_READ_ATTEMPTS:
                    raise
        return []

    def get_result_count_text(self):
        """The "12 results" text under the table."""
        return self.wait_visible(self.RESULT_COUNT).text

    def get_reported_result_count(self):
        return int(re.sub(r"\D+", "", self.get_result_count_text()))

    def is_list_view_selected(self):
        button = self.driver.find_element(*self.LIST_VIEW_BUTTON)
        return button.get_attribute("aria-pressed") == "true"

    def is_kanban_view_selected(self):
        button = self.driver.find_element(*self.KANBAN_VIEW_BUTTON)
        return button.get_attribute("aria-pressed") == "true"

    def is_kanban_button_enabled(self):
        return self.driver.find_element(*self.KANBAN_VIEW_BUTTON).is_enabled()

    def get_tab_labels(self):
        """The scope tabs on screen. Empty for a role with only one scope."""
        labels = []
        for candidate in self.SCOPE_TABS:
            if self.exists((By.XPATH, f"//button[normalize-space()='{candidate}']")):
                labels.append(candidate)
        return labels

    def has_tab_strip(self):
        return len(self.get_tab_labels()) > 0

    def has_legacy_teams_tickets_tab(self):
        """The old "Teams Tickets" tab was removed. True if it has come back."""
        return self.exists(
            (By.XPATH, "//*[contains(normalize-space(.),'Teams Tickets')]")
        )

    def get_chip_labels(self):
        labels = []
        for chip in self.driver.find_elements(*self.CHIPS):
            labels.append(chip.text.replace("\n", " ").strip())
        return labels

    def get_chip_count(self):
        return self.count(self.CHIPS)

    def get_active_filter_count(self):
        """The number on the Filter button's badge, or 0 when there is no badge."""
        badge = self.text_of(
            (
                By.XPATH,
                "//button[.//text()[contains(.,'Filter')]]/span[normalize-space()!='Filter']",
            )
        )
        digits = re.sub(r"\D+", "", badge)
        if not digits:
            return 0
        return int(digits)

    def row_has_badge(self, row_index, badge_text):
        return badge_text in self.driver.find_elements(*self.TABLE_ROWS)[row_index].text

    def any_row_has_badge(self, badge_text):
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            if badge_text in row.text:
                return True
        return False

    def get_column_values(self, column_name):
        """Every value in one column, top to bottom (found by the column's name)."""
        headers = self.get_column_headers()
        if column_name not in headers:
            raise ValueError(f"No column called '{column_name}'. Columns: {headers}")
        index = headers.index(column_name)
        values = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > index:
                values.append(self._cell_value(cells[index]))
        return values

    @staticmethod
    def _cell_value(cell):
        """
        A cell's first line of text, skipping avatar initials (e.g. "AN" before the
        handler's name). An avatar is a span with both aria-label and title.
        """
        initials = set()
        for avatar in cell.find_elements(By.CSS_SELECTOR, "span[aria-label][title]"):
            initials.add(avatar.text.strip())
        for line in cell.text.split("\n"):
            line = line.strip()
            if line and line not in initials:
                return line
        return ""

    # ---- SLA columns, working-day line, Refresh, merged rows ----

    SLA_COLUMN = "SLA"
    CURRENT_LEVEL_SLA_COLUMN = "Current-Level SLA"
    # The "<n> WD" line under the priority pill.
    WORKING_DAYS_LINE = re.compile(r"^(\d+) WD$")

    def has_refresh_button(self):
        return self.has_button("Refresh")

    def priority_working_day_lines(self):
        """
        A (department, working-day line) pair for every row. The working-day line is the
        last line of the Priority cell, or "" if the cell has only one line.
        """
        raw_headers = self.texts_of(self.COLUMN_HEADERS)
        priority_index = raw_headers.index("Priority")
        department_index = raw_headers.index("Department")
        result = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) <= max(priority_index, department_index):
                continue
            lines = []
            for line in cells[priority_index].text.split("\n"):
                if line.strip():
                    lines.append(line.strip())
            if len(lines) > 1:
                working_days = lines[-1]
            else:
                working_days = ""
            result.append((cells[department_index].text.strip(), working_days))
        return result

    def merged_rows(self):
        """Every row with a "Merged" badge, and whether it can be clicked."""
        found = []
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        for index, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 3:
                continue
            lines = []
            for line in cells[2].text.split("\n"):
                if line.strip():
                    lines.append(line.strip())
            if "Merged" not in lines:
                continue
            classes = row.get_attribute("class") or ""
            found.append(
                {
                    "index": index,
                    "reference": lines[0],
                    "clickable": "cursor-pointer" in classes,
                    "inert": "cursor-not-allowed" in classes,
                }
            )
        return found

    def reference_tooltip(self, row_index):
        """Hovers a row's reference cell and returns its tooltip text."""
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_index]
        reference_cell = row.find_elements(By.TAG_NAME, "td")[2]
        trigger = reference_cell.find_element(By.CSS_SELECTOR, "span[tabindex='0']")
        self.scroll_to_middle(trigger)
        ActionChains(self.driver).move_to_element(trigger).perform()
        try:
            return self.wait_visible((By.CSS_SELECTOR, "[role='tooltip']")).text.strip()
        finally:
            # Move the mouse onto the heading so the tooltip closes again.
            heading = self.driver.find_element(*self.HEADING)
            ActionChains(self.driver).move_to_element(heading).perform()

    def get_current_page_number(self):
        text = self.text_of(self.CURRENT_PAGE)
        if not text:
            return 1
        return int(text)

    def is_previous_page_disabled(self):
        return not self.driver.find_element(*self.PREVIOUS_PAGE).is_enabled()

    def table_scrolls_horizontally_without_moving_the_page(self):
        """True when the wide table scrolls sideways but the page itself does not."""
        table_width = self.driver.execute_script(
            "return arguments[0].scrollWidth;",
            self.driver.find_element(By.TAG_NAME, "table"),
        )
        body_overflow = self.driver.execute_script(
            "return document.body.scrollWidth - document.body.clientWidth;"
        )
        return table_width > 2000 and body_overflow <= 1
