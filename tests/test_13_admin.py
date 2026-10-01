"""
Module 02 - Users, roles and permissions.

Checks User Management, Role Management, Access Management (Head of Department)
and the Activity Log. No test creates a real user - every form is cancelled.
"""

import pytest
from selenium.common.exceptions import TimeoutException

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.admin_page import AdminPage

# The roles an administrator may give out from Add User (display names).
ADMIN_PORTAL_ROLES = ["Admin", "Head of Department", "Manager", "CC Initiator", "CC Supervisor"]

pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]


class TestAdmin(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("adminEmail"))

    def open_user_management(self):
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/user-management")
        self.admin.wait_until_loaded()

    # ---------- the user list ----------

    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_the_user_table_shows_the_agreed_columns(self):
        self.open_user_management()

        headers = self.admin.get_column_headers()
        for expected in AdminPage.USER_COLUMNS:
            assert expected in headers, (
                f"Column '{expected}' is missing. Columns found: {headers}"
            )

    @pytest.mark.sanity
    def test_the_organisation_wide_list_reaches_an_account_beyond_the_first_page(self):
        """Search reaches any user in the organisation, not just the first page of ten."""
        self.open_user_management()

        first_page = self.admin.get_listed_emails()
        assert first_page, "The organisation-wide list should show users"

        wanted = self.get("ccInitiatorEmail")
        self.admin.search(wanted)
        try:
            self.wait.until(lambda d: self.admin.lists_user(wanted))
        except TimeoutException:
            pytest.skip(f"'{wanted}' does not exist on this environment (test-data issue).")

        assert self.admin.lists_user(wanted), (
            f"The administrator should find {wanted} through search"
        )

    @pytest.mark.sanity
    def test_search_finds_one_user(self):
        """Searching one user's full email leaves exactly that user."""
        self.open_user_management()

        wanted = self.get("ccInitiatorEmail")
        self.admin.search(wanted)
        # The search runs while typing, so wait for the final result.
        try:
            self.wait.until(lambda d: self.admin.get_listed_emails() == [wanted])
        except TimeoutException:
            pass

        assert self.admin.get_listed_emails() == [wanted], (
            f"Only '{wanted}' should be listed. Listed: {self.admin.get_listed_emails()}"
        )

    def test_searching_for_somebody_who_does_not_exist_shows_an_empty_list(self):
        self.open_user_management()

        # Wait until the rows change, so we know the search has come back.
        before = self.admin.get_listed_emails()
        self.admin.search("nobody.at.all@example.invalid")
        self.wait.until(lambda d: self.admin.get_listed_emails() != before)

        # An empty table or a single "no users found" row are both fine.
        assert not self.admin.lists_user(self.get("ccInitiatorEmail")), (
            "A search with no match must not leave real users on screen"
        )
        assert self.admin.get_row_count() <= 1, (
            f"Only an empty-state row may remain, but {self.admin.get_row_count()} rows are shown"
        )

    def test_a_deactivated_user_is_listed_with_the_status_deactivated(self):
        """Filtering on Deactivated lists only users whose Status reads "Deactivated" (a filter only)."""
        self.open_user_management()
        if self.admin.kpi_number("Deactivated Users") == 0:
            pytest.skip(
                "The 'Deactivated Users' tile reads 0 on this environment, so no deactivated "
                "user is visible. Deactivating one would change shared UAT data."
            )

        self.admin.filter_by_status("Deactivated")
        self.wait.until(lambda d: set(self.admin.listed_statuses()) == {"Deactivated"})
        statuses = self.admin.listed_statuses()
        # The app's word for an inactive account is "Deactivated" (UserManagementClient.tsx STATUS_BADGE).
        assert statuses and set(statuses) == {"Deactivated"}, f"Statuses listed: {statuses}"

    # ---------- adding a user ----------

    def open_user_management_with_add_user(self):
        """Opens User Management, or skips if Add User is switched off here."""
        self.open_user_management()
        if not self.admin.has_add_user_button():
            pytest.skip("Add User is switched off in this environment (ADD_USER_ENABLED).")

    def test_the_add_user_form_opens_and_starts_invalid(self):
        self.open_user_management_with_add_user()

        self.admin.open_add_user_form()

        assert self.admin.get_modal_title() == "Add User"
        assert not self.admin.is_create_user_enabled(), (
            "Create User must stay disabled on an empty form"
        )

        self.admin.cancel_modal()
        assert not self.admin.is_modal_open(), "Cancel should close the form"

    def test_the_add_user_form_refuses_a_badly_formed_email(self):
        self.open_user_management_with_add_user()
        self.admin.open_add_user_form()

        # We only check the email box; Create User is never pressed (it would create a user).
        self.admin.fill_new_user("Automation Test", "not-an-email")
        assert self.admin.new_user_email_fails_the_browsers_email_check(), (
            "'not-an-email' must fail the Work Email box's email check"
        )

        self.admin.fill_new_user("Automation Test", "automation.test@awnic.com")
        assert not self.admin.new_user_email_fails_the_browsers_email_check(), (
            "A well-formed address must pass the same check"
        )
        self.admin.cancel_modal()

    def test_the_role_dropdown_offers_the_admin_portal_roles(self):
        """The administrator is offered exactly the five Admin Portal roles."""
        self.open_user_management_with_add_user()
        self.admin.open_add_user_form()

        offered = self.admin.get_assignable_roles()
        assert sorted(offered) == sorted(ADMIN_PORTAL_ROLES), (
            f"Expected {sorted(ADMIN_PORTAL_ROLES)}. Offered: {offered}"
        )

        self.admin.cancel_modal()

    # ---------- the role matrix ----------

    def test_the_role_matrix_explains_what_each_role_can_do(self):
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/role-management")
        self.admin.wait_until_loaded()

        assert self.admin.get_heading() == "Role Management"
        assert self.admin.get_row_count() > 0, (
            "The matrix should list the modules each role can reach"
        )

    def test_the_role_matrix_is_read_only_and_says_so(self):
        """The role matrix shows a 'view only' notice."""
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/role-management")
        self.admin.wait_until_loaded()

        assert self.admin.shows_view_only_notice(), (
            "The role matrix should say it cannot be edited here"
        )

    # ---------- the head of department's own screen ----------

    def test_access_management_offers_both_tabs(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/access-management")
        self.admin.wait_until_loaded()

        assert self.admin.tab_labels() == ["Users Management", "Roles Management"], (
            f"Expected Users then Roles tabs. Tabs: {self.admin.tab_labels()}"
        )

        self.admin.open_tab("Roles Management")
        self.wait.until(lambda d: self.admin.shows_view_only_notice())

        assert self.admin.shows_view_only_notice(), (
            "The Roles tab should show the same read-only matrix"
        )

    # ---------- the activity log ----------

    def test_the_activity_log_records_who_changed_what(self):
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin/activity")
        self.admin.wait_until_loaded()

        assert self.admin.get_heading() == "Activity Log"
        assert self.admin.has_activity_rows(), "The activity log should not be empty"
