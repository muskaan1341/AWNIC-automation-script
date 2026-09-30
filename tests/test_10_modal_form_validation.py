"""
THE MODAL FORMS - from QA/AWNIC-Form-QA-Documentation.xlsx.

Five small forms that only exist inside a pop-up, so they are easy to forget and easy to ship
broken. Each one has exactly one job and one or two rules, and the documentation records the
precise sentence each rule is supposed to produce:

  sheet 06  Reassign Ticket      free-text Name/Email replaced by a searchable peer picker
                                 (ReassignPocModal / ReassignInitiatorModal, 2026-09) - the
                                 confirm button is simply disabled until somebody is chosen,
                                 so the two typed-in sentences the sheet records no longer
                                 exist. What is still checkable in a browser is that the box
                                 offers the picker rather than free text.
  sheet 07  Manual Escalation    "Select an action to continue." - covered by
                                 test_07b_escalation.py, which presses the button by its real
                                 label ("Confirm"); not duplicated here.
  sheet 08a Reclassify (swap)    "Explain why the original classification was wrong."
  sheet 08b Move to Discarded    "Select why this is being discarded."
  sheet 10  Restore Discarded    "Select a complaint category to continue."

EVERY TEST HERE CANCELS. They prove the guard exists; not one of them completes the action, so
the suite can be pointed at a shared environment without changing any ticket.

WHY SO MANY SKIPS? These modals are only offered when the ticket is in the right state and the
signed-in role holds the right permission - a resolved ticket has no actions, a once-swapped
ticket cannot swap again. A skip that explains which condition was not met is far more useful
than a red failure that means "the seed data was not what I hoped".
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   Validation wording, modal forms
pytestmark = [pytest.mark.p2, pytest.mark.phase1, pytest.mark.regression]



class TestModalFormValidation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_action_menu_on_first_enquiry(self, role_key: str) -> None:
        """Opens the first enquiry and its More Action menu, or skips with the reason."""
        # Deployed environments can have an account that signs in fine but holds NO ROLE
        # (UAT had no cc_supervisor holder until 2026-09-30; supervisor-gen@awnic.com now holds it,
        # but compliance_officer still has none). Without
        # this, every test here waits out the full timeout on a heading that is never coming and
        # fails with "waiting for visibility of element located by By.tagName: h1" — which says
        # nothing about the real cause. Skip with the reason instead.
        #
        # Sign in as THE ROLE UNDER TEST FIRST. The guard asks about whoever is signed in right
        # now, so running it before login_once checked the previous account instead - e.g. the
        # reclassify tests (hodEmail) were being skipped or allowed on the supervisor's grants.
        self.login_once(self.get(role_key))
        self.require_ticket_access(role_key)
        # An OPEN ticket from the board, not the first list row - that row can be closed or held
        # for duplicate review, where the whole header is frozen by design (seen 2026-09-30).
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip(
                "No action menu for this role on this ticket - it is closed, resolved, or the "
                "role holds no write permission. All three are correct behaviour."
            )
        self.detail.open_more_action_menu()

    def open_action(self, role_key: str, menu_item: str) -> None:
        """Opens one named action, or skips when the ticket's state does not offer it."""
        self.open_action_menu_on_first_enquiry(role_key)
        if menu_item not in self.detail.get_open_menu_labels():
            pytest.skip(
                f"'{menu_item}' is not offered on this ticket for this role. "
                f"Offered: {self.detail.get_open_menu_labels()}"
            )
        self.detail.click_menu_item(menu_item)
        self.detail.wait_for_modal()

    # ==================================================================
    # Sheet 06 - Reassign Ticket
    # ==================================================================

    def test_reassign_asks_you_to_pick_somebody_rather_than_type_them_in(self):
        """
        WHAT REPLACED THE THREE OLD TESTS HERE, and why they could not simply be relabelled.

        Sheet 06 was written against a form with free-text "Name" and "Email" boxes, which is
        why it records "Enter the point-of-contact's name." and "Enter a valid point-of-contact
        email.". That form is gone. Reassign now opens a SEARCHABLE PICKER over people who
        already exist:

          * still in Tier 1  -> ReassignInitiatorModal, a CC Initiator picker,
          * past Tier 1      -> ReassignPocModal, the current escalation level's peers, with
                                the present holder filtered out (so "pre-fills the current POC"
                                is now the opposite of what the product does).

        Neither box can be given a name that is not on the list, and both keep the confirm
        button disabled until a person is selected - so the two typed-in error sentences are
        unreachable and the pre-fill test asserts behaviour that was deliberately removed.

        The rule worth keeping from sheet 06 is the one that still holds: a reassignment is
        made by CHOOSING an existing contact, never by typing one in. That is what this asserts.
        """
        self.open_action("supervisorEmail", "Reassign")

        assert self.detail.get_modal_title() in ("Reassign ticket", "Reassign CC Initiator"), (
            "Reassign should open one of the two picker modals. Title: "
            f"{self.detail.get_modal_title()}"
        )
        assert not self.detail.has_removed_free_text_reassign_field(), (
            "The free-text point-of-contact Name and Email boxes were removed when the picker "
            "landed - a reassignment is chosen from the list, not typed in"
        )
        self.detail.close_modal()

    # ==================================================================
    # Sheet 08a - Reclassify (the Inquiry <-> Complaint swap)
    # ==================================================================

    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_refuses_an_empty_reason(self):
        self.open_action("hodEmail", "Reclassify as Complaint")

        # "Reclassify", not "Confirm": ReclassifyConfirmModal labels its button per target type
        # (COPY[targetType].confirmLabel) - Reclassify for a swap, "Move to Discarded" for a
        # discard. Pressing a button that is not there left the modal untouched and the test
        # timed out on an error message nothing had produced.
        self.detail.confirm_modal_with("Reclassify")

        assert (
            self.detail.modal_error() == "Explain why the original classification was wrong."
        ), "A reclassification with no reason should say so in those words"
        self.detail.close_modal()

    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_warns_that_the_change_is_permanent(self):
        """Checklist: "A permanent-change warning banner shows before confirming"."""
        self.open_action("hodEmail", "Reclassify as Complaint")

        assert self.detail.modal_warns_permanent(), (
            "Changing a customer's case type is permanent, and the box should say so"
        )
        self.detail.close_modal()

    # ==================================================================
    # Sheet 08b - Move to Discarded
    # ==================================================================

    def test_discarding_refuses_to_act_with_no_reason_chosen(self):
        self.open_action("supervisorEmail", "Move to Discarded")

        # The same modal, so the same rule: its button reads "Move to Discarded" here.
        self.detail.confirm_modal_with("Move to Discarded")

        assert self.detail.modal_error() == "Select why this is being discarded.", (
            "Discarding without picking a reason should say so in those words"
        )
        self.detail.close_modal()


    def test_restoring_as_a_complaint_needs_a_category_first(self):
        """
        Checklist: "Restoring as Complaint with no category selected -> 'Select a complaint
        category to continue.'" and "Restoring as Enquiry has no extra required field".

        As the HEAD OF DEPARTMENT: Restore is gated on RECLASSIFY_TICKET_TYPE
        (app/tickets/discarded/page.tsx canRestore), which cc_supervisor does not hold - the
        supervisor is correctly offered only "View details". The confirm is pressed with no
        category, which RestoreConfirmModal refuses client-side before any request.
        """
        self.login_once(self.get("hodEmail"))
        self.open("/tickets/discarded")
        self.discarded.wait_until_loaded()

        if self.discarded.get_row_count() == 0:
            pytest.skip("Nothing discarded on this environment to restore.")
        row = -1
        for candidate in range(self.discarded.get_row_count()):
            if self.discarded.row_has_action_menu(candidate):
                row = candidate
                break
        if row < 0:
            pytest.skip("Every discarded row has already been restored.")

        self.discarded.open_row_menu(row)
        if not any("Complaint" in i for i in self.discarded.get_open_menu_labels()):
            pytest.skip("Restoring as a complaint is not offered to this role.")
        self.discarded.click_restore_as("Complaint")
        self.detail.wait_for_modal()

        self.detail.confirm_modal_with("Restore")

        assert self.detail.modal_error() == "Select a complaint category to continue.", (
            "Restoring as a complaint with no category should say so in those words"
        )
        self.detail.close_modal()
