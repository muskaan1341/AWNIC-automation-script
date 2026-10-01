"""
The dashboard at "/".

Checks the KPI tiles, that their numbers agree, and the Recent Ticket card.
"""

import re

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.dashboard_page import DashboardPage

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


class TestDashboard(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_dashboard(self):
        self.open("/")
        self.dashboard.wait_until_loaded()

    # ---------- the tiles ----------

    @pytest.mark.regression
    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_all_five_kpi_tiles_are_shown(self):
        self.open_dashboard()

        for label in DashboardPage.ORG_KPIS:
            assert self.dashboard.is_kpi_displayed(label), f"KPI tile missing: {label}"

    @pytest.mark.regression
    def test_kpi_tiles_show_real_numbers(self):
        self.open_dashboard()

        total = self.dashboard.get_kpi_value("Total Ticket")
        assert re.fullmatch(r"\d+", total), f"'Total Ticket' should be a number, got: '{total}'"
        assert int(total) > 0, "The total should not be 0"

    @pytest.mark.api_candidate
    def test_the_numbers_agree_with_each_other(self):
        self.open_dashboard()

        total = self.dashboard.get_kpi_number("Total Ticket")

        # Each of these tiles counts part of all tickets, so none can be bigger than the total.
        for subset in ["Open Cases", "High Priority", "Reputational Risk", "SLA Breaches"]:
            value = self.dashboard.get_kpi_number(subset)
            assert value <= total, f"{subset} ({value}) is more than Total Ticket ({total})"

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_clicking_a_tile_opens_the_tickets_behind_it(self):
        """The 'Open Cases' tile opens its own filtered list."""
        self.open_dashboard()

        assert self.dashboard.is_kpi_clickable("Open Cases"), "The KPI tile should be a link"
        href = self.dashboard.get_kpi_href("Open Cases")
        assert href.endswith("/tickets/list?view=open-cases"), f"Wrong tile link: {href}"

        self.dashboard.click_kpi("Open Cases")
        self.wait.until(lambda d: "view=open-cases" in d.current_url)
        self.list.wait_until_loaded()

        assert "/tickets/list?view=open-cases" in self.current_url(), (
            f"Should open the Open Cases list. Actual: {self.current_url()}"
        )
        assert not self.is_page_not_found(), "Should not show the 'not found' page"

    # ---------- the Recent Ticket card ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_recent_tickets_card_is_shown_with_its_type_tabs(self):
        self.open_dashboard()

        assert self.dashboard.is_recent_tickets_card_displayed(), "'Recent Ticket' card missing"
        assert self.dashboard.has_recent_tickets_tab("Enquiry"), "Enquiry tab missing"
        assert self.dashboard.has_recent_tickets_tab("Complaint"), "Complaint tab missing"
        assert self.dashboard.has_recent_tickets_tab("Discarded"), "Discarded tab missing"

    @pytest.mark.regression
    def test_view_all_link_on_recent_tickets_opens_a_working_page(self):
        """'View All' opens a real page (was defect TC-DASH-009)."""
        self.open_dashboard()

        href = self.dashboard.view_all_href()
        assert not href.endswith("/tickets"), f"'View All' points at the old /tickets route: {href}"

        self.dashboard.click_view_all()
        self.wait.until(lambda d: d.current_url != self.base_url + "/")

        assert not self.is_page_not_found(), (
            f"'View All' opened 'Page not found'. URL: {self.current_url()}"
        )

    @pytest.mark.quarantine("unexplained-2026-09-09")
    def test_switching_recent_ticket_tab_changes_the_view_all_target(self):
        self.open_dashboard()

        if not self.dashboard.has_recent_tickets_tab("Complaint"):
            pytest.skip("This role cannot see complaints.")
        self.dashboard.open_recent_tickets_tab("Complaint")
        self.wait.until(lambda d: "/tickets/complaints" in self.dashboard.view_all_href())

        assert "/tickets/complaints" in self.dashboard.view_all_href(), (
            f"View All should open the complaints list. Actual: {self.dashboard.view_all_href()}"
        )

    # ---------- the menu ----------

    @pytest.mark.regression
    def test_clicking_enquiries_in_the_menu_opens_the_enquiries_list(self):
        self.open("/")
        self.nav.wait_until_loaded()
        self.nav.click_item("Enquiries Tickets")

        self.wait_for_url_containing("/tickets/enquiries")
        assert "/tickets/enquiries" in self.current_url(), f"Actual URL: {self.current_url()}"
