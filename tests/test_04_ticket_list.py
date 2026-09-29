"""
MODULE 05 (part 1) - The Enquiries and Complaints lists.

Both are the same screen with different data, so one page object covers both.
Signed in as a Customer Care agent, who can see every ticket in the organisation.

Filters get their own class (test_05_ticket_filter.py) because there are enough of them to
be worth keeping separate.
"""

from __future__ import annotations

import re

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Ticket list search/filter — by type, department, status, etc.'
pytestmark = [pytest.mark.p1, pytest.mark.phase1]



class TestTicketList(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiries(self) -> None:
        """
        Shared first step, so no test repeats these lines.
        It names the role too - one test in this class signs in as a Head of Department,
        and nothing promises to run it last.
        """
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

    def wait_for_scoped_tab_to_load(self) -> None:
        """
        Waits for a scope tab's own fetch to land before anything is read off the table.

        "My Tickets" and "My Department" do not touch the URL - they re-fetch in the background
        and swap the table under you (TicketTypeListClient's `scoped` state). Reading the rows
        too early reads the ORGANISATION's rows and judges them as the tab's, which is a false
        failure on a scoping test. Rows or the empty state is the honest "it has settled"
        signal available without a loading marker in the DOM.
        """
        self.wait.until(
            lambda d: self.list.is_empty_state_displayed()
            or bool(self.list.get_reference_numbers())
        )

    def open_complaints(self) -> None:
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

    # ---------- the two lists open ----------

    @pytest.mark.regression
    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_enquiries_list_shows_rows_from_the_database(self):
        self.open_enquiries()

        assert self.list.get_row_count() > 0, (
            "The seeded database has enquiries, so rows are expected"
        )
        assert not self.list.is_empty_state_displayed(), (
            "The empty-state message should not be shown when there are rows"
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_every_enquiry_row_carries_an_inq_reference_number(self):
        """
        The two lists must never bleed into each other. An enquiry number starts INQ-, a
        complaint number starts COM-, and the prefix is how a customer refers to their case,
        so getting this wrong is not cosmetic.
        """
        self.open_enquiries()

        references = self.list.get_reference_numbers()
        assert references, "No reference numbers were read from the table"
        for reference in references:
            assert reference.startswith("INQ-"), (
                f"An enquiry number should start with INQ-, but was: {reference}"
            )

    @pytest.mark.regression
    def test_every_complaint_row_carries_a_com_reference_number(self):
        self.open_complaints()

        references = self.list.get_reference_numbers()
        assert references, "No reference numbers were read from the table"
        for reference in references:
            assert reference.startswith("COM-"), (
                f"A complaint number should start with COM-, but was: {reference}"
            )

    # ---------- columns and layout ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_table_shows_the_expected_columns(self):
        self.open_enquiries()

        headers = self.list.get_column_headers()
        for expected in [
            "Source",
            "Reference number",
            "Department",
            "Priority",
            "SLA",
            "Customer Name",
            "Status",
            "Current Handler",
        ]:
            assert expected in headers, (
                f"Column '{expected}' is missing. Columns found: {headers}"
            )

    @pytest.mark.regression
    def test_the_wide_table_scrolls_inside_itself_not_the_whole_page(self):
        """
        The table is 18 columns wide, far wider than any screen. That width has to be trapped
        inside the table's OWN scrollbar - if the whole page scrolls sideways instead, the
        menu and the header slide off and the screen becomes unusable.
        """
        self.open_enquiries()

        assert self.list.table_scrolls_horizontally_without_moving_the_page(), (
            "The table should scroll sideways on its own; the page body must not"
        )

    # ---------- search ----------

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_search_narrows_the_list_to_the_matching_ticket(self):
        self.open_enquiries()

        before = self.list.get_reference_numbers()
        assert len(before) > 1, "This test needs more than one enquiry to be meaningful"

        target = before[0]
        self.list.search(target)
        self.list.wait_for_row_count(1)

        assert self.list.get_reference_numbers() == [target], (
            "Searching for a reference number should leave only that ticket"
        )

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_search_for_something_that_does_not_exist_shows_the_empty_state(self):
        self.open_enquiries()

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        assert self.list.is_empty_state_displayed(), (
            "A search with no matches should show a message, not a stale list"
        )

    @pytest.mark.api_candidate
    def test_search_survives_unusual_characters(self):
        """
        Odd characters must not break the screen. A search box that crashes on a quote or an
        angle bracket is both a usability problem and a security smell.
        """
        self.open_enquiries()

        self.list.search("<script>'\"%&")
        self.list.wait_for_empty_state()

        assert self.list.is_empty_state_displayed(), (
            "An odd search should return nothing politely, not error"
        )
        assert not self.is_page_not_found(), "The page should still be the ticket list"

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_clearing_the_search_brings_all_the_rows_back(self):
        self.open_enquiries()
        original_rows = self.list.get_row_count()

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        self.list.clear_search()
        self.list.wait_for_row_count(original_rows)
        assert self.list.get_row_count() == original_rows, (
            "Clearing the search should restore the full list"
        )

    # ---------- the result count ----------

    @pytest.mark.regression
    def test_the_result_count_is_the_total_and_the_page_never_shows_more_than_that(self):
        """
        The footer count is the TOTAL number of matching tickets, not the number of rows on
        the page - the list is paginated at ten. So the right check is "the page never shows
        more rows than the total", not "they are equal".
        """
        self.open_enquiries()

        rows_on_this_page = self.list.get_row_count()
        total_matching = self.list.get_reported_result_count()

        assert rows_on_this_page <= total_matching, (
            f"The page shows {rows_on_this_page} rows but the footer only claims "
            f"{total_matching} results in total"
        )
        assert rows_on_this_page <= 10, (
            "The list pages at ten, so a page should never hold more than ten rows"
        )

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_searching_for_one_ticket_makes_the_count_say_one(self):
        """With a search that matches one ticket, the total and the rows DO line up."""
        self.open_enquiries()
        target = self.list.get_reference_numbers()[0]

        self.list.search(target)
        self.list.wait_for_row_count(1)

        assert self.list.get_reported_result_count() == 1, (
            "One matching ticket should be reported as '1 result'. Footer said: "
            f"{self.list.get_result_count_text()}"
        )

    # ---------- paging ----------

    @pytest.mark.api_candidate
    def test_moving_to_the_next_page_shows_different_tickets(self):
        self.open_enquiries()

        if self.list.get_reported_result_count() <= self.list.get_row_count():
            pytest.skip("Everything fits on one page, so there is no paging.")

        first_page = self.list.get_reference_numbers()
        assert self.list.is_previous_page_disabled(), (
            "There is no page before the first one, so Previous should be disabled"
        )

        self.list.go_to_next_page()
        self.list.wait_for_rows_to_change(first_page)

        assert self.list.get_current_page_number() == 2, "Should now be on page 2"
        assert self.list.get_reference_numbers() != first_page, (
            "Page 2 should show different tickets from page 1"
        )

    @pytest.mark.api_candidate
    def test_going_back_a_page_returns_the_same_tickets(self):
        self.open_enquiries()

        if self.list.get_reported_result_count() <= self.list.get_row_count():
            pytest.skip("Everything fits on one page, so there is no paging.")

        first_page = self.list.get_reference_numbers()
        self.list.go_to_next_page()
        self.list.wait_for_rows_to_change(first_page)

        self.list.go_to_previous_page()
        self.wait.until(lambda d: self.list.get_reference_numbers() == first_page)

        assert self.list.get_reference_numbers() == first_page, (
            "Coming back to page 1 should show exactly what was there before"
        )

    # ---------- sorting ----------

    @pytest.mark.regression
    def test_sorting_by_a_column_puts_it_in_the_url(self):
        self.open_enquiries()
        self.list.sort_by("Reference number")

        self.wait_for_url_containing("sort=reference_number")
        assert "sort=reference_number" in self.current_url(), (
            f"Actual URL: {self.current_url()}"
        )

    @pytest.mark.regression
    def test_sorting_twice_reverses_the_order(self):
        """
        Sorting twice reverses the order.

        WATCH OUT: the sort direction is left OUT of the URL when it is the default one. The
        first click gives "?sort=reference_number" with no "order" at all, so never wait for
        "order=desc" to appear on the first click.
        """
        self.open_enquiries()

        # A ticket still being classified HAS NO REFERENCE NUMBER YET - MagOneAI fetches or
        # generates it when the pipeline finishes - and the list renders that empty value as an
        # em dash (TruncatedText: an empty value shows "—"). The server sorts on the STORED
        # value, so an empty one comes FIRST ascending; comparing the em dash instead sorts it
        # last, which read a correctly ordered page as unordered and produced this test's only
        # failure on 2026-09-29. So the display is turned back into the value it stands for,
        # the same way for every read below.
        #
        # The blanks stay IN the comparison rather than being filtered out: where an empty
        # reference sits is part of the ordering being asserted, and dropping those rows would
        # stop the test noticing if they ever moved.
        def as_sorted_values(references: list[str]) -> list[str]:
            return ["" if reference == "\u2014" else reference for reference in references]

        self.list.sort_by("Reference number")
        self.wait_for_url_containing("sort=reference_number")
        first_direction = as_sorted_values(self.list.get_reference_numbers())
        assert len(first_direction) > 1, (
            "This test needs more than one enquiry on the page to have an order at all"
        )

        # WHAT "SORTED" MEANS HERE. Every reference on this list is INQ-<year>-<4 digits>, so
        # the numbers are zero-padded and plain text ordering is the same as numeric ordering.
        # Asserting the page is ACTUALLY in order is the point: the old version only checked
        # that the second click produced a different page from the first, which is equally true
        # of a sort that scrambled the rows, sorted on the wrong column, or merely paged.
        assert first_direction in (sorted(first_direction), sorted(first_direction, reverse=True)), (
            f"Sorting by reference number must put the page in order. Got: {first_direction}"
        )
        ascending_first = first_direction == sorted(first_direction)

        self.list.sort_by("Reference number")
        self.wait.until(
            lambda d: as_sorted_values(self.list.get_reference_numbers()) != first_direction
        )

        second_direction = as_sorted_values(self.list.get_reference_numbers())
        assert second_direction == sorted(second_direction, reverse=ascending_first), (
            "The second click must flip the direction - "
            f"{'ascending then descending' if ascending_first else 'descending then ascending'}. "
            f"First: {first_direction}. Second: {second_direction}"
        )

    # ---------- the two views ----------

    @pytest.mark.regression
    def test_list_view_is_selected_by_default_and_kanban_can_be_switched_on(self):
        self.open_enquiries()

        assert self.list.is_list_view_selected(), "List view should be selected on open"
        assert not self.list.is_kanban_view_selected()
        assert self.list.is_kanban_button_enabled(), (
            "The Kanban board is built now, so its button must not be disabled"
        )

        self.list.switch_to_kanban()
        self.wait.until(lambda d: self.list.is_kanban_view_selected())
        assert self.list.is_kanban_view_selected(), (
            "Clicking Kanban should select that view"
        )

    # ---------- the scope tabs ----------

    @pytest.mark.regression
    def test_the_department_tab_appears_only_for_somebody_who_has_a_department(self):
        self.login_once(self.get("hodEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        # The rule is organisation-wide sight AND a department recorded on the account (see
        # canViewDeptTab in lib/permissions.ts). A senior user with no department gets two
        # tabs, not three - which is right: a "My Department" tab would be an empty promise.
        if "My Department" not in self.list.get_tab_labels():
            pytest.skip(
                "This account has no department recorded on this environment, so the "
                f"'My Department' tab is correctly not offered. Tabs: {self.list.get_tab_labels()}"
            )

        # The ACCOUNT'S OWN department, as recorded for it in awnic_qa/users.py - the tab
        # substitutes exactly that value for any department filter (TicketTypeListClient:
        # `department: tab === "dept" ? [currentUserDepartment] : ...`).
        mine = users.by_email(self.get("hodEmail")).department
        assert mine, (
            f"{self.get('hodEmail')} has no department recorded in awnic_qa/users.py, so what "
            "'My Department' should show cannot be stated"
        )

        organisation_wide_total = self.list.get_reported_result_count()
        self.list.select_tab("My Department")
        self.wait_for_scoped_tab_to_load()

        if self.list.is_empty_state_displayed():
            pytest.skip(
                f"No {mine} tickets exist on this environment, so the tab correctly shows its "
                "empty state and there are no rows to check."
            )

        # The real check is not that the list got shorter - it is that every row left behind
        # belongs to THIS person's department. A count comparison proved nothing anyway: both
        # tabs page at ten, so "fewer rows" was true before the tab had even switched.
        departments = self.list.get_column_values("Department")
        assert departments, (
            "The tab shows rows but no Department values could be read - the column has moved "
            "or renamed, so this test proved nothing"
        )
        foreign = sorted({d for d in departments if d and d != mine})
        assert not foreign, (
            f"'My Department' must show only {mine!r} tickets. Also on screen: {foreign}"
        )
        assert self.list.get_reported_result_count() <= organisation_wide_total, (
            "One department can never hold more tickets than the whole organisation - "
            f"{self.list.get_reported_result_count()} vs {organisation_wide_total}"
        )

    @pytest.mark.regression
    def test_the_retired_teams_tickets_tab_is_gone(self):
        """
        The old "Teams Tickets" tab was REMOVED - team-level scoping was never built.
        This test exists purely so that if it ever comes back, somebody notices.
        """
        self.open_enquiries()

        assert not self.list.has_legacy_teams_tickets_tab(), (
            "'Teams Tickets' was removed. If it is back, team scoping has been re-added and "
            "this suite needs updating too."
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_switching_to_my_tickets_shows_only_tickets_assigned_to_me(self):
        """
        "My Tickets" is an OWNERSHIP filter, not merely a shorter list.

        It re-fetches with `assignedPocEmail = <the signed-in user>` (TicketTypeListClient), so
        every row it shows is one this person holds - which the Current Handler column names
        (handlerName(): the assigned POC's name, or their email when no name is recorded).

        The old version only asserted the row count had not grown. Both tabs page at ten, so
        that was true before the tab had even finished swapping, and it stayed true if the tab
        showed somebody else's tickets entirely.
        """
        self.open_enquiries()
        me = users.by_email(self.get("agentEmail"))
        organisation_wide_total = self.list.get_reported_result_count()

        self.list.select_tab("My Tickets")
        # The tabs do NOT write to the URL, so wait on the rows rather than the address bar.
        self.wait_for_scoped_tab_to_load()

        if self.list.is_empty_state_displayed():
            pytest.skip(
                f"No enquiry is assigned to {me.email} as its point of contact on this "
                "environment, so the tab correctly shows its empty state. Assign one to "
                "exercise the ownership filter."
            )

        handlers = self.list.get_column_values("Current Handler")
        assert handlers, (
            "The tab shows rows but no Current Handler values could be read - the column has "
            "moved or renamed, so this test proved nothing"
        )
        # The cell shows the handler's NAME when the ticket records one and their EMAIL when it
        # does not, so either one identifies the same person.
        not_mine = [h for h in handlers if me.name not in h and me.email not in h]
        assert not not_mine, (
            f"'My Tickets' must only show tickets held by {me.name} ({me.email}). Also on "
            f"screen: {sorted(set(not_mine))}"
        )
        assert self.list.get_reported_result_count() <= organisation_wide_total, (
            "One person's tickets can never outnumber the organisation's - "
            f"{self.list.get_reported_result_count()} vs {organisation_wide_total}"
        )

    # ---------- opening a ticket ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_clicking_a_row_opens_that_tickets_detail_page(self):
        self.open_enquiries()
        self.list.open_first_row()

        self.wait_for_ticket_detail_url()
        assert re.match(r".*/tickets/[^/]+$", self.current_url()), (
            f"Clicking a row should open /tickets/<id>. Actual: {self.current_url()}"
        )

    @pytest.mark.regression
    def test_agent_sees_the_create_enquiry_button(self):
        self.open_enquiries()

        assert self.list.has_button("Create Enquiry"), (
            "A Customer Care agent may create tickets, so the button should be there"
        )

    @pytest.mark.regression
    def test_opening_a_ticket_that_does_not_exist_shows_the_not_found_screen(self):
        self.open("/tickets/00000000-0000-0000-0000-000000000000")

        self.wait.until(lambda d: self.is_page_not_found())
        assert self.is_page_not_found(), (
            "A made-up ticket id should give the application's own 'not found' screen"
        )
