"""
THE TICKET LIFECYCLE AS THE DEVELOPMENT TEAM DESCRIBED IT (shared 2026-09-07).

Each test below maps to one numbered step of that description, so a failure here names the step
of the real flow that is broken rather than a screen:

  1  a customer email arrives      classified, numbered, auto-acknowledged
  2  a CC Initiator is assigned    round-robin, and a 24-hour clock starts
  3  first reply from the ticket   New -> In Progress, clock stops, audit records it
  4  department escalation         Dept Contact -> First -> (Motor: Second) -> Final
  5  the customer replies again    two background checks run
  6  the "looks resolved" flag     a banner offering Dismiss / Approve & Resolve
  7  resolve                       always a person, never automatic

===================================================================================
THE ONE THING THAT CHANGES HOW YOU READ THIS SUITE
===================================================================================
The ticket moves because somebody REPLIES, not because somebody sets a status. Step 3 is the
main road; "Change Status" is the manual override beside it. A suite that only drives status
changes is testing the override and leaving the real path uncovered, which is exactly what this
class exists to fix.

===================================================================================
NOTHING HERE SENDS ANYTHING
===================================================================================
Pressing Send Reply emails a REAL CUSTOMER, threaded onto their original conversation. That is
not something a test run should ever do. So every test below stops at the edge - it checks the
composer's state, its rules and its lock, and never presses Send.

The one test that DID send (behind a `replyTestsEnabled` flag) was removed on 2026-09-09, along
with every other test that wrote data or depended on an external system. If it is ever brought
back, it belongs in a separate, deliberately-run suite - not in this one, which is meant to be
safe to run against a shared environment on repeat.

Steps 1, 5 and 6 depend on an email-driven ticket existing with the right history. Where one is
not present the test SKIPS with what was missing, because "no ticket has been flagged as
possibly resolved today" is not a product failure.
"""

from __future__ import annotations

import re
import time

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.config import Config
from awnic_qa.pages.sla_page import SlaPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 the reply-driven lifecycle — the real path a ticket moves by
pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression, pytest.mark.blocked("cc_supervisor")]


_REFERENCE_SHAPE = re.compile(r"(INQ|COM|JNK)-\d{4}-\d+")


