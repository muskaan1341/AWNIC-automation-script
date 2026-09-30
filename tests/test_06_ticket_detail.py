"""
MODULE 05 (part 3) - One ticket's detail screen.

THE ONE IDEA TO UNDERSTAND HERE: the tabs and the buttons on this screen are not fixed. They
change with the KIND of ticket and with WHO is looking at it:

  Investigation & Resolution   only on a complaint (it is backed by the complaints register)
  Recommended Action Plan      only when the AI pipeline actually ran on this ticket
  More Action                  only the items the signed-in role is allowed to use

So "the screen has six tabs" is the wrong assertion to write. The right one is "a complaint
has the investigation tab and an enquiry does not".
"""

from __future__ import annotations

import re
import time

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.ticket_detail_page import TicketDetailPage

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
        # (UAT had no cc_supervisor holder until 2026-09-30; supervisor-gen@awnic.com now holds it,
        # but compliance_officer still has none). Without
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
    def test_every_ticket_always_has_the_four_core_tabs(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Overview", "Customer & Records", "SLA", "Audit"]:
            assert self.detail.has_tab(tab), (
                f"Every ticket should have the '{tab}' tab. Tabs: {self.detail.get_tab_labels()}"
            )

    @pytest.mark.regression
    def test_an_enquiry_has_no_investigation_tab(self):
        self.open_first_ticket_of("/tickets/enquiries")

        # The investigation tab is backed by the complaints register, which an enquiry has no
        # row in. Showing an empty tab would be worse than not showing it.
        assert not self.detail.has_tab("Investigation & Resolution"), (
            "Only a complaint has an investigation record"
        )

    @pytest.mark.regression
    def test_a_complaint_has_the_investigation_tab(self):
        self.open_first_ticket_of("/tickets/complaints")

        assert self.detail.has_tab("Investigation & Resolution"), (
            "A complaint should offer the Investigation & Resolution tab. "
            f"Tabs: {self.detail.get_tab_labels()}"
        )

    @pytest.mark.regression
    def test_every_tab_opens_its_own_page(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Customer & Records", "SLA", "Audit"]:
            self.detail.open_tab(tab)
            self.wait.until(lambda d: not self.is_page_not_found())
            assert not self.is_page_not_found(), (
                f"The '{tab}' tab should open a real page, not 'Page not found'"
            )

    @pytest.mark.regression
    def test_the_overview_tab_shows_the_core_ticket_cards(self):
        self.open_first_ticket_of("/tickets/enquiries")

        assert self.detail.has_section("Ticket Information"), (
            "The Overview tab should show the Ticket Information card"
        )
        assert self.detail.has_internal_notes_card(), (
            "The Overview tab should offer internal notes"
        )

    @pytest.mark.regression
    def test_going_back_returns_to_the_list_you_came_from(self):
        self.open_first_ticket_of("/tickets/enquiries")
        self.detail.go_back_to_list()

        self.wait_for_url_containing("/tickets/enquiries")
        assert "/tickets/enquiries" in self.current_url(), (
            f"'Back to Tickets' should return to the list. Actual: {self.current_url()}"
        )

    # ---------- AI honesty ----------
    @pytest.mark.regression
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
    def test_an_empty_internal_note_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        assert not self.detail.is_send_note_enabled(), (
            "Send should stay disabled while the note box is empty"
        )

    @pytest.mark.regression
    def test_a_note_made_only_of_spaces_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("     ")
        assert not self.detail.is_send_note_enabled(), (
            "Whitespace is not a note - Send should still be disabled"
        )

    @pytest.mark.regression
    def test_typing_a_note_enables_send(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("Called the customer, awaiting documents.")
        assert self.detail.is_send_note_enabled(), "A real note should make Send usable"

    # ---------- the action menu ----------


    # WHAT CHANGED (2026-09-30): these three used to drive a header "Change Status" button with
    # a menu of statuses. That button was REMOVED (client requirement 1.24 - see
    # TicketHeaderActions.tsx): In Progress is now set automatically when the assigned CC
    # Initiator opens the ticket, and the only manual status move left is "Resolve" inside More
    # Action. The old tests looked for the missing button and skipped every run ("correctly
    # hidden"), so they had silently stopped testing anything. Rewritten against the real UI;
    # every one stops at the confirmation box and CANCELS.

    def _open_enquiry_offering_resolve(self) -> None:
        """An open enquiry whose More Action offers Resolve, or a skip saying why not."""
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")
        offered = self.detail.more_action_labels()
        if TicketDetailPage.RESOLVE_ITEM not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Resolve "
                f"(status '{self.detail.current_status()}', menu {offered}) - it is escalated "
                "or held for duplicate review, where Resolve is hidden by design."
            )

    @pytest.mark.regression
    def test_marking_a_ticket_resolved_requires_a_resolution_note(self):
        """
        NOTHING IS EVER MARKED RESOLVED WITHOUT SOMEBODY SAYING HOW.

        More Action -> Resolve on an enquiry opens StatusChangeConfirmModal ("Change status"),
        which asks for a Resolution note and keeps its "Change Status" button dead until one is
        written - the same rule as dropping a card on the board's Resolved column, and the API
        rejects the move without a note (422). Cancelled at the end: nothing is resolved.
        """
        self._open_enquiry_offering_resolve()
        status_before = self.detail.current_status()

        self.detail.open_resolve()
        self.detail.wait_for_modal()

        assert self.detail.get_modal_title() == TicketDetailPage.RESOLVE_MODAL_TITLE, (
            f"Resolve should open the '{TicketDetailPage.RESOLVE_MODAL_TITLE}' confirmation. "
            f"Title: {self.detail.get_modal_title()}"
        )
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

        self.detail.close_modal()
        assert self.detail.current_status() == status_before, (
            "Cancelling the Resolve box must leave the ticket's status alone"
        )

    @pytest.mark.regression
    def test_the_resolve_box_offers_an_unticked_customer_email_opt_in(self):
        """
        Replaces "changing to a non-resolved status does not ask for a note": there is no
        non-resolved manual move left to pick. What the Resolve box still promises beside the
        note is the notify-customer opt-in (StatusChangeConfirmModal: "Notify customer by
        email"), and it must start UNTICKED so nobody emails a customer by accident.
        """
        self._open_enquiry_offering_resolve()

        self.detail.open_resolve()
        self.detail.wait_for_modal()

        assert self.detail.has_notify_customer_checkbox(), (
            "Resolving should offer to tell the customer"
        )
        assert not self.detail.is_notify_customer_checked(), "...but never tick it for them"
        self.detail.close_modal()

    @pytest.mark.regression
    def test_the_only_manual_status_move_is_resolve_inside_more_action(self):
        """
        Replaces "Change Status never offers the status the ticket is already in".

        With the status menu gone the contract is simpler and stricter: no standalone Change
        Status button in the header, and no raw status items (In Progress / Pending Department
        POC / Resolved) anywhere in More Action - only "Resolve".
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

        assert not self.detail.has_legacy_change_status_button(), (
            "The header 'Change Status' button was removed (requirement 1.24) and must not "
            "come back - Resolve lives in More Action now"
        )
        offered = self.detail.more_action_labels()
        stale = [
            item
            for item in ("Change Status", "In Progress", "Pending Department POC", "Resolved")
            if item in offered
        ]
        assert not stale, (
            f"More Action must not offer raw status moves any more. Offered: {offered}"
        )

    @pytest.mark.regression
    def test_resolving_a_complaint_goes_to_its_investigation_tab_not_a_box(self):
        """
        A complaint can only close through the Investigation & Resolution form, so Resolve on a
        complaint NAVIGATES there (…/investigation?from=resolve) instead of resolving in place.
        Read-only: arriving on the tab changes nothing.
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/complaints")
        offered = self.detail.more_action_labels()
        if TicketDetailPage.RESOLVE_ITEM not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Resolve (menu "
                f"{offered}) - escalated or on duplicate hold, where it is hidden by design."
            )

        self.detail.open_resolve()
        self.wait_for_url_containing("/investigation")

        assert "from=resolve" in self.current_url(), (
            f"Resolve on a complaint should land on its investigation tab. At: {self.current_url()}"
        )
        assert not self.detail.is_modal_open(), (
            "A complaint must not be resolved through the in-place confirmation box"
        )

    @pytest.mark.regression
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
        self.require_ticket_access()
        # An OPEN ticket, and one that actually offers the item. The first list row used to be
        # taken on faith; on 2026-09-30 it was held for duplicate review, where every header
        # action is frozen by design (reclassifyMenu.ts hides discard under duplicateHoldActive),
        # so the test timed out on a More Action button that correctly was not there.
        self.open_an_open_ticket_from("/tickets/enquiries")
        offered = self.detail.more_action_labels()
        if "Move to Discarded" not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Move to Discarded "
                f"({offered}) - held for duplicate review or pending classification, both of "
                "which freeze it by design."
            )

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
    def test_a_compliance_officer_is_not_offered_resolve(self):
        """
        KNOWN DEFECT (TKT-03) - expected to FAIL until the application is fixed.

        The header "Change Status" button this test used to look for is gone, so the old
        assertion ("no Change Status button") passed trivially and proved nothing. The DEFECT
        moved with the action: Resolve inside More Action is gated only on `!isEscalated &&
        canActNow && actionsEnabled` (TicketHeaderActions.tsx:77). It never checks
        MOVE_TICKET_STAGE - the page computes `canMoveStage` and passes it down
        (page.tsx:110/158, TicketDetailHeader.tsx:99), but TicketHeaderActions does not even
        destructure it. canActNow is true for a read-only role on any ticket with no CC
        Initiator assigned (ticket-permissions.ts:236), so a Compliance Officer - who holds no
        move-stage permission - is offered Resolve there, which the API then refuses with 403.

        Not a security hole (the API is the boundary); a UX/RBAC-mirroring defect against
        docs/rbac.md. The assertion states the CORRECT behaviour and is not weakened.
        Blocked as well: no account holds compliance_officer on UAT (re-checked 2026-09-30).
        """
        self.login_once(self.get("complianceEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/complaints")

        offered = self.detail.more_action_labels()
        assert TicketDetailPage.RESOLVE_ITEM not in offered, (
            "A compliance officer holds no move-stage permission, so 'Resolve' must not be "
            f"offered. More Action offered: {offered}. TicketHeaderActions.tsx gates Resolve "
            "on canActNow only, not on canMoveStage."
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
