"""
MODULE 10 - Escalation, and who is allowed to force it.

WHY THIS CLASS EXISTS: module 10 has 37 written test cases and had ZERO automation, which
made it the highest-risk screen in the product. (When this class was first written no ticket
had ever escalated on the live database; since 2026-09 the escalation scan has run for real on
UAT, which is what lets the board-lock test below check its rule instead of skipping.)

THE TWO WAYS A TICKET ESCALATES, and only one of them is testable from a browser:

  AUTOMATICALLY  a scheduled scan notices the SLA has been missed and moves the ticket up a
                 level on its own. There is no button for this and no way to make it happen
                 from the UI, so nothing here tries to.
  BY HAND        a supervisor decides not to wait. That is the "Manual Escalation" action,
                 and it is what these tests drive.

THE RULE THAT MATTERS MOST: MANUAL ESCALATION IS SUPERVISORY ONLY.
The client changed their mind about this in the 2026-08-12 amendment - the CC agent used to
have it and had it taken away. So an agent seeing this action is not a small styling slip; it
is a permission the client explicitly removed being handed back.

EVERY TEST HERE CANCELS. None of them completes an escalation, because escalating a real
ticket on a shared environment changes a row somebody else is looking at. They prove the guard
is there and the wording is right, which is what a guard is for.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Manual escalation (UI + underlying API)' + C-P1 'NOT CC Initiator — worth a dedicated regression test'
pytestmark = [pytest.mark.p1, pytest.mark.regression]


#: The More Action item that opens the modal. Confirmed against TicketHeaderActions.
ESCALATE_ACTION_LABEL = "Manual Escalation"

#: The exact sentence the modal shows when you submit without choosing an action.
#:
#: Taken from the modal's own code, and recorded in QA/AWNIC-Form-QA-Documentation.xlsx sheet
#: 07. Asserting the words, not merely "an error appeared", is the point: the documentation
#: says which sentence each rule produces, and a guard that blocks you with the wrong
#: explanation is still a guard nobody can get past.
NO_ACTION_CHOSEN_MESSAGE = "Select an action to continue."


class TestEscalation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_first_enquiry(self) -> None:
        """
        Opens an OPEN enquiry from the board (New / In Progress), or skips when there is none.

        Not "the first list row": on 2026-09-30 that row was held for duplicate review, where
        the whole header is frozen by design (TicketHeaderActions hides Manual Escalation under
        duplicateHoldActive), so both modal tests skipped with "No More Action menu" and never
        reached the modal. A board card in an open column is the shared, reliable choice.
        """
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

    # ==================================================================
    # Who is offered the action at all
    # ==================================================================

    @pytest.mark.phase2
    def test_escalating_without_choosing_an_action_is_refused(self):
        """
        The modal must not let you escalate without saying WHICH action you meant.

        The documented sentence is "Select an action to continue." Asserting on the exact
        wording is deliberate: a form that blocks you with the wrong explanation is still a
        form nobody can get past.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_enquiry()

        if not self.detail.has_more_action_menu():
            pytest.skip("No More Action menu on this ticket.")
        self.detail.open_more_action_menu()
        if ESCALATE_ACTION_LABEL not in self.detail.get_open_menu_labels():
            self.press_escape()
            pytest.skip(
                "Manual Escalation is not offered on this ticket - it is already escalated, "
                "resolved or closed."
            )
        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()

        # Submit with nothing chosen. The modal must stop us and say why.
        self.detail.confirm_modal_with("Confirm")

        assert self.detail.is_modal_open(), (
            "The modal must stay open when the form is incomplete - closing it would look like "
            "the escalation went through."
        )
        assert self.detail.modal_error() == NO_ACTION_CHOSEN_MESSAGE, (
            "An incomplete escalation must explain itself in the documented words."
        )

        self.detail.close_modal()

    @pytest.mark.phase2
    def test_the_escalation_modal_can_always_be_cancelled_without_escalating(self):
        """
        Cancelling closes the modal AND leaves the ticket exactly as escalated as it was.

        WHAT THIS REPLACED: "the modal is not open" straight after close_modal(), which itself
        waits for the modal to disappear - so the assertion could not fail on its own, and
        "change nothing" was never looked at. The ticket's stage label is read before, then
        again from a fresh load of the page (server truth, not the page's own state): a
        cancel that escalated anyway would now read "Escalated L1".
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_enquiry()
        stage_before = self.detail.current_status()

        if not self.detail.has_more_action_menu():
            pytest.skip("No More Action menu on this ticket.")
        self.detail.open_more_action_menu()
        if ESCALATE_ACTION_LABEL not in self.detail.get_open_menu_labels():
            self.press_escape()
            pytest.skip("Manual Escalation is not offered on this ticket.")
        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()
        self.detail.close_modal()

        self.driver.refresh()
        self.detail.wait_until_loaded()
        assert self.detail.current_status() == stage_before, (
            f"Cancelling must change nothing, but the ticket went from '{stage_before}' to "
            f"'{self.detail.current_status()}'."
        )

    # ==================================================================
    # Where escalation shows up once it has happened
    # ==================================================================

    @pytest.mark.phase1
    def test_an_escalated_ticket_cannot_be_moved_by_hand(self):
        """
        An escalated ticket is owned by the escalation engine, not by a person dragging a card.

        WHAT THIS REPLACED: an unconditional pytest.skip saying no ticket had ever escalated.
        That stopped being true - UAT now carries escalated tickets - so the rule can be
        checked. On the board it is enforced by removing the drag handle altogether
        (KanbanDnd: `draggable = canMove && !isEscalated(ticket)`), so the oracle is:
          * every card wearing the "Escalated ..." badge - in WHICHEVER column its stage puts
            it, since escalation is a badge and not a column (app/stages/mapping.py) - has NO
            drag handle,
          * while a card of the same board that is NOT escalated does have one. That control
            is what makes the first half mean "locked because escalated" rather than "this
            user cannot move anything".

        Signed in as the CC Initiator: the rule applies to every holder of MOVE_TICKET_STAGE
        (cc_initiator holds it - app/teams/seed_data.py), and that account is verified on
        UAT, so this does not wait on the CC Supervisor decision.
        """
        self.login_once(self.get("agentEmail"))

        escalated, movable = [], 0
        for queue in ("/tickets/enquiries", "/tickets/complaints"):
            self.open(queue)
            self.list.wait_until_loaded()
            self.list.switch_to_kanban()
            self.kanban.wait_until_loaded()
            for column in KanbanPage.COLUMNS:
                for card in self.kanban.cards_in(column):
                    if self.kanban.is_card_escalated(card):
                        escalated.append(
                            (
                                self.kanban.card_reference(card),
                                column,
                                self.kanban.is_card_draggable(card),
                            )
                        )
                    elif self.kanban.is_card_draggable(card):
                        movable += 1
            if escalated:
                break

        if not escalated:
            pytest.skip("No escalated ticket is on either board, so the lock has nothing to act on.")
        if movable == 0:
            pytest.skip(
                "No non-escalated card on that board can be picked up either, so a locked "
                "escalated card cannot be told apart from a board this user cannot move at all."
            )

        # NOT asserted any more: "every escalated card sits in Pending POC". That was a wrong
        # oracle. The column follows the ticket's STAGE (app/stages/mapping.py STAGE_TO_COLUMN),
        # and escalation is a breach_level BADGE, "never a column" (mapping.py:7-9) - the
        # apps/api scanners raise breach_level without moving stage_id (state_machine.py module
        # docstring). So a Tier-1-breached ticket escalates while still in New or In Progress;
        # the first UAT run as the supervisor (2026-09-30) found 85 such cards, all correct.
        # What the board DOES promise is below: an escalated card cannot be picked up.
        draggable = [ref for ref, _, can_drag in escalated if can_drag]
        assert not draggable, (
            f"Escalated tickets must not be draggable, but these can be picked up: {draggable}"
        )
