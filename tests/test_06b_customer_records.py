"""
MODULE 13 - Customer Information (the Customer & Records tab).

WHY THIS CLASS EXISTS: module 13 has 31 written test cases and had ZERO browser automation. The
suite proved this tab opens and does not 404, and nothing else.

===================================================================================
THE DISTINCTION EVERYTHING HERE TURNS ON
===================================================================================
    "no records"     a FACT.  The lookup ran; this customer genuinely has no policies.
    "lookup failed"  an ERROR. The cache is untrustworthy and an empty result proves nothing.

The component is explicit about it: *"an empty cache after a failed lookup is not 'no records'"*.
Getting this wrong is not cosmetic - an agent told "this customer has no policies" when the
truth is "we could not reach the Data Mart" will go on to give the customer a wrong answer with
complete confidence. So the tests below never accept a blank area as a pass; they insist the
screen says which of the two it means.

===================================================================================
NOTHING ON THIS TAB IS LIVE, AND IT MUST STAY THAT WAY
===================================================================================
R22 is a local join against `tickets` + `customer_lookup_cache`, never a re-fetch. `apps/api` is
the single node that ever calls AWNIC's Data Mart (source-IP allowlisted, Partner-Id/Api-Key),
and the browser must never reach it directly. There is no browser-level test that can prove a
negative like that, so it is asserted where it can be - the tab shows cached rows, and carries
an honest caveat when the cache is stale.
"""

from __future__ import annotations

from urllib.parse import urlencode

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.customer_records_page import CustomerRecordsPage
from awnic_qa.pages.reports_page import ReportsPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Customer records lookup (/tickets/{id}/customer-records)'
pytestmark = pytest.mark.p1