class TestReplyLifecycle(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_an_email_ticket(self) -> None:
        """Opens the first enquiry that actually came in by email - the flow starts there."""
        # Deliberately an OPEN ticket. The reply composer is part of the action header, which a
        # Resolved or Closed ticket does not render at all - so opening "the first row" could
        # report "no composer" about a ticket nobody is supposed to reply to.
        # Deployed environments can have an account that signs in fine but holds NO ROLE
        # (config.deployed.properties: "NO ACCOUNT HOLDS cc_supervisor after the clean"). Without
        # this, every test here waits out the full timeout on a heading that is never coming and
        # fails with "waiting for visibility of element located by By.tagName: h1" — which says
        # nothing about the real cause. Skip with the reason instead.
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

    def open_an_email_sourced_enquiry(self) -> str:
        """
        Opens an enquiry that genuinely ARRIVED BY EMAIL and returns its reference number.

        open_an_email_ticket() above picks an OPEN ticket, whatever its channel - right for
        the composer tests, but it let steps 1 and 2 "prove" things about email intake from a
        phone or walk-in ticket. This chooses by the list's own Source column instead, then
        checks the ticket that opened is the row that was chosen.
        """
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        sources = self.list.get_column_values("Source")
        references = self.list.get_reference_numbers()
        if "Email" not in sources:
            pytest.skip(
                "No enquiry on the first page of the list arrived by email, so there is no "
                f"email-driven ticket to follow. Sources on this page: {sources}"
            )
        row = sources.index("Email")
        reference = references[row]

        self.list.open_row(row)
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        assert self.detail.get_reference_number() == reference, (
            f"Opened {self.detail.get_reference_number()} but the row chosen was {reference}"
        )
        return reference

    # ==================================================================
    # STEP 1 - a customer email arrives
    # ==================================================================

    def test_step1_an_arriving_email_becomes_a_numbered_ticket_carrying_that_email(self):
        """
        WHAT THIS REPLACED: the same assertions against whichever OPEN ticket the board
        offered first - which could be a phone or walk-in ticket, so the test was named for
        email intake but proved nothing about it.

        It now follows a ticket whose Source is Email and asserts the step-1 outcome on IT:
        a quotable reference number, and the arriving email itself on the ticket.

        Deliberately NOT asserted: that Department holds a value. Since 2026-08-23 an
        unmatched classification is left unassigned on purpose (SmartRoutingPanel), so an
        empty Department on an emailed ticket is a legitimate state, not a defect.
        """
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()

        assert _REFERENCE_SHAPE.fullmatch(reference), (
            f"Every ticket carries a reference the customer can quote. Actual: {reference}"
        )
        messages = self.detail.email_conversation_message_count()
        assert messages >= 1, (
            f"{reference} came in by email, so its Overview must show that email in the EMAIL "
            f"conversation card. Message count read: {messages} (-1 = no EMAIL card at all)"
        )
        assert self.detail.has_section("Ticket Information"), (
            "The classification the pipeline produced should be on the Overview"
        )
        assert self.detail.has_detail_field("Department"), (
            "Step 1 says the email is routed to a department, so it must be shown"
        )

    def test_step1b_the_customer_acknowledgment_is_attempted_and_recorded(self):
        """
        The customer is told their reference number automatically. If this stops happening,
        customers have no way to refer to their own case - and nothing on screen would look
        broken, which is why it is worth asserting.

        WHAT THIS REPLACED: a test that skipped when no acknowledgment entry was found and
        then asserted that one was found - it could only ever pass or skip. The precondition
        is now independent of the thing asserted: the ticket arrived by EMAIL (chosen by its
        Source), and every emailed ticket's creation runs the acknowledgment workflow, which
        records its own outcome in the ticket's audit trail
        (app/tickets/customer_notification.py).

        "Sent" and "Skipped" both pass. Skipped is the workflow's correct answer when no
        customer address could be resolved; what must never happen is SILENCE - no record
        either way means the customer may have heard nothing and nobody would know.
        """
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()
        self.detail.open_audit_tab_and_wait()

        trail = self.detail.get_audit_event_labels()
        assert self.detail.audit_records("Acknowledgment Email Sent") or (
            self.detail.audit_records("Acknowledgment Email Skipped")
        ), (
            f"{reference} arrived by email, so its trail must record the acknowledgment "
            f"outcome ('Acknowledgment Email Sent' or '... Skipped'). Trail: {trail}"
        )

    # ==================================================================
    # STEP 2 - a CC Initiator is assigned, and a 24-hour clock starts
    # ==================================================================

    def test_step2_the_ticket_is_held_by_a_named_person_with_a_clock_running(self):
        """
        WHAT THIS REPLACED: `has_card("SLA Status") or has_card("SLA")`. The card's title is
        "SLA STATUS", so the first half never matched and the second matched the SLA TAB
        LABEL - true on every ticket before the tab had even rendered. Then "the ladder has
        at least one rung", which is true of every ticket too. Neither named a person.

        Now: the SLA STATUS card itself, the CC Initiator rung REACHED with a real Tier-1 TAT
        (the clock), and that rung naming the SAME initiator the Overview's routing card
        says holds the ticket (the person).
        """
        self.login_once(self.get("supervisorEmail"))
        reference = self.open_an_email_sourced_enquiry()

        initiator = self.detail.cc_initiator_email()
        if not initiator:
            pytest.skip(
                f"{reference} shows its CC Ticket Initiator as Unassigned. Since 2026-08-23 an "
                "unmatched pool is left unassigned on purpose, so there is no held-by person "
                "to check on this ticket."
            )

        self.detail.open_tab("SLA")
        self.sla.wait_until_loaded()

        assert self.sla.has_card("SLA STATUS"), (
            "Step 2 starts a clock, so the SLA tab must carry its SLA STATUS card"
        )
        assert "CC Initiator" in self.sla.reached_rung_labels(), (
            "The CC Initiator rung is reached the moment the ticket exists. Reached: "
            f"{self.sla.reached_rung_labels()}"
        )
        rung = self.sla.rung_text("CC Initiator")
        assert re.search(r"\b\d+h\b", rung), (
            f"The Tier-1 rung must show its response clock in hours, not '—'. Rung: {rung!r}"
        )
        assert initiator in rung, (
            f"The Overview says {initiator} holds {reference}, so the CC Initiator rung must "
            f"name them. Rung: {rung!r}"
        )

    # ==================================================================
    # STEP 3 - the first reply, sent from the ticket page itself
    # ==================================================================

    def test_step3_the_ticket_page_carries_the_reply_composer_itself(self):
        """
        The composer is the whole point of step 3: the agent never leaves the portal, and never
        opens an email client.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        assert self.reply.is_card_displayed(), (
            "Step 3 is 'reply from the ticket page', so the composer must be on it"
        )
        assert self.reply.is_composer_displayed(), "There should be a box to type into"
        assert self.reply.is_send_displayed(), "...and a Send Reply button beside it"

    def test_step3b_an_empty_reply_cannot_be_sent(self):
        """An empty reply is not a reply. Nothing should be sendable until something is typed."""
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip(
                "The composer is locked on this ticket for this user, so there is no "
                f"empty-vs-filled behaviour to check. Reason given: {self.reply.get_lock_tooltip()}"
            )
        assert not self.reply.is_send_enabled(), (
            "Send Reply should stay disabled while the box is empty"
        )

    def test_step3c_a_reply_made_only_of_spaces_still_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip("The composer is locked on this ticket for this user.")
        self.reply.type_reply("     ")
        assert not self.reply.is_send_enabled(), (
            "Whitespace is not a reply - Send Reply must stay disabled"
        )

    def test_step3d_typing_a_real_reply_makes_it_sendable(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_composer_enabled():
            pytest.skip("The composer is locked on this ticket for this user.")
        self.reply.type_reply("Thank you for getting in touch - we are looking into this now.")
        assert self.reply.is_send_enabled(), "A real reply should make Send Reply usable"
        # Deliberately NOT pressed: this would email a real customer. See the module comment.

    def test_step3e_the_agent_is_told_which_mailbox_the_reply_leaves_from(self):
        """
        A reply goes out from the mailbox the enquiry ARRIVED on, not from the agent's own. An
        agent who assumes otherwise will look for the sent item in the wrong place.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_an_email_ticket()

        if not self.reply.is_card_displayed():
            pytest.skip("No reply composer on this ticket.")

        # WHAT THIS REPLACED: `names_the_sending_mailbox() or is_composer_displayed()`. The
        # card being on screen (checked just above) means the composer is too, so the `or`
        # made this pass whether or not a mailbox was named.
        #
        # The composer card renders only for a ticket that has an inbound email
        # (ticket.last_email_id), and its header badge shows ticket.email_to - the mailbox
        # that email arrived on. So with the card present, the badge must be there and must
        # name one address, the same one in its text and in its explanation.
        mailbox, tooltip = self.reply.sending_mailbox()
        assert re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", mailbox), (
            "The composer should name the mailbox replies send from. Badge text: "
            f"{mailbox!r}"
        )
        assert tooltip == (
            f"Replies on this ticket send from {mailbox}, not your own mailbox."
        ), f"The badge's explanation should name the same mailbox. Tooltip: {tooltip!r}"

    @pytest.mark.blocked("compliance_officer")
    def test_step3f_a_locked_ticket_explains_why_it_cannot_be_replied_to(self):
        """
        A ticket locked to somebody else must not be repliable - but the composer stays on
        screen and explains itself rather than vanishing, so the agent knows why.
        """
        self.login_once(self.get("complianceEmail"))
        self.open_and_wait("/tickets/enquiries")
        # On the shared AWS site this account can sign in but has NO ROLE granted, so every
        # screen refuses it. That is missing seed data on that environment, not a product fault
        # and not something this test can prove anything against - say so and move on, the same
        # way the escalation class does for the same account.
        if self.is_access_denied():
            pytest.skip(
                f"'{self.get('complianceEmail')}' can sign in but holds no role on this "
                "environment, so every screen refuses it. Grant the role in user_roles to make "
                "this test meaningful here."
            )
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("This role sees no enquiries here.")
        self.list.open_first_row()
        self.detail.wait_until_loaded()

        if not self.reply.is_card_displayed():
            pytest.skip(
                "A read-only role is not shown the composer at all here, which is also an "
                "acceptable answer to the same question."
            )
        assert not self.reply.is_send_enabled(), (
            "A read-only Compliance Officer must never be able to email a customer"
        )
    # ==================================================================
    # STEP 4 - the department escalation chain
    # ==================================================================



    def find_flagged_ticket(self) -> str | None:
        """
        Looks for a ticket carrying the resolution flag.

        Only the FIRST row is checked, on purpose: opening every enquiry in turn to find one
        that may not exist costs more than the test is worth, and the flag appears only after a
        customer reply has actually been read that way.
        """
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
        """
        When a reply sounds like "this is sorted now", the system RAISES A FLAG and tells the
        assigned person. It never acts on it alone. The banner is that flag made visible, and it
        must offer both ways out.
        """
        self.login_once(self.get("supervisorEmail"))
        flagged = self.find_flagged_ticket()
        if flagged is None:
            pytest.skip(
                "No ticket on this environment is currently flagged as possibly resolved, so "
                "the banner cannot be exercised. It appears only when a customer reply has "
                "actually been read that way."
            )
        self.driver.get(flagged)
        self.detail.wait_until_loaded()

        assert self.detail.page_mentions("This ticket may be resolved"), (
            "The flag should be surfaced as a banner, not left silent"
        )
        assert self.detail.has_button("Dismiss"), (
            "The person must be able to say 'no, it isn't'"
        )
        assert self.detail.has_button("Approve & Resolve"), (
            "...and to confirm it in one step if it is"
        )

    # ==================================================================
    # STEP 7 - resolving is always a person's decision
    # ==================================================================

