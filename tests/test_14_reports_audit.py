"""
MODULE 15 (part 2) - Reports, the audit trail and customer history.

THE ONE PROMISE THESE SCREENS MAKE: no number here is ever invented. The management report is
calculated from the live tickets every single time it is opened - there is no stored copy and
no cached figure that could quietly go stale. That is why the tests below compare the report
against the ticket list rather than against a number written down in advance: a number that
only matches itself proves nothing.

THE OTHER PROMISE: the audit trail cannot be edited or deleted by anybody, including an
administrator. The database itself refuses it, so there is no screen to test for it - what we
CAN test is that no edit or delete control is ever offered.

===================================================================================
THE REPORT COVERS ONE CALENDAR MONTH. It did not always.
===================================================================================
It used to total every ticket that had ever existed. It now reports a single month, and with no
month in the URL it shows the PREVIOUS one. So "the report should count at least as many
tickets as the lists show" - which this class used to assert - is now exactly backwards: a
ticket created today is deliberately absent from last month's report. The relationship that
still holds, and the one asserted below, is the other direction: one month can never contain
more tickets than all of time.
"""

from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from selenium.webdriver.common.by import By

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.reports_page import ReportsPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P1 'Org-wide Audit Trail page is HOD + Manager only' + B-P2 config screens
pytestmark = [pytest.mark.p1, pytest.mark.phase1]


# ==================================================================
# Working out the reporting month the same way the application does
# ==================================================================
#
# AWNIC is UTC+4, and the report's month boundaries are Dubai-local midnight. Working the month
# out in the machine's own timezone would make these tests wrong for four hours every day - and
# only at the turn of a month, which is the worst kind of flake.
DUBAI = ZoneInfo("Asia/Dubai")


def _shift_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def current_month() -> tuple[int, int]:
    now = datetime.now(DUBAI)
    return now.year, now.month


def previous_month() -> tuple[int, int]:
    year, month = current_month()
    return _shift_months(year, month, -1)


def month_label(year_month: tuple[int, int]) -> str:
    """"August 2026" - exactly how the report and the selector spell it."""
    year, month = year_month
    return f"{datetime(year, month, 1).strftime('%B')} {year}"


def month_param(year_month: tuple[int, int]) -> str:
    """"2026-06" - the shape the ?month= query parameter takes."""
    year, month = year_month
    return f"{year:04d}-{month:02d}"


