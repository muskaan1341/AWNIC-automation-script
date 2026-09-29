"""
MODULE 05 (part 2) - Filtering the ticket list.

HOW THE FILTER DRAWER WORKS, because it is not obvious:
  - the Filter button opens a side drawer with nine dropdowns,
  - each dropdown is MULTI-choice, so picking a value does not close it,
  - NOTHING changes on the list until you press "Apply Filter". "Reset" clears the drawer,
    and closing the drawer without applying throws the draft away,
  - once applied, each chosen value becomes its own removable chip under the toolbar, and
    the Filter button grows a count badge.

That "nothing happens until Apply" design is the reason a test can safely pick several
values in a row without waiting for the list to reload between them.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Ticket list search/filter'
pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]



class TestTicketFilter(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiries(self) -> None:
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

    # ---------- the drawer itself ----------

    @pytest.mark.sanity
    def test_the_filter_drawer_offers_every_agreed_filter(self):
        self.open_enquiries()
        self.list.open_filter_drawer()

        expected = [
            "Priority",
            "Status",
            "Department",
            "Source",
            "Type",
            "Enquiry",
            "Sub Enquiry",
            "Duplicate",
            "SLA Status",
        ]
        for filter_name in expected:
            assert filter_name in self.list.visible_filter_names(), (
                f"Filter '{filter_name}' is missing. Present: {self.list.visible_filter_names()}"
            )

    def test_priority_offers_the_agreed_values(self):
        self.open_enquiries()
        self.list.open_filter_drawer()

        options = self.list.filter_options("Priority")
        for level in ["Low", "Medium", "High"]:
            assert level in options, (
                f"Priority should offer '{level}'. Actual: {options}"
            )

    def test_closing_the_drawer_without_applying_changes_nothing(self):
        self.open_enquiries()
        before = self.list.get_row_count()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.close_filter_drawer_without_applying()

        assert self.list.get_row_count() == before, (
            "A filter that was never applied must not change the list"
        )
        assert self.list.get_chip_count() == 0, "No chips should appear without Apply"

    # ---------- applying a filter ----------

    @pytest.mark.sanity
    def test_applying_a_filter_narrows_the_list_and_shows_a_chip(self):
        # The REPORTED total, not the rows on screen: the list shows ten a page, so with more
        # than ten enquiries "rows after <= rows before" compared 10 with at most 10 and could
        # not fail - even for a filter that widened the set.
        self.open_enquiries()
        before = self.list.get_reported_result_count()

        self.list.open_filter_drawer()
        chosen = self.list.select_first_filter_value("Priority")
        self.list.apply_filters()

        self.wait.until(lambda d: self.list.get_chip_count() > 0)

        assert self.list.get_chip_count() == 1, (
            "One chosen value should give exactly one chip"
        )
        assert chosen in self.list.get_chip_labels()[0], (
            f"The chip should name the value that was picked. Chips: {self.list.get_chip_labels()}"
        )
        assert self.list.get_reported_result_count() <= before, (
            f"A filter can only ever narrow the list, never widen it. Before: {before}, "
            f"after: {self.list.get_reported_result_count()}"
        )

    @pytest.mark.sanity
    def test_every_row_matches_the_filter_that_was_applied(self):
        self.open_enquiries()

        self.list.open_filter_drawer()
        chosen = self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() > 0)

        # The real test of a filter is not that the count changed - it is that every row left
        # behind actually matches.
        for value in self.list.get_column_values("Priority"):
            assert value == chosen, (
                f"A row with priority '{value}' survived a '{chosen}' filter"
            )

    def test_two_filters_give_two_chips_and_a_count_badge(self):
        self.open_enquiries()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.select_first_filter_value("Status")
        self.list.apply_filters()

        self.wait.until(lambda d: self.list.get_chip_count() == 2)
        assert self.list.get_chip_count() == 2, "Two chosen values should give two chips"
        assert self.list.get_active_filter_count() == 2, (
            "The Filter button should show how many filters are active"
        )

    # ---------- removing filters ----------

    def test_removing_a_chip_widens_the_list_again(self):
        # Reported totals, not rows on screen: with more than ten matches either way, a page
        # of ten rows looks identical filtered or not, so the old row-count check passed even
        # if removing the chip left the filter in force.
        self.open_enquiries()
        unfiltered = self.list.get_reported_result_count()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        chip_label = self.list.get_chip_labels()[0]
        self.list.remove_chip(chip_label)
        # Wait for the LIST to come back, not just for the chip to vanish. The chip goes the
        # instant it is clicked; the rows take another round trip to the server.
        self.wait.until(
            lambda d: self.list.get_chip_count() == 0
            and self.list.get_reported_result_count() == unfiltered
        )

        assert self.list.get_reported_result_count() == unfiltered, (
            "Removing the only chip should restore the full list. Unfiltered total: "
            f"{unfiltered}, now: {self.list.get_reported_result_count()}"
        )

    def test_clear_all_removes_every_filter_at_once(self):
        # Reported totals for the same reason as above: rows on screen cap at ten.
        self.open_enquiries()
        unfiltered = self.list.get_reported_result_count()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.select_first_filter_value("Status")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 2)

        self.list.clear_all_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 0)

        assert self.list.get_active_filter_count() == 0, "The count badge should be gone"
        self.wait.until(lambda d: self.list.get_reported_result_count() == unfiltered)
        assert self.list.get_reported_result_count() == unfiltered, (
            f"The full list should be back: {unfiltered} tickets, not "
            f"{self.list.get_reported_result_count()}"
        )

    # ---------- filters and the rest of the screen ----------

    def test_a_filtered_list_can_be_shared_as_a_link(self):
        """
        A filtered list must be shareable as a link. The chosen values go into the URL, so
        pasting that URL to a colleague shows them the same view - which is exactly how
        supervisors hand work over.
        """
        self.open_enquiries()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        shared_link = self.current_url()
        assert "priority" in shared_link, (
            "The applied filter should be in the URL so the view can be shared. "
            f"Actual: {shared_link}"
        )

        # The filtered TOTAL, not the rows on screen - a full page of ten looks the same
        # whether or not the link actually re-applied the filter.
        filtered_total = self.list.get_reported_result_count()
        self.driver.get(shared_link)
        self.list.wait_until_loaded()

        assert self.list.get_reported_result_count() == filtered_total, (
            "Re-opening the shared link should show the same filtered list: "
            f"{filtered_total} tickets, not {self.list.get_reported_result_count()}"
        )
        assert self.list.get_chip_count() == 1, "The chip should come back with the link"

    def test_filters_survive_opening_a_ticket_and_coming_back(self):
        self.open_enquiries()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        self.list.open_first_row()
        self.wait_for_ticket_detail_url()

        self.driver.back()
        self.list.wait_until_loaded()
        # The filter lives in the URL, so Back restores it - but the chips are rendered from
        # that URL after the page settles, so wait for them rather than reading too early.
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        assert self.list.get_chip_count() == 1, (
            "Going back to the list should keep the filter you were working with"
        )

    def test_a_combination_with_no_matches_shows_a_helpful_message(self):
        self.open_enquiries()

        # Search for something impossible on top of a filter - a guaranteed empty result.
        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        assert "match your filters" in self.list.get_empty_state_text().lower(), (
            "An empty filtered list should say the filters are why. "
            f"Actual: {self.list.get_empty_state_text()}"
        )
