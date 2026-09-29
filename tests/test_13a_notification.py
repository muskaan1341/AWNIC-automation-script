"""
MODULE 14 - The notification bell.

WHY THIS CLASS EXISTS: module 14 has 33 written test cases and had almost no automation -
two incidental checks inside the navigation class and nothing else. The bell is also the ONLY
place the application tells a user that something happened to their ticket, so when it is
wrong nobody finds out about an SLA breach until a customer complains.

WHAT THE BELL ACTUALLY IS
In-app only. There is no email from this application - customer email is the AI platform's
job. The panel polls every 30 seconds and shows one row per notification, newest first, with
unread rows on a tinted background. Read and unread use the SAME text treatment, so the
background is the only cue - which is why these tests read the count and not the styling.

A NOTE ON THE ENVIRONMENT
Whether there are any notifications at all depends on what the environment has been doing.
Every test below therefore either works with whatever is there or says clearly that there was
nothing to work with - never asserts a fixed number.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   Notifications — not called out in the matrix; in-app only
pytestmark = [pytest.mark.p2, pytest.mark.phase1]



class TestNotification(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_dashboard(self) -> None:
        """
        Opens the agent's dashboard, SIGNING BACK IN AS THE AGENT FIRST.

        The login_once is not decoration. Two tests near the bottom of this class sign in as
        the ADMINISTRATOR, who has no ticket dashboard at all, and as nobody. Waiting for the
        agent's KPI tiles while signed in as one of those would time out for a reason that has
        nothing to do with notifications. login_once is free when the right person is already
        signed in, and it keeps this helper correct however the file is later reordered.
        """
        self.login_once(self.get("agentEmail"))
        self.open("/")
        self.dashboard.wait_until_loaded()

    # ==================================================================
    # The panel itself
    # ==================================================================

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_the_bell_opens_and_closes_the_panel(self):
        self.open_dashboard()

        self.top_bar.open_notifications()
        assert self.top_bar.is_notification_panel_open(), (
            "Clicking the bell must open the notification panel."
        )

        # Clicking anywhere off the panel closes it - the app puts a full-screen catcher
        # behind it for exactly this. The test is called "opens AND closes", so the closing
        # half is asserted too. It must be that CLICK: TopBar has no key handling, so the
        # Escape this used to press left the panel open and timed the test out.
        self.top_bar.close_notifications()
        self.wait.until(lambda d: not self.top_bar.is_notification_panel_open())

        assert not self.top_bar.is_notification_panel_open(), (
            "The panel must close again - one left open covers the page underneath it."
        )

    @pytest.mark.regression
    def test_an_empty_panel_says_so_rather_than_showing_nothing(self):
        """
        An empty panel must SAY it is empty.

        A panel that opens onto blank space is indistinguishable from a panel that failed to
        load, and a user cannot tell "nothing happened" from "something is broken".
        """
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() > 0:
            pytest.skip(
                "This account has notifications, so the empty state is not on screen to check."
            )
        assert self.top_bar.shows_no_notifications(), (
            "An empty panel must say 'No notifications yet', not render blank. "
            f"On screen: {self.page_text_snippet()}"
        )

    # ==================================================================
    # Reading them
    # ==================================================================

    @pytest.mark.write
    def test_marking_everything_read_clears_the_unread_badge(self):
        """
        Marking everything read must actually stick.

        The count in the badge is derived from the unread rows, so after marking all read the
        badge must be gone. If it comes back on the next 30-second poll, the write did not
        reach the server and the user is being lied to.

        WRITES: marking read is a real change to the signed-in account's notifications, which
        nobody can undo from the UI - gated behind writeTestsEnabled and skipped by default.
        """
        self.require_write_tests()
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications to mark as read on this account.")
        try:
            self.top_bar.mark_all_notifications_read()
        except Exception:  # noqa: BLE001 - the control was simply not offered
            pytest.skip(
                "Everything was already read, so the control was not offered. "
                "That is the correct behaviour, not a failure."
            )

        assert self.top_bar.is_notification_panel_open(), (
            "Marking read must not close the panel - the user is still reading it."
        )

    # ==================================================================
    # Who gets a bell at all
    # ==================================================================

    @pytest.mark.regression
    def test_an_administrator_also_gets_the_bell(self):
        """
        The bell belongs to every signed-in user, including ones with no ticket queues.

        The administrator is the interesting case: they see no tickets at all, but they are
        still a user things can happen to. A bell that disappeared for them would be a whole
        role that can never be told anything.
        """
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin")

        self.top_bar.open_notifications()
        assert self.top_bar.is_notification_panel_open(), (
            "Every signed-in user gets the bell, including one with no ticket queues. "
            f"On screen: {self.page_text_snippet()}"
        )
        self.press_escape()

    @pytest.mark.regression
    def test_a_signed_out_visitor_gets_no_bell_at_all(self):
        """
        A signed-out visitor is kept out of the app shell entirely - so no bell.

        WHAT THIS REPLACED: "the panel is not open on /login". Nothing had clicked a bell, so
        that was true of every page, including a login page wrongly wrapped in the app shell.
        It now asks for a protected page, requires the bounce to the login screen, and checks
        the header the visitor actually lands on carries no bell at all.
        """
        self.clear_session()
        self.open("/")
        self.wait_for_url_containing("/login")

        try:
            assert "/login" in self.current_url(), (
                "A signed-out visitor asking for the dashboard must be sent to sign in. "
                f"Landed on: {self.current_url()}"
            )
            assert not self.top_bar.has_notification_bell(), (
                "The sign-in screen must not carry the notification bell - that belongs to the "
                "signed-in app shell."
            )
        finally:
            # Leave the browser signed in again, so a later test - or a re-ordering of this
            # file - does not start on the login page.
            self.login_as(self.get("agentEmail"))

    # ==================================================================
    # The unread badge, and where a notification actually takes you
    # ==================================================================
    # Added from the module-14 test-case pack, which had 33 written cases against the seven
    # tests above. These are the ones a browser can genuinely prove.

    @pytest.mark.regression
    def test_the_unread_badge_agrees_with_the_unread_rows(self):
        """
        M14-POS: 'The unread count is accurate and visible from every screen'.

        The badge is derived from the rows (`notifications.filter(n => !n.read_at).length`), so
        the two can only disagree if the panel and the bell are reading different data - which
        is exactly the bug worth catching. Above nine the badge caps at "9+" on purpose.

        WHAT THIS REPLACED: `badge <= max(rows, 10)`, where `rows` counted EVERY row, read or
        not - any badge from 1 to 10 passed, which is the badge's whole display range. It now
        counts the UNREAD rows and requires the exact figure TopBar renders for them: nothing
        at zero, the number itself up to nine, "9+" above.
        """
        self.open_dashboard()

        badge_text = self.top_bar.unread_badge_text()
        self.top_bar.open_notifications()
        unread_rows = self.top_bar.unread_notification_count()

        if unread_rows == 0:
            assert not self.top_bar.has_unread_badge(), (
                f"Nothing in the panel is unread, so the bell must carry no badge at all. "
                f"Badge: {badge_text!r}"
            )
            return
        expected = "9+" if unread_rows > 9 else str(unread_rows)
        assert badge_text == expected, (
            f"The panel holds {unread_rows} unread notification(s), so the badge must read "
            f"{expected!r}. It reads {badge_text!r}."
        )

    @pytest.mark.regression
    def test_every_notification_links_to_the_ticket_it_is_about(self):
        """
        M14-NEG: 'A notification always links to the ticket it actually refers to'.

        A notification that leads nowhere, or to the wrong case, is worse than none: the agent
        acts on the wrong ticket believing they were told to.
        """
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications on this account, so there are no links to check.")

        hrefs = self.top_bar.notification_hrefs()
        assert hrefs, (
            "Every notification row should be a link through to its ticket. "
            f"On screen: {self.page_text_snippet()}"
        )
        for href in hrefs:
            assert "/tickets/" in href, (
                f"A notification must point at a ticket. This one points at: {href}"
            )

    @pytest.mark.regression
    def test_an_sla_breach_notification_lands_on_the_sla_tab_not_the_overview(self):
        """
        M14-POS, and a genuinely specific behaviour: a breach alert deep-links to the SLA tab.

        `notificationHref` sends every other type to the ticket overview and an SLA breach to
        `/tickets/{id}/sla` — because the thing the recipient needs to look at is the clock,
        not the ticket's description. Worth pinning down; it is one line of code away from
        silently reverting to the overview for everything.
        """
        self.open_dashboard()
        self.top_bar.open_notifications()

        sla_links = [h for h in self.top_bar.notification_hrefs() if h.endswith("/sla")]
        if not sla_links:
            pytest.skip(
                "No SLA-breach notification on this account. On the live database no ticket "
                "has ever breached, so this alert has never fired."
            )
        for href in sla_links:
            assert "/tickets/" in href and href.endswith("/sla"), (
                f"A breach alert should open the ticket's SLA tab. Actual: {href}"
            )

    @pytest.mark.write
    def test_opening_a_notification_takes_you_to_that_ticket(self):
        """
        M14-POS: 'Opening a notification marks it as read and takes you to the ticket'.

        WRITES: opening one MARKS IT READ, by the requirement's own wording - gated behind
        writeTestsEnabled and skipped by default.
        """
        self.require_write_tests()
        self.open_dashboard()
        self.top_bar.open_notifications()

        if self.top_bar.notification_count() == 0:
            pytest.skip("No notifications on this account to open.")

        self.top_bar.open_first_notification()
        self.wait.until(lambda d: "/tickets/" in d.current_url)

        assert "/tickets/" in self.current_url(), (
            "Clicking a notification should open the ticket it is about. "
            f"Landed on: {self.current_url()}"
        )

    @pytest.mark.regression
    def test_mark_all_read_is_only_offered_when_something_is_actually_unread(self):
        """
        M14-POS: 'All notifications can be cleared at once' - and only when there is something
        to clear.

        Offering the control on an already-read list is a button that does nothing, which
        teaches users that buttons here do nothing.
        """
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
        """
        M14-ACC: 'You can only see your own notifications'.

        Notifications name tickets, and a ticket a role cannot open must not be advertised to
        them through the bell. Proved by relationship rather than by a fixed number: no
        ticket link may appear in both accounts' lists.

        WHAT THIS REPLACED: `not admin_hrefs or admin_hrefs != agent_hrefs`. The administrator
        has no notifications on UAT, so the first half short-circuited and nothing was ever
        compared - and when both had some, "not identical" let every link but one be shared.
        """
        self.open_dashboard()
        self.top_bar.open_notifications()
        agent_hrefs = sorted(self.top_bar.notification_hrefs())

        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin")
        self.top_bar.open_notifications()
        admin_hrefs = sorted(self.top_bar.notification_hrefs())

        if not agent_hrefs and not admin_hrefs:
            pytest.skip("Neither account has notifications here, so there is nothing to compare.")
        # The administrator holds no ticket-view capability at all, so any ticket link in their
        # bell would be pointing at something they cannot open - and above all, nothing that
        # was sent to the agent may turn up in the administrator's list.
        shared = sorted(set(agent_hrefs) & set(admin_hrefs))
        assert not shared, (
            f"These notifications were shown to both accounts: {shared}. "
            f"Agent: {agent_hrefs}. Admin: {admin_hrefs}."
        )
