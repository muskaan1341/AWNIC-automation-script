"""
The side menu and the breadcrumb.

The menu shape depends on the role:
  - Head of Department / Complaints Manager: a collapsible "Tickets" group
  - CC Initiator / Supervisor: flat entries ("Enquiries Tickets", "Complaint Tickets", ...)
  - Complaint Handler (one ticket type): a single "Tickets" link
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


class TestNavigation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("ccInitiatorEmail"))

    def open_menu_as(self, email_key):
        self.login_once(self.get(email_key))
        self.open("/")
        self.nav.wait_until_loaded()

    # ---------- the three menu shapes ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_a_cc_initiator_gets_flat_ticket_entries(self):
        self.open_menu_as("ccInitiatorEmail")

        assert not self.nav.has_tickets_group(), "A CC Initiator should get flat entries, not a group"
        assert self.nav.has_item("Enquiries Tickets"), "Enquiries entry missing"
        assert self.nav.has_item("Complaint Tickets"), "Complaints entry missing"
        assert self.nav.has_item("Discarded Tickets"), "Discarded entry missing"

    def test_a_head_of_department_gets_the_collapsible_tickets_group(self):
        self.open_menu_as("hodEmail")

        assert self.nav.has_tickets_group(), "A Head of Department should get the 'Tickets' group"

    def test_the_tickets_group_opens_and_closes(self):
        self.open_menu_as("hodEmail")

        was_expanded = self.nav.is_tickets_group_expanded()
        self.nav.toggle_tickets_group()
        self.wait.until(lambda d: self.nav.is_tickets_group_expanded() != was_expanded)

        assert self.nav.is_tickets_group_expanded() != was_expanded, (
            "Clicking the group header should open or close it"
        )

    def test_a_single_queue_role_gets_one_tickets_link(self):
        self.open_menu_as("complaintHandlerEmail")

        assert self.nav.has_item("Tickets"), "A one-type role should get a single 'Tickets' link"
        assert not self.nav.has_item("Enquiries Tickets"), "Enquiries entry should not be shown"

    @pytest.mark.sanity
    def test_an_administrators_dashboard_link_points_at_the_admin_dashboard(self):
        self.login_once(self.get("adminEmail"))
        self.open("/admin")
        self.nav.wait_until_loaded()

        assert self.nav.dashboard_href().endswith("/admin"), (
            f"Admin's Dashboard link should go to /admin. Actual: {self.nav.dashboard_href()}"
        )

    def test_nothing_is_greyed_out_for_any_role(self):
        for role in ["ccInitiatorEmail", "hodEmail", "adminEmail", "complaintHandlerEmail"]:
            self.open_menu_as(role)
            assert self.nav.disabled_item_count() == 0, (
                f"Disabled menu items for {self.get(role)}: {self.nav.disabled_item_labels()}"
            )

    @pytest.mark.sanity
    def test_a_role_is_offered_only_the_menu_entries_its_permissions_allow(self):
        """A CC Initiator gets the ticket queues but no admin pages; an admin gets the opposite."""
        administration = [
            "User Management",
            "Role Management",
            "Activity",
            "Audit Trail",
            "Access Management",
        ]

        # CC Initiator
        self.open_menu_as("ccInitiatorEmail")
        initiator_menu = self.nav.all_item_labels()
        for queue in ["Enquiries Tickets", "Complaint Tickets", "Discarded Tickets"]:
            assert self.nav.has_item(queue), f"CC Initiator should see '{queue}'. Menu: {initiator_menu}"

        offered_to_initiator = []
        for entry in administration:
            if self.nav.has_item(entry):
                offered_to_initiator.append(entry)
        assert not offered_to_initiator, f"CC Initiator should not see admin entries: {offered_to_initiator}"

        # Admin
        self.open_menu_as("adminEmail")
        admin_menu = self.nav.all_item_labels()
        for entry in ["User Management", "Role Management"]:
            assert self.nav.has_item(entry), f"Admin should see '{entry}'. Menu: {admin_menu}"
        assert self.nav.has_no_ticket_queues(), (
            f"Admin should not see any ticket queue. Menu: {admin_menu}"
        )

        assert admin_menu != initiator_menu, (
            f"The two menus should differ. CC Initiator: {initiator_menu}. Admin: {admin_menu}"
        )

    # ---------- the breadcrumb ----------
    # The breadcrumb follows the menu shape: a CC Initiator sees "Enquiries Tickets",
    # a Head of Department sees "Tickets / Enquiries".

    def test_the_breadcrumb_starts_with_the_cc_initiators_flat_queue_label(self):
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        trail = self.top_bar.get_breadcrumb_labels()
        assert "Enquiries Tickets" in trail, f"Breadcrumb: {trail}"

    def test_a_head_of_departments_breadcrumb_uses_the_grouped_shape(self):
        self.login_once(self.get("hodEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        trail = self.top_bar.get_breadcrumb_labels()
        assert "Tickets" in trail, f"Breadcrumb should start with 'Tickets': {trail}"
        assert "Enquiries" in trail, f"Breadcrumb should include 'Enquiries': {trail}"

    def test_opening_a_ticket_adds_its_reference_to_the_breadcrumb(self):
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        # open_first_row() returns the reference of the ticket it actually opened
        # (it skips merged duplicates, which cannot be opened).
        reference = self.list.open_first_row()
        self.detail.wait_until_loaded()

        assert reference in self.top_bar.get_breadcrumb_labels(), (
            f"Breadcrumb should end with the ticket. Trail: {self.top_bar.get_breadcrumb_labels()}"
        )
