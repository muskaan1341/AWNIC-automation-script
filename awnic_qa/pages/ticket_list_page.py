"""
A ticket list screen.

The Enquiries list and the Complaints list are the SAME screen with different data, so one
page object covers both - only the heading and the Create button text change:
  /tickets/enquiries   heading "Enquiries Tickets",  button "Create Enquiry"
  /tickets/complaints  heading "Complaints Tickets", button "Create Complaint"

The Discarded list is a genuinely different table with its own five columns, so it has its
own page object (DiscardedListPage). Reusing this class over there is the commonest way to
fail that screen for the wrong reason.

THREE THINGS ABOUT THIS SCREEN THAT WILL CATCH YOU OUT:
 1. The scope tabs (My Tickets / My Department / Organization Tickets) are CLIENT-SIDE only.
    They do not write anything into the URL, so never wait for a query parameter - wait for
    the rows to change instead.
 2. A role with a restricted scope sees NO tabs at all, because it only has one view.
 3. "6 results" is three separate pieces of text in the page: "6", " result", "s".
    contains(text(),'result') looks only at the first piece and never matches.
"""

from __future__ import annotations

import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage, Locator

#: How many times to re-read a table that is redrawing. See get_reference_numbers().
STALE_READ_ATTEMPTS = 3

#: The nine filters the drawer offers, and the id the app gives each one.
#:
#: Every filter dropdown carries a real id ("filter-priority", "filter-sla_status", ...),
#: which is a far better locator than hunting for a label and then its neighbour. This map is
#: also the readable list of what can be filtered on.
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
    #: The scope tabs the screen can render, in order.
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

    # See point 3 in the module comment: ask whether ANY piece of text contains "result".
    RESULT_COUNT = (By.XPATH, "//div[text()[contains(.,'result')]]")
    EMPTY_STATE = (
        By.XPATH,
        "//td[contains(text(),'No tickets yet') or contains(text(),'match your filters')]",
    )

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self) -> None:
        """Waits until the table has been rendered. Call this after opening the page."""
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text: str) -> None:
        """
        Types into the search box and COMMITS the term with Enter.

        The ticket-list search is no longer live: TicketListToolbar.tsx only runs it when the
        term is committed (SearchInput's onSubmit, fired on Enter) - typing just updates a local
        draft. Typing alone therefore left the list unfiltered and every search test timed out.
        The test must still wait for the result to change - see wait_for_row_count below.
        """
        self.type_into(self.SEARCH_INPUT, text)
        self.wait_visible(self.SEARCH_INPUT).send_keys(Keys.ENTER)

    def clear_search(self) -> None:
        """Empties the box and commits the empty term, for the same reason as search()."""
        box = self.wait_visible(self.SEARCH_INPUT)
        self.clear_box(box)
        box.send_keys(Keys.ENTER)

    def click_create_button(self, label: str) -> None:
        self.click_button(label)

    def switch_to_kanban(self) -> None:
        self.click(self.KANBAN_VIEW_BUTTON)

    def switch_to_list(self) -> None:
        self.click(self.LIST_VIEW_BUTTON)

    def select_tab(self, label: str) -> None:
        """Selects a scope tab. Nothing appears in the URL, so wait on the rows afterwards."""
        self.click_button(label)

    def sort_by(self, column_name: str) -> None:
        self.click((By.XPATH, f"//th//button[normalize-space()='{column_name}']"))

    def open_first_row(self) -> str:
        """
        Opens the first row the application will ACTUALLY open, and returns its reference.

        NOT simply "row one". DataTable renders a row inert when the list marks it disabled -
        on the ticket lists that is a merged duplicate (TicketTypeListClient passes
        `rowDisabled={(t) => t.is_duplicate}`) - and an inert row is given no click handler at
        all. Clicking it therefore does nothing, and a test that took row one on faith sat
        waiting for a navigation that was never coming, failing forty seconds later pointing
        at whatever screen it meant to reach rather than at the merged ticket in front of it.
        That is exactly what happened on 2026-09-29, when a merged enquiry became the newest
        one and so sorted to the top of the list.

        Which rows are which is read from the product's own rendering - `cursor-pointer` on a
        live row, `cursor-not-allowed` on an inert one (DataTable) - rather than guessed from
        a status, a badge or a ticket id, so this keeps working whatever rowDisabled is used
        for next. Skipping an inert row is not weakening anything: the row being unopenable is
        the product behaving correctly, and every caller here wants "a ticket I can open".
        """
        inert: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            classes = row.get_attribute("class") or ""
            cells = row.find_elements(By.TAG_NAME, "td")
            reference = (
                cells[2].text.strip().split("\n")[0].strip() if len(cells) >= 3 else "?"
            )
            if "cursor-pointer" in classes:
                self.scroll_to_middle(row)
                row.click()
                return reference
            if "cursor-not-allowed" in classes:
                inert.append(reference)

        # Fail NOW, with the reason, rather than clicking nothing and waiting out the full
        # timeout on a URL that cannot change.
        raise AssertionError(
            "No row on this list can be opened. Rows on screen: "
            f"{self.get_row_count()}; deliberately inert (merged duplicates): {inert or 'none'}. "
            "An inert row is correct product behaviour, so this means the list holds nothing "
            "else to open - seed an openable ticket, or narrow the list first."
        )

    def open_row(self, row_index: int) -> None:
        """Opens the ticket on one row (0 = the first), for a test that chose it by content."""
        self.driver.find_elements(*self.TABLE_ROWS)[row_index].click()

    def open_row_menu(self, row_index: int) -> None:
        """Opens a row's action menu WITHOUT firing the row's own navigate-on-click."""
        self.driver.find_elements(*self.TABLE_ROWS)[row_index].find_element(
            By.CSS_SELECTOR, "button[aria-label^='Actions for']"
        ).click()

    # ---- filters ----

    def open_filter_drawer(self) -> None:
        self.click(self.FILTER_BUTTON)
        self.wait_visible(self.FILTER_DRAWER)

    @staticmethod
    def filter_dropdown(filter_label: str) -> Locator:
        field_id = FILTER_IDS.get(filter_label)
        if field_id is None:
            raise ValueError(
                f"No filter called '{filter_label}'. Known: {sorted(FILTER_IDS)}"
            )
        return (By.ID, field_id)

    def select_filter_value(self, filter_label: str, option_label: str) -> None:
        """Picks a value inside one of the drawer's dropdowns. Filters are multi-choice."""
        self.choose_option(self.filter_dropdown(filter_label), option_label)

    def select_first_filter_value(self, filter_label: str) -> str:
        """Picks whatever the first value is, and returns it."""
        return self.choose_first_option(self.filter_dropdown(filter_label))

    def filter_options(self, filter_label: str) -> list[str]:
        """The values one filter dropdown offers."""
        return self.read_dropdown_options(self.filter_dropdown(filter_label))

    def visible_filter_names(self) -> list[str]:
        """Every filter the drawer puts on screen."""
        return [
            name for name in FILTER_IDS if self.exists(self.filter_dropdown(name))
        ]

    def apply_filters(self) -> None:
        self.click_button("Apply Filter")
        self.wait_gone(self.FILTER_DRAWER)

    def reset_filters(self) -> None:
        self.click_button("Reset")

    def close_filter_drawer_without_applying(self) -> None:
        """
        Shuts the drawer without pressing Apply.

        Uses the drawer's own Close button rather than clicking the dark backdrop behind it.
        The backdrop covers the whole screen, so its centre point sits UNDER the drawer panel,
        and Selenium refuses the click with "element click intercepted - another element would
        receive the click". The Close button is what a person would reach for anyway.
        """
        self.click((By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']"))
        self.wait_gone(self.FILTER_DRAWER)

    def remove_chip(self, chip_label: str) -> None:
        self.click((By.CSS_SELECTOR, f"button[aria-label='Remove {chip_label} filter']"))

    def clear_all_filters(self) -> None:
        self.click(self.CLEAR_ALL_CHIPS)

    # ---- paging ----

    def go_to_next_page(self) -> None:
        self.click(self.NEXT_PAGE)

    def go_to_previous_page(self) -> None:
        self.click(self.PREVIOUS_PAGE)

    def set_page_size(self, size: str) -> None:
        self.choose_option((By.CSS_SELECTOR, "button[aria-label='Results per page']"), size)

    # ---- waits that belong to this screen ----

    def wait_for_row_count(self, expected: int) -> None:
        self.wait_for_count(self.TABLE_ROWS, expected)

    def wait_for_rows_to_change(self, previous_references: list[str]) -> None:
        """Waits until the rows are no longer the set we captured before an action."""
        self.wait.until(lambda d: self.get_reference_numbers() != previous_references)

    def wait_for_empty_state(self) -> None:
        self.wait.until(lambda d: self.exists(self.EMPTY_STATE))

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self) -> str:
        return self.wait_visible(self.HEADING).text

    def get_row_count(self) -> int:
        return self.count(self.TABLE_ROWS)

    def is_search_input_displayed(self) -> bool:
        return self.exists(self.SEARCH_INPUT)

    def is_empty_state_displayed(self) -> bool:
        return self.exists(self.EMPTY_STATE)

    def get_empty_state_text(self) -> str:
        return self.text_of(self.EMPTY_STATE)

    def get_column_headers(self) -> list[str]:
        """All column headings, left to right."""
        return [header for header in self.texts_of(self.COLUMN_HEADERS) if header]

    def get_reference_numbers(self) -> list[str]:
        """
        The reference number in each row (the 3rd column).

        The cell can also hold a badge under the number ("Duplicate" / "Merged"), so we take
        only the FIRST line - otherwise every assertion on a flagged ticket fails on text it
        was never meant to include.
        """
        # READ THE WHOLE TABLE AGAIN IF IT MOVES UNDER US.
        #
        # This method takes two steps: find the rows, then reach inside each row for its
        # cells. Paging re-renders the table between those two steps, so the row we are
        # holding is thrown away by React before we ask it anything - Selenium calls that a
        # "stale element reference" and it failed going_back_a_page_returns_the_same_tickets.
        #
        # It is also called from inside wait.until(...), which runs it over and over while the
        # table is redrawing - exactly the moment rows go stale. Starting the read again is
        # the right answer: a table in the middle of redrawing has no correct answer to give
        # yet, and the next attempt a moment later does.
        for attempt in range(1, STALE_READ_ATTEMPTS + 1):
            try:
                return self._read_reference_numbers_once()
            except StaleElementReferenceException:
                if attempt == STALE_READ_ATTEMPTS:
                    raise
        return []

    def _read_reference_numbers_once(self) -> list[str]:
        numbers: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                numbers.append(cells[2].text.strip().split("\n")[0].strip())
        return numbers

    def get_column_values(self, column_name: str) -> list[str]:
        """
        Every row's value in ONE named column, in page order.

        WHY BY NAME AND NOT BY INDEX. This table is eighteen columns wide and the set of them
        differs by role, so "the department is the 7th cell" is true for one account and
        quietly wrong for the next - which is the kind of bug that makes a scoping test pass
        against the wrong column. Finding the header first and using ITS position means the
        test asks for what it actually means.

        Raises if the column is not on screen: for a role that cannot see it that is a real
        finding, and returning [] would let a test "pass" by reading nothing at all.
        """
        headers = self.get_column_headers()
        if column_name not in headers:
            raise AssertionError(
                f"There is no {column_name!r} column on this list. Showing: {headers}"
            )
        # Index against the RAW headers, not get_column_headers(), which drops empty ones.
        # This table's last <th> is empty (the row-menu column), so the two happen to agree
        # here - but they would not if an empty header ever appeared on the left, and the
        # cells are counted from the left.
        raw_headers = self.texts_of(self.COLUMN_HEADERS)
        index = raw_headers.index(column_name)
        values: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            # The EMPTY-STATE row is a single <td> spanning the whole table ("No tickets
            # yet"), so it is a <tr> like any other but carries no column values. Skipping
            # short rows keeps it out of the answer instead of silently returning nothing.
            if index < len(cells):
                values.append(cells[index].text.strip())
        return values

    def get_result_count_text(self) -> str:
        """The "12 results" line under the table."""
        return self.wait_visible(self.RESULT_COUNT).text

    def get_reported_result_count(self) -> int:
        return int(re.sub(r"\D+", "", self.get_result_count_text()))

    def is_list_view_selected(self) -> bool:
        return (
            self.driver.find_element(*self.LIST_VIEW_BUTTON).get_attribute("aria-pressed")
            == "true"
        )

    def is_kanban_view_selected(self) -> bool:
        return (
            self.driver.find_element(*self.KANBAN_VIEW_BUTTON).get_attribute("aria-pressed")
            == "true"
        )

    def is_kanban_button_enabled(self) -> bool:
        """Neither view button may be disabled - the Kanban board is built now."""
        return self.driver.find_element(*self.KANBAN_VIEW_BUTTON).is_enabled()

    def get_tab_labels(self) -> list[str]:
        """The scope tabs actually on screen. Empty for a role with a restricted scope."""
        return [
            candidate
            for candidate in self.SCOPE_TABS
            if self.exists((By.XPATH, f"//button[normalize-space()='{candidate}']"))
        ]

    def has_tab_strip(self) -> bool:
        return len(self.get_tab_labels()) > 0

    def has_legacy_teams_tickets_tab(self) -> bool:
        """
        The old "Teams Tickets" tab was REMOVED. This exists only so a regression that brings
        it back is caught loudly, rather than quietly passing an out-of-date assertion.
        """
        return self.exists(
            (By.XPATH, "//*[contains(normalize-space(.),'Teams Tickets')]")
        )

    def get_chip_labels(self) -> list[str]:
        return [
            chip.text.replace("\n", " ").strip()
            for chip in self.driver.find_elements(*self.CHIPS)
        ]

    def get_chip_count(self) -> int:
        return self.count(self.CHIPS)

    def get_active_filter_count(self) -> int:
        """
        The number in the badge on the Filter button, or 0 when no filter is applied.

        The badge is a small <span> INSIDE the button, and it is not rendered at all until at
        least one filter is active - so "no badge" legitimately means zero.
        """
        badge = self.text_of(
            (
                By.XPATH,
                "//button[.//text()[contains(.,'Filter')]]/span[normalize-space()!='Filter']",
            )
        )
        digits = re.sub(r"\D+", "", badge)
        return 0 if not digits else int(digits)

    def row_has_badge(self, row_index: int, badge_text: str) -> bool:
        return badge_text in self.driver.find_elements(*self.TABLE_ROWS)[row_index].text

    def any_row_has_badge(self, badge_text: str) -> bool:
        return any(
            badge_text in row.text for row in self.driver.find_elements(*self.TABLE_ROWS)
        )

    def get_column_values(self, column_name: str) -> list[str]:
        """Every value in one column, top to bottom - used to prove a sort or a filter worked."""
        headers = self.get_column_headers()
        if column_name not in headers:
            raise ValueError(f"No column called '{column_name}'. Columns: {headers}")
        index = headers.index(column_name)
        values: list[str] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > index:
                values.append(self._cell_value(cells[index]))
        return values

    @staticmethod
    def _cell_value(cell) -> str:
        """
        One cell's value as a person reads it - the AVATAR'S INITIALS ARE NOT A VALUE.

        Current Handler leads with an Avatar, a <span> whose text is the initials ("AN" for
        Ahmed Nabil Saad Hassouna) with the handler's name beside it. Taking the cell's first
        line therefore returned "AN" for every row, so an ownership test comparing against a
        name or an email could not match however correct the product was - which is exactly
        how it failed on 2026-09-29.

        An avatar is identified by what the component itself puts on it (Avatar.tsx renders
        BOTH aria-label and title with the person's full label), not by its position or its
        styling, and only its text is dropped - every other column is unaffected, since no
        other cell holds one.
        """
        initials = {
            avatar.text.strip()
            for avatar in cell.find_elements(By.CSS_SELECTOR, "span[aria-label][title]")
        }
        for line in cell.text.split("\n"):
            line = line.strip()
            if line and line not in initials:
                return line
        return ""

    # ---- U11 / U15: the SLA columns, the working-day line, Refresh, merged rows ----

    #: TicketTypeListClient.tsx: the whole-ticket clock and the current holder's clock.
    SLA_COLUMN = "SLA"
    CURRENT_LEVEL_SLA_COLUMN = "Current-Level SLA"
    #: TicketPriorityCell.tsx renders "<n> WD" under the priority pill.
    WORKING_DAYS_LINE = re.compile(r"^(\d+) WD$")

    def has_refresh_button(self) -> bool:
        """RefreshButton.tsx - a secondary Button whose text is "Refresh"."""
        return self.has_button("Refresh")

    def priority_working_day_lines(self) -> list[tuple[str, str]]:
        """
        (department, working-day line) for every row on the page.

        The Priority cell is TWO lines - the pill ("High") and "<n> WD" beneath it - so the
        generic get_column_values() (first line only) cannot read it. The line is taken as the
        cell's LAST line; "" when the cell has only one. The department travels with it because
        the figure is the whole-ticket ceiling only once a department is assigned
        (TicketPriorityCell falls back to sla_days before that).
        """
        raw = self.texts_of(self.COLUMN_HEADERS)
        pri, dept = raw.index("Priority"), raw.index("Department")
        out: list[tuple[str, str]] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) <= max(pri, dept):
                continue
            lines = [ln.strip() for ln in cells[pri].text.split("\n") if ln.strip()]
            out.append((cells[dept].text.strip(), lines[-1] if len(lines) > 1 else ""))
        return out

    def merged_rows(self) -> list[dict]:
        """
        Every row whose reference cell carries the "Merged" badge (TicketReferenceCell.tsx),
        with whether the product left it clickable. A merged row is rendered inert on the
        per-type lists (rowDisabled={(t) => t.is_duplicate} -> DataTable "cursor-not-allowed").
        """
        found: list[dict] = []
        for index, row in enumerate(self.driver.find_elements(*self.TABLE_ROWS)):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 3:
                continue
            lines = [ln.strip() for ln in cells[2].text.split("\n") if ln.strip()]
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

    def reference_tooltip(self, row_index: int) -> str:
        """
        Hovers a row's reference cell and returns the tooltip it reveals ("" if none).

        Tooltip.tsx wraps the cell in a focusable <span> and portals role="tooltip" to <body>
        on mouseenter; the merged-into sentence ("This ticket has been merged into X.") lives
        only there.
        """
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_index]
        trigger = row.find_elements(By.TAG_NAME, "td")[2].find_element(
            By.CSS_SELECTOR, "span[tabindex='0']"
        )
        self.scroll_to_middle(trigger)
        ActionChains(self.driver).move_to_element(trigger).perform()
        try:
            return self.wait_visible((By.CSS_SELECTOR, "[role='tooltip']")).text.strip()
        finally:
            # Move off the cell (onto the page heading) so the tooltip closes again.
            ActionChains(self.driver).move_to_element(
                self.driver.find_element(*self.HEADING)
            ).perform()

    def get_current_page_number(self) -> int:
        text = self.text_of(self.CURRENT_PAGE)
        return 1 if not text else int(text)

    def is_previous_page_disabled(self) -> bool:
        return not self.driver.find_element(*self.PREVIOUS_PAGE).is_enabled()

    def table_scrolls_horizontally_without_moving_the_page(self) -> bool:
        """
        The table has its own sideways scrollbar, and the PAGE body must never scroll
        sideways. 18 columns do not fit on any screen, so the wide part has to be trapped
        inside the table's own container.
        """
        table_width = self.driver.execute_script(
            "return arguments[0].scrollWidth;",
            self.driver.find_element(By.TAG_NAME, "table"),
        )
        body_overflow = self.driver.execute_script(
            "return document.body.scrollWidth - document.body.clientWidth;"
        )
        return table_width > 2000 and body_overflow <= 1
