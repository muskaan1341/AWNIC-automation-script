"""
Manual escalation tests.

Only supervisors can escalate a ticket by hand. Every test here cancels the
escalation modal, so no real ticket is escalated.
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

pytestmark = [pytest.mark.p1, pytest.mark.regression]


# The More Action menu item that opens the escalation modal.
ESCALATE_ACTION_LABEL = "Manual Escalation"

# The error shown when you submit without choosing an action.
NO_ACTION_CHOSEN_MESSAGE = "Select an action to continue."


class TestEscalation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_first_enquiry(self):
        """Opens an open enquiry (New / In Progress) from the board, or skips if none."""
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

    # ---------- the escalation modal ----------

    @pytest.mark.phase2
    def test_escalating_without_choosing_an_action_is_refused(self):
        """Submitting without choosing an action shows 'Select an action to continue.'"""
        self.login_once(self.get("supervisorEmail"))
        self.open_first_enquiry()

        if not self.detail.has_more_action_menu():
            pytest.skip("No More Action menu on this ticket.")
        self.detail.open_more_action_menu()
        if ESCALATE_ACTION_LABEL not in self.detail.get_open_menu_labels():
            self.press_escape()
            pytest.skip("Manual Escalation is not offered on this ticket.")
        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()

        # Submit with nothing chosen.
        self.detail.confirm_modal_with("Confirm")

        assert self.detail.is_modal_open(), "The modal should stay open when the form is incomplete."
        assert self.detail.modal_error() == NO_ACTION_CHOSEN_MESSAGE, (
            "Wrong error message for an incomplete escalation."
        )

        self.detail.close_modal()

    @pytest.mark.phase2
    def test_the_escalation_modal_can_always_be_cancelled_without_escalating(self):
        """Cancelling the modal leaves the ticket's stage unchanged."""
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

        # Reload so we read the stage saved on the server.
        self.driver.refresh()
        self.detail.wait_until_loaded()
        assert self.detail.current_status() == stage_before, (
            f"The stage changed from '{stage_before}' to '{self.detail.current_status()}'."
        )

    # ---------- escalated tickets on the board ----------

    @pytest.mark.phase1
    def test_an_escalated_ticket_cannot_be_moved_by_hand(self):
        """Escalated cards cannot be dragged, while other cards on the same board can."""
        # The CC agent (initiator) can also move cards, and has a role on UAT.
        self.login_once(self.get("agentEmail"))

        escalated = []
        movable = 0
        for queue in ("/tickets/enquiries", "/tickets/complaints"):
            self.open(queue)
            self.list.wait_until_loaded()
            self.list.switch_to_kanban()
            self.kanban.wait_until_loaded()
            for column in KanbanPage.COLUMNS:
                for card in self.kanban.cards_in(column):
                    if self.kanban.is_card_escalated(card):
                        reference = self.kanban.card_reference(card)
                        can_drag = self.kanban.is_card_draggable(card)
                        escalated.append((reference, column, can_drag))
                    elif self.kanban.is_card_draggable(card):
                        movable += 1
            if escalated:
                break

        if not escalated:
            pytest.skip("No escalated ticket is on either board.")
        if movable == 0:
            pytest.skip("No card on that board can be dragged at all, so the lock cannot be told apart.")

        # Escalated cards can sit in any column, so only the drag lock is checked.
        draggable = []
        for reference, column, can_drag in escalated:
            if can_drag:
                draggable.append(reference)
        assert not draggable, (
            f"Escalated tickets must not be draggable, but these can be picked up: {draggable}"
        )
