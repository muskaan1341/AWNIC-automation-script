"""
The read-only oversight screens. They share one page object because each is just
a heading, some tiles and a table:

  /reports       the management report (covers ONE calendar month, the previous one by default)
  /audit-trail   the organisation-wide audit trail
  /history       Customer History
  /teams-sla     Teams & SLA configuration (seven tabs)
  /historical    the Historical Complaints archive

Note: because the report covers only one month, its "Total Tickets" is normally SMALLER
than the ticket lists. The heading is "Team Performance Report" ("Reports" is only the menu label).
"""

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage

# The Employee Performance card: its title, then the nearest wrapper that holds a table.
_EMPLOYEE_CARD = "//h3[normalize-space()='Employee Performance']/ancestor::div[.//table][1]"


class ReportsPage(BasePage):
    # The six tiles at the top of the management report.
    REPORT_KPIS = [
        "Total Tickets",
        "Open",
        "Resolved",
        "SLA Breaches",
        "SLA Compliance",
        "Avg. Resolution Time",
    ]

    # The three breakdown cards.
    REPORT_TABLES = ["By Department", "By Status", "By Priority"]

    # Every card on the report, top to bottom.
    REPORT_SECTIONS = [
        "Team Structure",
        "Employee Performance",
        "By Department",
        "By Status",
        "By Priority",
    ]

    # The Employee Performance table columns, in screen order.
    EMPLOYEE_COLUMNS = [
        "Employee",
        "Team",
        "Resolved",
        "Avg. Resolution",
        "SLA Breaches",
        "Escalations",
        "Current Load",
    ]

    HEADING = (By.TAG_NAME, "h1")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")

    # ---- the month selector (the only dropdown on /reports) ----
    MONTH_PICKER_TRIGGER = (By.CSS_SELECTOR, "button[aria-haspopup='listbox']")
    REPORTING_PERIOD_LINE = (
        By.XPATH,
        "//p[contains(normalize-space(.),'Reporting period')]",
    )

    # ---- Team Structure ----
    TEAM_TREE = (By.CSS_SELECTOR, "[data-testid='team-tree']")
    TEAM_BRANCHES = (By.CSS_SELECTOR, "[data-testid='team-tree'] > li > button")
    TEAM_EMPLOYEES = (
        By.CSS_SELECTOR,
        "[data-testid='team-tree'] ul[role='group'] > li[role='treeitem']",
    )

    # ---- Employee Performance ----
    EMPLOYEE_TABLE = (By.XPATH, _EMPLOYEE_CARD + "//table")
    EMPLOYEE_ROWS = (By.XPATH, _EMPLOYEE_CARD + "//table/tbody/tr")
    EMPLOYEE_HEADERS = (By.XPATH, _EMPLOYEE_CARD + "//table/thead//th")

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self):
        self.wait_visible(self.HEADING)

    def wait_for_table(self):
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def wait_for_report(self):
        """Waits for the report figures, not just the heading (the page shows a skeleton first)."""
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.is_kpi_displayed("Total Tickets"))

    # ---- the month selector ----

    def choose_month(self, label):
        """
        Picks a month by its label, e.g. "July 2026".
        Not using choose_option(): picking a month reloads the page, so there is nothing to tidy up after.
        """
        self.open_dropdown(self.MONTH_PICKER_TRIGGER)
        option = (
            By.XPATH,
            "//ul[@role='listbox']//button[@role='option']"
            f"[normalize-space()='{label}']",
        )
        # Scroll inside the list only - scrolling the page moves the dropdown panel.
        self._scroll_within_listbox(self.wait_visible(option))
        self.click(option, scroll=False)

    def get_month_options(self):
        """Every month the selector offers, without choosing one."""
        options = self.read_dropdown_options(self.MONTH_PICKER_TRIGGER)
        # Extra safety: close the panel with Escape if it is still open.
        self.close_any_open_dropdown()
        return options

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self):
        return self.wait_visible(self.HEADING).text

    def is_kpi_displayed(self, label):
        return self.exists((By.XPATH, f"//div[normalize-space()='{label}']"))

    def get_kpi_value(self, label):
        """The number on a tile (the value sits in the div after the label's row)."""
        return self.wait_visible(
            (
                By.XPATH,
                f"//div[normalize-space()='{label}']/parent::div/following-sibling::div",
            )
        ).text

    def get_kpi_number(self, label):
        return int(re.sub(r"\D+", "", self.get_kpi_value(label)))

    def has_card(self, title):
        """True when a named card (e.g. "By Department") is on the page. Case does not matter."""
        return self.exists(self.text_ignoring_case(title))

    def get_row_count(self):
        return self.count(self.TABLE_ROWS)

    def shows_empty_state(self):
        """True when the screen shows a "No ..." message instead of data."""
        return self.exists(
            (
                By.XPATH,
                "//*[contains(normalize-space(.),'No ')"
                " and not(.//*[contains(normalize-space(.),'No ')])]",
            )
        )

    # ---- the reporting period ----

    def get_reporting_period_line(self):
        """
        The "Reporting period ... Generated ..." line, or "" while the page is reloading.
        Never raises, because tests poll it inside a wait.
        """
        return self.text_of(self.REPORTING_PERIOD_LINE)

    def get_selected_month(self):
        """The month the selector is showing, e.g. "August 2026"."""
        return self.wait_visible(self.MONTH_PICKER_TRIGGER).text.strip()

    def has_month_picker(self):
        return self.exists(self.MONTH_PICKER_TRIGGER)

    # ---- Team Structure ----

    def has_team_tree(self):
        return self.exists(self.TEAM_TREE)

    def get_team_rows(self):
        """The text of each team row."""
        return self.texts_of(self.TEAM_BRANCHES)

    def get_employee_rows_in_tree(self):
        """The employees shown under their teams (every team starts expanded)."""
        return self.texts_of(self.TEAM_EMPLOYEES)

    def collapse_first_team(self):
        branches = self.driver.find_elements(*self.TEAM_BRANCHES)
        if branches:
            self.scroll_to_middle(branches[0])
            branches[0].click()

    def count_employees_in_tree(self):
        return self.count(self.TEAM_EMPLOYEES)

    # ---- Employee Performance ----

    def has_employee_table(self):
        return self.exists(self.EMPLOYEE_TABLE)

    def get_employee_table_columns(self):
        columns = []
        for header in self.texts_of(self.EMPLOYEE_HEADERS):
            if header:
                columns.append(header)
        return columns

    def get_employee_row_count(self):
        return self.count(self.EMPLOYEE_ROWS)

    def get_employee_row(self, one_based_row):
        """The cells of one employee row, left to right. Row 1 is the top row."""
        rows = self.driver.find_elements(*self.EMPLOYEE_ROWS)
        if len(rows) < one_based_row:
            return []
        cells = []
        for cell in rows[one_based_row - 1].find_elements(By.TAG_NAME, "td"):
            cells.append(cell.text.strip())
        return cells

    def employee_table_says_no_activity(self):
        return self.exists(
            self.innermost_containing("No employee activity recorded for this period")
        )

    # ---- the audit trail ----

    def has_audit_entries(self):
        """True when the audit trail shows entries (each entry has an <h4> title)."""
        says_empty = self.exists(
            (By.XPATH, "//*[contains(normalize-space(.),'No audit events')]")
        )
        return not says_empty and self.count((By.CSS_SELECTOR, "h4")) > 0

    def audit_contains(self, text):
        return self.exists(self.innermost_containing(text))

    # ---- Customer History ----

    def search_customer(self, text):
        self.type_into((By.CSS_SELECTOR, "input[placeholder^='Search']"), text)

    def shows_customer_list(self):
        return self.exists((By.TAG_NAME, "table")) or self.exists((By.CSS_SELECTOR, "li"))

    HISTORY_SEARCH = (By.CSS_SELECTOR, "input[placeholder^='Search a customer']")
    # The grouped section labels, in screen order.
    # PR #301 added a fourth group for archive rows (customer-history-view.ts GROUP_LABELS).
    HISTORY_GROUPS = ["Enquiry Tickets", "Complaint Tickets", "Discarded Tickets", "Historical Complaints"]
    HISTORY_ROW_LINKS = (By.XPATH, "//a[contains(@href,'/tickets/') and contains(@href,'returnTo=')]")

    def has_history_search(self):
        return self.exists(self.HISTORY_SEARCH)

    def history_view_is(self, label):
        """True when the Grouped / Timeline button with this label is the selected one."""
        buttons = self.driver.find_elements(
            By.XPATH, f"//button[@aria-pressed][normalize-space()='{label}']"
        )
        return bool(buttons) and buttons[0].get_attribute("aria-pressed") == "true"

    def switch_history_view(self, label):
        self.click((By.XPATH, f"//button[@aria-pressed][normalize-space()='{label}']"))
        self.wait.until(lambda d: self.history_view_is(label))

    def history_group_labels(self):
        """The group sections shown. Uses textContent because the labels are shown in uppercase."""
        labels = []
        for button in self.driver.find_elements(By.XPATH, "//button[@aria-expanded]"):
            text = (button.get_attribute("textContent") or "").strip()
            for group in self.HISTORY_GROUPS:
                if text.startswith(group):
                    labels.append(group)
        return labels

    def expand_all_history_groups(self):
        for button in self.driver.find_elements(By.XPATH, "//button[@aria-expanded='false']"):
            text = (button.get_attribute("textContent") or "").strip()
            for group in self.HISTORY_GROUPS:
                if text.startswith(group):
                    self.scroll_to_middle(button)
                    button.click()
                    break

    def history_references(self):
        """Reference number of every history row (the first bold span in the row)."""
        refs = []
        for link in self.driver.find_elements(*self.HISTORY_ROW_LINKS):
            spans = link.find_elements(By.CSS_SELECTOR, "span.font-semibold")
            if spans:
                refs.append(spans[0].text.strip())
        return refs

    # ---- Teams & SLA ----

    # Tab label -> tab key. The tab's panel has id="tabpanel-<key>".
    TEAMS_SLA_TABS = {
        "Teams": "teams",
        "SLA Policy": "sla",
        "Escalation Ladder": "escalation-ladder",
        "CC Initiator Pools": "cc-initiator-pools",
        "Working Hours": "working-hours",
        "Holidays": "holidays",
        "Classification": "classification",
    }
    # Button labels that mean "this can change data". Matched exactly, not as a prefix.
    EDIT_BUTTON_LABELS = ("Save", "Edit", "Add", "Remove", "Delete", "Update", "Add Team")

    def teams_sla_tab_labels(self):
        labels = []
        for text in self.texts_of((By.CSS_SELECTOR, "[role='tablist'] [role='tab']")):
            if text:
                labels.append(text)
        return labels

    def open_teams_sla_tab(self, label):
        """Opens a tab and returns its panel element."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))
        panel = (By.ID, f"tabpanel-{self.TEAMS_SLA_TABS[label]}")
        return self.wait_visible(panel)

    @staticmethod
    def enabled_edit_controls(panel):
        """
        Lists everything inside a tab panel that could change data: enabled inputs
        (search boxes excluded), switches, and buttons with an editing label.
        """
        found = []
        for el in panel.find_elements(By.CSS_SELECTOR, "input, textarea, select"):
            placeholder = (el.get_attribute("placeholder") or "").lower()
            kind = (el.get_attribute("type") or "").lower()
            if kind in ("search", "hidden") or placeholder.startswith("search"):
                continue
            if el.is_enabled() and el.get_attribute("readonly") is None:
                found.append(f"<{el.tag_name} type={kind or '-'}>")
        for el in panel.find_elements(By.CSS_SELECTOR, "[role='switch']"):
            if el.is_enabled():
                found.append(f"switch '{el.get_attribute('aria-label')}'")
        for el in panel.find_elements(By.TAG_NAME, "button"):
            text = el.text.strip()
            if text in ReportsPage.EDIT_BUTTON_LABELS:
                found.append(f"button '{text}'")
        return found

    @staticmethod
    def holiday_controls(panel):
        """The edit controls inside the Holidays tab (empty lists when absent)."""
        return {
            "date_inputs": panel.find_elements(By.CSS_SELECTOR, "input[type='date']"),
            "add_buttons": panel.find_elements(By.XPATH, ".//button[normalize-space()='Add']"),
            "remove_buttons": panel.find_elements(
                By.CSS_SELECTOR, "button[aria-label^='Remove ']"
            ),
        }

    @staticmethod
    def pool_controls(panel):
        """The CC Initiator Pools controls: daily-limit box, Save button, availability switches."""
        return {
            "limit_inputs": panel.find_elements(By.CSS_SELECTOR, "input[type='number']"),
            "save_buttons": panel.find_elements(By.XPATH, ".//button[normalize-space()='Save']"),
            "switches": panel.find_elements(By.CSS_SELECTOR, "[role='switch']"),
        }

    # ---- Teams & SLA: the Working Hours editor ----

    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")
    MODAL_TITLE = (By.CSS_SELECTOR, "div[role='dialog'] h2")
    MODAL_CANCEL = (By.XPATH, "//div[@role='dialog']//button[normalize-space()='Cancel']")
    WORKING_HOURS_EDIT = (
        By.XPATH, "//div[@id='tabpanel-working-hours']//button[normalize-space()='Edit']"
    )
    # The two read-only boxes on the Working Hours card (Start, End).
    WORKING_HOURS_VALUES = (By.CSS_SELECTOR, "#tabpanel-working-hours input[disabled]")

    def has_working_hours_edit(self):
        return self.exists(self.WORKING_HOURS_EDIT)

    def working_hours_on_card(self):
        """[start, end] as shown on the Working Hours card, e.g. ["08:00", "17:00"]."""
        values = []
        for box in self.driver.find_elements(*self.WORKING_HOURS_VALUES):
            values.append(box.get_attribute("value"))
        return values

    def open_working_hours_editor(self):
        self.click(self.WORKING_HOURS_EDIT)
        self.wait_visible(self.MODAL)

    def modal_title(self):
        return self.text_of(self.MODAL_TITLE)

    def modal_box_value(self, box_id):
        """The value of a text box inside the open modal (e.g. "wh-start")."""
        return self.driver.find_element(By.ID, box_id).get_attribute("value")

    def modal_has_button(self, text):
        return self.exists((By.XPATH, f"//div[@role='dialog']//button[normalize-space()='{text}']"))

    def modal_button_is_enabled(self, text):
        return self.driver.find_element(
            By.XPATH, f"//div[@role='dialog']//button[normalize-space()='{text}']"
        ).is_enabled()

    def cancel_open_modal(self):
        """Presses Cancel inside the open modal (never Save) and waits for it to close."""
        self.click(self.MODAL_CANCEL)
        self.wait_gone(self.MODAL)

    def is_modal_open(self):
        return self.exists(self.MODAL)

    # ---- Teams & SLA: the Escalation Ladder (Non-Motor / Motor) ----

    _LADDER = "//div[@id='tabpanel-escalation-ladder']"
    # "Add" per rung opens the add-contact modal. Its aria-label is "Add <level> contact for <scope>".
    LADDER_ADD_BUTTONS = (By.XPATH, _LADDER + "//button[starts-with(@aria-label,'Add ')]")
    # "Remove" per contact. NEVER clicked: it deactivates the contact straight away, no confirm.
    LADDER_REMOVE_BUTTONS = (By.XPATH, _LADDER + "//button[starts-with(@aria-label,'Remove ')]")
    LADDER_LEVEL_LABELS = (By.XPATH, _LADDER + "//ol/li/div/div[contains(@class,'uppercase')]")

    def choose_ladder_scope(self, label):
        """Switches the ladder between "Non-Motor" and "Motor"."""
        scope = (By.XPATH, self._LADDER + f"//button[@role='tab'][normalize-space()='{label}']")
        self.click(scope)
        self.wait.until(
            lambda d: d.find_element(*scope).get_attribute("aria-selected") == "true"
        )

    def ladder_level_labels(self):
        """The rungs of the ladder on screen, top to bottom (textContent: they are CSS-uppercased)."""
        labels = []
        for element in self.driver.find_elements(*self.LADDER_LEVEL_LABELS):
            labels.append((element.get_attribute("textContent") or "").strip())
        return labels

    def ladder_add_labels(self):
        """The aria-label of every "Add" button on the ladder."""
        labels = []
        for button in self.driver.find_elements(*self.LADDER_ADD_BUTTONS):
            labels.append(button.get_attribute("aria-label"))
        return labels

    def ladder_remove_count(self):
        return self.count(self.LADDER_REMOVE_BUTTONS)

    def ladder_text(self):
        return self.driver.find_element(By.ID, "tabpanel-escalation-ladder").text

    def open_ladder_add_modal(self, aria_label):
        """Presses the "Add" button with this aria-label and waits for the modal."""
        self.click((By.XPATH, self._LADDER + f"//button[@aria-label=\"{aria_label}\"]"))
        self.wait_visible(self.MODAL)

    # ---- Teams & SLA: the CC Initiator Pools roster ----

    _POOLS = "//div[@id='tabpanel-cc-initiator-pools']"
    POOL_BUTTONS = (By.XPATH, _POOLS + "//ul/li/button")
    ROSTER_HEADERS = (By.XPATH, _POOLS + "//*[@data-testid='cc-initiator-members']//thead//th")
    ROSTER_ROWS = (By.XPATH, _POOLS + "//*[@data-testid='cc-initiator-members']//tbody/tr")

    def pool_labels(self):
        """The pools listed on the left of the CC Initiator Pools tab (e.g. "Complaints", "Others")."""
        return self.texts_of(self.POOL_BUTTONS)

    def pool_roster(self, pool_label):
        """
        Opens one pool and returns its members as (name, status) pairs.
        Status is the roster's own word: "Available", "At limit", "Paused" or "Account off".
        """
        self.click((By.XPATH, self._POOLS + f"//ul/li/button[normalize-space()='{pool_label}']"))
        # The heading above the table switches to the pool's name.
        self.wait_visible((By.XPATH, self._POOLS + f"//h3[normalize-space(text())='{pool_label}']"))
        headers = self.texts_of(self.ROSTER_HEADERS)
        if "Person" not in headers or "Status" not in headers:
            return []
        person_at = headers.index("Person")
        status_at = headers.index("Status")
        roster = []
        for row in self.driver.find_elements(*self.ROSTER_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) <= max(person_at, status_at):
                continue  # the "No members assigned" row
            name = cells[person_at].text.strip().split("\n")[0]
            roster.append((name, cells[status_at].text.strip()))
        return roster

    # ---- Historical Complaints ----

    HISTORICAL_HEADING = "Historical Complaints"
    IMPORT_BUTTON = (By.XPATH, "//button[normalize-space()='Import']")
    TEMPLATE_BUTTON = (By.XPATH, "//button[normalize-space()='Download template']")
    IMPORT_FILE_INPUT = (By.CSS_SELECTOR, "input[type='file'][accept='.xlsx']")
    IMPORT_RESULT_CALLOUT = (
        By.XPATH, "//*[normalize-space()='Nothing was imported.' "
        "or normalize-space()='Fix the rows below and re-upload — nothing was imported.']",
    )

    def has_import_controls(self):
        return self.exists(self.IMPORT_BUTTON) and self.exists(self.TEMPLATE_BUTTON)

    # PR #301: the archive is paginated, searchable and filterable.
    ARCHIVE_ROWS = (By.CSS_SELECTOR, "[data-testid='historical-complaints-table'] tbody tr")
    ARCHIVE_EMPTY = "No historical complaints match your search."
    ARCHIVE_SEARCH = (By.CSS_SELECTOR, "input[aria-label='Search historical complaints']")
    # The pagination footer's "N results" line (a leaf element).
    RESULTS_LINE = (
        By.XPATH, "//div[not(*)][contains(normalize-space(.),' result')]"
    )
    FILTER_DRAWER = (By.CSS_SELECTOR, "div[role='dialog']")
    # The four filters in the Filter drawer: label -> the dropdown's id.
    ARCHIVE_FILTERS = {
        "Category": "hist-filter-complaint_category",
        "Department": "hist-filter-assigned_department",
        "Source": "hist-filter-source",
        "Final Status": "hist-filter-final_status",
    }

    def archive_row_count(self):
        """
        How many complaints the archive holds (the "N results" total, all pages).
        PR #301 paginated the table and changed its empty message, so rows on screen are no
        longer the whole archive.
        """
        if self.exists(self.innermost_containing(self.ARCHIVE_EMPTY)):
            return 0
        return self.archive_total()

    def archive_total(self):
        """The number in the pagination footer's "N results" line."""
        for text in self.texts_of(self.RESULTS_LINE):
            words = text.split()
            if len(words) == 2 and words[0].isdigit() and words[1] in ("result", "results"):
                return int(words[0])
        return self.count(self.ARCHIVE_ROWS)

    def archive_cells(self, column):
        """Every row's value in one archive column (found by its header), top to bottom."""
        headers = self.texts_of(
            (By.CSS_SELECTOR, "[data-testid='historical-complaints-table'] thead th")
        )
        at = headers.index(column)
        values = []
        for row in self.driver.find_elements(*self.ARCHIVE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > at:
                values.append(cells[at].text.strip())
        return values

    def search_archive(self, text):
        """Types into the archive search box and presses Enter (the search runs on Enter)."""
        self.type_into(self.ARCHIVE_SEARCH, text)
        self.driver.find_element(*self.ARCHIVE_SEARCH).send_keys(Keys.ENTER)

    def open_archive_filter(self):
        self.click((By.XPATH, "//button[starts-with(normalize-space(),'Filter')]"))
        self.wait_visible(self.FILTER_DRAWER)

    def archive_filter_labels(self):
        """The field labels inside the Filter drawer, top to bottom."""
        return self.texts_of((By.CSS_SELECTOR, "div[role='dialog'] label"))

    def archive_filter_options(self, label):
        trigger = (By.ID, self.ARCHIVE_FILTERS[label])
        return self.read_dropdown_options(trigger)

    def tick_archive_filter(self, label, value):
        """Ticks one value in a filter (multi-select: the list stays open, so close it by its trigger)."""
        trigger = (By.ID, self.ARCHIVE_FILTERS[label])
        self.open_dropdown(trigger)
        option = (
            By.XPATH,
            f"//ul[@role='listbox']//button[@role='option'][normalize-space()=\"{value}\"]",
        )
        self._scroll_within_listbox(self.wait_visible(option))
        self.click(option, scroll=False)
        self._close_dropdown_if_still_open(trigger)

    def apply_archive_filter(self):
        self.click((By.XPATH, "//div[@role='dialog']//button[normalize-space()='Apply Filter']"))
        self.wait_gone(self.FILTER_DRAWER)

    def close_drawer(self):
        self.click((By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']"))
        self.wait_gone(self.FILTER_DRAWER)

    def open_first_archive_row(self):
        """Clicks the first archive row and returns its Complaint ID."""
        complaint_id = self.archive_cells("Complaint ID")[0]
        self.driver.find_elements(*self.ARCHIVE_ROWS)[0].click()
        self.wait.until(lambda d: "/historical/" in d.current_url)
        return complaint_id

    def historical_detail_tabs(self):
        """The tab labels on a /historical/<id> detail page."""
        tabs = []
        for link in self.driver.find_elements(By.XPATH, "//a[contains(@href,'/historical/')]"):
            text = link.text.strip()
            if text and text not in tabs:
                tabs.append(text)
        return tabs

    def upload_import_file(self, path):
        """
        Sends a file to the hidden Import file input.
        The input is hidden (class "hidden"), so that class is removed first - Selenium cannot type into a hidden input.
        """
        box = self.driver.find_element(*self.IMPORT_FILE_INPUT)
        self.driver.execute_script("arguments[0].classList.remove('hidden');", box)
        box.send_keys(path)

    def wait_for_import_rejection(self):
        """Waits for the failed-import message and returns its title."""
        body = self.wait_visible(self.IMPORT_RESULT_CALLOUT)
        return body.find_element(By.XPATH, "preceding-sibling::p[1]").text.strip()
