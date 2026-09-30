"""
The read-only oversight screens. Four of them share this page object because they are all
"a heading, some tiles, and a table" and nothing else:

  /reports       the management report - see the warning below, this one CHANGED
  /audit-trail   the organisation-wide audit trail
  /history       Customer History - every past case for one customer
  /teams-sla     Teams & SLA configuration (seven tabs - see the Teams & SLA section below)
  /historical    the Historical Complaints archive (R46 import lives here, HOD only)

NOTHING ON THESE SCREENS IS EVER INVENTED. The report is calculated live from the tickets
every time it is opened - there is no stored copy, no cache, and no placeholder number. That
is why the tests below compare the report's figures against the ticket list rather than
against a value written down in advance.

===================================================================================
READ THIS BEFORE WRITING A REPORT TEST - the report is now ONE CALENDAR MONTH
===================================================================================
The management report used to cover every ticket that had ever existed. It does not any
more. It now reports on a SINGLE calendar month, and when no month is asked for it shows the
PREVIOUS one (apps/api app/reports/period.py, Dubai-local month boundaries).

Two consequences, and both have already caught this suite out:

  1. The report's "Total Tickets" is normally SMALLER than the ticket lists, not bigger.
     A ticket created today is not in last month's report. Any test comparing the two must
     say "the month cannot exceed all time", never the other way round.

  2. The heading is "Team Performance Report", not "Reports". "Reports" is only the
     breadcrumb and the menu label now.
"""

from __future__ import annotations

import re

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage

#: Anchored on the card TITLE, then "the nearest ancestor that actually contains a table".
#: Counting div levels ("ancestor::div[4]") would break the moment the Card component gains
#: or loses a wrapper, which is exactly the kind of edit nobody thinks to check tests for.
_EMPLOYEE_CARD = "//h3[normalize-space()='Employee Performance']/ancestor::div[.//table][1]"


