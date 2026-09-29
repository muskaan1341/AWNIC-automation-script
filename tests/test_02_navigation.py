"""
MODULE 01 (part 2) and MODULE 14 - The menu, the top bar and notifications.

THE MENU HAS THREE SHAPES, and which one you get depends on your role. This trips people up
constantly, so it is worth stating plainly:

  a role that CONFIGURES things (Head of Department, Complaints Manager)
      gets a collapsible "Tickets" GROUP with Enquiries / Complaints / Discarded inside it

  a role that sees SEVERAL ticket types but configures nothing (CC Agent, Supervisor)
      gets FLAT entries: "Enquiries Tickets", "Complaint Tickets", "Discarded Tickets"

  a role that sees exactly ONE type (Complaint Handler)
      gets a single "Tickets" link, because a group of one is pointless

So a test that asserts "the menu contains 'Enquiries Tickets'" is only correct for the
middle shape. Assert the SHAPE that matches the role you signed in as.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P1 role-shaped nav — the menu must mirror the role's actual grants
pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]



class TestNavigation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        """Was @BeforeClass(dependsOnMethods = "openBrowser")."""
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_menu_as(self, email_key: str) -> None:
        self.login_once(self.get(email_key))
        self.open("/")
        self.nav.wait_until_loaded()

    # ---------- the three menu shapes ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_an_agent_gets_flat_ticket_entries(self):
        self.open_menu_as("agentEmail")

        assert not self.nav.has_tickets_group(), (
            "An agent configures nothing, so the queues are flat entries, not a group"
        )
        assert self.nav.has_item("Enquiries Tickets"), "Enquiries entry missing"
        assert self.nav.has_item("Complaint Tickets"), "Complaints entry missing"
        assert self.nav.has_item("Discarded Tickets"), "Discarded entry missing"

    def test_a_head_of_department_gets_the_collapsible_tickets_group(self):
        self.open_menu_as("hodEmail")

        assert self.nav.has_tickets_group(), (
            "A configuring role gets the collapsible 'Tickets' group"
        )

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

        assert self.nav.has_item("Tickets"), (
            "A role with one visible type gets a single 'Tickets' link"
        )
        assert not self.nav.has_item("Enquiries Tickets"), (
            "...and definitely not a queue they cannot see"
        )

    @pytest.mark.sanity
    def test_an_administrators_dashboard_link_points_at_the_admin_dashboard(self):
        self.login_once(self.get("adminEmail"))
        self.open("/admin")
        self.nav.wait_until_loaded()

        assert self.nav.dashboard_href().endswith("/admin"), (
            "An administrator has no ticket dashboard, so their Dashboard link should go to "
            f"/admin. Actual: {self.nav.dashboard_href()}"
        )

    def test_nothing_is_greyed_out_for_any_role(self):
        for role in ["agentEmail", "hodEmail", "adminEmail", "complaintHandlerEmail"]:
            self.open_menu_as(role)
            assert self.nav.disabled_item_count() == 0, (
                "Every rendered menu entry should be a working link. Disabled for "
                f"{self.get(role)}: {self.nav.disabled_item_labels()}"
            )

    @pytest.mark.sanity
    def test_a_role_is_offered_only_the_menu_entries_its_permissions_allow(self):
        """
        The menu is built from CAPABILITY KEYS, so two roles get two different shapes - and it
        is WHICH entries differ that matters.

        WHAT THIS USED TO ASSERT: `admin_menu != agent_menu` - that the two lists were not
        identical. One entry differing anywhere satisfied it, so an administrator offered every
        ticket queue, or an agent offered User Management, passed just as happily. The menu is
        the advisory half of the RBAC model (docs/rbac.md: the API is the boundary, the UI
        mirrors it), and an entry offered to somebody who cannot use it is exactly what that
        mirror is supposed to prevent.

        Each item in SideNav declares the keys it needs (`requires`): the administration
        entries want MANAGE_USERS_ORG_WIDE, which a CC Initiator does not hold, and the ticket
        queues want the ticket-type keys, which the platform admin does not hold.
        """
        administration = [
            "User Management",
            "Role Management",
            "Activity",
            "Audit Trail",
            "Access Management",
        ]

        self.open_menu_as("agentEmail")
        agent_menu = self.nav.all_item_labels()
        for queue in ["Enquiries Tickets", "Complaint Tickets", "Discarded Tickets"]:
            assert self.nav.has_item(queue), (
                f"A CC Initiator works every queue, so '{queue}' should be offered. "
                f"Menu: {agent_menu}"
            )
        offered_to_agent = [entry for entry in administration if self.nav.has_item(entry)]
        assert not offered_to_agent, (
            "A CC Initiator administers nothing, so these must not be offered at all: "
            f"{offered_to_agent}"
        )

        self.open_menu_as("adminEmail")
        admin_menu = self.nav.all_item_labels()
        for entry in ["User Management", "Role Management"]:
            assert self.nav.has_item(entry), (
                f"The platform administrator manages people, so '{entry}' should be offered. "
                f"Menu: {admin_menu}"
            )
        assert self.nav.has_no_ticket_queues(), (
            "The platform administrator holds no ticket capability, so no queue may be "
            f"offered. Menu: {admin_menu}"
        )

        assert admin_menu != agent_menu, (
            "...and the two menus must therefore not be identical. "
            f"Agent: {agent_menu}. Admin: {admin_menu}"
        )

    # ---------- the breadcrumb ----------
    #
    # THE BREADCRUMB MIRRORS THE MENU, and both depend on your role.
    #
    # An agent's queues are flat entries, so their trail starts with the flat label,
    # "Enquiries Tickets". A Head of Department's queues live inside a "Tickets" group, so
    # their trail starts "Tickets / Enquiries" instead. Keeping the two in step matters: a
    # breadcrumb that names a menu item the user does not have is simply confusing.

    def test_the_breadcrumb_starts_with_the_agents_flat_queue_label(self):
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        trail = self.top_bar.get_breadcrumb_labels()
        assert "Enquiries Tickets" in trail, (
            f"An agent's menu uses the flat label, so their breadcrumb should too. Trail: {trail}"
        )

    def test_a_head_of_departments_breadcrumb_uses_the_grouped_shape(self):
        self.login_once(self.get("hodEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        trail = self.top_bar.get_breadcrumb_labels()
        assert "Tickets" in trail, (
            f"A grouped menu should give a 'Tickets' crumb first. Trail: {trail}"
        )
        assert "Enquiries" in trail, f"...then the queue's grouped label. Trail: {trail}"

    def test_opening_a_ticket_adds_its_reference_to_the_breadcrumb(self):
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()

        # The reference of the row that ACTUALLY opened. Reading row 1 separately was wrong
        # whenever row 1 is inert - a merged duplicate is deliberately unopenable, so
        # open_first_row() skips it and opens the next ticket, and the breadcrumb then names
        # that one. Taking the reference from the click itself keeps the two in step.
        reference = self.list.open_first_row()
        self.detail.wait_until_loaded()

        assert reference in self.top_bar.get_breadcrumb_labels(), (
            f"The open ticket should be the last crumb. "
            f"Trail: {self.top_bar.get_breadcrumb_labels()}"
        )

    # ---------- the top bar ----------



