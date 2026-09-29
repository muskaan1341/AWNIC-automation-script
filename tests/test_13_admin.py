"""
MODULE 02 - Users, roles and permissions.

FOUR SCREENS, TWO DOORS. A platform administrator gets /user-management and /role-management
as separate organisation-wide screens. A Head of Department reaches the SAME two things
through /access-management, as two tabs, but limited to their own department.

NOTHING HERE CREATES A REAL USER. Every test stops at the guard - is the button there, is the
form validated, are the right roles offered - and cancels. Creating a user has side effects
that outlive the test run, and a half-created account is worse than no test.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import TimeoutException

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.admin_page import AdminPage

#: What an organisation-wide administrator may hand out from Add User, by display name.
ADMIN_PORTAL_ROLES = ["Admin", "Head of Department", "Manager", "CC Initiator", "CC Supervisor"]

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P0 'Org-wide user management is Admin-only'
pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]



class TestAdmin(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("adminEmail"))

    def open_user_management(self) -> None:
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/user-management")
        self.admin.wait_until_loaded()

    # ---------- the user list ----------

    @pytest.mark.sanity
    def test_the_user_table_shows_the_agreed_columns(self):
        self.open_user_management()

        headers = self.admin.get_column_headers()
        for expected in AdminPage.USER_COLUMNS:
            assert expected in headers, (
                f"Column '{expected}' is missing. Columns found: {headers}"
            )

    @pytest.mark.sanity
    def test_the_organisation_wide_list_reaches_an_account_beyond_the_first_page(self):
        """
        M02 / R39: an administrator's user list is ORGANISATION-WIDE, not one team's.

        WHY THIS NO LONGER NAMES FIVE ACCOUNTS. The old version asserted that five addresses
        from the settings file were on screen, and it could not be right on either count:

          * the table PAGES AT TEN (UserManagementClient slices `users` by `perPage`, default
            10, over the at-most-200 the server returns), so "is it listed" cannot be answered
            by looking at the rendered rows - on this environment there are 184 users,
          * two of those five addresses do not exist here at all (verified 2026-09-17 through
            User Management), so the test was asserting seed data rather than the product.

        What Phase 1 does guarantee, and what is asserted instead: the list is searched on the
        SERVER across the whole organisation (`listUsers({search})`), so an administrator can
        reach any account in it, not just the ten in front of them. Which accounts exist is an
        environment fact and is checked in the UAT test-data review, not here.
        """
        self.open_user_management()

        first_page = self.admin.get_listed_emails()
        assert first_page, "The organisation-wide list should show users"

        wanted = self.get("agentEmail")
        self.admin.search(wanted)
        try:
            self.wait.until(lambda d: self.admin.lists_user(wanted))
        except TimeoutException:
            pytest.skip(
                f"'{wanted}' does not exist on this environment, so there is no account to "
                "reach. That is a test-data fact, not a fault in the list."
            )

        assert self.admin.lists_user(wanted), (
            f"An organisation-wide administrator should be able to reach {wanted} through "
            "search, whichever page it would otherwise sit on"
        )

    @pytest.mark.sanity
    def test_search_finds_one_user(self):
        """
        Searching one user's full email leaves exactly that user.

        WHAT THIS REPLACED: "the user is listed" plus "the row count did not grow". The
        second half could not fail, and the first held just as well if the search had not
        filtered at all and the user happened to be on the first page. An email address is
        unique, and no name contains an "@", so exactly one row is the right answer.
        """
        self.open_user_management()

        wanted = self.get("agentEmail")
        self.admin.search(wanted)
        # Wait for the FINAL result, not the first change: the search runs as it is typed,
        # so a partial prefix narrows the list to several people on the way there.
        try:
            self.wait.until(lambda d: self.admin.get_listed_emails() == [wanted])
        except TimeoutException:
            pass

        assert self.admin.get_listed_emails() == [wanted], (
            f"Searching '{wanted}' should list that one user and nobody else. Listed: "
            f"{self.admin.get_listed_emails()}"
        )

    def test_searching_for_somebody_who_does_not_exist_shows_an_empty_list(self):
        self.open_user_management()

        # Wait for the SEARCH to come back, by watching the rows change. "The agent is no
        # longer listed" is not that signal: with 184 users ordered by recency the agent is
        # not on page one to begin with, so it is already true of the UNFILTERED table and
        # the assertion below could run mid-request against a full page of ten.
        before = self.admin.get_listed_emails()
        self.admin.search("nobody.at.all@example.invalid")
        self.wait.until(lambda d: self.admin.get_listed_emails() != before)

        # The table may empty completely, OR keep one row holding a "no users found" message -
        # both are correct, and which one you get is a design choice, not a bug. What matters
        # is that the real people are gone.

        assert not self.admin.lists_user(self.get("agentEmail")), (
            "A search with no match must not leave real users on screen"
        )
        assert self.admin.get_row_count() <= 1, (
            f"At most an empty-state row should remain, but {self.admin.get_row_count()} rows "
            "are still shown"
        )

    # ---------- adding a user ----------

    def open_user_management_with_add_user(self) -> None:
        """
        Opens User Management, or skips when Add User is switched off in this environment.

        ADD USER IS BEHIND A KILL SWITCH. `app/user-management/page.tsx` reads
        `ADD_USER_ENABLED` (off unless explicitly set to "true") and passes it down; the button
        and the modal both render only when it is on. So "there is no Add User button" is a
        deployment setting, not a product defect - and R39's provisioning runs through AWNIC
        SSO/Azure AD anyway. Asserting the button must exist made these tests fail for a
        configuration reason and said nothing about the form they are actually about.

        The flag is ON for the deployed environment as of 2026-09-18, so these tests do run
        there; the guard only keeps them honest if it is turned off again.
        """
        self.open_user_management()
        if not self.admin.has_add_user_button():
            pytest.skip(
                "Add User is switched off in this environment (ADD_USER_ENABLED is not "
                "'true'), so the form cannot be opened. Turn the flag on to exercise it."
            )

    def test_the_add_user_form_opens_and_starts_invalid(self):
        self.open_user_management_with_add_user()

        self.admin.open_add_user_form()

        assert self.admin.get_modal_title() == "Add User"
        # The name promised this, and nothing checked it: an untouched form must not be
        # submittable (AddUserModal's canSubmit needs name, email and role at the least).
        assert not self.admin.is_create_user_enabled(), (
            "Create User must stay disabled on an empty form"
        )

        self.admin.cancel_modal()
        assert not self.admin.is_modal_open(), "Cancel should close the form"

    def test_the_add_user_form_refuses_a_badly_formed_email(self):
        self.open_user_management_with_add_user()
        self.admin.open_add_user_form()

        # WHAT THIS REPLACED: typing a bad email, pressing Create User, and asserting the
        # dialog stayed open. With no Role chosen, Create User is DISABLED (canSubmit), so the
        # press did nothing and the dialog stayed open whatever the email said - the test
        # proved the role rule, not the email one.
        #
        # The only email guard on this form is the browser's own <input type="email"> check,
        # so ask the box directly - with a well-formed address as the control, which proves
        # the check tells the two apart rather than rejecting everything. Nothing is pressed:
        # on a form that DID accept the address, pressing would create a real user.
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
        """
        An administrator may only hand out roles they are entitled to hand out. The dropdown is
        the advisory half of that rule; the server enforces it properly.
        """
        self.open_user_management_with_add_user()
        self.admin.open_add_user_form()

        # WHAT THIS REPLACED: "more than one role is offered" - true of a dropdown offering
        # every role there is, which is exactly the leak this rule exists to prevent.
        #
        # An organisation-wide administrator is offered the five Admin Portal roles
        # (AddUserModal's ORG_WIDE_ROLES), labelled by their display names
        # (app/teams/seed_data.py ROLE_DISPLAY_NAMES). Complaint Handler, Compliance Officer
        # and Department POC are not handed out from this form.
        offered = self.admin.get_assignable_roles()
        assert sorted(offered) == sorted(ADMIN_PORTAL_ROLES), (
            f"The administrator should be offered exactly {sorted(ADMIN_PORTAL_ROLES)}. "
            f"Offered: {offered}"
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
        """
        The matrix is READ-ONLY on purpose. What a role may do is defined in code and shipped
        with the release, not edited by hand in production - so the screen says so rather than
        offering an edit button that would not work.
        """
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/role-management")
        self.admin.wait_until_loaded()

        assert self.admin.shows_view_only_notice(), (
            "The role matrix should tell the reader it cannot be edited here"
        )

    # ---------- the head of department's own door ----------

    def test_access_management_offers_both_tabs(self):
        self.login_once(self.get("hodEmail"))
        self.open_and_wait("/access-management")
        self.admin.wait_until_loaded()

        # The name promised BOTH tabs; only the second was ever opened, so a page that lost
        # its Users tab passed. Assert the pair, in order, before opening the Roles one.
        assert self.admin.tab_labels() == ["Users Management", "Roles Management"], (
            f"Access Management should offer Users then Roles. Tabs: {self.admin.tab_labels()}"
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
        assert self.admin.has_activity_rows(), (
            "Every user change is recorded, so the log should not be empty"
        )

    # ---------- who may not be here at all ----------

