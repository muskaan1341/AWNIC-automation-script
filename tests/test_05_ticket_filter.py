"""
Filtering the ticket list.

The Filter button opens a drawer of dropdowns. Nothing changes on the list until
"Apply Filter" is pressed. Each applied value then shows as a chip under the toolbar.
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


class TestTicketFilter(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiries(self):
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
            assert level in options, f"Priority should offer '{level}'. Actual: {options}"

    def test_closing_the_drawer_without_applying_changes_nothing(self):
        self.open_enquiries()
        before = self.list.get_row_count()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.close_filter_drawer_without_applying()

        assert self.list.get_row_count() == before, "A filter that was not applied should change nothing"
        assert self.list.get_chip_count() == 0, "No chips should appear without Apply"

    # ---------- applying a filter ----------

    @pytest.mark.sanity
    def test_applying_a_filter_narrows_the_list_and_shows_a_chip(self):
        # Compare the total count, not the rows on screen (a page shows max 10 rows).
        self.open_enquiries()
        before = self.list.get_reported_result_count()

        self.list.open_filter_drawer()
        chosen = self.list.select_first_filter_value("Priority")
        self.list.apply_filters()

        self.wait.until(lambda d: self.list.get_chip_count() > 0)

        assert self.list.get_chip_count() == 1, "One chosen value should give one chip"
        assert chosen in self.list.get_chip_labels()[0], (
            f"The chip should show the picked value. Chips: {self.list.get_chip_labels()}"
        )
        assert self.list.get_reported_result_count() <= before, (
            f"A filter should not increase the count. Before: {before}, "
            f"after: {self.list.get_reported_result_count()}"
        )

    @pytest.mark.sanity
    def test_every_row_matches_the_filter_that_was_applied(self):
        self.open_enquiries()

        self.list.open_filter_drawer()
        chosen = self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() > 0)

        for value in self.list.get_column_values("Priority"):
            assert value == chosen, f"A row with priority '{value}' is shown for a '{chosen}' filter"

    def test_two_filters_give_two_chips_and_a_count_badge(self):
        self.open_enquiries()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.select_first_filter_value("Status")
        self.list.apply_filters()

        self.wait.until(lambda d: self.list.get_chip_count() == 2)
        assert self.list.get_chip_count() == 2, "Two chosen values should give two chips"
        assert self.list.get_active_filter_count() == 2, "The Filter button should show 2"

    # ---------- removing filters ----------

    def test_removing_a_chip_widens_the_list_again(self):
        # Compare the total count, not the rows on screen (a page shows max 10 rows).
        self.open_enquiries()
        unfiltered = self.list.get_reported_result_count()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        chip_label = self.list.get_chip_labels()[0]
        self.list.remove_chip(chip_label)
        # Wait for the list to reload too, not only for the chip to go.
        self.wait.until(
            lambda d: self.list.get_chip_count() == 0
            and self.list.get_reported_result_count() == unfiltered
        )

        assert self.list.get_reported_result_count() == unfiltered, (
            f"Removing the chip should restore the full list. Expected {unfiltered}, "
            f"now: {self.list.get_reported_result_count()}"
        )

    def test_clear_all_removes_every_filter_at_once(self):
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
            f"Expected {unfiltered} tickets, got {self.list.get_reported_result_count()}"
        )

    # ---------- filters and the rest of the screen ----------

    def test_a_filtered_list_can_be_shared_as_a_link(self):
        """The applied filter is in the URL, so opening that URL shows the same list."""
        self.open_enquiries()

        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        shared_link = self.current_url()
        assert "priority" in shared_link, f"The filter should be in the URL. Actual: {shared_link}"

        filtered_total = self.list.get_reported_result_count()
        self.driver.get(shared_link)
        self.list.wait_until_loaded()

        assert self.list.get_reported_result_count() == filtered_total, (
            f"The link should show the same list: expected {filtered_total}, "
            f"got {self.list.get_reported_result_count()}"
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
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        assert self.list.get_chip_count() == 1, "Going back should keep the filter"

    def test_a_combination_with_no_matches_shows_a_helpful_message(self):
        self.open_enquiries()

        # Apply a filter, then search for something that does not exist.
        self.list.open_filter_drawer()
        self.list.select_first_filter_value("Priority")
        self.list.apply_filters()
        self.wait.until(lambda d: self.list.get_chip_count() == 1)

        self.list.search("zzz-no-such-ticket-zzz")
        self.list.wait_for_empty_state()

        assert "match your filters" in self.list.get_empty_state_text().lower(), (
            f"The empty message should mention the filters. Actual: {self.list.get_empty_state_text()}"
        )
