"""
The read-only oversight screens. Four of them share this page object because they are all
"a heading, some tiles, and a table" and nothing else:

  /reports       the management report - see the warning below, this one CHANGED
  /audit-trail   the organisation-wide audit trail
  /history       Customer History - every past case for one customer
  /teams-sla     Teams & SLA configuration

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
