"""
Discarded queue tests.

Discarded tickets are junk (spam, wrong recipient). They are never deleted and can be
restored. A restored ticket stays on this list with a "Restored" badge and no action menu.
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.discarded_list_page import DiscardedListPage

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


class TestDiscarded(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_discarded(self, role_key="supervisorEmail"):
        self.login_once(self.get(role_key))
        self.require_ticket_access(role_key)
        self.open("/tickets/discarded")
        self.discarded.wait_until_loaded()

    # ---------- the list ----------

    @pytest.mark.regression
    def test_it_has_its_own_five_columns_not_the_ticket_lists_eighteen(self):
        self.open_discarded()

        headers = self.discarded.get_column_headers()
        for expected in DiscardedListPage.EXPECTED_COLUMNS:
            assert expected in headers, f"Column '{expected}' is missing. Columns: {headers}"
        assert "Current Handler" not in headers, (
            "The discarded list should not have a Current Handler column"
        )

    @pytest.mark.regression
    def test_discarded_items_carry_the_junk_reference_prefix(self):
        self.open_discarded()

        if self.discarded.get_row_count() == 0:
            pytest.skip("Nothing discarded in the seed data. Run 'make seed-demo'.")
        # Restored rows also show their old JNK- number.
        for reference in self.discarded.get_reference_numbers():
            assert reference.startswith("JNK-"), (
                f"A discarded item should show a JNK- number, but showed: {reference}"
            )

    @pytest.mark.regression
    def test_the_search_box_says_what_it_actually_searches(self):
        self.open_discarded()

        hint = self.discarded.get_search_placeholder().lower()
        assert "sender" in hint and "subject" in hint, (
            f"The search hint should mention sender and subject. Actual: {hint}"
        )

    @pytest.mark.quarantine("unexplained-2026-09")
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

    def _first_restorable_row(self):
        """The first row that has not already been restored."""
        for row in range(self.discarded.get_row_count()):
            if self.discarded.row_has_action_menu(row):
                return row
        pytest.skip("Every discarded row has already been restored.")

    @pytest.mark.regression
    def test_the_row_menu_offers_restoring_as_either_type(self):
        """The row menu offers restoring as an Enquiry and as a Complaint."""
        # Head of Department: the supervisor is not allowed to restore.
        self.open_discarded("hodEmail")

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
    def test_an_already_restored_row_stays_on_the_list_but_loses_its_actions(self):
        """Rows badged Restored have no action menu; every other row has one."""
        self.open_discarded()

        restored = []
        for row in range(self.discarded.get_row_count()):
            if self.discarded.row_is_badged_restored(row):
                restored.append(row)
        if not restored:
            pytest.skip("No restored row on the first page. Run apps/api/scripts/seed_discard_restore_demo.py.")

        references = self.discarded.get_reference_numbers()
        for row in range(self.discarded.get_row_count()):
            if row in restored:
                assert not self.discarded.row_has_action_menu(row), (
                    f"{references[row]} is Restored, so it must not have an action menu"
                )
            else:
                assert self.discarded.row_has_action_menu(row), (
                    f"{references[row]} is not restored, so it should have an action menu"
                )
