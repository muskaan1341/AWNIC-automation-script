"""
MODULE 15 (part 1) - The dashboard at "/".

This is the screen a Customer Care agent lands on after signing in, so it is the first thing
anyone sees every morning. The tests below check that the numbers are real, that they agree
with each other, and that clicking one takes you to the tickets behind it.

Signs in ONCE for the whole class; every test then navigates to the page it needs.
"""

from __future__ import annotations

import re

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.dashboard_page import DashboardPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B core UI — the landing screen every agent starts from
pytestmark = [pytest.mark.p1, pytest.mark.phase1]



class TestDashboard(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_dashboard(self) -> None:
        """Shared first step - every test in this class begins here."""
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
        assert re.fullmatch(r"\d+", total), (
            f"'Total Ticket' should show a plain number, but showed: '{total}'"
        )
        assert int(total) > 0, (
            "The seeded database has tickets, so the total should not be 0"
        )

    @pytest.mark.api_candidate
    def test_the_numbers_agree_with_each_other(self):
        self.open_dashboard()

        total = self.dashboard.get_kpi_number("Total Ticket")

        # Each of these counts a subset of all tickets, so none of them can ever be bigger
        # than the total. A figure that IS bigger means the tiles are counting different
        # populations, which is the classic dashboard bug - and it is a REAL risk here rather
        # than a theoretical one: "SLA Breaches" is read from slaBreachStats while the other
        # four come from stats (lib/dashboard-layout.ts's dashboardKpis), so two sources have
        # to agree on screen.
        #
        # LATER: the exact arithmetic belongs to the stats endpoint (see the coverage matrix's
        # API list). Keep this cross-tile invariant here until that lands - it is the only
        # check that the ASSEMBLED dashboard is coherent, which an API test cannot see.
        for subset in ["Open Cases", "High Priority", "Reputational Risk", "SLA Breaches"]:
            value = self.dashboard.get_kpi_number(subset)
            assert value <= total, (
                f"{subset} ({value}) cannot be more than Total Ticket ({total})"
            )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_clicking_a_tile_opens_the_tickets_behind_it(self):
        """
        A KPI tile drills into ITS OWN filtered list, not just "a ticket page".

        Every tile links to `/tickets/list?view=<its id>` (dashboardViewHref), which is what
        makes the number on it answerable - press "Open Cases" and you get the open cases, not
        the whole queue. The old assertion only checked the address contained "/tickets", which
        is equally true of the unfiltered list, a ticket detail page, and the enquiries queue -
        so a tile wired to the wrong view, or to no view at all, passed.
        """
        self.open_dashboard()

        assert self.dashboard.is_kpi_clickable("Open Cases"), (
            "A KPI tile should be a link that drills into its own filtered list"
        )
        href = self.dashboard.get_kpi_href("Open Cases")
        assert href.endswith("/tickets/list?view=open-cases"), (
            "The 'Open Cases' tile must point at its own view of the cross-type list. "
            f"Actual: {href}"
        )

        self.dashboard.click_kpi("Open Cases")
        self.wait.until(lambda d: "view=open-cases" in d.current_url)
        self.list.wait_until_loaded()

        assert "/tickets/list?view=open-cases" in self.current_url(), (
            f"Clicking 'Open Cases' should open that filtered list. Actual: {self.current_url()}"
        )
        assert not self.is_page_not_found(), (
            "The tile's own view must be a real page, not the 'not found' screen"
        )

    # ---------- the Recent Ticket card ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_recent_tickets_card_is_shown_with_its_type_tabs(self):
        self.open_dashboard()

        assert self.dashboard.is_recent_tickets_card_displayed(), (
            "The 'Recent Ticket' card should be on the dashboard"
        )
        # An agent can see all three ticket types, so all three tabs should be offered.
        assert self.dashboard.has_recent_tickets_tab("Enquiry"), "Enquiry tab missing"
        assert self.dashboard.has_recent_tickets_tab("Complaint"), "Complaint tab missing"
        assert self.dashboard.has_recent_tickets_tab("Discarded"), "Discarded tab missing"

    @pytest.mark.regression
    def test_view_all_link_on_recent_tickets_opens_a_working_page(self):
        """
        This one used to FAIL on purpose.

        "View All" pointed at /tickets, a route that no longer exists - it was split into
        /tickets/enquiries and /tickets/complaints - so the link landed on "Page not found".
        It was tracked as defect TC-DASH-009 and the assertion was deliberately never
        weakened to make the suite green.

        The application has since been fixed: each tab now carries its own View All link.
        The test is unchanged and should now PASS. If it ever goes red again, the same
        regression has come back.
        """
        self.open_dashboard()

        href = self.dashboard.view_all_href()
        assert not href.endswith("/tickets"), (
            f"'View All' must not point at the retired /tickets route. Actual: {href}"
        )

        self.dashboard.click_view_all()
        self.wait.until(lambda d: d.current_url != self.base_url + "/")

        assert not self.is_page_not_found(), (
            f"'View All' landed on the 'Page not found' screen. Actual URL: {self.current_url()}"
        )

    @pytest.mark.quarantine("unexplained-2026-09-09")
    def test_switching_recent_ticket_tab_changes_the_view_all_target(self):
        self.open_dashboard()

        if not self.dashboard.has_recent_tickets_tab("Complaint"):
            pytest.skip("This role cannot see complaints, so the tab is correctly not offered.")
        self.dashboard.open_recent_tickets_tab("Complaint")
        self.wait.until(lambda d: "/tickets/complaints" in self.dashboard.view_all_href())

        assert "/tickets/complaints" in self.dashboard.view_all_href(), (
            "Once the Complaint tab is selected, its View All should open the complaints "
            f"list. Actual: {self.dashboard.view_all_href()}"
        )

    # ---------- the menu around it ----------




    @pytest.mark.regression
    def test_clicking_enquiries_in_the_menu_opens_the_enquiries_list(self):
        self.open("/")
        self.nav.wait_until_loaded()
        self.nav.click_item("Enquiries Tickets")

        self.wait_for_url_containing("/tickets/enquiries")
        assert "/tickets/enquiries" in self.current_url(), f"Actual URL: {self.current_url()}"