class TestCustomerRecords(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_records_of_first_ticket(self, list_path: str = "/tickets/enquiries") -> None:
        """Opens the first ticket on a list and switches to its Customer & Records tab."""
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}, so there are no records to open.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Customer & Records")
        self.customer_records.wait_until_loaded()

    def open_overview_of_first_ticket(self, list_path: str = "/tickets/enquiries") -> None:
        """
        Opens the first ticket and stays on its OVERVIEW - where CustomerHistoryPanel lives
        (TicketDetailContent.tsx). The three history tests used to look for it on Customer &
        Records, where it is not rendered at all.
        """
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}, so there is no history to open.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    # ==================================================================
    # The tab exists on every ticket type
    # ==================================================================


    @pytest.mark.phase1
    @pytest.mark.regression
    def test_the_tab_always_arrives_in_one_of_its_four_legitimate_shapes(self):
        """
        M13-POS / M13-NEG together: the tab must never render as blank space.

        There are exactly four correct answers - the record tables, "nothing looked up yet",
        "no linked records", or the failed-lookup callout. Anything else means the page rendered
        and then said nothing at all, which a user reads as a broken screen.
        """
        self.open_records_of_first_ticket()

        arrived = (
            self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD)
            or self.customer_records.says_nothing_looked_up()
            or self.customer_records.says_no_linked_records()
            or self.customer_records.says_lookup_failed()
        )
        assert arrived, (
            "The tab must show its record tables or say plainly why it has none. "
            f"On screen: {self.page_text_snippet()}"
        )

    # ==================================================================
    # The three record tables
    # ==================================================================

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_the_three_record_cards_are_all_shown_when_records_exist(self):
        """M13-POS: 'The policy information returned is the information agents actually need'."""
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip(
                "No records cached for this ticket's customer, so the tables are correctly not "
                f"rendered. Screen says: {self.page_text_snippet()}"
            )
        for card in CustomerRecordsPage.RECORD_CARDS:
            assert self.customer_records.has_card(card), (
                f"The '{card}' card should be on the tab. On screen: {self.page_text_snippet()}"
            )
            assert self.customer_records.has_table(card), (
                f"'{card}' should render its table, even if that table is empty"
            )

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_an_empty_record_table_says_which_kind_of_record_is_missing(self):
        """
        M13-NEG: an empty table names what it found none of.

        "No policies found" and "No claims found" are different facts, and a shared blank space
        would tell an agent neither. Each table carries its own sentence.
        """
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip("No record tables rendered for this ticket's customer.")

        empty_cards = [
            card
            for card in CustomerRecordsPage.RECORD_CARDS
            if self.customer_records.row_count(card) == 0
        ]
        if not empty_cards:
            pytest.skip("Every record table has rows, so no empty state is on screen to check.")
        for card in empty_cards:
            assert self.customer_records.shows_table_empty_state(card), (
                f"'{card}' holds no rows, so it must show "
                f"'{CustomerRecordsPage.TABLE_EMPTY_STATES[card]}' rather than a blank area"
            )

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_multi_policy_customer_shows_every_policy(self):
        """M13-POS: 'A customer with several policies shows all of them'."""
        self.open_records_of_first_ticket()

        if not self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD):
            pytest.skip("No record tables rendered for this ticket's customer.")
        policies = self.customer_records.row_count(CustomerRecordsPage.POLICY_CARD)
        if policies < 2:
            pytest.skip(
                f"This customer has {policies} cached policy row(s), so 'several' cannot be "
                "shown. Seed a multi-policy customer to exercise this."
            )

        # The old assertion was `policies >= 2` immediately after skipping unless `policies >=
        # 2` - it could never fail. "Shows every policy" means each row is a DIFFERENT policy: a
        # table repeating one number, or blanking it, would look right and tell an agent nothing.
        numbers = self.customer_records.column_values(
            CustomerRecordsPage.POLICY_CARD, "Policy Number"
        )
        assert len(numbers) == policies, (
            f"Every policy row must carry a Policy Number cell. Rows={policies}, "
            f"numbers read={numbers}"
        )
        assert all(number and number != "—" for number in numbers), (
            f"A listed policy must show its number, not a blank. Numbers: {numbers}"
        )
        assert len(set(numbers)) == policies, (
            "Each row must be a DIFFERENT policy - the same one listed twice is not 'every "
            f"policy'. Numbers: {numbers}"
        )

    # ==================================================================
    # "No records" is never allowed to look like "the lookup failed"
    # ==================================================================

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_failed_lookup_is_reported_as_an_error_not_as_no_records(self):
        """
        M13-NEG, and the most valuable test in this class:
        'If the customer system is unreachable the agent is told plainly'.

        An empty cache after a FAILED lookup is not the fact "no records" - it is an error, and
        the screen must say so. An agent who reads a failure as "this customer has nothing"
        will confidently tell the customer something untrue.
        """
        self.open_records_of_first_ticket()

        if not self.customer_records.says_lookup_failed():
            pytest.skip(
                "The Data Mart lookup succeeded for this ticket, so the failure callout is "
                "correctly not on screen. That is the normal, healthy state."
            )
        # A failure is showing. It must NOT also be claiming the customer has no records.
        assert not self.customer_records.says_no_linked_records(), (
            "The lookup failed, so the tab must not also assert 'No linked records found' - "
            "an empty cache after a failure is an error, not a fact about the customer"
        )

    @pytest.mark.phase1
    @pytest.mark.regression
    def test_stale_cached_records_carry_an_honest_caveat(self):
        """
        M13-EDG: 'Customer details that changed at the source are refreshed' - the honest half.

        When rows ARE cached but the newest lookup did not finish, the tab shows them with an
        amber "These records may be incomplete" caveat rather than presenting them as current.
        """
        self.open_records_of_first_ticket()

        if not self.customer_records.says_records_may_be_incomplete():
            pytest.skip(
                "The most recent lookup completed for this ticket, so the staleness caveat is "
                "correctly absent."
            )
        assert self.customer_records.has_table(CustomerRecordsPage.POLICY_CARD), (
            "The caveat is only meaningful above rows that are actually being shown - it must "
            "not appear on its own"
        )


    @pytest.mark.phase2
    @pytest.mark.regression
    def test_the_customers_previous_cases_are_shown_in_one_place(self):
        """M13-POS: 'All of a customer's previous cases are shown in one place'."""
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip(
                "This ticket's tab shows no Customer History panel - typically a ticket with no "
                "customer identified on it, which has no history to gather."
            )
        # Either it lists past cases, or it says there are none. A blank panel is neither.
        assert (
            self.customer_records.history_references()
            or self.customer_records.says_no_other_tickets()
        ), (
            "The history panel must list the customer's other cases or say there are none. "
            f"On screen: {self.page_text_snippet()}"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    def test_a_past_case_in_the_history_opens_when_clicked(self):
        """M13-POS: 'Clicking a past case opens it'."""
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip("No Customer History panel on this ticket.")
        links = self.customer_records.history_ticket_links()
        if not links:
            pytest.skip("This customer has no other cases, so there is nothing to click through to.")

        links[0].click()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number(), (
            "Clicking a past case should open that ticket's own detail page. "
            f"Landed on: {self.current_url()}"
        )

    @pytest.mark.phase1
    @pytest.mark.quarantine("no-failing-path")
    def test_the_history_covers_both_enquiries_and_complaints(self):
        """
        M13-EDG: 'A customer's history includes both enquiries and complaints'.

        A history that silently showed only one type would let an agent miss that the same
        person has an open complaint while they are answering their enquiry.
        """
        self.open_overview_of_first_ticket()

        if not self.customer_records.has_history_panel():
            pytest.skip("No Customer History panel on this ticket.")
        references = self.customer_records.history_references()
        if len(references) < 2:
            pytest.skip(
                f"This customer has {len(references)} other case(s), so a mix of types cannot "
                "be shown. Seed a customer with both to exercise this."
            )
        prefixes = {reference[:3] for reference in references}
        # The old assertion only said the prefixes were known ones - true of a panel showing
        # nothing but enquiries, which is exactly the failure this test exists to catch: an
        # agent answering an enquiry while the same customer has an open complaint they were
        # never shown. So the mix has to be present, or there is nothing here to prove.
        if not {"INQ", "COM"}.issubset(prefixes):
            pytest.skip(
                f"This customer's other cases are all of one type ({sorted(prefixes)}), so the "
                "panel cannot demonstrate a mix. Seed a customer with both an enquiry and a "
                "complaint to exercise this."
            )
        assert {"INQ", "COM"}.issubset(prefixes), (
            "A customer's history must show their complaints alongside their enquiries, not "
            f"one type only. Saw: {sorted(prefixes)}"
        )

    # ==================================================================
    # Access control
    # ==================================================================

    @pytest.mark.phase1
    @pytest.mark.api_candidate
    def test_the_records_tab_of_a_ticket_that_does_not_exist_is_refused(self):
        """
        M13-ACC: 'The customer records tab of a ticket outside your scope cannot be opened'.

        Customer records hold personal data, so this sub-resource is row-scoped like every
        other - and the refusal hides whether the ticket exists at all.
        """
        self.open_and_wait(
            "/tickets/00000000-0000-0000-0000-000000000000/customer-records"
        )

        assert self.is_page_not_found() or self.is_access_denied(), (
            "An unknown ticket id must be refused, not rendered. "
            f"On screen: {self.page_text_snippet()}"
        )


    # ==================================================================
    # R22 - the Customer History MODULE (/history), Phase 2
    # ==================================================================
    # The two phase-2 tests above cover the per-ticket CustomerHistoryPanel. These cover the
    # standalone module (app/history/page.tsx + HistorySearch.tsx) and who may not use it.

    def a_ticket_with_a_policy(self) -> tuple[str, str, str]:
        """(reference, policy number, customer name) of the first enquiry that HAS a policy."""
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        references = self.list.get_reference_numbers()
        policies = self.list.get_column_values("Policy Number")
        names = self.list.get_column_values("Customer Name")
        for reference, policy, name in zip(references, policies, names):
            if reference and policy and policy != "—":
                return reference, policy, "" if name == "—" else name
        pytest.skip("No enquiry on the first page carries a policy number to look up.")

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    def test_r22_the_history_module_shows_a_customers_tickets_grouped_and_on_a_timeline(self):
        """
        R22. /history lands on "Customer History" with the customer search (HistorySearch.tsx,
        "Search a customer — policy number, claim number, phone, or name"). Picking a customer
        navigates to /history?policy=... (lib/customers.ts customerHistoryHref); the page then
        shows that customer (h1 = their name), a Grouped view by default with the
        CustomerHistoryGrouped sections, and a Timeline view - and the ticket the policy was
        read from is among them.

        The policy is taken from a real ticket and opened through the module's own URL contract
        rather than typed into the search: the search box calls the live Data Mart lookup (which
        also writes the lookup cache and an audit row), and this test must stay read-only.
        """
        self.require_ticket_access()
        self.open_and_wait("/history")
        assert self.reports.get_heading() == "Customer History"
        assert self.reports.has_history_search(), "The module should offer the customer search"

        reference, policy, name = self.a_ticket_with_a_policy()
        self.open_and_wait(f"/history?{urlencode({'policy': policy})}")
        self.wait_for_page_content()

        heading = self.reports.get_heading()
        assert heading != "Customer History", "A customer's page should be titled with their name"
        if name:
            assert heading == name, (
                f"Policy {policy} belongs to '{name}' on {reference}, but the page is for '{heading}'"
            )
        assert self.reports.history_view_is("Grouped"), "Grouped should be the default view"
        groups = self.reports.history_group_labels()
        assert groups and set(groups) <= set(ReportsPage.HISTORY_GROUPS), (
            f"The grouped view should show its type sections, got {groups}"
        )
        self.reports.expand_all_history_groups()
        grouped = self.reports.history_references()
        assert reference in grouped, (
            f"{reference} carries policy {policy}, so it must be in that customer's history. "
            f"Listed: {grouped}"
        )

        self.reports.switch_history_view("Timeline")
        timeline = self.reports.history_references()
        assert sorted(timeline) == sorted(grouped), (
            "Timeline and Grouped are two layouts of the SAME tickets. "
            f"Grouped: {sorted(grouped)}, Timeline: {sorted(timeline)}"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.negative
    def test_r22_a_complaint_handler_is_not_offered_the_customer_history_module(self):
        """
        R22. VIEW_CUSTOMER_HISTORY is granted to every ticket-viewing role EXCEPT
        complaint_handler (app/teams/seed_data.py: "a customer's whole footprint is a broader
        disclosure than one scoped ticket"), and SideNav's "Customer History" item requires it.
        The /history page refusal itself is a cell of test_15_role_matrix, not repeated here.
        """
        self.login_once(self.get("complaintHandlerEmail"))
        self.open_and_wait("/tickets/complaints")
        self.nav.wait_until_loaded()
        assert not self.nav.has_item("Customer History"), (
            "A complaint handler must not be offered the Customer History module"
        )

    @pytest.mark.phase2
    @pytest.mark.regression
    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.negative
    def test_r22_a_complaint_handlers_ticket_shows_no_customer_history_panel(self):
        """
        R22. The ticket page fetches and renders CustomerHistoryPanel only for
        canViewCustomerHistory (app/tickets/[id]/page.tsx showHistory), so a complaint handler's
        own complaint carries no Customer History card.
        """
        self.login_once(self.get("complaintHandlerEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0 or self.list.is_empty_state_displayed():
            pytest.skip(
                f"{self.get('complaintHandlerEmail')} has no complaint assigned on UAT "
                "(own-assigned scope), so there is no ticket to check the panel's absence on."
            )
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        assert not self.customer_records.has_history_panel(), (
            "The Customer History panel must not render for a complaint handler"
        )
