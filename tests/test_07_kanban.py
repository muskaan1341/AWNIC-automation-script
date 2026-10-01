"""
Kanban board tests.

The board has four columns: New, In Progress, Pending POC, Resolved.
A card can never be dragged back into New, and dropping on Resolved asks for a note first.
"""

import re

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

pytestmark = [pytest.mark.p0, pytest.mark.phase1]


class TestKanban(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_board(self):
        """Opens the enquiries list and switches it to the board."""
        # Skips (instead of timing out) if the signed-in account has no role.
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

    def first_reference_on_the_board(self):
        """Returns the reference number of any card on the board."""
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
                f"The '{column}' header count does not match its cards"
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
        # Use the reported total - the list only shows ten rows per page.
        tickets_in_list = self.list.get_reported_result_count()

        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        # Closed tickets are not on the board, so the board may show fewer cards, never more.
        assert self.kanban.total_card_count() <= tickets_in_list, (
            f"The board shows {self.kanban.total_card_count()} cards but the list has only "
            f"{tickets_in_list} tickets"
        )

    @pytest.mark.regression
    def test_a_card_carries_enough_to_work_from_without_opening_it(self):
        """A card shows the reference number, the type chip and the date received."""
        self.open_board()

        card = self.kanban.first_card_in(
            self.kanban.column_of(self.first_reference_on_the_board())
        )
        text = card.text

        assert re.fullmatch(r"INQ-[\w-]+", self.kanban.card_reference(card)), (
            f"The card link should be an enquiry reference. Link: "
            f"'{self.kanban.card_reference(card)}'. Card: {text}"
        )
        assert "Inquiry" in text, f"The card should show the 'Inquiry' chip. Card: {text}"
        assert re.search(r"\b\d{2}/\d{2}/\d{4}\b", text), (
            f"The card should show the date received. Card: {text}"
        )

    # ---------- who may move a card ----------

    @pytest.mark.regression
    def test_a_supervisor_has_cards_they_can_pick_up(self):
        """At least one card on the board can be dragged by a supervisor."""
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
            f"None of the {draggable + locked} cards is draggable for a supervisor. "
            f"First card's wrapper: {first_wrapper}"
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
                    "A compliance officer must not be able to drag any card"
                )

    # ---------- moving a card ----------

    @pytest.mark.write
    def test_a_card_can_be_dragged_from_new_to_in_progress(self):
        """A card dragged from New lands in In Progress. (Moves a real ticket.)"""
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
    # Blocked on shared UAT: a mis-aimed drag would really move a ticket.
    @pytest.mark.blocked("shared_uat_no_drag")
    def test_a_card_cannot_be_dragged_backwards_into_new(self):
        """Dragging a card back into New is refused and the card stays put."""
        self.login_once(self.get("supervisorEmail"))
        self.open_board()

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) == 0:
            pytest.skip("Nothing in In Progress to drag backwards.")

        card = self.kanban.first_card_in(KanbanPage.IN_PROGRESS)
        if not self.kanban.is_card_draggable(card):
            pytest.skip("The first In Progress card is escalated, so it cannot be picked up.")

        reference = self.kanban.card_reference(card)
        new_before = self.kanban.card_count(KanbanPage.NEW)
        in_progress_before = self.kanban.card_count(KanbanPage.IN_PROGRESS)

        self.drag_card(card, self.kanban.column_element(KanbanPage.NEW))

        # Wait for the error banner so the board has finished reacting.
        self.wait.until(lambda d: self.kanban.shows_blocked_move_error())
        assert self.kanban.error_message() == "A ticket can't be moved back to New.", (
            f"Wrong error banner: '{self.kanban.error_message()}'"
        )

        assert self.kanban.column_of(reference) == KanbanPage.IN_PROGRESS, (
            f"{reference} should still be in In Progress. "
            f"It is now in: '{self.kanban.column_of(reference)}'"
        )
        assert not self.kanban.column_contains(KanbanPage.NEW, reference), (
            f"{reference} must not appear in New"
        )
        assert self.kanban.card_count(KanbanPage.NEW) == new_before, (
            "Nothing may move back into New"
        )
        assert self.kanban.card_count(KanbanPage.IN_PROGRESS) == in_progress_before, (
            "The card should have stayed where it was"
        )

    @pytest.mark.regression
    def test_a_card_names_the_customer_it_belongs_to(self):
        """The customer name on a card matches the name on its ticket."""
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
            pytest.skip("No card on the board shows a customer name.")

        # Read these before opening the ticket - the card element is gone after navigation.
        reference = self.kanban.card_reference(named)
        name_on_card = self.kanban.card_customer_name(named)

        self.kanban.open_card(named)
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number() == reference, (
            f"The card for {reference} opened {self.detail.get_reference_number()}"
        )
        name_on_ticket = self.detail.get_detail_field_value("Customer Name")
        # A long name is cut short with "..." on the card, so compare as a prefix.
        assert name_on_ticket.startswith(name_on_card.rstrip("…. ")), (
            f"The card shows '{name_on_card}' on {reference}, but the ticket says "
            f"'{name_on_ticket}'"
        )

    @pytest.mark.regression
    # Blocked on shared UAT: a mis-aimed drag would really move a ticket.
    @pytest.mark.blocked("shared_uat_no_drag")
    def test_resolving_asks_for_resolution_details_first(self):
        """Dropping on Resolved opens a box whose Resolve button needs a note first."""
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
            f"Expected the resolve box. Title: {self.kanban.modal_title()}"
        )
        assert not self.kanban.is_modal_confirm_enabled("Resolve"), (
            "Resolve must stay disabled until a note is written"
        )

        self.kanban.type_resolution_note("Customer confirmed the policy was reinstated.")
        assert self.kanban.is_modal_confirm_enabled("Resolve"), (
            "Resolve should be enabled once a note is written"
        )

        # Cancel so no real ticket is resolved.
        self.kanban.cancel_modal()

    @pytest.mark.regression
    # Blocked on shared UAT: a mis-aimed drag would really move a ticket.
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

        assert self.kanban.column_of(reference) == KanbanPage.IN_PROGRESS, (
            f"{reference} should still be in In Progress. "
            f"It is now in: '{self.kanban.column_of(reference)}'"
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
            f"Clicking a card should open the ticket. URL: {self.current_url()}"
        )
        self.detail.wait_until_loaded()
        assert self.detail.get_reference_number() == reference, (
            f"Clicking the card for {reference} opened "
            f"{self.detail.get_reference_number()} instead"
        )
