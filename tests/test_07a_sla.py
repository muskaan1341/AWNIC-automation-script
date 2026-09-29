"""
MODULE 09 - SLA timers, and the ladder that shows where a ticket stands.

WHY THIS CLASS EXISTS: until now nothing drove this screen at all. Module 09 has 35 written
test cases and had ZERO automation, which mattered more than the number suggests - the SLA
engine is the part of the system the client's requirements care most about, and on the live
database no SLA has ever actually breached, so this screen had never been checked by a
machine OR exercised by real traffic.

WHAT THESE TESTS CAN AND CANNOT PROVE
They can prove the screen is honest about what it is showing: that the deadline comes from a
named matrix rule rather than from nowhere, that the ladder has the right rungs for the kind
of ticket, and that the reached/pending split is internally consistent. They CANNOT prove the
deadline arithmetic is right - that needs a clock, working-hours data and a ticket aged on
purpose, which belongs in the API tests, not here.

THE MOTOR RULE IS THE INTERESTING ONE. A motor ticket escalates through FOUR levels and a
non-motor ticket through THREE: L2 exists only for motor. Getting that wrong in either
direction is a real defect - a non-motor ticket showing an L2 rung would be inventing a step
nobody at AWNIC has, and a motor ticket missing it would be hiding one.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.sla_page import SlaPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 SLA correctness — the ladder and the matrix rule behind a deadline
pytestmark = [pytest.mark.p1, pytest.mark.phase1]



class TestSla(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        """
        Signs in as the CC AGENT, not the supervisor the rest of the suite tends to use.

        Deliberate. The SLA tab is readable by every ticket-viewing role, so any of them would
        do in principle - but on the shared environment as of 2026-09-04 the agent is the ONLY
        ticket-viewing account that has actually been granted its role. Signing in as the
        supervisor here would skip every test in the class for a reason that has nothing to do
        with the SLA screen. See BaseTest.require_ticket_access.
        """
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_sla_tab_of_first_ticket(self, list_path: str) -> None:
        """
        Opens the first ticket on a list and switches to its SLA tab.

        Skips rather than fails when the list is empty. An environment with no tickets is a
        legitimate state - it is not this screen being broken - and a test that shouted about
        it would be reporting the seed data, not the product.
        """
        self.require_ticket_access("agentEmail")
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No tickets on {list_path}, so there is no SLA tab to open.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("SLA")
        self.sla.wait_until_loaded()

    # ==================================================================
    # The screen itself
    # ==================================================================

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
            f"SLA Status must state the deadline date. On screen: {self.page_text_snippet()}"
        )
        assert self.sla.has_row("SLA (Days)"), (
            "SLA Status must state how many days the rule allows."
        )

        # An em dash is the app's own "nothing here" value and is a legitimate answer - a
        # discarded ticket genuinely has no deadline. Blank, though, is never right: it would
        # mean the row rendered and then said nothing at all.
        assert self.sla.value_of("SLA (Days)").strip(), (
            "The day count rendered but was empty. A missing value must read '—', never blank."
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_matrix_rule_card_says_which_rule_produced_the_deadline(self):
        """
        The whole point of the Matrix Rule card: WHERE the number came from.

        A deadline with no traceable source is exactly the problem this application was built
        to remove - the old process had SLA days written into an AI prompt, with no way to see
        which rule produced a given date.

        WHY THIS NO LONGER ASKS FOR AN "Enquiry Type" ROW. The lookup changed: a matrix rule is
        matched on DEPARTMENT ALONE since migration 106 ("every department has exactly one row
        now, `inquiry_type` is no longer part of the lookup" - SlaMatrixRuleCard.tsx), and the
        card renders Department / Product / Motor Case / Regular / Reputational. Asking for a
        row the product deliberately stopped drawing tested the old rule, not the current one.

        What the card must still do is unchanged, and is what is asserted here: name the rule
        it resolved (its key, the department) and show the TATs that rule produced.
        """
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        assert self.sla.has_card("MATRIX RULE"), (
            "The deadline must be traceable to a matrix rule."
        )
        if not self.sla.has_row("Department"):
            pytest.skip(
                "No SLA matrix rule is configured for this ticket's department, so the card "
                "correctly shows its empty state rather than a rule. `sla_matrix` is unseeded "
                "on a fresh environment by design - seed it to exercise this."
            )
        assert self.sla.has_row("Regular") and self.sla.has_row("Reputational"), (
            "A rule is only traceable if the card shows the TATs it produced - the regular and "
            f"reputational-risk hours. On screen: {self.page_text_snippet()}"
        )

    @pytest.mark.regression
    def test_the_matrix_rule_says_whether_this_is_a_motor_case(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        if not self.sla.has_row("Motor Case"):
            pytest.skip(
                "No matrix rule resolved for this ticket, so there is no Motor Case row to "
                "read. That is a data gap, not a screen fault."
            )
        motor_case = self.sla.value_of("Motor Case")
        assert motor_case in ("Yes", "No"), (
            "Motor Case decides whether the ladder has four rungs or five, so it must be a "
            f"plain Yes or No. Actual: '{motor_case}'"
        )

    # ==================================================================
    # The escalation ladder
    # ==================================================================

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_ladder_draws_every_rung_this_ticket_can_reach(self):
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        rungs = self.sla.rung_labels()
        assert rungs, (
            "The escalation ladder rendered with no rungs at all. "
            f"On screen: {self.page_text_snippet()}"
        )

        for expected in SlaPage.NON_MOTOR_RUNGS:
            assert expected in rungs, (
                f"Every ladder has a '{expected}' rung. Actual rungs: {rungs}"
            )

    @pytest.mark.regression
    def test_the_second_level_rung_appears_only_for_a_motor_ticket(self):
        """
        L2 IS MOTOR-ONLY. This is the rule most worth protecting on this screen.

        Non-motor escalates Dept POC -> First -> Final. Motor has one more step in between.
        The ladder must not invent that step for a ticket that does not have it.
        """
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        if not self.sla.has_row("Motor Case"):
            pytest.skip("No matrix rule for this ticket, so motor cannot be determined.")
        is_motor = self.sla.value_of("Motor Case") == "Yes"
        shows_l2 = self.sla.has_rung(SlaPage.MOTOR_ONLY_RUNG)

        assert shows_l2 == is_motor, (
            "A motor ticket escalates through four levels, so the L2 rung must be shown."
            if is_motor
            else (
                "A NON-motor ticket goes L1 straight to Final - showing an L2 rung invents a "
                f"step this ticket does not have. Rungs: {self.sla.rung_labels()}"
            )
        )

    @pytest.mark.regression
    def test_every_rung_is_either_reached_or_pending_and_never_both(self):
        """
        Every rung is drawn exactly once, either reached or pending - never both, never neither.

        This is the cheapest possible check on the ladder's internal honesty. If reached plus
        pending does not equal the number of rungs, the page is drawing a rung in a state that
        has no meaning, and every colour on the screen is then suspect.
        """
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        rungs = self.sla.rung_count()
        reached = self.sla.reached_count()
        pending = self.sla.pending_count()

        assert reached + pending == rungs, (
            f"Each rung must be in exactly one state. Rungs={rungs} reached={reached} "
            f"pending={pending}"
        )

    @pytest.mark.regression
    def test_the_ladder_is_filled_from_the_bottom_with_no_gaps(self):
        """
        The ladder fills from the bottom up - it can never show a gap.

        Reaching "Final Escalation" while "L1" is still pending would be nonsense: you cannot
        arrive at the top without passing the rungs below it. A ladder that drew it anyway
        would tell a supervisor a ticket had climbed a level it never touched.

        WHAT THIS USED TO ASSERT. Only that the number of green circles was not greater than
        the number of rungs - which is true of ANY ladder, including one showing Final reached
        while L1 is still pending, and true again if the ladder drew its rungs in any order at
        all. It could not say which rungs were green, because reached_count() counts circles
        and never maps them back to a rung. SlaPage.reached_rung_labels() now does.

        The two halves asserted here are the ladder's actual contract (SlaEscalationLadder):
        the rungs are rendered in one fixed order, and a rung is green when its own position is
        at or below the reached level - so the green ones are always the LEADING run.
        """
        self.open_sla_tab_of_first_ticket("/tickets/enquiries")

        drawn = self.sla.rung_labels()
        expected = (
            SlaPage.MOTOR_RUNGS
            if self.sla.has_rung(SlaPage.MOTOR_ONLY_RUNG)
            else SlaPage.NON_MOTOR_RUNGS
        )
        assert drawn == expected, (
            "The ladder must draw its rungs bottom-to-top in the agreed order - reading them "
            f"in any other order makes 'how far has this climbed' meaningless. Expected "
            f"{expected}, drew {drawn}"
        )

        reached = self.sla.reached_rung_labels()
        assert reached == drawn[: len(reached)], (
            "The reached rungs must be the leading run of the ladder: a pending rung below a "
            f"reached one is a gap, and the ticket never climbed through it. Reached {reached} "
            f"on a ladder of {drawn}"
        )

    # ==================================================================
    # A complaint has the same SLA screen
    # ==================================================================

    @pytest.mark.regression
    def test_a_complaint_gets_the_same_sla_screen_as_an_enquiry(self):
        self.open_sla_tab_of_first_ticket("/tickets/complaints")

        assert self.sla.has_card("ESCALATION LADDER"), (
            "The SLA tab is not type-specific - a complaint gets the same ladder. "
            f"On screen: {self.page_text_snippet()}"
        )
        assert self.sla.rung_labels(), "A complaint's ladder must draw its rungs too."

    # ==================================================================
    # Access control
    # ==================================================================

    @pytest.mark.api_candidate
    def test_the_sla_tab_of_a_ticket_that_does_not_exist_is_refused(self):
        """
        The SLA tab is a per-ticket sub-resource, so it is row-scoped like every other one.

        A made-up ticket id must produce the application's own "not available" screen, NOT a
        stack trace and NOT an empty SLA card. The wording is deliberately the same whether the
        ticket is missing or merely invisible to you, so nobody can discover which tickets
        exist by trying ids.
        """
        self.open_and_wait("/tickets/00000000-0000-0000-0000-000000000000/sla")

        assert self.is_page_not_found() or self.is_access_denied(), (
            f"An unknown ticket id must be refused, not rendered. "
            f"On screen: {self.page_text_snippet()}"
        )

