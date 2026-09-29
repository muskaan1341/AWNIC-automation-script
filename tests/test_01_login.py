"""
MODULE 01 - Signing in and out.

The application signs you in with an EMAIL ONLY. There is no password box anywhere, because
the real login is AWNIC One single sign-on and this local form stands in for it. So there is
nothing like "wrong password" to test. The negative cases are instead "this email does not
exist" and "this page needs a session you do not have".

Every test here starts SIGNED OUT, which is why this class has a per-test sign-out fixture
rather than the class-scoped sign-in the rest of the suite uses.
"""

from __future__ import annotations

from urllib.parse import quote

import pytest
from selenium.webdriver.common.by import By

from awnic_qa import users
from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P0 Auth (dev-login rejects a non-seeded email) + C-P0 (no-role users get 403 everywhere; protected routes bounce)
pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]



class TestLogin(BaseTest):
    @pytest.fixture(autouse=True)
    def start_signed_out(self, ensure_browser_alive):
        """Was @BeforeMethod(alwaysRun = true). Depends on the browser check so it runs after."""
        self.clear_session()

    # ---------- the form itself ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_login_page_shows_the_dev_email_form(self):
        self.login.open()

        assert self.login.is_heading_displayed(), "The 'Welcome back' heading should be visible"
        assert self.login.is_email_input_displayed(), "The email box should be visible"
        assert self.login.get_sign_in_button_text() == "Sign in (dev)"
        assert self.login.get_email_input_type() == "email", (
            "The box should be type=email so the browser itself can check the format"
        )

    def test_the_email_box_is_focused_so_you_can_just_start_typing(self):
        self.login.open()

        assert self.login.is_email_input_focused(), (
            "The email box should already have the cursor when the page opens"
        )

    # ---------- signing in ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_valid_email_signs_in_and_lands_on_the_dashboard(self):
        self.login_as(self.get("agentEmail"))

        # The dashboard is at "/", NOT at "/dashboard". There is no /dashboard route at all.
        assert self.current_url() == self.base_url + "/", (
            "A signed-in agent should land on the dashboard at /"
        )

        self.dashboard.wait_until_loaded()
        assert self.dashboard.is_kpi_displayed("Total Ticket"), (
            "The dashboard should show its tiles after signing in"
        )

    def test_signing_in_works_with_the_keyboard_alone(self):
        self.login.open()
        self.login.sign_in_with_keyboard_only(self.get("agentEmail"))

        self.wait.until(lambda d: "/login" not in d.current_url)
        assert "/login" not in self.current_url(), (
            "Pressing Enter in the email box should submit the form"
        )
        # Leaving the login page proves only that SOMETHING happened. Being signed in as the
        # person whose email was typed is what "signing in works" means.
        assert self.top_bar.get_signed_in_email() == self.get("agentEmail"), (
            "The keyboard sign-in should leave the typed account signed in"
        )

    def test_signed_in_user_sees_their_own_email_in_the_top_bar(self):
        self.login_as(self.get("agentEmail"))

        assert self.top_bar.get_signed_in_email() == self.get("agentEmail"), (
            "The top bar should show the email of whoever signed in"
        )

    def test_the_greeting_names_the_signed_in_person(self):
        self.login_as(self.get("agentEmail"))
        self.dashboard.wait_until_loaded()

        # The heading is "<time of day>, <display name>" (DashboardGreeting), the band being
        # one of three fixed phrases (greetingForHour). The name is not hard-coded here: it is
        # the configured agent's own name from awnic_qa.users, which is keyed on the same
        # config value this test signs in with - so a seed refresh that renames the account
        # updates both together.
        #
        # WHAT THIS REPLACED: "a comma with something after it", which any name - including
        # SOMEBODY ELSE'S - satisfied. The test is called "names the signed-in person".
        greeting = self.dashboard.get_greeting()
        band, _, name = greeting.partition(", ")
        assert band in ("Good morning", "Good afternoon", "Good evening"), (
            f"The greeting should open with the time-of-day phrase. Actual: {greeting}"
        )
        assert name == users.CC_AGENT.name, (
            f"The greeting should name {users.CC_AGENT.name}, who signed in. Actual: {greeting}"
        )

    # ---------- rejecting bad sign-ins ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_unknown_email_is_rejected(self):
        self.login.open()
        self.login.sign_in(self.get("unknownEmail"))

        assert self.login.get_error_message() == "No matching account for this email"
        assert "/login" in self.current_url(), (
            "A rejected sign-in must stay on the login page"
        )

    def test_empty_email_is_blocked_by_the_browser(self):
        self.login.open()
        self.login.click_sign_in()

        # The box is marked "required", so the browser stops the form before it is ever sent.
        assert self.login.get_email_validation_message(), (
            "The browser should refuse to submit an empty required field"
        )
        assert "/login" in self.current_url()
        assert not self.login.has_error_message(), (
            "Nothing reached the server, so there should be no server error message"
        )

    def test_badly_formatted_email_is_blocked_by_the_browser(self):
        self.login.open()
        self.login.sign_in("not-an-email")

        assert self.login.get_email_validation_message(), (
            "type=email should reject a value with no @ sign"
        )
        assert "/login" in self.current_url()

    # ---------- protecting pages ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_unauthenticated_user_is_sent_to_login_with_a_redirect_back(self):
        self.open("/tickets/enquiries")

        self.wait_for_url_containing("/login")
        assert "redirect=%2Ftickets%2Fenquiries" in self.current_url(), (
            f"The login URL should remember where the visitor was going. "
            f"Actual: {self.current_url()}"
        )

    def test_a_deep_link_to_one_ticket_survives_the_sign_in_detour(self):
        """
        A link to ONE ticket's sub-page is remembered in full - id and tab included.

        WHAT THIS REPLACED: it opened /reports, a fixed top-level page, so the name's "one
        ticket" was never exercised and it repeated the list-page test above. A ticket link is
        the case that matters in practice (it is what a notification email or a colleague
        sends), and it is the one with a dynamic segment that a redirect could truncate.

        Asserted at the redirect parameter, deliberately. The login page honours `redirect`
        after its silent session refresh, but the DEV sign-in form always lands on "/"
        (app/login/page.tsx router.push("/")), so an end-to-end "and you arrive back on the
        ticket" check would fail by design on this environment's sign-in stand-in.
        """
        ticket_tab = "/tickets/00000000-0000-0000-0000-000000000000/sla"
        self.open(ticket_tab)

        self.wait_for_url_containing("/login")
        assert "redirect=" + quote(ticket_tab, safe="") in self.current_url(), (
            f"The whole ticket path, id and tab included, should be remembered. "
            f"Actual: {self.current_url()}"
        )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_every_protected_area_bounces_a_signed_out_visitor(self):
        # One loop instead of six near-identical tests. A new protected area only needs a new
        # line here.
        #
        # /webform-test is NOT in this list and must never be added to it - it is customer
        # intake and is public on purpose. The test below is its counterpart.
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
                f"{path} should not open for a signed-out visitor. "
                f"Actual: {self.current_url()}"
            )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_the_customer_intake_form_is_deliberately_public(self):
        """
        The one page that must NOT bounce a signed-out visitor.

        Customer intake never gets a login wall (R03) - a customer filing a complaint from
        AWNIC's website has no account and never will. /webform-test stands in for that form
        while the vendor's API is unshared, and it is listed in apps/web's middleware
        PUBLIC_PATHS beside /login for exactly that reason.

        This is asserted here, next to the rule it is the exception to, so that anybody
        tightening route protection sees immediately that the exception is deliberate rather
        than an oversight to be cleaned up.
        """
        self.open("/webform-test")
        self.wait_for_page_load()

        assert "/login" not in self.current_url(), (
            f"Customer intake must stay reachable without an account (R03). "
            f"Actual: {self.current_url()}"
        )
        # Asserted inline rather than through a page object: the website-intake tests were
        # removed (they created real tickets and needed a service token), but THIS test is not
        # an intake test - it is an access-control one that happens to point at the intake URL.
        # It stays because it is the counterpart to the protected-paths loop above, and it is
        # read-only.
        assert "Not the real AWNIC website form" in self.driver.find_element(
            By.TAG_NAME, "body"
        ).text, (
            f"Expected the intake harness. The page shows: {self.page_text_snippet()}"
        )

    # ---------- signing out ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_sign_out_ends_the_session_and_protects_pages_again(self):
        self.login_as(self.get("agentEmail"))
        self.top_bar.sign_out()

        self.wait_for_url_containing("/login")

        # The real check is not the redirect - it is that the session is genuinely gone.
        self.open("/tickets/enquiries")
        self.wait_for_url_containing("/login")
        assert "/login" in self.current_url(), (
            "After signing out, a protected page must not open"
        )

    def test_an_old_link_does_not_work_after_signing_out(self):
        self.login_as(self.get("agentEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        page_visited_while_signed_in = self.current_url()

        self.top_bar.sign_out()
        self.wait_for_url_containing("/login")

        self.driver.get(page_visited_while_signed_in)
        self.wait_for_url_containing("/login")
        assert "/login" in self.current_url(), (
            "Re-opening a page from the browser history must not revive a dead session"
        )
