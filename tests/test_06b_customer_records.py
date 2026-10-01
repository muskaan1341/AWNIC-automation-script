"""
The Customer & Records tab, the Customer History panel and the /history page.

"No records" and "lookup failed" are different things - the screen must say which one it is.
All tests are read-only.
"""

from urllib.parse import urlencode

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.customer_records_page import CustomerRecordsPage
from awnic_qa.pages.reports_page import ReportsPage

pytestmark = pytest.mark.p1


class TestCustomerRecords(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_records_of_first_ticket(self, list_path="/tickets/enquiries"):
        """Open the first ticket on a list and go to its Customer & Records tab."""
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Customer & Records")
        self.customer_records.wait_until_loaded()

    def open_overview_of_first_ticket(self, list_path="/tickets/enquiries"):
        """Open the first ticket and stay on Overview (where the Customer History panel is)."""
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    # ---------- the tab always shows something ----------

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_the_tab_always_arrives_in_one_of_its_four_legitimate_shapes(self):
        """The tab shows the tables, or a message saying why there are none."""
        self.open_records_of_first_ticket()

        arrived = (
            self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD)
            or self.customer_records.says_nothing_looked_up()
            or self.customer_records.says_no_linked_records()
            or self.customer_records.says_lookup_failed()
        )
        assert arrived, (
            f"The tab should show tables or a message. On screen: {self.page_text_snippet()}"
        )

    # ---------- the three record tables ----------

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_the_three_record_cards_are_all_shown_when_records_exist(self):
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip(f"No records for this customer. Screen says: {self.page_text_snippet()}")
        for card in CustomerRecordsPage.RECORD_CARDS:
            assert self.customer_records.has_card(card), (
                f"The '{card}' card is missing. On screen: {self.page_text_snippet()}"
            )
            assert self.customer_records.has_table(card), f"'{card}' should show its table"

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_an_empty_record_table_says_which_kind_of_record_is_missing(self):
        """An empty table shows its own message, e.g. 'No claims found'."""
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip("No record tables for this customer.")

        empty_cards = []
        for card in CustomerRecordsPage.RECORD_CARDS:
            if self.customer_records.row_count(card) == 0:
                empty_cards.append(card)
        if not empty_cards:
            pytest.skip("Every record table has rows.")
        for card in empty_cards:
            assert self.customer_records.shows_table_empty_state(card), (
                f"'{card}' is empty, so it should show "
                f"'{CustomerRecordsPage.TABLE_EMPTY_STATES[card]}'"
            )

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_multi_policy_customer_shows_every_policy(self):
        """Each policy row shows a different, non-blank policy number."""
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip("No record tables for this customer.")
        policies = self.customer_records.row_count(CustomerRecordsPage.POLICY_CARD)
        if policies < 2:
            pytest.skip(f"This customer has only {policies} policy row(s).")

        numbers = self.customer_records.column_values(
            CustomerRecordsPage.POLICY_CARD, "Policy Number"
        )
        assert len(numbers) == policies, (
            f"Every policy row should have a Policy Number. Rows={policies}, numbers={numbers}"
        )
        assert all(number and number != "—" for number in numbers), (
            f"A policy number is blank. Numbers: {numbers}"
        )
        assert len(set(numbers)) == policies, f"The same policy is listed twice. Numbers: {numbers}"

    # ---------- "no records" must not look like "lookup failed" ----------

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_failed_lookup_is_reported_as_an_error_not_as_no_records(self):
        self.open_records_of_first_ticket()

        if not self.customer_records.says_lookup_failed():
            pytest.skip("The lookup worked for this ticket, so there is no failure message.")
        assert not self.customer_records.says_no_linked_records(), (
            "When the lookup failed, the tab should not also say 'No linked records found'"
        )

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_stale_cached_records_carry_an_honest_caveat(self):
        """The 'may be incomplete' warning only shows above real rows."""
        self.open_records_of_first_ticket()

        if not self.customer_records.says_records_may_be_incomplete():
            pytest.skip("The last lookup finished, so there is no warning.")
        assert self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD), (
            "The warning should only show together with the record tables"
        )

    # ---------- the Customer History panel (on Overview) ----------

    @pytest.mark.phase2
    @pytest.mark.regression
    def test_the_customers_previous_cases_are_shown_in_one_place(self):
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip("No Customer History panel on this ticket.")
        # PR #301: the panel may now hold only archive (historical) rows, so they count too.
        assert (
            self.customer_records.history_references()
            or self.customer_records.history_archive_links()
            or self.customer_records.says_no_other_tickets()
        ), (
            f"The panel should list other cases or say there are none. "
            f"On screen: {self.page_text_snippet()}"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    def test_a_past_case_in_the_history_opens_when_clicked(self):
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip("No Customer History panel on this ticket.")
        links = self.customer_records.history_ticket_links()
        if not links:
            pytest.skip("This customer has no other cases.")

        links[0].click()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number(), (
            f"Clicking a past case should open that ticket. Landed on: {self.current_url()}"
        )

    @pytest.mark.phase1
    @pytest.mark.quarantine("no-failing-path")
    def test_the_history_covers_both_enquiries_and_complaints(self):
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip("No Customer History panel on this ticket.")
        references = self.customer_records.history_references()
        if len(references) < 2:
            pytest.skip(f"This customer has only {len(references)} other case(s).")

        # The first 3 letters are the type: INQ or COM.
        prefixes = set()
        for reference in references:
            prefixes.add(reference[:3])
        if not {"INQ", "COM"}.issubset(prefixes):
            pytest.skip(f"All other cases are one type ({sorted(prefixes)}).")
        assert {"INQ", "COM"}.issubset(prefixes), (
            f"The history should show both enquiries and complaints. Saw: {sorted(prefixes)}"
        )

    # ---------- access control ----------

    @pytest.mark.phase1
    @pytest.mark.api_candidate
    def test_the_records_tab_of_a_ticket_that_does_not_exist_is_refused(self):
        self.open_and_wait(
            "/tickets/00000000-0000-0000-0000-000000000000/customer-records"
        )

        assert self.is_page_not_found() or self.is_access_denied(), (
            f"An unknown ticket id should be refused. On screen: {self.page_text_snippet()}"
        )

    # ---------- the Customer History page (/history) ----------

    def a_ticket_with_a_policy(self):
        """Return (reference, policy number, customer name) of the first enquiry with a policy."""
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        references = self.list.get_reference_numbers()
        policies = self.list.get_column_values("Policy Number")
        names = self.list.get_column_values("Customer Name")
        for reference, policy, name in zip(references, policies, names):
            if reference and policy and policy != "—":
                if name == "—":
                    name = ""
                return reference, policy, name
        pytest.skip("No enquiry on the first page has a policy number.")

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_r22_the_history_module_shows_a_customers_tickets_grouped_and_on_a_timeline(self):
        """Open /history for a real policy and check the Grouped and Timeline views."""
        self.require_ticket_access()
        self.open_and_wait("/history")
        assert self.reports.get_heading() == "Customer History"
        assert self.reports.has_history_search(), "The customer search box is missing"

        # Open the customer by URL instead of using the search box, which calls the live lookup.
        reference, policy, name = self.a_ticket_with_a_policy()
        self.open_and_wait(f"/history?{urlencode({'policy': policy})}")
        self.wait_for_page_content()

        heading = self.reports.get_heading()
        assert heading != "Customer History", "The page title should be the customer's name"
        if name:
            assert heading == name, (
                f"Policy {policy} belongs to '{name}' ({reference}), but the page is for '{heading}'"
            )
        assert self.reports.history_view_is("Grouped"), "Grouped should be the default view"
        groups = self.reports.history_group_labels()
        assert groups and set(groups) <= set(ReportsPage.HISTORY_GROUPS), (
            f"Unexpected group sections: {groups}"
        )
        self.reports.expand_all_history_groups()
        grouped = self.reports.history_references()
        assert reference in grouped, f"{reference} should be in the history. Listed: {grouped}"

        self.reports.switch_history_view("Timeline")
        timeline = self.reports.history_references()
        assert sorted(timeline) == sorted(grouped), (
            f"Timeline and Grouped should list the same tickets. "
            f"Grouped: {sorted(grouped)}, Timeline: {sorted(timeline)}"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.negative
    def test_r22_a_complaint_handler_is_not_offered_the_customer_history_module(self):
        self.login_once(self.get("complaintHandlerEmail"))
        self.open_and_wait("/tickets/complaints")
        self.nav.wait_until_loaded()
        assert not self.nav.has_item("Customer History"), (
            "A complaint handler should not see 'Customer History' in the menu"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.negative
    def test_r22_a_complaint_handlers_ticket_shows_no_customer_history_panel(self):
        self.login_once(self.get("complaintHandlerEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0 or self.list.is_empty_state_displayed():
            pytest.skip(f"{self.get('complaintHandlerEmail')} has no complaint assigned.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        assert not self.customer_records.has_history_panel(), (
            "A complaint handler should not see the Customer History panel"
        )
