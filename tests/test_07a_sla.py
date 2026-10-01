"""
SLA tab tests.

Checks the SLA tab of a ticket: its three cards, the matrix rule behind the deadline,
and the escalation ladder (motor tickets have an extra L2 rung, non-motor do not).
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.sla_page import SlaPage

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


class TestSla(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        # Signs in as the CC Initiator: on the shared site it is the ticket-viewing account with a role.
        request.cls.login_class(request.cls.get("ccInitiatorEmail"))

    def open_sla_tab_of_first_ticket(self, list_path):
        """Opens the first ticket on a list and switches to its SLA tab."""
        self.require_ticket_access("ccInitiatorEmail")
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}, so there is no SLA tab to open.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("SLA")
        self.sla.wait_until_loaded()

    # ---------- the screen itself ----------

    @pytest.mark.regression
    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_the_sla_tab_shows_its_three_cards(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        for title in SlaPage.CARD_TITLES:
            assert self.sla.has_card(title), (
                f"The SLA tab should show the '{title}' card. On screen: {self.page_text_snippet()}"
            )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_deadline_and_the_day_count_are_both_stated(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        assert self.sla.has_row("SLA Deadline Date"), (
            f"The deadline date row is missing. On screen: {self.page_text_snippet()}"
        )
        assert self.sla.has_row("SLA (Days)"), "The SLA (Days) row is missing."

        # An empty value must show '—', never be blank.
        assert self.sla.value_of("SLA (Days)").strip(), (
            "SLA (Days) is blank. An empty value must read '—'."
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_matrix_rule_card_says_which_rule_produced_the_deadline(self):
        """The Matrix Rule card names the department rule and shows its TAT hours."""
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        assert self.sla.has_card("MATRIX RULE"), "The Matrix Rule card is missing."
        if not self.sla.has_row("Department"):
            pytest.skip("No SLA matrix rule is set up for this ticket's department.")
        assert self.sla.has_row("Regular") and self.sla.has_row("Reputational"), (
            f"The rule should show its Regular and Reputational hours. "
            f"On screen: {self.page_text_snippet()}"
        )

    @pytest.mark.regression
    def test_the_matrix_rule_says_whether_this_is_a_motor_case(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        if not self.sla.has_row("Motor Case"):
            pytest.skip("No matrix rule for this ticket, so there is no Motor Case row.")
        motor_case = self.sla.value_of("Motor Case")
        assert motor_case in ("Yes", "No"), (
            f"Motor Case should be Yes or No. Actual: '{motor_case}'"
        )

    # ---------- the escalation ladder ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_ladder_draws_every_rung_this_ticket_can_reach(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        rungs = self.sla.rung_labels()
        assert rungs, f"The ladder has no rungs. On screen: {self.page_text_snippet()}"

        for expected in SlaPage.NON_MOTOR_RUNGS:
            assert expected in rungs, f"The ladder is missing '{expected}'. Rungs: {rungs}"

    @pytest.mark.regression
    def test_the_second_level_rung_appears_only_for_a_motor_ticket(self):
        """The L2 rung is shown for motor tickets only."""
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        if not self.sla.has_row("Motor Case"):
            pytest.skip("No matrix rule for this ticket, so motor cannot be determined.")
        is_motor = self.sla.value_of("Motor Case") == "Yes"
        shows_l2 = self.sla.has_rung(SlaPage.MOTOR_ONLY_RUNG)

        if is_motor:
            message = "A motor ticket should show the L2 rung."
        else:
            message = f"A non-motor ticket should not show L2. Rungs: {self.sla.rung_labels()}"
        assert shows_l2 == is_motor, message

    @pytest.mark.regression
    def test_every_rung_is_either_reached_or_pending_and_never_both(self):
        """Reached rungs plus pending rungs equals the total number of rungs."""
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        rungs = self.sla.rung_count()
        reached = self.sla.reached_count()
        pending = self.sla.pending_count()

        assert reached + pending == rungs, (
            f"Rungs={rungs} reached={reached} pending={pending}"
        )

    @pytest.mark.regression
    def test_the_ladder_is_filled_from_the_bottom_with_no_gaps(self):
        """Rungs are in the agreed order and the reached ones come first, with no gaps."""
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        drawn = self.sla.rung_labels()
        if self.sla.has_rung(SlaPage.MOTOR_ONLY_RUNG):
            expected = SlaPage.MOTOR_RUNGS
        else:
            expected = SlaPage.NON_MOTOR_RUNGS
        assert drawn == expected, f"Rungs out of order. Expected {expected}, got {drawn}"

        reached = self.sla.reached_rung_labels()
        assert reached == drawn[: len(reached)], (
            f"Reached rungs must start from the bottom. Reached {reached} on ladder {drawn}"
        )

    # ---------- a complaint has the same SLA screen ----------

    @pytest.mark.regression
    def test_a_complaint_gets_the_same_sla_screen_as_an_enquiry(self):
        self.open_sla_tab_of_first_ticket("/tickets/complaints")

        assert self.sla.has_card("ESCALATION LADDER"), (
            f"A complaint should show the escalation ladder. On screen: {self.page_text_snippet()}"
        )
        assert self.sla.rung_labels(), "A complaint's ladder must draw its rungs too."

    # ---------- access control ----------

    @pytest.mark.api_candidate
    def test_the_sla_tab_of_a_ticket_that_does_not_exist_is_refused(self):
        """A made-up ticket id shows the 'not available' screen."""
        self.open_and_wait("/tickets/00000000-0000-0000-0000-000000000000/sla")

        assert self.is_page_not_found() or self.is_access_denied(), (
            f"An unknown ticket id must be refused. On screen: {self.page_text_snippet()}"
        )