class ReportsPage(BasePage):
    #: The six tiles at the top of the management report.
    REPORT_KPIS = [
        "Total Tickets",
        "Open",
        "Resolved",
        "SLA Breaches",
        "SLA Compliance",
        "Avg. Resolution Time",
    ]

    #: The three breakdown cards underneath the org hierarchy.
    REPORT_TABLES = ["By Department", "By Status", "By Priority"]

    #: Every card the report renders, top to bottom. The first two are the September addition.
    REPORT_SECTIONS = [
        "Team Structure",
        "Employee Performance",
        "By Department",
        "By Status",
        "By Priority",
    ]

    #: The columns of the Employee Performance table, in the order the report renders them.
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

    # ---- the month selector (a CustomSelect, so no native <select> here) ----
    # Only one dropdown exists on /reports, which is why the trigger needs no further
    # qualification. If a second one is ever added, scope this to the header instead.
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

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.HEADING)

    def wait_for_table(self) -> None:
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def wait_for_report(self) -> None:
        """
        Waits until the report itself has finished rendering, not merely the heading.

        /reports has its own loading.tsx skeleton, so the heading and the month selector are
        on screen while the figures are still being fetched. Waiting for a KPI tile as well is
        the difference between reading the report and reading its skeleton.
        """
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.is_kpi_displayed("Total Tickets"))

    # ---- the month selector ----

    def choose_month(self, label: str) -> None:
        """
        Picks a month by its visible label, e.g. "July 2026".

        Deliberately NOT BasePage.choose_option: choosing a month navigates (the selector
        pushes /reports?month=...), so the tidy-up click that choose_option makes afterwards
        can land on a page that is already being replaced. The panel closes itself here, so
        there is nothing to tidy.
        """
        self.open_dropdown(self.MONTH_PICKER_TRIGGER)
        option = (
            By.XPATH,
            "//ul[@role='listbox']//button[@role='option']"
            f"[normalize-space()='{label}']",
        )
        # scroll=False for the same reason choose_option uses it: the panel is fixed,
        # portaled to <body>, and re-anchors on every scroll event, so scrolling to "reach"
        # an option moves the option instead of the window. This selector sits top-right,
        # where the notification toast stack lands, which made it doubly prone to it.
        self._scroll_within_listbox(self.wait_visible(option))
        self.click(option, scroll=False)

    def get_month_options(self) -> list[str]:
        """Every month the selector offers, without choosing one."""
        options = self.read_dropdown_options(self.MONTH_PICKER_TRIGGER)
        # Belt and braces: read_dropdown_options already closes the panel. If anything is
        # still up, Escape it - never by re-clicking the trigger, which is a TOGGLE and would
        # re-open the panel we are trying to shut.
        self.close_any_open_dropdown()
        return options

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self) -> str:
        return self.wait_visible(self.HEADING).text

    def is_kpi_displayed(self, label: str) -> bool:
        return self.exists((By.XPATH, f"//div[normalize-space()='{label}']"))

    def get_kpi_value(self, label: str) -> str:
        """A tile's number. Same three-level layout as the dashboard tiles."""
        return self.wait_visible(
            (
                By.XPATH,
                f"//div[normalize-space()='{label}']/parent::div/following-sibling::div",
            )
        ).text

    def get_kpi_number(self, label: str) -> int:
        return int(re.sub(r"\D+", "", self.get_kpi_value(label)))

    def has_card(self, title: str) -> bool:
        """True when a named card (e.g. "By Department") is on the page. Case does not matter."""
        return self.exists(self.text_ignoring_case(title))

    def get_row_count(self) -> int:
        return self.count(self.TABLE_ROWS)

    def shows_empty_state(self) -> bool:
        """True when the screen shows an honest "nothing to show" instead of an error."""
        return self.exists(
            (
                By.XPATH,
                "//*[contains(normalize-space(.),'No ')"
                " and not(.//*[contains(normalize-space(.),'No ')])]",
            )
        )

    # ---- the reporting period ----

    def get_reporting_period_line(self) -> str:
        """
        The whole "Reporting period August 2026 - Generated 2 Sep 2026" line, or "" while the
        page is between renders.

        Never raises, on purpose: tests wait on this line to change after a month is chosen,
        and a getter that raised mid-navigation would blow up the wait it is being polled
        inside instead of simply not matching yet.
        """
        return self.text_of(self.REPORTING_PERIOD_LINE)

    def get_selected_month(self) -> str:
        """The month the selector is currently showing, e.g. "August 2026"."""
        return self.wait_visible(self.MONTH_PICKER_TRIGGER).text.strip()

    def has_month_picker(self) -> bool:
        return self.exists(self.MONTH_PICKER_TRIGGER)

    # ---- Team Structure ----

    def has_team_tree(self) -> bool:
        return self.exists(self.TEAM_TREE)

    def get_team_rows(self) -> list[str]:
        """The teams listed, each with its own summary line ("<name> 4 employees 12 resolved …")."""
        return self.texts_of(self.TEAM_BRANCHES)

    def get_employee_rows_in_tree(self) -> list[str]:
        """
        The employees currently shown underneath their teams.

        Every branch starts EXPANDED (defaultOpen), so these are visible without clicking
        anything. Collapsing a branch removes its children from the DOM entirely, which is
        what the collapse test asserts on.
        """
        return self.texts_of(self.TEAM_EMPLOYEES)

    def collapse_first_team(self) -> None:
        branches = self.driver.find_elements(*self.TEAM_BRANCHES)
        if branches:
            self.scroll_to_middle(branches[0])
            branches[0].click()

    def count_employees_in_tree(self) -> int:
        return self.count(self.TEAM_EMPLOYEES)

    # ---- Employee Performance ----

    def has_employee_table(self) -> bool:
        return self.exists(self.EMPLOYEE_TABLE)

    def get_employee_table_columns(self) -> list[str]:
        return [header for header in self.texts_of(self.EMPLOYEE_HEADERS) if header]

    def get_employee_row_count(self) -> int:
        return self.count(self.EMPLOYEE_ROWS)

    def get_employee_row(self, one_based_row: int) -> list[str]:
        """One employee row's cells, left to right. Row 1 is the top performer."""
        rows = self.driver.find_elements(*self.EMPLOYEE_ROWS)
        if len(rows) < one_based_row:
            return []
        return [
            cell.text.strip()
            for cell in rows[one_based_row - 1].find_elements(By.TAG_NAME, "td")
        ]

    def employee_table_says_no_activity(self) -> bool:
        """True when the report honestly says the month had no employee activity."""
        return self.exists(
            self.innermost_containing("No employee activity recorded for this period")
        )

    # ---- the audit trail ----

    def has_audit_entries(self) -> bool:
        """
        True when the audit trail is actually showing recorded actions.

        Each entry is a block with an <h4> title (the event name) - NOT a table row and not a
        list item, which is what caught this check out the first time. The screen also has an
        explicit "nothing here yet" message, so absence of that is the other half of the answer.
        """
        says_empty = self.exists(
            (By.XPATH, "//*[contains(normalize-space(.),'No audit events')]")
        )
        return not says_empty and self.count((By.CSS_SELECTOR, "h4")) > 0

    def audit_contains(self, text: str) -> bool:
        """True when a named event type appears in the audit trail."""
        return self.exists(self.innermost_containing(text))

    # ---- Customer History ----

    def search_customer(self, text: str) -> None:
        self.type_into((By.CSS_SELECTOR, "input[placeholder^='Search']"), text)

    def shows_customer_list(self) -> bool:
        return self.exists((By.TAG_NAME, "table")) or self.exists((By.CSS_SELECTOR, "li"))

    #: app/history/HistorySearch.tsx placeholder.
    HISTORY_SEARCH = (By.CSS_SELECTOR, "input[placeholder^='Search a customer']")
    #: CustomerHistoryGrouped.tsx section labels, in its reading order.
    HISTORY_GROUPS = ["Enquiry Tickets", "Complaint Tickets", "Discarded Tickets"]
    HISTORY_ROW_LINKS = (By.XPATH, "//a[contains(@href,'/tickets/') and contains(@href,'returnTo=')]")

    def has_history_search(self) -> bool:
        return self.exists(self.HISTORY_SEARCH)

    def history_view_is(self, label: str) -> bool:
        """The Grouped / Timeline switch (CustomerHistoryView) - aria-pressed on the chosen one."""
        buttons = self.driver.find_elements(
            By.XPATH, f"//button[@aria-pressed][normalize-space()='{label}']"
        )
        return bool(buttons) and buttons[0].get_attribute("aria-pressed") == "true"

    def switch_history_view(self, label: str) -> None:
        self.click((By.XPATH, f"//button[@aria-pressed][normalize-space()='{label}']"))
        self.wait.until(lambda d: self.history_view_is(label))

    def history_group_labels(self) -> list[str]:
        """The grouped sections shown (textContent - the labels are CSS-uppercased)."""
        labels = []
        for button in self.driver.find_elements(By.XPATH, "//button[@aria-expanded]"):
            text = (button.get_attribute("textContent") or "").strip()
            labels += [g for g in self.HISTORY_GROUPS if text.startswith(g)]
        return labels

    def expand_all_history_groups(self) -> None:
        for button in self.driver.find_elements(By.XPATH, "//button[@aria-expanded='false']"):
            text = (button.get_attribute("textContent") or "").strip()
            if any(text.startswith(g) for g in self.HISTORY_GROUPS):
                self.scroll_to_middle(button)
                button.click()

    def history_references(self) -> list[str]:
        """Reference numbers of every history row on screen (the row's first bold span)."""
        refs = []
        for link in self.driver.find_elements(*self.HISTORY_ROW_LINKS):
            spans = link.find_elements(By.CSS_SELECTOR, "span.font-semibold")
            if spans:
                refs.append(spans[0].text.strip())
        return refs

    # ---- Teams & SLA (components/teams-sla/TeamsSlaClient.tsx) ----

    #: Tab label -> the tab's key, which Tabs.tsx turns into id="tabpanel-<key>".
    TEAMS_SLA_TABS = {
        "Teams": "teams",
        "SLA Policy": "sla",
        "Escalation Ladder": "escalation-ladder",
        "CC Initiator Pools": "cc-initiator-pools",
        "Working Hours": "working-hours",
        "Holidays": "holidays",
        "Classification": "classification",
    }
    #: Button labels whose presence means a panel can CHANGE something - matched EXACTLY, never
    #: as a prefix: the Classification tree's own node buttons are taxonomy values, and an
    #: enquiry named e.g. "Add driver" is data, not an edit control.
    EDIT_BUTTON_LABELS = ("Save", "Edit", "Add", "Remove", "Delete", "Update", "Add Team")

    def teams_sla_tab_labels(self) -> list[str]:
        return [t for t in self.texts_of((By.CSS_SELECTOR, "[role='tablist'] [role='tab']")) if t]

    def open_teams_sla_tab(self, label: str):
        """Selects a tab and returns its (now visible) tabpanel element."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))
        panel = (By.ID, f"tabpanel-{self.TEAMS_SLA_TABS[label]}")
        return self.wait_visible(panel)

    @staticmethod
    def enabled_edit_controls(panel) -> list[str]:
        """
        What inside a tabpanel could change data: enabled text/number/date inputs, textareas
        and selects (a search box is navigation, not editing, so type=search and the
        placeholder "Search..." boxes are left out), switches, and buttons labelled with an
        editing verb.
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
    def holiday_controls(panel) -> dict:
        """HolidaysCard.tsx edit controls inside the Holidays tabpanel (empty lists when absent)."""
        return {
            "date_inputs": panel.find_elements(By.CSS_SELECTOR, "input[type='date']"),
            "add_buttons": panel.find_elements(By.XPATH, ".//button[normalize-space()='Add']"),
            "remove_buttons": panel.find_elements(
                By.CSS_SELECTOR, "button[aria-label^='Remove ']"
            ),
        }

    @staticmethod
    def pool_controls(panel) -> dict:
        """CC Initiator Pools controls: the daily-limit box + Save (CcInitiatorDailyLimit) and
        the per-initiator availability switches (CcInitiatorMembersTable)."""
        return {
            "limit_inputs": panel.find_elements(By.CSS_SELECTOR, "input[type='number']"),
            "save_buttons": panel.find_elements(By.XPATH, ".//button[normalize-space()='Save']"),
            "switches": panel.find_elements(By.CSS_SELECTOR, "[role='switch']"),
        }

    # ---- Historical Complaints (components/complaints/HistoricalArchiveClient.tsx) ----

    HISTORICAL_HEADING = "Historical Complaints"
    IMPORT_BUTTON = (By.XPATH, "//button[normalize-space()='Import']")
    TEMPLATE_BUTTON = (By.XPATH, "//button[normalize-space()='Download template']")
    IMPORT_FILE_INPUT = (By.CSS_SELECTOR, "input[type='file'][accept='.xlsx']")
    IMPORT_RESULT_CALLOUT = (
        By.XPATH, "//*[normalize-space()='Nothing was imported.' "
        "or normalize-space()='Fix the rows below and re-upload — nothing was imported.']",
    )

    def has_import_controls(self) -> bool:
        return self.exists(self.IMPORT_BUTTON) and self.exists(self.TEMPLATE_BUTTON)

    def archive_row_count(self) -> int:
        """Data rows in the archive table (0 for the "No historical complaints" empty row)."""
        if self.exists(self.innermost_containing("No historical complaints imported yet")):
            return 0
        return self.count((By.CSS_SELECTOR, "table tbody tr"))

    def upload_import_file(self, path: str) -> None:
        """
        Hands a file to the hidden Import <input> - the same element the Import button clicks.

        The input is `class="hidden"` (display:none), which chromedriver will not type into,
        so the class is dropped first. Nothing else about the upload is simulated: the page's
        own onChange posts the file exactly as a person's pick would.
        """
        box = self.driver.find_element(*self.IMPORT_FILE_INPUT)
        self.driver.execute_script("arguments[0].classList.remove('hidden');", box)
        box.send_keys(path)

    def wait_for_import_rejection(self) -> str:
        """Waits for the failed-import Callout and returns its title (the API's message)."""
        body = self.wait_visible(self.IMPORT_RESULT_CALLOUT)
        return body.find_element(By.XPATH, "preceding-sibling::p[1]").text.strip()
