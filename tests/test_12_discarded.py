"""
MODULE 07 (part 2) - The Discarded queue.

WHAT "DISCARDED" MEANS HERE: junk that arrived in the mailbox - marketing email, spam, a
message meant for somebody else. It is moved out of the working queues so it stops polluting
the SLA figures, but it is NEVER deleted. Everything about it is kept, and it can be brought
back if the decision turns out to be wrong.

TWO THINGS THAT SURPRISE PEOPLE:
  1. A RESTORED ticket stays on this list forever, badged "Restored", so the record of the
     mistake survives. It just loses its action menu, because restoring it again makes no
     sense.
  2. A restored row shows the number it was DISCARDED under, not the new number it now has -
     so that a customer quoting the old number can still be traced.

This screen is a DIFFERENT table from the enquiries list, with only five columns.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.discarded_list_page import DiscardedListPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Discard a ticket — moves correctly, shows in the separate Discarded list'
pytestmark = [pytest.mark.p1, pytest.mark.phase1]



class TestDiscarded(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_discarded(self) -> None:
        # Names its own role on purpose: two tests in this class sign in as a complaint
        # handler. pytest runs methods in DEFINITION order, so those two come last here - but
        # login_once is free when the right person is already signed in, and it keeps this
        # helper correct however the file is later reordered.
        self.login_once(self.get("supervisorEmail"))
        # Say WHY when this account has no role, instead of waiting 20 seconds for a heading
        # that is never coming. See BaseTest.require_ticket_access.
        self.require_ticket_access("supervisorEmail")
        self.open("/tickets/discarded")
        self.discarded.wait_until_loaded()

    # ---------- the list ----------

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_it_has_its_own_five_columns_not_the_ticket_lists_eighteen(self):
        self.open_discarded()

        headers = self.discarded.get_column_headers()
        for expected in DiscardedListPage.EXPECTED_COLUMNS:
            assert expected in headers, (
                f"Column '{expected}' is missing. Columns found: {headers}"
            )
        assert "Current Handler" not in headers, (
            "Discarded junk has no handler, so that column belongs to the other list"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_discarded_items_carry_the_junk_reference_prefix(self):
        self.open_discarded()

        if self.discarded.get_row_count() == 0:
            pytest.skip("Nothing discarded in the seed data. Run 'make seed-demo'.")
        # A restored row deliberately shows its OLD discarded number, so every row on this
        # screen should carry the junk prefix, restored or not.
        for reference in self.discarded.get_reference_numbers():
            assert reference.startswith("JNK-"), (
                f"A discarded item should show a JNK- number, but showed: {reference}"
            )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_the_search_box_says_what_it_actually_searches(self):
        self.open_discarded()

        hint = self.discarded.get_search_placeholder().lower()
        assert "sender" in hint and "subject" in hint, (
            f"The search hint should tell the tester which fields are covered. Actual: {hint}"
        )

    @pytest.mark.quarantine("unexplained-2026-09")
    @pytest.mark.blocked("cc_supervisor")
    def test_search_narrows_the_discarded_list(self):
        self.open_discarded()

        if self.discarded.get_row_count() < 2:
            pytest.skip("Need at least two discarded items for this to mean anything.")
        target = self.discarded.get_reference_numbers()[0]
        self.discarded.search(target)
        self.discarded.wait_for_row_count(1)

        assert self.discarded.get_reference_numbers() == [target], (
            "Searching a reference number should leave only that row"
        )

    # ---------- restoring ----------

    def _first_restorable_row(self) -> int:
        """The first row that has not already been restored."""
        for row in range(self.discarded.get_row_count()):
            if self.discarded.row_has_action_menu(row):
                return row
        pytest.skip("Every discarded row has already been restored.")

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_the_row_menu_offers_restoring_as_either_type(self):
        """
        Restoring must be a CHOICE, not an automatic guess. A discarded message could turn
        out to be either an enquiry or a complaint, and only a person can tell which - so the
        menu offers both, and neither happens by itself.
        """
        self.open_discarded()

        row_to_use = self._first_restorable_row()
        self.discarded.open_row_menu(row_to_use)

        offered = self.discarded.get_open_menu_labels()
        assert any("Enquiry" in item for item in offered), (
            f"Restoring as an enquiry should be offered. Menu: {offered}"
        )
        assert any("Complaint" in item for item in offered), (
            f"Restoring as a complaint should be offered. Menu: {offered}"
        )

    @pytest.mark.regression
    @pytest.mark.blocked("cc_supervisor")
    def test_an_already_restored_row_stays_on_the_list_but_loses_its_actions(self):
        """
        A restored ticket stays on this list, badged "Restored", with NO action menu - and
        every row that is still junk keeps its menu. The badge and the menu are two readings
        of the same fact (DiscardedTicketListClient's isRestored), so they must agree on
        every row.

        WHAT THIS REPLACED: it looked for any row without a menu, then asserted that row had
        no menu - the inner check restated the `if` and could not fail. It never tied the
        menu-less row to the badged one, and "badged" meant the word "restored" appearing
        anywhere in any row, subject lines included.
        """
        self.open_discarded()

        restored = [
            row
            for row in range(self.discarded.get_row_count())
            if self.discarded.row_is_badged_restored(row)
        ]
        if not restored:
            pytest.skip(
                "No restored row on the first page of this list. "
                "Run apps/api/scripts/seed_discard_restore_demo.py."
            )

        references = self.discarded.get_reference_numbers()
        for row in range(self.discarded.get_row_count()):
            if row in restored:
                assert not self.discarded.row_has_action_menu(row), (
                    f"{references[row]} is badged Restored, so it must not offer restoring again"
                )
            else:
                assert self.discarded.row_has_action_menu(row), (
                    f"{references[row]} is not restored, so it must keep its action menu - "
                    "only a restored row loses it"
                )

    # ---------- who may see this queue at all ----------

