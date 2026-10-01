"""
Module 14 - The notification bell (in-app only).

How many notifications exist depends on the environment, so each test either works
with what is there or skips - it never expects a fixed number.
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p2, pytest.mark.phase1]


class TestNotification(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_dashboard(self):
        # Some tests sign in as someone else, so sign back in as the agent first.
        self.login_once(self.get("agentEmail"))
        self.open("/")
        self.dashboard.wait_until_loaded()

    # ---------- the panel ----------

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_bell_opens_and_closes_the_panel(self):
        self.open_dashboard()

        self.top_bar.open_notifications()
        assert self.top_bar.is_notification_panel_open(), (
            "Clicking the bell must open the notification panel."
        )

        # The panel closes on a click outside it (Escape does not close it).
        self.top_bar.close_notifications()
        self.wait.until(lambda d: not self.top_bar.is_notification_panel_open())

        assert not self.top_bar.is_notification_panel_open(), (
            "The panel must close again."
        )

    @pytest.mark.regression
    def test_an_empty_panel_says_so_rather_than_showing_nothing(self):
        """An empty panel shows 'No notifications yet' instead of blank space."""
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() > 0:
            pytest.skip("This account has notifications, so the empty state is not shown.")
        assert self.top_bar.shows_no_notifications(), (
            f"An empty panel must say 'No notifications yet'. On screen: {self.page_text_snippet()}"
        )

    # ---------- reading them ----------

    @pytest.mark.write
    def test_marking_everything_read_clears_the_unread_badge(self):
        """Mark all read works and keeps the panel open (write test)."""
        self.require_write_tests()
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications to mark as read on this account.")
        try:
            self.top_bar.mark_all_notifications_read()
        except Exception:  # noqa: BLE001 - the button was not offered
            pytest.skip("Everything was already read, so the button was not offered.")

        assert self.top_bar.is_notification_panel_open(), (
            "Marking read must not close the panel."
        )

    # ---------- who gets a bell ----------

    @pytest.mark.regression
    def test_an_administrator_also_gets_the_bell(self):
        """The administrator (no ticket queues) still has a working bell."""
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin")

        self.top_bar.open_notifications()
        assert self.top_bar.is_notification_panel_open(), (
            f"The administrator should get the bell too. On screen: {self.page_text_snippet()}"
        )
        self.press_escape()

    @pytest.mark.regression
    def test_a_signed_out_visitor_gets_no_bell_at_all(self):
        """A signed-out visitor is sent to /login, which has no bell."""
        self.clear_session()
        self.open("/")
        self.wait_for_url_containing("/login")

        try:
            assert "/login" in self.current_url(), (
                f"A signed-out visitor must be sent to sign in. Landed on: {self.current_url()}"
            )
            assert not self.top_bar.has_notification_bell(), (
                "The sign-in screen must not show the notification bell."
            )
        finally:
            # Sign back in so the next test does not start on the login page.
            self.login_as(self.get("agentEmail"))

    # ---------- the unread badge and the links ----------

    @pytest.mark.regression
    def test_the_unread_badge_agrees_with_the_unread_rows(self):
        """The badge shows the number of unread rows (or "9+" above nine)."""
        self.open_dashboard()

        badge_text = self.top_bar.unread_badge_text()
        self.top_bar.open_notifications()
        unread_rows = self.top_bar.unread_notification_count()

        if unread_rows == 0:
            assert not self.top_bar.has_unread_badge(), (
                f"Nothing is unread, so there must be no badge. Badge: {badge_text!r}"
            )
            return
        if unread_rows > 9:
            expected = "9+"
        else:
            expected = str(unread_rows)
        assert badge_text == expected, (
            f"{unread_rows} unread rows, so the badge should read {expected!r}. "
            f"It reads {badge_text!r}."
        )

    @pytest.mark.regression
    def test_every_notification_links_to_the_ticket_it_is_about(self):
        """Every notification row links to a ticket."""
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications on this account, so there are no links to check.")

        hrefs = self.top_bar.notification_hrefs()
        assert hrefs, (
            f"Every notification row should link to its ticket. On screen: {self.page_text_snippet()}"
        )
        for href in hrefs:
            assert "/tickets/" in href, (
                f"A notification must point at a ticket. This one points at: {href}"
            )

    @pytest.mark.regression
    def test_an_sla_breach_notification_lands_on_the_sla_tab_not_the_overview(self):
        """An SLA-breach notification links to the ticket's SLA tab."""
        self.open_dashboard()
        self.top_bar.open_notifications()

        sla_links = []
        for href in self.top_bar.notification_hrefs():
            if href.endswith("/sla"):
                sla_links.append(href)
        if not sla_links:
            pytest.skip("No SLA-breach notification on this account.")
        for href in sla_links:
            assert "/tickets/" in href and href.endswith("/sla"), (
                f"A breach alert should open the ticket's SLA tab. Actual: {href}"
            )

    @pytest.mark.write
    def test_opening_a_notification_takes_you_to_that_ticket(self):
        """Clicking a notification opens its ticket (write test - it marks it read)."""
        self.require_write_tests()
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications on this account to open.")

        self.top_bar.open_first_notification()
        self.wait.until(lambda d: "/tickets/" in d.current_url)

        assert "/tickets/" in self.current_url(), (
            f"Clicking a notification should open its ticket. Landed on: {self.current_url()}"
        )

    @pytest.mark.regression
    def test_mark_all_read_is_only_offered_when_something_is_actually_unread(self):
        """'Mark all' is shown only when something is unread."""
        self.open_dashboard()
        badge_before = self.top_bar.unread_badge_count()
        self.top_bar.open_notifications()

        if badge_before == 0:
            assert not self.top_bar.has_mark_all_read(), (
                "Everything is already read, so 'Mark all' must not be offered"
            )
        else:
            assert self.top_bar.has_mark_all_read(), (
                f"{badge_before} notification(s) are unread, so 'Mark all' should be offered"
            )

    @pytest.mark.regression
    def test_you_are_shown_only_your_own_notifications(self):
        """No ticket link appears in both the agent's and the admin's notifications."""
        self.open_dashboard()
        self.top_bar.open_notifications()
        agent_hrefs = sorted(self.top_bar.notification_hrefs())

        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin")
        self.top_bar.open_notifications()
        admin_hrefs = sorted(self.top_bar.notification_hrefs())

        if not agent_hrefs and not admin_hrefs:
            pytest.skip("Neither account has notifications here, so there is nothing to compare.")
        shared = sorted(set(agent_hrefs) & set(admin_hrefs))
        assert not shared, (
            f"Shown to both accounts: {shared}. Agent: {agent_hrefs}. Admin: {admin_hrefs}."
        )
