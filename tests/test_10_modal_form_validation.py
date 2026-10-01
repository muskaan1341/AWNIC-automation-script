"""
Pop-up (modal) form tests.

Checks the rules of the Reassign, Reclassify, Move to Discarded and Restore pop-ups.
Every test closes the pop-up without confirming, so no ticket is changed.
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p2, pytest.mark.phase1, pytest.mark.regression]


class TestModalFormValidation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_action_menu_on_first_enquiry(self, role_key):
        """Opens an open enquiry and its More Action menu, or skips."""
        # Sign in first - require_ticket_access checks whoever is signed in right now.
        self.login_once(self.get(role_key))
        self.require_ticket_access(role_key)
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip("No action menu for this role on this ticket.")
        self.detail.open_more_action_menu()

    def open_action(self, role_key, menu_item):
        """Opens one action's pop-up, or skips if the menu does not offer it."""
        self.open_action_menu_on_first_enquiry(role_key)
        if menu_item not in self.detail.get_open_menu_labels():
            pytest.skip(
                f"'{menu_item}' is not offered here. Offered: {self.detail.get_open_menu_labels()}"
            )
        self.detail.click_menu_item(menu_item)
        self.detail.wait_for_modal()

    # ---------- Reassign ----------

    def test_reassign_asks_you_to_pick_somebody_rather_than_type_them_in(self):
        """Reassign opens a picker of existing people, with no free-text Name/Email boxes."""
        self.open_action("supervisorEmail", "Reassign")

        assert self.detail.get_modal_title() in ("Reassign ticket", "Reassign CC Initiator"), (
            f"Unexpected pop-up title: {self.detail.get_modal_title()}"
        )
        assert not self.detail.has_removed_free_text_reassign_field(), (
            "Reassign should use a picker, not free-text Name and Email boxes"
        )
        self.detail.close_modal()

    # ---------- Reclassify (Inquiry <-> Complaint) ----------

    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_refuses_an_empty_reason(self):
        self.open_action("hodEmail", "Reclassify as Complaint")

        # The confirm button is labelled "Reclassify" in this pop-up.
        self.detail.confirm_modal_with("Reclassify")

        assert (
            self.detail.modal_error() == "Explain why the original classification was wrong."
        ), "Wrong error message for an empty reason"
        self.detail.close_modal()

    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_warns_that_the_change_is_permanent(self):
        self.open_action("hodEmail", "Reclassify as Complaint")

        assert self.detail.modal_warns_permanent(), "The pop-up should warn the change is permanent"
        self.detail.close_modal()

    # ---------- Move to Discarded ----------

    def test_discarding_refuses_to_act_with_no_reason_chosen(self):
        self.open_action("supervisorEmail", "Move to Discarded")

        # The confirm button is labelled "Move to Discarded" in this pop-up.
        self.detail.confirm_modal_with("Move to Discarded")

        assert self.detail.modal_error() == "Select why this is being discarded.", (
            "Wrong error message for a discard with no reason"
        )
        self.detail.close_modal()

    # ---------- Restore from Discarded ----------

    def test_restoring_as_a_complaint_needs_a_category_first(self):
        """Restoring as a complaint without a category shows an error."""
        # Head of Department: the supervisor is not allowed to restore.
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
        complaint_offered = False
        for label in self.discarded.get_open_menu_labels():
            if "Complaint" in label:
                complaint_offered = True
        if not complaint_offered:
            pytest.skip("Restoring as a complaint is not offered to this role.")
        self.discarded.click_restore_as("Complaint")
        self.detail.wait_for_modal()

        self.detail.confirm_modal_with("Restore")

        assert self.detail.modal_error() == "Select a complaint category to continue.", (
            "Wrong error message for a restore with no category"
        )
        self.detail.close_modal()
