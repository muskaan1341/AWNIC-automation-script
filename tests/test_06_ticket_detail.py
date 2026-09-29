"""
MODULE 05 (part 3) - One ticket's detail screen.

THE ONE IDEA TO UNDERSTAND HERE: the tabs and the buttons on this screen are not fixed. They
change with the KIND of ticket and with WHO is looking at it:

  Investigation & Resolution   only on a complaint (it is backed by the complaints register)
  Recommended Action Plan      only when the AI pipeline actually ran on this ticket
  More Action / Change Status  only the items the signed-in role is allowed to use

So "the screen has six tabs" is the wrong assertion to write. The right one is "a complaint
has the investigation tab and an enquiry does not".
"""

from __future__ import annotations

import re
import time

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P0 'Ticket detail page — all tabs load without error for a ticket of each type'
pytestmark = [pytest.mark.p0, pytest.mark.phase1]



class TestTicketDetail(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_first_ticket_of(self, list_path: str) -> None:
        """Opens the first ticket on a list and waits for the detail screen."""
        # Deployed environments can have an account that signs in fine but holds NO ROLE
        # (config.deployed.properties: "NO ACCOUNT HOLDS cc_supervisor after the clean"). Without
        # this, every test here waits out the full timeout on a heading that is never coming and
        # fails with "waiting for visibility of element located by By.tagName: h1" — which says
        # nothing about the real cause. Skip with the reason instead.
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        self.list.open_first_row()
        self.detail.wait_until_loaded()

    # ---------- what the screen shows ----------

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_opening_a_ticket_shows_its_reference_number_as_the_heading(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        expected = self.list.get_reference_numbers()[0]

        self.list.open_first_row()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number() == expected, (
            "The detail page should open the ticket whose row was clicked"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_every_ticket_always_has_the_four_core_tabs(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Overview", "Customer & Records", "SLA", "Audit"]:
            assert self.detail.has_tab(tab), (
                f"Every ticket should have the '{tab}' tab. Tabs: {self.detail.get_tab_labels()}"
            )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_an_enquiry_has_no_investigation_tab(self):
        self.open_first_ticket_of("/tickets/enquiries")

        # The investigation tab is backed by the complaints register, which an enquiry has no
        # row in. Showing an empty tab would be worse than not showing it.
        assert not self.detail.has_tab("Investigation & Resolution"), (
            "Only a complaint has an investigation record"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_a_complaint_has_the_investigation_tab(self):
        self.open_first_ticket_of("/tickets/complaints")

        assert self.detail.has_tab("Investigation & Resolution"), (
            "A complaint should offer the Investigation & Resolution tab. "
            f"Tabs: {self.detail.get_tab_labels()}"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_every_tab_opens_its_own_page(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Customer & Records", "SLA", "Audit"]:
            self.detail.open_tab(tab)
            self.wait.until(lambda d: not self.is_page_not_found())
            assert not self.is_page_not_found(), (
                f"The '{tab}' tab should open a real page, not 'Page not found'"
            )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_the_overview_tab_shows_the_core_ticket_cards(self):
        self.open_first_ticket_of("/tickets/enquiries")

        assert self.detail.has_section("Ticket Information"), (
            "The Overview tab should show the Ticket Information card"
        )
        assert self.detail.has_internal_notes_card(), (
            "The Overview tab should offer internal notes"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_going_back_returns_to_the_list_you_came_from(self):
        self.open_first_ticket_of("/tickets/enquiries")
        self.detail.go_back_to_list()

        self.wait_for_url_containing("/tickets/enquiries")
        assert "/tickets/enquiries" in self.current_url(), (
            f"'Back to Tickets' should return to the list. Actual: {self.current_url()}"
        )

    # ---------- AI honesty ----------
    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_an_enquiry_shows_the_enquiry_taxonomy_in_its_ticket_information(self):
        """
        TICKET INFORMATION shows the ENQUIRY taxonomy on an enquiry.

        A note on "Enquiry Summary", because it has moved twice and a test chasing it has
        already been wrong once: it is a standalone CARD, not a field in this grid. It was
        briefly a DetailField here in early September and was moved back out again (commit
        f1c7388, "remove EnquirySummaryCard and integrate its functionality into
        TicketSummaryCard"). So this test asserts the fields that are genuinely stable - the
        taxonomy - and leaves the summary to the card tests above, which is where it lives.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        assert self.detail.has_section("Ticket Information")
        assert self.detail.has_detail_field("Sub-Enquiry"), (
            "An enquiry is classified down to a sub-enquiry, so the field should be shown"
        )
        assert not self.detail.has_detail_field("Complaint Category"), (
            "The complaint taxonomy belongs to complaints, not to enquiries"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_a_complaint_shows_the_complaint_field_set_instead_of_the_enquiry_one(self):
        """
        The complaint side of the same card shows the complaint taxonomy instead. Enquiry
        Summary belongs to the Inquiry branch only, so it must not appear here.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/complaints")

        assert self.detail.has_detail_field("Complaint Category"), (
            "A complaint should be described by the complaint taxonomy"
        )
        assert not self.detail.has_detail_field("Enquiry Summary"), (
            "Enquiry Summary belongs to the Inquiry branch of the card, not the complaint one"
        )

    # ---------- internal notes ----------

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_an_empty_internal_note_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        assert not self.detail.is_send_note_enabled(), (
            "Send should stay disabled while the note box is empty"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_a_note_made_only_of_spaces_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("     ")
        assert not self.detail.is_send_note_enabled(), (
            "Whitespace is not a note - Send should still be disabled"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_typing_a_note_enables_send(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("Called the customer, awaiting documents.")
        assert self.detail.is_send_note_enabled(), "A real note should make Send usable"

    # ---------- the action menu ----------


    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_marking_a_ticket_resolved_requires_a_resolution_note(self):
        """
        NOTHING IS EVER MARKED RESOLVED WITHOUT SOMEBODY SAYING HOW.

        Choosing "Resolved" from the status menu opens a box that asks for a resolution note,
        and the confirm button stays dead until one is written. This is the same rule the
        Kanban board enforces when a card is dropped into the Resolved column, and the API
        rejects the change without a note - so all three layers agree.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        if not self.detail.has_change_status_button():
            pytest.skip(
                "This ticket is escalated or already closed, so Change Status is correctly "
                "hidden. Seed an open ticket to exercise this path."
            )

        self.detail.open_status_menu()
        if "Resolved" not in self.detail.get_open_menu_labels():
            pytest.skip("This ticket is already Resolved, so that option is correctly not offered.")
        self.detail.click_menu_item("Resolved")
        self.detail.wait_for_modal()

        assert self.detail.has_resolution_note_box(), (
            "Resolving should ask HOW the ticket was resolved"
        )
        assert not self.detail.is_status_confirm_enabled(), (
            "Confirm must stay disabled until a resolution note is written"
        )

        self.detail.type_status_resolution_note(
            "Policy document was re-issued and emailed to the customer."
        )
        assert self.detail.is_status_confirm_enabled(), (
            "With a note written, the change should become possible"
        )

        # Cancel - this test proves the guard exists, it does not resolve a real ticket.
        self.detail.close_modal()

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_changing_to_a_non_resolved_status_does_not_ask_for_a_note(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        if not self.detail.has_change_status_button():
            pytest.skip("Change Status is correctly hidden on this ticket.")

        self.detail.open_status_menu()
        offered = self.detail.get_open_menu_labels()
        plain_status = next((s for s in offered if s != "Resolved"), None)
        if plain_status is None:
            pytest.skip("Only 'Resolved' is offered here.")

        self.detail.click_menu_item(plain_status)
        self.detail.wait_for_modal()

        assert not self.detail.has_resolution_note_box(), (
            f"Only resolving needs an explanation; '{plain_status}' should not ask for one"
        )
        assert self.detail.is_status_confirm_enabled(), (
            "With nothing else required, the change should be possible straight away"
        )
        self.detail.close_modal()

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_change_status_never_offers_the_status_the_ticket_is_already_in(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        if not self.detail.has_change_status_button():
            pytest.skip(
                "This ticket is escalated or already closed, so Change Status is hidden by "
                "design. Seed an open ticket to exercise this path."
            )

        current = self.detail.current_status()
        self.detail.open_status_menu()
        offered = self.detail.get_open_menu_labels()

        assert offered, "The status menu should offer something"
        # THE POINT OF THE TEST, which the old version never made: the menu must not offer the
        # status the ticket is ALREADY in. "Something is offered" was equally true of a menu
        # listing the current status back at the user - a move that means nothing and that the
        # API would refuse.
        assert current, (
            "The ticket's current status should be shown beside its reference number"
        )
        assert current not in offered, (
            f"The ticket is already '{current}', so that must not be offered as a change. "
            f"Offered: {offered}"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_discarding_asks_for_confirmation_and_never_offers_to_email_the_customer(self):
        """
        Discarding is destructive, so it must ask first - and it must NOT offer to email the
        customer.

        That second half is deliberate product behaviour, not an omission: discarding is what
        happens to junk mail, and writing to tell somebody their spam was binned would be
        absurd. Every OTHER write flow does carry the opt-in (see the reclassify test below),
        so the two together pin down the rule rather than just observing it.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.open_more_action_menu()
        self.detail.click_menu_item("Move to Discarded")
        self.detail.wait_for_modal()

        assert self.detail.is_modal_open(), "Discarding must ask before it happens"
        assert not self.detail.has_notify_customer_checkbox(), (
            "Discarding junk must not offer to email the customer about it"
        )

        # Cancel - this test only checks the guard, it does not actually discard anything.
        self.detail.close_modal()
        assert not self.detail.is_modal_open(), "Cancel should close the box without acting"

    @pytest.mark.regression
    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_offers_an_unticked_customer_email_opt_in(self):
        """
        A RECLASSIFICATION does offer to tell the customer - and the box starts UNTICKED, so
        nobody emails a customer by accident.
        """
        self.login_once(self.get("hodEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip("This role is offered no write actions here.")
        self.detail.open_more_action_menu()
        if "Reclassify as Complaint" not in self.detail.get_open_menu_labels():
            pytest.skip(
                "This ticket has already used its one-time swap, or is outside the window, so "
                "reclassifying is correctly not offered."
            )
        self.detail.click_menu_item("Reclassify as Complaint")
        self.detail.wait_for_modal()

        assert self.detail.has_notify_customer_checkbox(), (
            "Changing a customer's case type should offer to tell them"
        )
        assert not self.detail.is_notify_customer_checked(), "...but never tick it for them"
        self.detail.close_modal()

    # ---------- a role that may look but not touch ----------


    @pytest.mark.quarantine("TKT-03")
    @pytest.mark.blocked("compliance_officer")
    def test_a_compliance_officer_is_not_offered_the_change_status_button(self):
        """
        KNOWN DEFECT - this test is expected to FAIL until the application is fixed.

        A compliance officer is read-only, yet the "Change Status" button is still offered to
        them. Every other action on this header is hidden from a role that cannot use it -
        "More Action" checks canReclassify / canDiscard / canReassign / canManualEscalate /
        canEdit - but Change Status is gated on nothing at all. It is only hidden when the
        ticket is escalated or already closed.

        This is NOT a security hole: the API is the real boundary and refuses the change. It is
        a UX defect - the user is invited to press a button that is guaranteed to fail - and it
        breaks the rule in docs/rbac.md that every in-page action mirrors its permission. The
        fix is a canMoveStage prop, passed the same way canEdit already is.

        The assertion below states the CORRECT behaviour on purpose and has not been weakened
        to make the suite green.
        """
        self.login_once(self.get("complianceEmail"))
        self.open_first_ticket_of("/tickets/complaints")

        assert not self.detail.has_change_status_button(), (
            "A compliance officer holds no move-stage permission, so 'Change Status' should "
            "be hidden. It is not gated on any capability today - see TicketHeaderActions.tsx, "
            "which receives canEdit/canReassign/etc but no canMoveStage."
        )

    # ==================================================================
    # The reclassification window, surfaced proactively (module 07)
    # ==================================================================
    # Added from the module-07 test-case pack. The swap between Inquiry and Complaint is legal
    # only while the ticket is still with the CC Initiator, only once in a ticket's life, and
    # never once a complaints-register row exists. Rather than let a user press the button and
    # collect a 409, the API tells the screen up front through two advisory read fields
    # (can_reclassify_now / reclassify_blocked_reason) and the menu renders the item DISABLED
    # with the reason on it. The 409 stays the enforcement backstop.

    @pytest.mark.regression
    @pytest.mark.blocked("tier1_window")
    def test_a_blocked_swap_is_shown_greyed_out_with_its_reason_not_simply_hidden(self):
        """
        M07-NEG: 'The type cannot be changed once a department has been assigned' /
        '...after the first response deadline has passed'.

        The point is HOW the block is presented. Hiding the item entirely would leave the user
        wondering where it went; letting them press it and collect a 409 wastes their time. The
        product does neither — it lists the action, greys it out, and says why.

        A holder of the capability whose ticket is still inside its window sees it enabled; one
        whose window has closed sees it disabled with a reason. Both are correct, so this test
        asserts the pairing rather than one fixed outcome.
        """
        self.login_once(self.get("hodEmail"))
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip("This ticket offers no action menu to this role.")
        if not self.detail.offers_reclassify_in_any_state():
            pytest.skip(
                "Reclassify is not on this role's menu at all, which is a capability question "
                "rather than a window one - covered by the role matrix."
            )

        self.detail.open_more_action_menu()
        disabled = self.detail.reclassify_item_is_disabled()
        reason = self.detail.reclassify_blocked_reason()
        self.press_escape()

        if not disabled:
            # Still inside the window. Nothing to prove about the blocked presentation.
            pytest.skip(
                "This ticket is still inside its Tier-1 window, so the swap is correctly "
                "offered as usable. Seed a ticket past the window to exercise the block."
            )
        assert reason, (
            "A greyed-out Reclassify must carry the one-line reason the API supplied "
            "(reclassify_blocked_reason). A disabled item with no explanation is worse than no "
            "item at all - the user cannot tell a rule from a bug."
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_the_discard_reason_list_offers_real_choices(self):
        """
        M07-POS: 'The discard reason list covers the real junk AWNIC receives' and
        'The reason for discarding is kept and shown'.

        Discarding is refused without a reason (asserted in the modal-validation class); this
        checks the other half — that the list being chosen from is populated at all. An empty
        dropdown would make the guard unsatisfiable and the action impossible.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.offers_action("Move to Discarded"):
            pytest.skip("This role is not offered discarding on this ticket.")

        self.detail.open_action("Move to Discarded")
        reasons = self.detail.get_escalation_actions()  # same CustomSelect shape
        self.detail.close_modal()

        assert reasons, (
            "The discard modal must offer at least one reason to choose from - the action "
            "cannot be completed without one, so an empty list makes discarding impossible"
        )
