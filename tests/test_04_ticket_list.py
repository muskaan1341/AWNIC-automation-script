"""
The Enquiries and Complaints ticket lists.

Both lists are the same screen with different data. Signed in as a CC Initiator.
Filters are tested in test_05_ticket_filter.py.
"""

import re

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


class TestTicketList(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("ccInitiatorEmail"))

    def open_enquiries(self):
        # Sign in again as the CC Initiator, because one test in this class switches to a HOD.
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

    def wait_for_scoped_tab_to_load(self):
        """Wait until the tab has loaded rows or shows the empty message."""
        # The scope tabs do not change the URL, so wait on the table itself.
        self.wait.until(
            lambda d: self.list.is_empty_state_displayed()
            or bool(self.list.get_reference_numbers())
        )

    def open_complaints(self):
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

    # ---------- the two lists open ----------

    @pytest.mark.regression
    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_enquiries_list_shows_rows_from_the_database(self):
        self.open_enquiries()

        assert self.list.get_row_count() > 0, "Expected some enquiry rows"
        assert not self.list.is_empty_state_displayed(), "Empty message should not show when there are rows"

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_every_enquiry_row_carries_an_inq_reference_number(self):
        self.open_enquiries()

        references = self.list.get_reference_numbers()
        assert references, "No reference numbers were read from the table"
        for reference in references:
            assert reference.startswith("INQ-"), f"Enquiry number should start with INQ-: {reference}"

    @pytest.mark.regression
    def test_every_complaint_row_carries_a_com_reference_number(self):
        self.open_complaints()

        references = self.list.get_reference_numbers()
        assert references, "No reference numbers were read from the table"
        for reference in references:
            assert reference.startswith("COM-"), f"Complaint number should start with COM-: {reference}"

    # ---------- columns and layout ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_table_shows_the_expected_columns(self):
        self.open_enquiries()

        headers = self.list.get_column_headers()
        expected_columns = [
            "Source",
            "Reference number",
            "Department",
            "Priority",
            "SLA",
            "Customer Name",
            "Status",
            "Current Handler",
        ]
        for expected in expected_columns:
            assert expected in headers, f"Column '{expected}' is missing. Columns: {headers}"

    @pytest.mark.regression
    def test_the_wide_table_scrolls_inside_itself_not_the_whole_page(self):
        """The wide table scrolls sideways by itself; the page does not."""
        self.open_enquiries()

        assert self.list.table_scrolls_horizontally_without_moving_the_page(), (
            "The table should scroll sideways, not the whole page"
        )

    # ---------- search ----------

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_search_narrows_the_list_to_the_matching_ticket(self):
        self.open_enquiries()

        before = self.list.get_reference_numbers()
        assert len(before) > 1, "This test needs more than one enquiry"

        target = before[0]
        self.list.search(target)
        self.list.wait_for_row_count(1)

        assert self.list.get_reference_numbers() == [target], "Search should leave only that ticket"

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_search_for_something_that_does_not_exist_shows_the_empty_state(self):
        self.open_enquiries()

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        assert self.list.is_empty_state_displayed(), "A search with no matches should show the empty message"

    @pytest.mark.api_candidate
    def test_search_survives_unusual_characters(self):
        """Odd characters in the search box must not break the page."""
        self.open_enquiries()

        self.list.search("<script>'\"%&")
        self.list.wait_for_empty_state()

        assert self.list.is_empty_state_displayed(), "An odd search should just return nothing"
        assert not self.is_page_not_found(), "The page should still be the ticket list"

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_clearing_the_search_brings_all_the_rows_back(self):
        self.open_enquiries()
        original_rows = self.list.get_row_count()

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        self.list.clear_search()
        self.list.wait_for_row_count(original_rows)
        assert self.list.get_row_count() == original_rows, "Clearing the search should bring all rows back"

    # ---------- the result count ----------

    @pytest.mark.regression
    def test_the_result_count_is_the_total_and_the_page_never_shows_more_than_that(self):
        """The footer shows the total count; a page shows at most 10 rows."""
        self.open_enquiries()

        rows_on_this_page = self.list.get_row_count()
        total_matching = self.list.get_reported_result_count()

        assert rows_on_this_page <= total_matching, (
            f"Page shows {rows_on_this_page} rows but the total is {total_matching}"
        )
        assert rows_on_this_page <= 10, "A page should never have more than 10 rows"

    @pytest.mark.quarantine("FUNC_011/FUNC_045")
    def test_searching_for_one_ticket_makes_the_count_say_one(self):
        self.open_enquiries()
        target = self.list.get_reference_numbers()[0]

        self.list.search(target)
        self.list.wait_for_row_count(1)

        assert self.list.get_reported_result_count() == 1, (
            f"Count should be 1. Footer said: {self.list.get_result_count_text()}"
        )

    # ---------- paging ----------

    @pytest.mark.api_candidate
    def test_moving_to_the_next_page_shows_different_tickets(self):
        self.open_enquiries()

        if self.list.get_reported_result_count() <= self.list.get_row_count():
            pytest.skip("Everything fits on one page.")

        first_page = self.list.get_reference_numbers()
        assert self.list.is_previous_page_disabled(), "Previous should be disabled on page 1"

        self.list.go_to_next_page()
        self.list.wait_for_rows_to_change(first_page)

        assert self.list.get_current_page_number() == 2, "Should now be on page 2"
        assert self.list.get_reference_numbers() != first_page, "Page 2 should show different tickets"

    @pytest.mark.api_candidate
    def test_going_back_a_page_returns_the_same_tickets(self):
        self.open_enquiries()

        if self.list.get_reported_result_count() <= self.list.get_row_count():
            pytest.skip("Everything fits on one page.")

        first_page = self.list.get_reference_numbers()
        self.list.go_to_next_page()
        self.list.wait_for_rows_to_change(first_page)

        self.list.go_to_previous_page()
        self.wait.until(lambda d: self.list.get_reference_numbers() == first_page)

        assert self.list.get_reference_numbers() == first_page, "Page 1 should show the same tickets again"

    # ---------- sorting ----------

    @pytest.mark.regression
    def test_sorting_by_a_column_puts_it_in_the_url(self):
        self.open_enquiries()
        self.list.sort_by("Reference number")

        self.wait_for_url_containing("sort=reference_number")
        assert "sort=reference_number" in self.current_url(), f"Actual URL: {self.current_url()}"

    @pytest.mark.regression
    def test_sorting_twice_reverses_the_order(self):
        # Note: the first click adds only "sort=reference_number" to the URL (no "order=").
        self.open_enquiries()

        # A ticket with no reference yet shows "—" in the list. Treat it as "" so it
        # sorts the same way the server sorts it.
        def as_sorted_values(references):
            values = []
            for reference in references:
                if reference == "—":
                    values.append("")
                else:
                    values.append(reference)
            return values

        self.list.sort_by("Reference number")
        self.wait_for_url_containing("sort=reference_number")
        first_direction = as_sorted_values(self.list.get_reference_numbers())
        assert len(first_direction) > 1, "This test needs more than one enquiry on the page"

        # The first click must put the page in order (either direction).
        assert first_direction in (sorted(first_direction), sorted(first_direction, reverse=True)), (
            f"The page should be sorted by reference number. Got: {first_direction}"
        )
        ascending_first = first_direction == sorted(first_direction)

        self.list.sort_by("Reference number")
        self.wait.until(
            lambda d: as_sorted_values(self.list.get_reference_numbers()) != first_direction
        )

        # The second click must flip the direction.
        second_direction = as_sorted_values(self.list.get_reference_numbers())
        assert second_direction == sorted(second_direction, reverse=ascending_first), (
            f"The second click should reverse the order. First: {first_direction}. "
            f"Second: {second_direction}"
        )

    # ---------- the two views ----------

    @pytest.mark.regression
    def test_list_view_is_selected_by_default_and_kanban_can_be_switched_on(self):
        self.open_enquiries()

        assert self.list.is_list_view_selected(), "List view should be selected on open"
        assert not self.list.is_kanban_view_selected()
        assert self.list.is_kanban_button_enabled(), "The Kanban button should be enabled"

        self.list.switch_to_kanban()
        self.wait.until(lambda d: self.list.is_kanban_view_selected())
        assert self.list.is_kanban_view_selected(), "Clicking Kanban should select that view"

    # ---------- the scope tabs ----------

    @pytest.mark.regression
    def test_the_department_tab_appears_only_for_somebody_who_has_a_department(self):
        self.login_once(self.get("hodEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        # A user with no department gets no "My Department" tab.
        if "My Department" not in self.list.get_tab_labels():
            pytest.skip(
                f"This account has no department here, so no 'My Department' tab. "
                f"Tabs: {self.list.get_tab_labels()}"
            )

        mine = users.by_email(self.get("hodEmail")).department
        assert mine, f"{self.get('hodEmail')} has no department in awnic_qa/users.py"

        organisation_wide_total = self.list.get_reported_result_count()
        self.list.select_tab("My Department")
        self.wait_for_scoped_tab_to_load()

        if self.list.is_empty_state_displayed():
            pytest.skip(f"No {mine} tickets exist here, so there are no rows to check.")

        # Every row left must belong to my department.
        departments = self.list.get_column_values("Department")
        assert departments, "No Department values could be read from the table"
        foreign = []
        for d in departments:
            if d and d != mine and d not in foreign:
                foreign.append(d)
        foreign.sort()
        assert not foreign, f"'My Department' should show only {mine!r} tickets. Also shown: {foreign}"
        assert self.list.get_reported_result_count() <= organisation_wide_total, (
            f"Department count is more than the total: "
            f"{self.list.get_reported_result_count()} vs {organisation_wide_total}"
        )

    @pytest.mark.regression
    def test_the_retired_teams_tickets_tab_is_gone(self):
        """The old 'Teams Tickets' tab was removed and should not come back."""
        self.open_enquiries()

        assert not self.list.has_legacy_teams_tickets_tab(), "'Teams Tickets' tab should not be shown"

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_switching_to_my_tickets_shows_only_tickets_assigned_to_me(self):
        """'My Tickets' shows only tickets whose Current Handler is me."""
        self.open_enquiries()
        me = users.by_email(self.get("ccInitiatorEmail"))
        organisation_wide_total = self.list.get_reported_result_count()

        self.list.select_tab("My Tickets")
        self.wait_for_scoped_tab_to_load()

        if self.list.is_empty_state_displayed():
            pytest.skip(f"No enquiry is assigned to {me.email} here, so the tab is empty.")

        handlers = self.list.get_column_values("Current Handler")
        assert handlers, "No Current Handler values could be read from the table"

        # The cell shows the handler's name, or their email if no name is set.
        not_mine = []
        for h in handlers:
            if me.name not in h and me.email not in h:
                not_mine.append(h)
        assert not not_mine, (
            f"'My Tickets' should only show tickets of {me.name} ({me.email}). "
            f"Also shown: {sorted(set(not_mine))}"
        )
        assert self.list.get_reported_result_count() <= organisation_wide_total, (
            f"My ticket count is more than the total: "
            f"{self.list.get_reported_result_count()} vs {organisation_wide_total}"
        )

    # ---------- opening a ticket ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_clicking_a_row_opens_that_tickets_detail_page(self):
        self.open_enquiries()
        self.list.open_first_row()

        self.wait_for_ticket_detail_url()
        assert re.match(r".*/tickets/[^/]+$", self.current_url()), (
            f"Should open /tickets/<id>. Actual: {self.current_url()}"
        )

    @pytest.mark.regression
    def test_a_cc_initiator_sees_the_create_enquiry_button(self):
        self.open_enquiries()

        assert self.list.has_button("Create Enquiry"), "The CC Initiator should see 'Create Enquiry'"

    @pytest.mark.regression
    def test_opening_a_ticket_that_does_not_exist_shows_the_not_found_screen(self):
        self.open("/tickets/00000000-0000-0000-0000-000000000000")

        self.wait.until(lambda d: self.is_page_not_found())
        assert self.is_page_not_found(), "A made-up ticket id should show the 'not found' page"
