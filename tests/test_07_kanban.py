"""
MODULE 08 - The Kanban board.

HOW THE BOARD WORKS
Four columns: New, In Progress, Pending POC, Resolved. The application actually has nine
stages behind the scenes, and they collapse into those four - the three "Escalated" stages
all live inside Pending POC, shown as a badge on the card rather than as a column of their
own. "Closed" is off the board entirely.

THE RULES A DRAG MUST OBEY
  - New is a SOURCE only. A ticket can never be dragged back into it.
  - Dropping onto Resolved asks for a resolution note first. Nothing is ever resolved
    automatically - a person types why.
  - Dropping onto Pending POC asks which named contact takes it.
  - An escalated card cannot be dragged at all; the escalation engine owns it.

WHY THE DRAG CODE LOOKS ODD: see BaseTest.drag_card. The short version is that the board uses
pointer events and Selenium's built-in drag_and_drop speaks a different, older protocol that
this board ignores completely.
"""

from __future__ import annotations

import re

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P0 'Kanban board — loads, 4 correct columns' + 'Stage-transition state machine — invalid moves rejected'
pytestmark = [pytest.mark.p0, pytest.mark.phase1]



class TestKanban(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_board(self) -> None:
        """Opens the enquiries list and switches it to the board."""
        # Deployed environments can have an account that signs in fine but holds NO ROLE
        # (UAT had no cc_supervisor holder until 2026-09-30; supervisor-gen@awnic.com now holds it,
        # but compliance_officer still has none). Without
        # this, every test here waits out the full timeout on a heading that is never coming and
        # fails with "waiting for visibility of element located by By.tagName: h1" — which says
        # nothing about the real cause. Skip with the reason instead.
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

    def first_reference_on_the_board(self) -> str:
        """Finds any reference number currently on the board, so a test can follow one ticket."""
        for column in KanbanPage.COLUMNS:
            if self.kanban.card_count(column) > 0:
                text = self.kanban.first_card_in(column).text
                for line in text.split("\n"):
                    if line.strip().startswith("INQ-"):
                        return line.strip()
        pytest.skip("The board has no cards - run 'make seed-demo' first.")

    # ---------- the board itself ----------

    @pytest.mark.regression
    def test_the_board_shows_exactly_the_four_agreed_columns(self):
        self.open_board()

        assert self.kanban.get_column_titles() == KanbanPage.COLUMNS, (
            "The board must show exactly these four columns, in this order"
        )

    @pytest.mark.regression
    def test_each_column_header_count_matches_the_cards_below_it(self):
        self.open_board()

        for column in KanbanPage.COLUMNS:
            assert self.kanban.header_count(column) == self.kanban.card_count(column), (
                f"The '{column}' header count disagrees with the cards in it"
            )

    @pytest.mark.regression
    def test_an_empty_column_explains_itself_instead_of_looking_broken(self):
        self.open_board()

        for column in KanbanPage.COLUMNS:
            if self.kanban.card_count(column) == 0:
                assert self.kanban.shows_drop_hint(column), (
                    f"The empty '{column}' column should say 'Drop tickets here'"
                )
                return
        pytest.skip("Every column has cards, so there is no empty one to check.")

    @pytest.mark.regression
    def test_the_board_and_the_list_tell_the_same_story(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        # The REPORTED TOTAL, not get_row_count() - the list pages at ten, so on any
        # environment with more than ten enquiries the rows on screen are not the ticket count
        # and the board legitimately shows more than them. That comparison passed locally
        # (fewer than ten seeded enquiries) and failed on the shared AWS site with 99 - a test
        # bug that only a larger data set could expose.
        tickets_in_list = self.list.get_reported_result_count()

        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        # Closed tickets are off the board on purpose, so the board can legitimately show
        # FEWER cards than the list holds - but never more.
        assert self.kanban.total_card_count() <= tickets_in_list, (
            f"The board shows {self.kanban.total_card_count()} cards but the list holds only "
            f"{tickets_in_list} tickets - the board cannot invent tickets"
        )

    @pytest.mark.regression
    def test_a_card_carries_enough_to_work_from_without_opening_it(self):
        """
        The card is a work surface, not a label: a handler triages from it without opening
        the ticket. So assert the things it always carries - a real reference number on its
        ticket link, the reference-type chip, and the date the ticket arrived.

        WHAT THIS REPLACED: "INQ- appears somewhere in the card's text" and "the card is not
        empty". The second could not fail - any rendered card has text - and the first was
        satisfied by the word appearing anywhere at all, including inside a customer name.
        """
        self.open_board()

        card = self.kanban.first_card_in(
            self.kanban.column_of(self.first_reference_on_the_board())
        )
        text = card.text

        assert re.fullmatch(r"INQ-[\w-]+", self.kanban.card_reference(card)), (
            "A card's ticket link should read as a real enquiry reference number. Link text: "
            f"'{self.kanban.card_reference(card)}'. Card text: {text}"
        )
        assert "Inquiry" in text, (
            "Every card carries its reference-type chip, and this is the enquiries board. "
            f"Card text: {text}"
        )
        assert re.search(r"\b\d{2}/\d{2}/\d{4}\b", text), (
            f"A card should show the date the ticket arrived. Card text: {text}"
        )

    # ---------- who may move a card ----------

    @pytest.mark.regression
    def test_a_supervisor_has_cards_they_can_pick_up(self):
        """
        A supervisor may move tickets, so at least SOME card must be pickable.

        Deliberately "at least one" rather than "the first one": an escalated ticket is
        correctly locked, and whichever card happens to be first on a shared environment is not
        something a test should depend on.
        """
        self.open_board()

        if self.kanban.total_card_count() == 0:
            pytest.skip("The board is empty - run 'make seed-demo' first.")

        draggable = 0
        locked = 0
        for column in KanbanPage.COLUMNS:
            for card in self.kanban.cards_in(column):
                if self.kanban.is_card_draggable(card):
                    draggable += 1
                else:
                    locked += 1

        first_wrapper = self.kanban.describe_card_wrapper(
            self.kanban.first_card_in(
                self.kanban.column_of(self.first_reference_on_the_board())
            )
        )
        assert draggable > 0, (
            "A supervisor holds the move-stage permission, so at least one of the "
            f"{draggable + locked} cards should be draggable. None were. Either the permission "
            "is missing, every ticket is escalated, or the drag library labels its handles "
            f"differently now. First card's wrapper: {first_wrapper}"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("compliance_officer")
    def test_a_read_only_role_cannot_drag_anything(self):
        self.login_once(self.get("complianceEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        if self.kanban.total_card_count() == 0:
            pytest.skip("No cards visible to this role, so there is nothing to check.")
        for column in KanbanPage.COLUMNS:
            for card in self.kanban.cards_in(column):
                assert not self.kanban.is_card_draggable(card), (
                    "A compliance officer holds no move permission, so no card may be draggable"
                )

    # ---------- moving a card ----------

    @pytest.mark.write
    def test_a_card_can_be_dragged_from_new_to_in_progress(self):
        """
        The everyday move: pick a card out of New and drop it into In Progress.

        Asserts on the OUTCOME - the card is now in the other column - never on the animation.

        WRITES: this MOVES A REAL TICKET, and the board refuses to move it back into New, so it
        is gated behind writeTestsEnabled and skipped by default.
        """
        self.require_write_tests()
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.card_count(KanbanPage.NEW) == 0:
            pytest.skip("Nothing in the New column to drag. Run 'make seed-demo'.")

        card = self.kanban.first_card_in(KanbanPage.NEW)
        if not self.kanban.is_card_draggable(card):
            pytest.skip("The first New card is escalated, so it is correctly locked.")

        new_before = self.kanban.card_count(KanbanPage.NEW)
        in_progress_before = self.kanban.card_count(KanbanPage.IN_PROGRESS)

        self.drag_card(card, self.kanban.column_element(KanbanPage.IN_PROGRESS))

        self.kanban.wait_for_card_count(KanbanPage.IN_PROGRESS, in_progress_before + 1)
        assert self.kanban.card_count(KanbanPage.NEW) == new_before - 1, (
            "The card should have left the New column"
        )

    @pytest.mark.regression
    # 2026-09-30: the supervisor account exists now, but this test DRAGS a real card on the
    # shared UAT board. Its drop is meant to be refused (New) or cancelled (Resolved box), yet a
    # drop that lands one column off calls submitMove (KanbanBoard.tsx onDragEnd) - a real stage
    # write. UAT runs are read-only, so it stays blocked there; run it on a local/seeded stack.
    @pytest.mark.blocked("shared_uat_no_drag")
    def test_a_card_cannot_be_dragged_backwards_into_new(self):
        """
        "New" is a source, not a destination. The state machine refuses the move, so the card
        must snap back where it came from.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) == 0:
            pytest.skip("Nothing in In Progress to drag backwards.")

        card = self.kanban.first_card_in(KanbanPage.IN_PROGRESS)
        # An escalated card carries no drag listeners at all, so dragging it produces no drop
        # event, no refusal, and no banner - the assertions below would then fail for a reason
        # that has nothing to do with the backwards rule. Escalation is a separate rule with
        # its own message ("Escalated tickets are managed by the escalation engine."), proved
        # by test_a_read_only_role_cannot_drag_anything and the draggability checks.
        if not self.kanban.is_card_draggable(card):
            pytest.skip("The first In Progress card is escalated, so it cannot be picked up.")

        reference = self.kanban.card_reference(card)
        new_before = self.kanban.card_count(KanbanPage.NEW)
        in_progress_before = self.kanban.card_count(KanbanPage.IN_PROGRESS)

        self.drag_card(card, self.kanban.column_element(KanbanPage.NEW))

        # The board does not just silently snap the card back - it says why, and it says which
        # rule refused. Waiting on the banner first also means the assertions below run AFTER
        # the board has finished reacting, not in the gap before it has reacted at all (when
        # the counts would still agree for the wrong reason).
        self.wait.until(lambda d: self.kanban.shows_blocked_move_error())
        assert self.kanban.error_message() == "A ticket can't be moved back to New.", (
            "The refusal must name THIS rule. A different explanation means some other rule "
            f"stopped the move. Banner said: '{self.kanban.error_message()}'"
        )

        # Where the card actually ended up - not merely how many cards each column holds.
        assert self.kanban.column_of(reference) == KanbanPage.IN_PROGRESS, (
            f"{reference} was dragged at New and refused, so it must still be in In Progress. "
            f"It is now in: '{self.kanban.column_of(reference)}'"
        )
        assert not self.kanban.column_contains(KanbanPage.NEW, reference), (
            f"{reference} must not appear in New - New is a source, never a destination"
        )
        assert self.kanban.card_count(KanbanPage.NEW) == new_before, (
            "Nothing may move back into New"
        )
        assert self.kanban.card_count(KanbanPage.IN_PROGRESS) == in_progress_before, (
            "The card should have stayed where it was"
        )

    @pytest.mark.regression
    def test_a_card_names_the_customer_it_belongs_to(self):
        """
        A card carries the customer's name, so a handler can triage the board at a glance.

        WHAT THIS REPLACED: "the word 'Customer' appears on at least one card". That proved
        the label renders - nothing more. It could not tell a card showing the right person
        from a card showing somebody else's name, which is the only failure that matters
        here: triaging off a board that mislabels who a ticket belongs to is worse than a
        board with no names on it at all.

        So this follows ONE card through to its own ticket and checks the two agree.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.total_card_count() == 0:
            pytest.skip("The board is empty - run 'make seed-demo' first.")

        named = None
        for column in KanbanPage.COLUMNS:
            for card in self.kanban.cards_in(column):
                if self.kanban.card_customer_name(card):
                    named = card
                    break
            if named is not None:
                break

        if named is None:
            pytest.skip(
                "No ticket on this board has a customer name recorded, so there is no "
                "card-to-ticket pair to compare. (A ticket with no customer name correctly "
                "shows no Customer line - see CustomerDetailsCard's 'not yet identified'.)"
            )

        # Read both off the card BEFORE navigating - the element dies with the page.
        reference = self.kanban.card_reference(named)
        name_on_card = self.kanban.card_customer_name(named)

        self.kanban.open_card(named)
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number() == reference, (
            f"The card for {reference} should open that ticket, not "
            f"{self.detail.get_reference_number()}"
        )
        name_on_ticket = self.detail.get_detail_field_value("Customer Name")
        # The card truncates a long name with a CSS ellipsis, so it is a prefix of the
        # ticket's value rather than always equal to it. Anything that is NOT a prefix is a
        # different person, which is exactly what this test exists to catch.
        assert name_on_ticket.startswith(name_on_card.rstrip("…. ")), (
            f"The board names '{name_on_card}' on {reference}, but the ticket itself "
            f"records '{name_on_ticket}'"
        )

    @pytest.mark.regression
    # 2026-09-30: the supervisor account exists now, but this test DRAGS a real card on the
    # shared UAT board. Its drop is meant to be refused (New) or cancelled (Resolved box), yet a
    # drop that lands one column off calls submitMove (KanbanBoard.tsx onDragEnd) - a real stage
    # write. UAT runs are read-only, so it stays blocked there; run it on a local/seeded stack.
    @pytest.mark.blocked("shared_uat_no_drag")
    def test_resolving_asks_for_resolution_details_first(self):
        """
        Nothing is ever resolved silently. Dropping onto Resolved opens a box that asks how it
        was resolved, and the confirm button stays dead until somebody types an answer.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) == 0:
            pytest.skip("Nothing in In Progress to resolve.")

        card = self.kanban.first_card_in(KanbanPage.IN_PROGRESS)
        if not self.kanban.is_card_draggable(card):
            pytest.skip("The card is escalated, so it is correctly locked.")

        self.drag_card(card, self.kanban.column_element(KanbanPage.RESOLVED))
        self.kanban.wait_for_modal()

        assert self.kanban.modal_title().startswith("Resolve"), (
            f"Dropping onto Resolved should open the resolution box. "
            f"Title: {self.kanban.modal_title()}"
        )
        assert not self.kanban.is_modal_confirm_enabled("Resolve"), (
            "Resolve must stay disabled until a resolution note is written"
        )

        self.kanban.type_resolution_note("Customer confirmed the policy was reinstated.")
        assert self.kanban.is_modal_confirm_enabled("Resolve"), (
            "With a note written, Resolve should become usable"
        )

        # Cancel: this test proves the guard exists, it does not resolve a real ticket.
        self.kanban.cancel_modal()

    @pytest.mark.regression
    # 2026-09-30: the supervisor account exists now, but this test DRAGS a real card on the
    # shared UAT board. Its drop is meant to be refused (New) or cancelled (Resolved box), yet a
    # drop that lands one column off calls submitMove (KanbanBoard.tsx onDragEnd) - a real stage
    # write. UAT runs are read-only, so it stays blocked there; run it on a local/seeded stack.
    @pytest.mark.blocked("shared_uat_no_drag")
    def test_cancelling_the_resolve_box_leaves_the_ticket_where_it_was(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) == 0:
            pytest.skip("Nothing in In Progress to try.")

        resolved_before = self.kanban.card_count(KanbanPage.RESOLVED)
        card = self.kanban.first_card_in(KanbanPage.IN_PROGRESS)
        if not self.kanban.is_card_draggable(card):
            pytest.skip("The card is escalated, so it is correctly locked.")

        reference = self.kanban.card_reference(card)
        self.drag_card(card, self.kanban.column_element(KanbanPage.RESOLVED))
        self.kanban.wait_for_modal()
        self.kanban.cancel_modal()

        # Where THIS ticket is, not just how many cards Resolved holds - a count can stay put
        # while the dragged card lands somewhere it should never have gone.
        assert self.kanban.column_of(reference) == KanbanPage.IN_PROGRESS, (
            f"Cancelling must leave {reference} in In Progress. It is now in: "
            f"'{self.kanban.column_of(reference)}'"
        )
        assert self.kanban.card_count(KanbanPage.RESOLVED) == resolved_before, (
            "Cancelling must not move the ticket"
        )

    # ---------- clicking rather than dragging ----------

    @pytest.mark.regression
    def test_clicking_a_card_opens_its_ticket(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        column = self.kanban.column_of(self.first_reference_on_the_board())
        card = self.kanban.first_card_in(column)
        reference = self.kanban.card_reference(card)
        self.kanban.open_card(card)

        self.wait_for_ticket_detail_url()
        assert re.match(r".*/tickets/[^/]+$", self.current_url()), (
            f"A click (as opposed to a drag) should open the ticket. Actual: {self.current_url()}"
        )
        # ...and its OWN ticket. A URL shaped like a ticket page proves the click navigated;
        # only the reference number proves it navigated to the card that was clicked.
        self.detail.wait_until_loaded()
        assert self.detail.get_reference_number() == reference, (
            f"Clicking the card for {reference} opened "
            f"{self.detail.get_reference_number()} instead"
        )
