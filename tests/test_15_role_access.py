"""
Access control - who may see and do what.

Checks the menu each role gets AND that typing a forbidden URL directly is refused
(a hidden button alone is not protection).
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]


class TestRoleAccess(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def start_from_the_cc_initiator(self, request, browser):
        request.cls.login_class(request.cls.get("ccInitiatorEmail"))

    # ---------- complaint handler: only complaints assigned to them ----------

    def test_complaint_handler_sees_only_complaints_assigned_to_them(self):
        """Every complaint the Complaint Handler sees has them as its Department POC."""
        handler = self.get("complaintHandlerEmail")
        self.login_once(handler)
        self.require_ticket_access("complaintHandlerEmail")

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.is_empty_state_displayed():
            pytest.skip(f"{handler} has no complaints assigned, so there is nothing to check.")
        their_total = self.list.get_reported_result_count()
        references = self.list.get_reference_numbers()

        # Open each row and check whose complaint it is.
        for row, reference in enumerate(references):
            if row:
                self.open("/tickets/complaints")
                self.list.wait_until_loaded()
            self.list.open_row(row)
            self.wait_for_ticket_detail_url()
            self.detail.wait_until_loaded()

            assert self.detail.get_reference_number() == reference, (
                f"Row {row} was {reference} but {self.detail.get_reference_number()} opened"
            )
            assert self.detail.department_poc_email() == handler, (
                f"{handler} can see {reference}, whose Department POC is "
                f"'{self.detail.department_poc_email()}'"
            )

        # The CC Initiator sees all complaints, so the handler cannot have more.
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        organisation_wide = self.list.get_reported_result_count()

        assert their_total <= organisation_wide, (
            f"Handler sees {their_total} complaints but the CC Initiator sees only {organisation_wide}"
        )

    def test_complaint_handler_gets_no_scope_tabs(self):
        """The Complaint Handler gets no scope tab strip (they only have one view)."""
        self.login_once(self.get("complaintHandlerEmail"))
        self.require_ticket_access("complaintHandlerEmail")

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

        assert not self.list.has_tab_strip(), (
            f"A restricted-scope role should get no tabs. Tabs found: {self.list.get_tab_labels()}"
        )

    # ---------- head of department ----------

    def test_head_of_department_sees_the_administration_entries(self):
        self.login_once(self.get("hodEmail"))

        self.open("/")
        self.nav.wait_until_loaded()

        assert self.nav.has_item("Access Management"), (
            "A Head of Department should see Access Management"
        )
        assert self.nav.has_item("Audit Trail"), "A Head of Department should see Audit Trail"
        assert self.nav.has_tickets_group(), (
            "A Head of Department should get the collapsible 'Tickets' group"
        )

    @pytest.mark.sanity
    def test_head_of_department_does_not_get_the_organisation_wide_admin_screens(self):
        """Only the platform administrator gets User Management and Role Management."""
        self.login_once(self.get("hodEmail"))

        self.open("/")
        self.nav.wait_until_loaded()

        assert not self.nav.has_item("User Management"), (
            "User Management is for the platform administrator only"
        )
        assert not self.nav.has_item("Role Management"), (
            "Role Management is for the platform administrator only"
        )

    # ---------- platform administrator: users, not tickets ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_admin_lands_on_the_user_admin_dashboard_instead_of_the_ticket_dashboard(self):
        self.login_once(self.get("adminEmail"))

        # Sign-in lands on "/" first and then forwards the admin to "/admin".
        self.wait_for_url("/admin")

        assert self.current_url() == self.base_url + "/admin", (
            "An admin should be forwarded from / to /admin"
        )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_admin_sees_user_statistics_and_no_ticket_queues(self):
        self.login_once(self.get("adminEmail"))

        self.open_and_wait("/admin")
        self.nav.wait_until_loaded()

        assert self.dashboard.is_kpi_displayed("Total Users"), (
            "The admin dashboard should count users"
        )
        assert self.nav.has_item("User Management"), "An admin manages users"
        assert self.nav.has_item("Role Management"), "An admin manages roles"
        assert self.nav.has_no_ticket_queues(), (
            f"An admin must see no ticket queues. Menu: {self.nav.all_item_labels()}"
        )

    @pytest.mark.sanity
    def test_a_cc_initiator_is_refused_every_screen_their_role_does_not_cover(self):
        """Typing an admin-only URL as a CC Initiator is refused."""
        self.login_once(self.get("ccInitiatorEmail"))

        forbidden = [
            "/user-management",
            "/role-management",
            "/audit-trail",
            "/access-management",
            "/admin/activity",
        ]

        for path in forbidden:
            self.open_and_wait(path)
            assert (
                self.is_access_denied()
                or self.is_page_not_found()
                or path not in self.current_url()
            ), (
                f"The CC Initiator reached {path}. URL: {self.current_url()} - "
                f"page says: {self.page_text_snippet()}"
            )

    def test_every_tab_of_somebody_elses_ticket_is_refused(self):
        """Every tab of a complaint not assigned to the handler is refused."""
        owned_by_them = self.reference("COM", self.get("complaintHandlerTicketTail"))

        # Step 1: as the CC Initiator (sees everything), find a complaint that is not the handler's.
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

        all_complaints = self.list.get_reference_numbers()
        row_of_someone_elses = -1
        for row, ref in enumerate(all_complaints):
            if ref != owned_by_them:
                row_of_someone_elses = row
                break
        if row_of_someone_elses < 0:
            pytest.skip("Only one complaint exists, so there is no other ticket to try.")

        self.list.search(all_complaints[row_of_someone_elses])
        self.list.wait_for_row_count(1)
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        someone_elses_ticket = self.current_url()[len(self.base_url):]

        # Step 2: as the complaint handler, every tab of that ticket must be refused.
        self.login_once(self.get("complaintHandlerEmail"))
        self.require_ticket_access("complaintHandlerEmail")
        for tab in ["", "/audit", "/sla", "/customer-records", "/investigation"]:
            # open_and_wait (not open) so we check the page after it has loaded.
            self.open_and_wait(someone_elses_ticket + tab)
            assert self.is_page_not_found() or self.is_access_denied(), (
                f"The '{tab}' tab of another user's ticket must be refused. "
                f"URL: {self.current_url()}"
            )
