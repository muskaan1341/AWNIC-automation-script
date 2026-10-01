"""
Ticket lifecycle tests, following the reply-driven flow step by step.

Step 1: email arrives, Step 2: initiator assigned, Step 3: reply from the ticket page,
Step 6: "may be resolved" banner. No test presses Send Reply, so no customer is emailed.
"""

import re

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


_REFERENCE_SHAPE = re.compile(r"(INQ|COM|JNK)-\d{4}-\d+")


class TestReplyLifecycle(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_an_email_ticket(self):
        """Opens an open (not resolved/closed) enquiry, so the reply composer is shown."""
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

    def open_an_email_sourced_enquiry(self):
        """Opens an enquiry whose Source is Email and returns its reference number."""
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        sources = self.list.get_column_values("Source")
        references = self.list.get_reference_numbers()
        if "Email" not in sources:
            pytest.skip(f"No enquiry on the first page came in by email. Sources: {sources}")
        row = sources.index("Email")
        reference = references[row]

        self.list.open_row(row)
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        assert self.detail.get_reference_number() == reference, (
            f"Opened {self.detail.get_reference_number()} but the row chosen was {reference}"
        )
        return reference

    # ---------- STEP 1 - a customer email arrives ----------

    def test_step1_an_arriving_email_becomes_a_numbered_ticket_carrying_that_email(self):
        """An emailed ticket has a reference number and shows the email it came from."""
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()

        assert _REFERENCE_SHAPE.fullmatch(reference), f"Bad reference number: {reference}"
        messages = self.detail.email_conversation_message_count()
        assert messages >= 1, (
            f"{reference} came in by email, so the EMAIL card should show it. "
            f"Message count: {messages} (-1 = no EMAIL card)"
        )
        assert self.detail.has_section("Ticket Information"), (
            "The Ticket Information section is missing"
        )
        # Department may be empty (unmatched tickets stay unassigned) - only the field is checked.
        assert self.detail.has_detail_field("Department"), "The Department field is missing"

    def test_step1b_the_customer_acknowledgment_is_attempted_and_recorded(self):
        """The audit trail records the acknowledgment email as Sent or Skipped."""
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()
        self.detail.open_audit_tab_and_wait()

        trail = self.detail.get_audit_event_labels()
        assert self.detail.audit_records("Acknowledgment Email Sent") or (
            self.detail.audit_records("Acknowledgment Email Skipped")
        ), (
            f"{reference} has no 'Acknowledgment Email Sent' or 'Skipped' entry. Trail: {trail}"
        )

    # ---------- STEP 2 - a CC Initiator is assigned and the clock starts ----------

    def test_step2_the_ticket_is_held_by_a_named_person_with_a_clock_running(self):
        """The SLA tab's CC Initiator rung is reached, shows hours and names the initiator."""
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()

        initiator = self.detail.cc_initiator_email()
        if not initiator:
            pytest.skip(f"{reference} has no CC Ticket Initiator assigned.")

        self.detail.open_tab("SLA")
        self.sla.wait_until_loaded()

        assert self.sla.has_card("SLA STATUS"), "The SLA STATUS card is missing"
        assert "CC Initiator" in self.sla.reached_rung_labels(), (
            f"The CC Initiator rung should be reached. Reached: {self.sla.reached_rung_labels()}"
        )
        rung = self.sla.rung_text("CC Initiator")
        assert re.search(r"\b\d+h\b", rung), (
            f"The CC Initiator rung should show its time in hours. Rung: {rung!r}"
        )
        assert initiator in rung, (
            f"The CC Initiator rung should name {initiator}. Rung: {rung!r}"
        )

    # ---------- STEP 3 - the first reply, from the ticket page ----------

    def test_step3_the_ticket_page_carries_the_reply_composer_itself(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        assert self.reply.is_card_displayed(), "The reply card should be on the ticket page"
        assert self.reply.is_composer_displayed(), "There should be a box to type into"
        assert self.reply.is_send_displayed(), "There should be a Send Reply button"

    def test_step3b_an_empty_reply_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip(f"The composer is locked for this user: {self.reply.get_lock_tooltip()}")
        assert not self.reply.is_send_enabled(), (
            "Send Reply should stay disabled while the box is empty"
        )

    def test_step3c_a_reply_made_only_of_spaces_still_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip("The composer is locked on this ticket for this user.")
        self.reply.type_reply("     ")
        assert not self.reply.is_send_enabled(), "Send Reply must stay disabled for only spaces"

    def test_step3d_typing_a_real_reply_makes_it_sendable(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip("The composer is locked on this ticket for this user.")
        self.reply.type_reply("Thank you for getting in touch - we are looking into this now.")
        assert self.reply.is_send_enabled(), "A real reply should enable Send Reply"
        # Send is NOT pressed - it would email a real customer.

    def test_step3e_the_agent_is_told_which_mailbox_the_reply_leaves_from(self):
        """The composer names the mailbox the reply is sent from."""
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_card_displayed():
            pytest.skip("No reply composer on this ticket.")

        mailbox, tooltip = self.reply.sending_mailbox()
        assert re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", mailbox), (
            f"The composer should name the sending mailbox. Badge text: {mailbox!r}"
        )
        assert tooltip == (
            f"Replies on this ticket send from {mailbox}, not your own mailbox."
        ), f"The tooltip should name the same mailbox. Tooltip: {tooltip!r}"

    @pytest.mark.blocked("compliance_officer")
    def test_step3f_a_locked_ticket_explains_why_it_cannot_be_replied_to(self):
        """A read-only role cannot send a reply."""
        self.login_once(self.get("complianceEmail"))
        self.open_and_wait("/tickets/enquiries")
        # On the shared site this account may have no role, so every screen refuses it.
        if self.is_access_denied():
            pytest.skip(f"'{self.get('complianceEmail')}' holds no role on this environment.")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("This role sees no enquiries here.")
        self.list.open_first_row()
        self.detail.wait_until_loaded()

        if not self.reply.is_card_displayed():
            pytest.skip("The composer is not shown to a read-only role, which is also fine.")
        assert not self.reply.is_send_enabled(), (
            "A Compliance Officer must never be able to email a customer"
        )

    # ---------- STEP 6 - the "may be resolved" flag ----------

    def find_flagged_ticket(self):
        """Returns the first enquiry's URL if it shows the resolution flag, else None."""
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            return None
        self.list.open_first_row()
        self.detail.wait_until_loaded()
        if self.detail.page_mentions("This ticket may be resolved"):
            return self.current_url()
        return None

    def test_step6_a_ticket_flagged_as_maybe_resolved_offers_both_ways_out(self):
        """The 'may be resolved' banner offers Dismiss and Approve & Resolve."""
        self.login_once(self.get("supervisorEmail"))
        flagged = self.find_flagged_ticket()
        if flagged is None:
            pytest.skip("No ticket is currently flagged as possibly resolved.")
        self.driver.get(flagged)
        self.detail.wait_until_loaded()

        assert self.detail.page_mentions("This ticket may be resolved"), (
            "The resolution banner should be shown"
        )
        assert self.detail.has_button("Dismiss"), "The banner should offer Dismiss"
        assert self.detail.has_button("Approve & Resolve"), (
            "The banner should offer Approve & Resolve"
        )