class TestReportsAudit(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("hodEmail"))

    # ==================================================================
    # The management report - the screen itself
    # ==================================================================

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_report_opens_for_a_manager(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        # "Reports" is the MENU label and the breadcrumb. The page's own heading names what the
        # report actually is.
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
        # Every ticket in the month is counted as exactly one of the two - the report defines
        # Resolved as "total minus open", so these must add up EXACTLY, not merely fit inside.
        assert open_count + resolved == total, (
            f"Open ({open_count}) + Resolved ({resolved}) must equal the total ({total}) - "
            "every ticket is in exactly one of the two"
        )

    @pytest.mark.api_candidate
    def test_the_reports_month_cannot_hold_more_tickets_than_exist_altogether(self):
        """
        The real accuracy check: one month's report can never contain more tickets than the
        ticket lists hold in total. This is the test that catches a report reading from a stale
        cache, or one that quietly stopped applying its month window.
        """
        self.login_once(self.get("hodEmail"))

        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        enquiries = self.list.get_reported_result_count()

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        complaints = self.list.get_reported_result_count()

        # The discarded queue is a different table with its own page object, but the "N results"
        # line under it comes from the shared Pagination component, so the count is read the
        # same way.
        self.open("/tickets/discarded")
        self.discarded.wait_until_loaded()
        discarded_count = self.list.get_reported_result_count()

        self.open_and_wait("/reports")
        self.reports.wait_for_report()
        report_total = self.reports.get_kpi_number("Total Tickets")

        # The report counts EVERY ticket created in the month, discarded ones included - it
        # applies no reference_type filter - so all three queues belong on the right-hand side.
        everything = enquiries + complaints + discarded_count
        assert report_total <= everything, (
            f"The report counts {report_total} tickets for one month, but only {everything} "
            "exist in total across all three queues - a single month cannot contain more "
            "tickets than have ever been created"
        )

    # ==================================================================
    # The reporting month
    # ==================================================================

    @pytest.mark.regression
    def test_the_report_names_the_month_it_covers(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        # With no month in the URL the report covers the PREVIOUS calendar month, worked out in
        # Dubai time (the API's own rule - app/reports/period.py). Building the expected label
        # the same way keeps this test correct on 1 January and on a month boundary.
        expected = month_label(previous_month())

        assert expected in self.reports.get_reporting_period_line(), (
            f"The report should say which month it covers. Expected '{expected}', line reads: "
            f"{self.reports.get_reporting_period_line()}"
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

        assert len(months) == 12, (
            f"The selector lists a rolling year of months. Actual: {months}"
        )
        assert months[0] == month_label(current_month()), (
            f"The list should start at the current month. Actual: {months}"
        )
        assert month_label(previous_month()) in months, (
            f"The month the report defaults to must be selectable. Actual: {months}"
        )

    @pytest.mark.quarantine("unexplained-2026-09-09")
    def test_choosing_another_month_rebuilds_the_report_for_it(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        current = self.reports.get_selected_month()
        other = next(
            (month for month in self.reports.get_month_options() if month != current), None
        )
        if other is None:
            pytest.skip("Only one month is selectable here.")

        self.reports.choose_month(other)

        # The month goes into the URL, so the report is bookmarkable and shareable - the whole
        # reason it is a server round trip rather than client-side filtering.
        self.wait_for_url_containing("month=")
        self.wait.until(lambda d: other in self.reports.get_reporting_period_line())

        assert other in self.reports.get_reporting_period_line(), (
            f"Choosing {other} should rebuild the report for that month. Line reads: "
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
            f"A month in the URL should be the month reported. Expected {month_label(wanted)}, "
            f"line reads: {self.reports.get_reporting_period_line()}"
        )

    @pytest.mark.regression
    def test_a_nonsense_month_does_not_produce_a_report(self):
        """
        A month that is not a month is rejected by the API before any query runs (the route
        pattern-checks it), so the screen must not pretend to report on it.
        """
        self.login_once(self.get("hodEmail"))
        # Plain open() plus a load wait, NOT open_and_wait(): open_and_wait looks for a heading
        # or a table to decide the page has arrived, and the whole point here is that neither
        # should turn up.
        self.open("/reports?month=not-a-month")
        self.wait_for_page_load()

        reported = (
            len(
                self.driver.find_elements(
                    By.XPATH, "//h1[normalize-space()='Team Performance Report']"
                )
            )
            > 0
            and self.reports.is_kpi_displayed("Total Tickets")
        )
        assert not reported, (
            "A malformed month must never render a report as though it were valid. "
            f"The page shows: {self.page_text_snippet()}"
        )

    # ==================================================================
    # Team Structure and Employee Performance
    # ==================================================================

    @pytest.mark.regression
    def test_the_team_structure_lists_teams_with_their_employees_underneath(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        assert self.reports.has_card("Team Structure"), (
            "The report should show the org hierarchy it reports on"
        )

        if not self.reports.has_team_tree():
            pytest.skip(
                "No team activity in the reporting month, so the tree shows its empty state. "
                "Choose a month with resolved tickets to exercise this."
            )
        assert self.reports.get_team_rows(), "A rendered tree should list at least one team"
        assert self.reports.count_employees_in_tree() > 0, (
            "Teams start expanded, so their employees should already be visible"
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
            "Collapsing a team should hide the employees underneath it"
        )

    @pytest.mark.regression
    def test_the_employee_table_carries_every_metric_a_manager_analyses(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        if self.reports.employee_table_says_no_activity():
            pytest.skip(
                "No employee activity in the reporting month, so the table shows its empty "
                "state instead of columns."
            )
        assert self.reports.has_employee_table(), "Employee Performance should be a table"

        # COMPARE WITHOUT CASE. These headers are styled uppercase by CSS, and Selenium reports
        # the text the user actually SEES - so "Employee" in the markup comes back as
        # "EMPLOYEE". Asserting on the exact case was testing the stylesheet, not the report.
        # (BasePage.text_ignoring_case exists for the same reason.)
        columns = [c.lower() for c in self.reports.get_employee_table_columns()]
        for column in ReportsPage.EMPLOYEE_COLUMNS:
            assert column.lower() in columns, (
                f"The employee table is missing the '{column}' column. "
                f"Actual: {self.reports.get_employee_table_columns()}"
            )

    @pytest.mark.api_candidate
    def test_the_employee_table_is_ranked_by_tickets_resolved(self):
        """
        The table is a RANKING - the top performer first. If it ever stopped being sorted, the
        rank numbers down the left would be telling the reader something untrue.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        rows = self.reports.get_employee_row_count()
        if rows < 2:
            pytest.skip(
                "Fewer than two employees were active in the reporting month, so there is no "
                "ordering to check."
            )
        previous = float("inf")
        for row in range(1, rows + 1):
            cells = self.reports.get_employee_row(row)
            assert cells[0] == str(row), (
                f"Row {row} should carry rank {row}. Actual: {cells}"
            )
            resolved = int(re.sub(r"\D+", "", cells[3]))
            assert resolved <= previous, (
                f"Row {row} resolved {resolved}, which is more than the row above "
                f"({previous}) - the table is meant to be ranked"
            )
            previous = resolved

    @pytest.mark.api_candidate
    def test_the_tree_and_the_table_describe_the_same_people(self):
        """
        Both sections are built from the same list of people. If the tree and the table ever
        disagreed about how many employees were active, one of them would be wrong.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/reports")
        self.reports.wait_for_report()

        if not self.reports.has_team_tree() or self.reports.employee_table_says_no_activity():
            pytest.skip("No employee activity in the reporting month.")
        assert self.reports.count_employees_in_tree() == self.reports.get_employee_row_count(), (
            "The org tree and the employee table are the same people counted twice - they must agree"
        )

    # ==================================================================
    # The audit trail
    # ==================================================================

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_audit_trail_opens_and_has_entries(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/audit-trail")
        self.reports.wait_until_loaded()

        assert self.reports.get_heading() == "Audit Trail"
        assert self.reports.has_audit_entries(), (
            "The seeded data includes recorded actions, so the trail should not be empty"
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_audit_trail_offers_no_way_to_edit_or_delete_an_entry(self):
        """
        Nobody may edit or delete an audit entry - not even the most senior role that can read
        it. The database refuses it outright (`ticket_audit` has REVOKE UPDATE, DELETE for the
        runtime role, and no update/delete path exists in app/audit/), so what this test checks
        is the visible half: that the screen never offers the controls in the first place.

        WHY THE HEAD OF DEPARTMENT AND NOT THE ADMINISTRATOR. This used to sign in as the admin
        account and then skip itself, every single run, on "this account cannot read the audit
        trail" - which is correct product behaviour, not an environment quirk: the page gates on
        VIEW_AUDIT_CONFIG_CHANGES (app/audit-trail/page.tsx), granted to head_of_department and
        manager only (app/teams/seed_data.py). The platform admin manages users, not tickets, so
        it can never see this screen and the test could never reach its assertions. The Head of
        Department is the documented reader, and is who the rest of this class signs in as.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/audit-trail")

        assert not self.is_access_denied(), (
            "A Head of Department holds VIEW_AUDIT_CONFIG_CHANGES, so the audit trail must "
            f"open for them. Page says: {self.page_text_snippet()}"
        )
        assert not self.reports.has_button("Delete"), "An audit entry may never be deleted"
        assert not self.reports.has_button("Edit"), "An audit entry may never be edited"

    @pytest.mark.regression
    def test_a_tickets_own_history_is_on_its_audit_tab(self):
        """
        R29: every ticket keeps its OWN history, on its own route.

        WHAT THIS USED TO PROVE, AND WHY THAT WAS NOT ENOUGH. The old version waited until the
        page was not the "not found" screen and asserted exactly that - which is also true of a
        blank tab, a spinner that never resolved, and an error card. "It is not a 404" says
        nothing about a history being kept.

        The tab renders AuditTrailCard, the same component the organisation-wide trail uses, so
        there are exactly two honest outcomes: named entries, or its own "No audit events
        recorded for this ticket yet" sentence. A card that renders neither is the failure this
        now catches.
        """
        self.login_once(self.get("hodEmail"))

        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.open_first_row()
        self.detail.wait_until_loaded()
        self.detail.open_audit_tab_and_wait()

        assert "/audit" in self.current_url(), (
            "The Audit tab is the ticket's OWN route (/tickets/{id}/audit), so a ticket's "
            f"history is never the organisation-wide trail. Landed on: {self.current_url()}"
        )

        entries = self.detail.get_audit_event_labels()
        if not entries:
            assert self.detail.page_mentions("No audit events"), (
                "With nothing recorded yet the tab must say so in words - a blank card is "
                f"indistinguishable from one that failed to load. On screen: {self.page_text_snippet()}"
            )
            return

        for entry in entries:
            assert entry.strip(), (
                f"Every recorded action must name what happened. Entries read: {entries}"
            )

    # ==================================================================
    # Customer history
    # ==================================================================



