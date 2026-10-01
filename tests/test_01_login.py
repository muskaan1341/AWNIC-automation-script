"""
Login and logout.

Sign-in uses an email only (no password box). Every test here starts signed out.
"""

from urllib.parse import quote

import pytest
from selenium.webdriver.common.by import By

from awnic_qa import users
from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]


class TestLogin(BaseTest):
    @pytest.fixture(autouse=True)
    def start_signed_out(self, ensure_browser_alive):
        """Sign out before every test."""
        self.clear_session()

    # ---------- the form itself ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_login_page_shows_the_dev_email_form(self):
        self.login.open()

        assert self.login.is_heading_displayed(), "The 'Welcome back' heading should be visible"
        assert self.login.is_email_input_displayed(), "The email box should be visible"
        assert self.login.get_sign_in_button_text() == "Sign in (dev)"
        assert self.login.get_email_input_type() == "email", "The email box should be type=email"

    def test_the_email_box_is_focused_so_you_can_just_start_typing(self):
        self.login.open()

        assert self.login.is_email_input_focused(), "The email box should have the cursor on page open"

    # ---------- signing in ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_valid_email_signs_in_and_lands_on_the_dashboard(self):
        self.login_as(self.get("agentEmail"))

        # The dashboard is at "/", not "/dashboard".
        assert self.current_url() == self.base_url + "/", "An agent should land on the dashboard at /"

        self.dashboard.wait_until_loaded()
        assert self.dashboard.is_kpi_displayed("Total Ticket"), "The dashboard tiles should show"

    def test_signing_in_works_with_the_keyboard_alone(self):
        self.login.open()
        self.login.sign_in_with_keyboard_only(self.get("agentEmail"))

        self.wait.until(lambda d: "/login" not in d.current_url)
        assert "/login" not in self.current_url(), "Pressing Enter should submit the form"
        assert self.top_bar.get_signed_in_email() == self.get("agentEmail"), (
            "The typed account should be signed in"
        )

    def test_signed_in_user_sees_their_own_email_in_the_top_bar(self):
        self.login_as(self.get("agentEmail"))

        assert self.top_bar.get_signed_in_email() == self.get("agentEmail"), (
            "The top bar should show the signed-in email"
        )

    def test_the_greeting_names_the_signed_in_person(self):
        self.login_as(self.get("agentEmail"))
        self.dashboard.wait_until_loaded()

        # The greeting looks like "Good morning, <name>".
        greeting = self.dashboard.get_greeting()
        band, _, name = greeting.partition(", ")
        assert band in ("Good morning", "Good afternoon", "Good evening"), (
            f"Greeting should start with the time of day. Actual: {greeting}"
        )
        assert name == users.CC_AGENT.name, (
            f"Greeting should name {users.CC_AGENT.name}. Actual: {greeting}"
        )

    # ---------- rejecting bad sign-ins ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_unknown_email_is_rejected(self):
        self.login.open()
        self.login.sign_in(self.get("unknownEmail"))

        assert self.login.get_error_message() == "No matching account for this email"
        assert "/login" in self.current_url(), "A rejected sign-in should stay on the login page"

    def test_empty_email_is_blocked_by_the_browser(self):
        self.login.open()
        self.login.click_sign_in()

        assert self.login.get_email_validation_message(), "The browser should block an empty email"
        assert "/login" in self.current_url()
        assert not self.login.has_error_message(), "There should be no server error message"

    def test_badly_formatted_email_is_blocked_by_the_browser(self):
        self.login.open()
        self.login.sign_in("not-an-email")

        assert self.login.get_email_validation_message(), "The browser should block an email with no @"
        assert "/login" in self.current_url()

    # ---------- protecting pages ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_unauthenticated_user_is_sent_to_login_with_a_redirect_back(self):
        self.open("/tickets/enquiries")

        self.wait_for_url_containing("/login")
        assert "redirect=%2Ftickets%2Fenquiries" in self.current_url(), (
            f"The login URL should remember the page. Actual: {self.current_url()}"
        )

    def test_a_deep_link_to_one_ticket_survives_the_sign_in_detour(self):
        """The full ticket link (id and tab) is kept in the redirect parameter."""
        ticket_tab = "/tickets/00000000-0000-0000-0000-000000000000/sla"
        self.open(ticket_tab)

        self.wait_for_url_containing("/login")
        assert "redirect=" + quote(ticket_tab, safe="") in self.current_url(), (
            f"The whole ticket path should be remembered. Actual: {self.current_url()}"
        )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_every_protected_area_bounces_a_signed_out_visitor(self):
        # /webform-test is public on purpose - do not add it here (see the next test).
        protected_paths = [
            "/",
            "/tickets/enquiries",
            "/tickets/complaints",
            "/tickets/discarded",
            "/reports",
            "/audit-trail",
            "/user-management",
        ]

        for path in protected_paths:
            self.open(path)
            self.wait_for_url_containing("/login")
            assert "/login" in self.current_url(), (
                f"{path} should not open when signed out. Actual: {self.current_url()}"
            )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_the_customer_intake_form_is_deliberately_public(self):
        """The customer intake form must open without signing in."""
        self.open("/webform-test")
        self.wait_for_page_load()

        assert "/login" not in self.current_url(), (
            f"Customer intake should not need a login. Actual: {self.current_url()}"
        )
        assert "Not the real AWNIC website form" in self.driver.find_element(
            By.TAG_NAME, "body"
        ).text, (
            f"Expected the intake form page. The page shows: {self.page_text_snippet()}"
        )

    # ---------- signing out ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_sign_out_ends_the_session_and_protects_pages_again(self):
        self.login_as(self.get("agentEmail"))
        self.top_bar.sign_out()

        self.wait_for_url_containing("/login")

        self.open("/tickets/enquiries")
        self.wait_for_url_containing("/login")
        assert "/login" in self.current_url(), "After sign out, a protected page should not open"

    def test_an_old_link_does_not_work_after_signing_out(self):
        self.login_as(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        page_visited_while_signed_in = self.current_url()

        self.top_bar.sign_out()
        self.wait_for_url_containing("/login")

        self.driver.get(page_visited_while_signed_in)
        self.wait_for_url_containing("/login")
        assert "/login" in self.current_url(), "An old link should not work after sign out"
