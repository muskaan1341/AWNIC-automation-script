"""
Module 15 (part 2) - Reports, the audit trail and a ticket's own history.

The report covers one calendar month (the previous month by default), counted in Dubai time.
Report figures are checked against each other and against the ticket lists.
The audit trail must never offer an edit or delete button.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from selenium.webdriver.common.by import By

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.reports_page import ReportsPage

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


# ---------- month helpers (the report uses Dubai time) ----------

DUBAI = ZoneInfo("Asia/Dubai")


def _shift_months(year, month, delta):
    """Move (year, month) forward or back by `delta` months."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def current_month():
    now = datetime.now(DUBAI)
    return now.year, now.month


def previous_month():
    year, month = current_month()
    return _shift_months(year, month, -1)


def month_label(year_month):
    """(2026, 8) -> "August 2026", as the report shows it."""
    year, month = year_month
    return f"{datetime(year, month, 1).strftime('%B')} {year}"


def month_param(year_month):
    """(2026, 6) -> "2026-06", as used in ?month= in the URL."""
    year, month = year_month
    return f"{year:04d}-{month:02d}"


class TestReportsAudit(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("hodEmail"))

    # ---------- the management report ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_report_opens_for_a_manager(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        assert self.reports.get_heading() == "Team Performance Report"
        assert not self.is_access_denied(), "A Head of Department may run the report"

    @pytest.mark.regression
    def test_the_report_shows_every_section(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        for card in ReportsPage.REPORT_SECTIONS:
            assert self.reports.has_card(card), (
                f"The report should include the '{card}' section"
            )

    @pytest.mark.regression
    def test_the_report_breaks_the_figures_down_three_ways(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        for card in ReportsPage.REPORT_TABLES:
            assert self.reports.has_card(card), (
                f"The report should break the totals down '{card}'"
            )

    @pytest.mark.api_candidate
    def test_the_report_figures_agree_with_each_other(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        total = self.reports.get_kpi_number("Total Tickets")
        open_count = self.reports.get_kpi_number("Open")
        resolved = self.reports.get_kpi_number("Resolved")

        assert open_count <= total, f"Open ({open_count}) cannot exceed total ({total})"
        assert resolved <= total, f"Resolved ({resolved}) cannot exceed total ({total})"
        assert open_count + resolved == total, (
            f"Open ({open_count}) + Resolved ({resolved}) must equal the total ({total})"
        )

    @pytest.mark.api_candidate
    def test_the_reports_month_cannot_hold_more_tickets_than_exist_altogether(self):
        """One month's report total is not more than all tickets in the three lists."""
        self.login_once(self.get("hodEmail"))

        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        enquiries = self.list.get_reported_result_count()

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        complaints = self.list.get_reported_result_count()

        # The discarded list uses the same "N results" line, so self.list can read it.
        self.open("/tickets/discarded")
        self.discarded.wait_until_loaded()
        discarded_count = self.list.get_reported_result_count()

        self.open_and_wait("/reports")
        self.reports.wait_for_report()
        report_total = self.reports.get_kpi_number("Total Tickets")

        # The report includes discarded tickets, so all three lists are added up.
        everything = enquiries + complaints + discarded_count
        assert report_total <= everything, (
            f"The report counts {report_total} tickets for one month, but only {everything} "
            "tickets exist in total"
        )

    # ---------- the reporting month ----------

    @pytest.mark.regression
    def test_the_report_names_the_month_it_covers(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        # With no month in the URL, the report shows the previous month.
        expected = month_label(previous_month())

        assert expected in self.reports.get_reporting_period_line(), (
            f"Expected '{expected}', line reads: {self.reports.get_reporting_period_line()}"
        )
        assert self.reports.get_selected_month() == expected, (
            "The month selector should agree with the reporting period line"
        )

    @pytest.mark.quarantine("unexplained-2026-09-09")
    def test_the_month_selector_offers_the_last_twelve_months(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        assert self.reports.has_month_picker(), "The report should offer a month selector"
        months = self.reports.get_month_options()

        assert len(months) == 12, f"Expected 12 months. Actual: {months}"
        assert months[0] == month_label(current_month()), (
            f"The list should start at the current month. Actual: {months}"
        )
        assert month_label(previous_month()) in months, (
            f"The default month must be selectable. Actual: {months}"
        )

    @pytest.mark.quarantine("unexplained-2026-09-09")
    def test_choosing_another_month_rebuilds_the_report_for_it(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        # Pick the first month that is not the one already selected.
        current = self.reports.get_selected_month()
        other = None
        for month in self.reports.get_month_options():
            if month != current:
                other = month
                break
        if other is None:
            pytest.skip("Only one month is selectable here.")

        self.reports.choose_month(other)

        self.wait_for_url_containing("month=")
        self.wait.until(lambda d: other in self.reports.get_reporting_period_line())

        assert other in self.reports.get_reporting_period_line(), (
            f"The report should now cover {other}. Line reads: "
            f"{self.reports.get_reporting_period_line()}"
        )
        assert self.reports.get_selected_month() == other, (
            "The selector should keep showing the month that was chosen"
        )

    @pytest.mark.regression
    def test_a_bookmarked_month_opens_straight_into_that_month(self):
        self.login_once(self.get("hodEmail"))

        year, month = previous_month()
        wanted = _shift_months(year, month, -2)
        self.open_and_wait(f"/reports?month={month_param(wanted)}")
        self.reports.wait_for_report()

        assert month_label(wanted) in self.reports.get_reporting_period_line(), (
            f"Expected {month_label(wanted)}, line reads: {self.reports.get_reporting_period_line()}"
        )

    @pytest.mark.regression
    def test_a_nonsense_month_does_not_produce_a_report(self):
        """A month like "not-a-month" in the URL must not show a report."""
        self.login_once(self.get("hodEmail"))
        # open_and_wait() waits for a heading or table, which should not appear here.
        self.open("/reports?month=not-a-month")
        self.wait_for_page_load()

        headings = self.driver.find_elements(
            By.XPATH, "//h1[normalize-space()='Team Performance Report']"
        )
        reported = len(headings) > 0 and self.reports.is_kpi_displayed("Total Tickets")
        assert not reported, (
            f"A bad month must not show a report. The page shows: {self.page_text_snippet()}"
        )

    # ---------- Team Structure and Employee Performance ----------

    @pytest.mark.regression
    def test_the_team_structure_lists_teams_with_their_employees_underneath(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        assert self.reports.has_card("Team Structure"), (
            "The report should show the Team Structure section"
        )

        if not self.reports.has_team_tree():
            pytest.skip("No team activity in the reporting month (empty state shown).")
        assert self.reports.get_team_rows(), "The tree should list at least one team"
        assert self.reports.count_employees_in_tree() > 0, (
            "Teams start expanded, so their employees should be visible"
        )

    @pytest.mark.regression
    def test_a_team_branch_can_be_collapsed(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        if not self.reports.has_team_tree() or self.reports.count_employees_in_tree() == 0:
            pytest.skip("No team activity in the reporting month, so there is no branch to collapse.")
        before = self.reports.count_employees_in_tree()
        self.reports.collapse_first_team()

        self.wait.until(lambda d: self.reports.count_employees_in_tree() < before)
        assert self.reports.count_employees_in_tree() < before, (
            "Collapsing a team should hide its employees"
        )

    @pytest.mark.regression
    def test_the_employee_table_carries_every_metric_a_manager_analyses(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        if self.reports.employee_table_says_no_activity():
            pytest.skip("No employee activity in the reporting month (empty state shown).")
        assert self.reports.has_employee_table(), "Employee Performance should be a table"

        # Headers are shown in uppercase by CSS, so compare in lowercase.
        columns = []
        for header in self.reports.get_employee_table_columns():
            columns.append(header.lower())
        for column in ReportsPage.EMPLOYEE_COLUMNS:
            assert column.lower() in columns, (
                f"Missing column '{column}'. Actual: {self.reports.get_employee_table_columns()}"
            )

    @pytest.mark.api_candidate
    def test_the_employee_table_is_ranked_by_tickets_resolved(self):
        """Rows are numbered 1, 2, 3... and sorted by tickets resolved, highest first."""
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        rows = self.reports.get_employee_row_count()
        if rows < 2:
            pytest.skip("Fewer than two active employees, so there is no order to check.")
        previous = float("inf")
        for row in range(1, rows + 1):
            cells = self.reports.get_employee_row(row)
            assert cells[0] == str(row), f"Row {row} should have rank {row}. Actual: {cells}"
            resolved = int(re.sub(r"\D+", "", cells[3]))
            assert resolved <= previous, (
                f"Row {row} resolved {resolved}, more than the row above ({previous})"
            )
            previous = resolved

    @pytest.mark.api_candidate
    def test_the_tree_and_the_table_describe_the_same_people(self):
        """The team tree and the employee table show the same number of people."""
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        if not self.reports.has_team_tree() or self.reports.employee_table_says_no_activity():
            pytest.skip("No employee activity in the reporting month.")
        assert self.reports.count_employees_in_tree() == self.reports.get_employee_row_count(), (
            "The team tree and the employee table should list the same number of people"
        )

    # ---------- the audit trail ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_audit_trail_opens_and_has_entries(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/audit-trail")
        self.reports.wait_until_loaded()

        assert self.reports.get_heading() == "Audit Trail"
        assert self.reports.has_audit_entries(), "The audit trail should not be empty"

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_audit_trail_offers_no_way_to_edit_or_delete_an_entry(self):
        """The audit trail has no Edit or Delete buttons."""
        # Head of Department, not Admin: only HOD and Manager can open the audit trail.
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/audit-trail")

        assert not self.is_access_denied(), (
            f"The audit trail must open for a Head of Department. Page says: {self.page_text_snippet()}"
        )
        assert not self.reports.has_button("Delete"), "An audit entry may never be deleted"
        assert not self.reports.has_button("Edit"), "An audit entry may never be edited"

    @pytest.mark.regression
    def test_a_tickets_own_history_is_on_its_audit_tab(self):
        """A ticket's Audit tab lists its events, or says there are none yet."""
        self.login_once(self.get("hodEmail"))

        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.open_first_row()
        self.detail.wait_until_loaded()
        self.detail.open_audit_tab_and_wait()

        assert "/audit" in self.current_url(), (
            f"The Audit tab should open /tickets/{{id}}/audit. Landed on: {self.current_url()}"
        )

        entries = self.detail.get_audit_event_labels()
        if not entries:
            assert self.detail.page_mentions("No audit events"), (
                f"An empty Audit tab must say 'No audit events'. On screen: {self.page_text_snippet()}"
            )
            return

        for entry in entries:
            assert entry.strip(), f"Every entry must say what happened. Entries: {entries}"
