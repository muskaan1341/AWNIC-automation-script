"""
The parent of every test class. It does three jobs:

  1. opens the browser before the class and closes it after,
  2. builds every page object ONCE, so a test never writes "SomethingPage(...)",
  3. holds the handful of helpers every test needs - open(), login_as(), clear_session().

A test class therefore starts like this and nothing else:

    class TestSomething(BaseTest):
        def test_something(self):
            self.open("/")
            ...

If the class needs to be signed in for all of its tests, add the class-scoped hook:

    class TestSomething(BaseTest):
        @pytest.fixture(scope="class", autouse=True)
        def sign_in(self, browser):
            self.login_as(self.get("agentEmail"))

WHY IS THE BROWSER OPENED PER CLASS, NOT PER TEST?
The sign-in endpoint is rate limited to 10 requests per minute per IP address. A fresh
browser and a fresh login for every single test method would trip that limit part way
through the run and produce failures that have nothing to do with the product. So each
class opens one browser, signs in once, and each test navigates to the page it needs.

The browser lifecycle itself lives in conftest.py as class- and function-scoped fixtures,
which is how pytest expresses TestNG's @BeforeClass / @AfterClass / @BeforeMethod.
"""

from __future__ import annotations

import re
import time
from datetime import date

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from awnic_qa.config import Config
from awnic_qa.pages.admin_page import AdminPage
from awnic_qa.pages.customer_records_page import CustomerRecordsPage
from awnic_qa.pages.dashboard_page import DashboardPage
from awnic_qa.pages.discarded_list_page import DiscardedListPage
from awnic_qa.pages.investigation_page import InvestigationPage
from awnic_qa.pages.kanban_page import KanbanPage
from awnic_qa.pages.login_page import LoginPage
from awnic_qa.pages.new_ticket_page import NewTicketPage
from awnic_qa.pages.reply_page import ReplyPage
from awnic_qa.pages.reports_page import ReportsPage
from awnic_qa.pages.side_nav_page import SideNavPage
from awnic_qa.pages.sla_page import SlaPage
from awnic_qa.pages.ticket_detail_page import TicketDetailPage
from awnic_qa.pages.ticket_edit_page import TicketEditPage
from awnic_qa.pages.ticket_list_page import TicketListPage
from awnic_qa.pages.top_bar_page import TopBarPage

#: A ticket id is a UUID. See wait_for_ticket_detail_url().
_TICKET_DETAIL_URL = re.compile(
    r".*/tickets/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class SignInError(RuntimeError):
    """The suite could not sign in. Carries the reason the page gave."""


class BaseTest:
    # Set by the class-scoped `browser` fixture in conftest.py.
    driver = None
    wait = None
    base_url: str = ""

    #: Whoever is signed in right now, so login_once can skip a needless round trip.
    signed_in_as: str | None = None

    # ---- page objects: created once, used by name in every test ----
    login: LoginPage
    nav: SideNavPage
    top_bar: TopBarPage
    dashboard: DashboardPage
    list: TicketListPage
    detail: TicketDetailPage
    new_ticket: NewTicketPage
    edit_ticket: TicketEditPage
    kanban: KanbanPage
    discarded: DiscardedListPage
    admin: AdminPage
    reports: ReportsPage
    reply: ReplyPage
    sla: SlaPage
    investigation: InvestigationPage
    customer_records: CustomerRecordsPage

    # ==================================================================
    # Wiring - called by the fixtures in conftest.py
    # ==================================================================

    @classmethod
    def build_page_objects(cls) -> None:
        cls.login = LoginPage(cls.driver, cls.wait, cls.base_url)
        cls.nav = SideNavPage(cls.driver, cls.wait)
        cls.top_bar = TopBarPage(cls.driver, cls.wait)
        cls.dashboard = DashboardPage(cls.driver, cls.wait)
        cls.list = TicketListPage(cls.driver, cls.wait)
        cls.detail = TicketDetailPage(cls.driver, cls.wait)
        cls.new_ticket = NewTicketPage(cls.driver, cls.wait)
        cls.edit_ticket = TicketEditPage(cls.driver, cls.wait)
        cls.kanban = KanbanPage(cls.driver, cls.wait)
        cls.discarded = DiscardedListPage(cls.driver, cls.wait)
        cls.admin = AdminPage(cls.driver, cls.wait)
        cls.reports = ReportsPage(cls.driver, cls.wait)
        cls.reply = ReplyPage(cls.driver, cls.wait)
        cls.sla = SlaPage(cls.driver, cls.wait)
        cls.investigation = InvestigationPage(cls.driver, cls.wait)
        cls.customer_records = CustomerRecordsPage(cls.driver, cls.wait)

    @classmethod
    def login_class(cls, email: str) -> None:
        """
        Signs in for a whole test class - the equivalent of TestNG's @BeforeClass sign-in.

        Every piece of state this needs (driver, wait, page objects, signed_in_as) lives on
        the CLASS, set there by the `browser` fixture, so a throwaway instance is enough to
        reach the instance methods. A class-scoped pytest fixture has no test instance of its
        own, which is why this exists rather than calling login_as directly.

        Used as:
            @pytest.fixture(scope="class", autouse=True)
            def sign_in(self, request, browser):
                request.cls.login_class(request.cls.get("agentEmail"))
        """
        cls().login_as(email)

    # ==================================================================
    # Settings
    # ==================================================================

    @staticmethod
    def get(key: str) -> str:
        """A value from config.properties, e.g. get("agentEmail")."""
        return Config.get(key)

    @staticmethod
    def reference(prefix: str, tail: str) -> str:
        """
        A seeded reference number, e.g. reference("COM", "0001") -> "COM-2026-0001".

        The seed script stamps the CURRENT year into every reference number, so writing
        "COM-2026-0001" in a test would quietly start failing on 1 January.
        """
        return f"{prefix}-{date.today().year}-{tail}"

    # ==================================================================
    # Navigation and sign-in
    # ==================================================================

    def open(self, path: str) -> None:
        """Opens a page of the application, e.g. open("/tickets/enquiries")."""
        self.driver.get(self.base_url + path)

    def open_and_wait(self, path: str) -> None:
        """
        Opens a page and waits until it has actually finished arriving.

        USE THIS, NOT open(), WHENEVER THE NEXT LINE ASKS "was I allowed in?". A plain open()
        returns as soon as the browser starts loading, so checking for the access-denied panel
        straight afterwards can read a page that has not rendered yet - and an empty page looks
        exactly like "I was allowed in". That is a false pass on an access-control test, which
        is the worst kind of green there is.

        "Finished arriving" means one of: the access-denied panel is up, the not-found screen
        is up, a heading has rendered, or we were redirected somewhere else entirely.
        """
        self.open(path)
        # First: the browser has finished loading. Without this, everything below can be
        # asked of a page that has not arrived, and an empty page looks exactly like
        # "I was allowed in" - a false pass on an access test, the worst kind of green.
        self.wait_for_page_load()
        # Then: something recognisable is on screen. Note the admin dashboard has no <h1>
        # at all - it is built from KPI tiles - so a heading alone is not enough to go on.
        self.wait.until(
            lambda d: self.is_access_denied()
            or self.is_page_not_found()
            or path not in d.current_url
            or len(
                d.find_elements(
                    By.CSS_SELECTOR,
                    "h1, h2, table, [data-testid^='admin-stat-'], [data-testid^='user-stat-']",
                )
            )
            > 0
        )

    def wait_for_page_load(self) -> None:
        """
        Waits only until the browser has finished loading - no assumption about WHAT arrived.

        open_and_wait() is the one to reach for normally, because it also waits for something
        recognisable to render. Use this one for the handful of tests whose whole point is
        that a page did NOT render (a rejected query string, an error page), where waiting for
        a heading or a table would time out on a perfectly correct result.
        """
        self.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def wait_for_page_content(self) -> None:
        """
        Waits until the route has actually RESOLVED - skeleton gone, real page rendered.

        wait_for_page_load() only waits for document.readyState, which goes "complete" while
        Next's route-level loading.tsx skeleton is still on screen. A test that asked "was I
        refused?" at that moment read the skeleton and reported a data-isolation breach that
        had not happened (2026-09-29); the server had answered 404 exactly as it should.

        Waits on the skeleton's own signal (loading.tsx sets aria-busy="true") plus a real
        heading, so it settles on EITHER outcome - the ticket, or the refusal - and never
        assumes which one arrives. Use it wherever the point of the test is what the resolved
        page says.
        """
        self.wait.until(
            lambda d: not d.find_elements(By.CSS_SELECTOR, "[aria-busy='true']")
            and d.find_elements(By.TAG_NAME, "h1")
        )

    def page_text_snippet(self) -> str:
        """
        The first few hundred characters the page is showing.

        Only for failure messages. "The agent reached /user-management" is a frustrating thing
        to read on its own; "...and the page said: You don't have access to User Management"
        tells you immediately that the product is fine and the test is looking in the wrong
        place.
        """
        text = (
            self.driver.find_element(By.TAG_NAME, "body").text.replace("\n", " | ").strip()
        )
        return text[:400] + "…" if len(text) > 400 else text

    def wait_for_ticket_detail_url(self) -> None:
        """
        Waits until a TICKET DETAIL page is open.

        The obvious ".*/tickets/[^/]+$" is a trap: it also matches
        "/tickets/complaints?search=COM-2026-0005", because the query string contains no
        slash. A ticket id is a UUID, so match that instead - otherwise a test can believe it
        opened a ticket while it is still sitting on the list.
        """
        self.wait.until(lambda d: _TICKET_DETAIL_URL.match(d.current_url) is not None)

    def wait_for_url_containing(self, fragment: str) -> None:
        """Waits until the address bar contains this text."""
        self.wait.until(EC.url_contains(fragment))

    def wait_for_url(self, path: str) -> None:
        """Waits until the address bar is exactly base_url + path."""
        self.wait.until(lambda d: d.current_url == self.base_url + path)

    def current_url(self) -> str:
        return self.driver.current_url

    def login_as(self, email: str) -> None:
        """
        Signs in with the dev email login.

        The application has no password field - AWNIC One single sign-on is the real login,
        and locally that is replaced by a form that takes an email only. Signs the previous
        user out first, so one test class can move between roles.
        """
        try:
            self._login_or_retry_after_rate_limit(email)
        except SignInError as cannot_sign_in:
            # On a SHARED environment only a few of the eight roles have an account, so a
            # test for one of the others should say "not available here" rather than shout
            # that something is broken. On your own laptop every account is seeded, so this
            # stays switched off and a failed sign-in is reported as the real problem it is.
            #
            # ONLY a genuinely missing account may skip. This used to skip on ANY sign-in
            # failure, which meant a broken browser, a site that was down or a rate-limited
            # endpoint all reported themselves as "no account here" - a quiet green-ish skip
            # hiding a real problem. The API says exactly one sentence for a missing account
            # ("No matching account for this email", app/auth/routes.py), so that sentence
            # is what we look for; anything else is a failure and is reported as one.
            if Config.get_bool("missingAccountsAreSkipped") and _looks_like_a_missing_account(
                str(cannot_sign_in)
            ):
                pytest.skip(
                    f"No usable account for {email} on this environment, so this test "
                    f"cannot run here. ({cannot_sign_in})"
                )
            raise
        type(self).signed_in_as = email

    def require_ticket_access(self, account_key: str | None = None) -> None:
        """
        Skips the calling test when the signed-in account has been granted NO ROLE.

        WHY THIS EXISTS - it turns twenty mystery failures into one clear sentence.

        An account with no role in `user_roles` can sign in perfectly well and then see
        nothing at all: every screen answers "You don't have access to ...". A test that
        simply waited for the page heading then sat there for the full timeout and failed
        with "waiting for visibility of element located by By.tagName: h1" - which says
        nothing whatsoever about the real problem. That single cause produced most of the
        red in the 2026-09-03 run.

        On the shared environment as of 2026-09-04, FIVE of the seven test accounts are in
        this state - supervisor, hod, complaints.manager, complaints.officer and compliance
        all have zero rows in user_roles. The roles themselves are configured correctly; it
        is only the grant to these accounts that is missing.

        Call this straight after signing in, before opening the screen under test. With no
        argument it asks about whoever is signed in right now.
        """
        who = (
            self.get(account_key)
            if account_key is not None
            else (self.signed_in_as or "(nobody)")
        )
        self.open("/tickets/enquiries")
        self.wait_for_page_load()
        if self.is_access_denied():
            pytest.skip(
                f"The account '{who}' can sign in but has NO ROLE granted, so every "
                "screen refuses it. This is missing seed data on this environment, "
                "not a fault in the product or in this test. Grant the role in "
                "user_roles and this test will run."
            )

    def require_write_tests(self) -> None:
        """
        Skips the calling test unless this environment allows writing.

        Every test that CHANGES REAL DATA calls this first - creating a ticket, moving one
        between board columns, marking somebody's notifications read. On a shared environment
        they are switched off, so a routine run does not leave changes that other people
        testing the same site would have to wonder about.
        """
        if not Config.get_bool("writeTestsEnabled"):
            pytest.skip(
                "Write test disabled; enable writeTestsEnabled explicitly. This test changes "
                "real data and writeTestsEnabled is false for this environment. Run with "
                "-D writeTestsEnabled=true to include it."
            )

    def _login_or_retry_after_rate_limit(self, email: str) -> None:
        try:
            self._attempt_login(email)
        except SignInError as first_attempt:
            # The sign-in endpoint allows only 10 requests a minute per computer. A suite
            # with a dozen classes, each signing in, can genuinely hit that - and when it
            # does, the failure has nothing to do with the product. Waiting out the minute
            # and trying once more turns a confusing red run into a slightly slower green
            # one. Anything that fails the SECOND time is a real problem and is reported.
            if not _looks_like_rate_limiting(str(first_attempt)):
                raise
            print("Sign-in was rate limited. Waiting a minute and trying once more.")
            time.sleep(65)
            self._attempt_login(email)

    def _attempt_login(self, email: str) -> None:
        self.clear_session()
        self.login.open()
        self.login.sign_in(email)
        try:
            self.wait.until_not(EC.url_contains("/login"))
        except TimeoutException as timeout:
            # Say WHY the sign-in failed instead of a bare "timed out after 40 seconds".
            reason = (
                self.login.get_error_message()
                if self.login.has_error_message()
                else "no error shown"
            )
            raise SignInError(
                f"Could not sign in as {email} - still on the login page. Page says: {reason}"
            ) from timeout

    def login_once(self, email: str) -> None:
        """
        Signs in ONLY if somebody else (or nobody) is signed in.

        RoleAccessTest walks through several accounts and checks a few things about each.
        Calling login_as before every single check would be a login per assertion and would
        hit the 10-per-minute rate limit half way through the class.
        """
        if email != self.signed_in_as:
            self.login_as(email)

    def clear_session(self) -> None:
        """
        Puts the browser back into a signed-out state.

        TWO cookie deletes are needed, and this is a real quirk of the application:
        access_token is stored on path "/", but refresh_token is stored on "/api/v1/auth".
        Chrome only deletes cookies visible to the CURRENT page, so deleting from /login
        alone leaves refresh_token behind - and the login page silently uses it to sign us
        straight back in, which makes every "signed out" test pass while testing nothing.

        So the delete happens on /api/v1/auth/me, where BOTH paths are visible, and never
        on /login first. /login fires POST /auth/refresh the moment it mounts; while the
        refresh cookie still exists that call succeeds, and its Set-Cookie can land AFTER
        the delete, reviving the session and redirecting to "/" (reproduced 4/4 against
        the deployed site on 2026-09-17). The auth/me URL is plain JSON - no page script,
        no refresh call - so nothing can race the delete there.

        login.open() then waits for the email box, which the login page only renders once
        its own refresh call has FAILED - i.e. the server confirmed there is no session.
        """
        self.driver.get(self.base_url + "/api/v1/auth/me")
        self.driver.delete_all_cookies()

        self.login.open()
        type(self).signed_in_as = None

    # ==================================================================
    # Shared checks - screens that look the same everywhere
    # ==================================================================

    def is_access_denied(self) -> bool:
        """
        True when the current page is one of the shared "you don't have access" panels.

        Twelve screens use the same sentence with only the module name changing (Dashboard,
        Reports, Audit Trail, User Management, ...), so one matcher covers all of them.
        Matching on the FIXED half of the sentence keeps it working when a module is added.
        """
        return (
            len(
                self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(normalize-space(.),\"You don't have access to\")"
                    " and not(.//*[contains(normalize-space(.),\"You don't have access to\")])]",
                )
            )
            > 0
        )

    def is_page_not_found(self) -> bool:
        """
        The application's own "you cannot have this" screen - NOT the stock Next.js 404.

        There are TWO wordings and both count:
          "Page not found"        a URL that matches no route at all
          "Ticket not available"  a ticket that either does not exist OR that this user may
                                  not see. The wording is deliberately the same for both, so
                                  nobody can work out which tickets exist by probing ids.
        """
        return (
            len(
                self.driver.find_elements(
                    By.XPATH,
                    "//h1[normalize-space()='Page not found' "
                    "or normalize-space()='Ticket not available']",
                )
            )
            > 0
        )

    # ==================================================================
    # Kanban drag
    # ==================================================================

    def drag_card(self, card, target_column) -> None:
        """
        Drags a Kanban card onto a column.

        WHY NOT ActionChains.drag_and_drop(card, column)?
        That convenience method speaks the LEGACY HTML5 drag protocol (dragstart / dragover /
        drop). The board is built on a library called dnd-kit, which listens to POINTER
        events instead (pointerdown / pointermove / pointerup). The two never meet: the card
        simply does not move, and the test fails for a reason that has nothing to do with the
        product.

        The sequence below is what dnd-kit actually needs: press, a small move to get past its
        5-pixel "is this a drag or a click?" threshold, then moves into the target so it
        registers a hover, then release. One big jump straight into the target is often not
        seen at all.

        Always assert on the OUTCOME afterwards (column counts, the ticket's status), never on
        the animation - the animation is not a behaviour anybody specified.
        """
        (
            ActionChains(self.driver)
            .move_to_element(card)
            .click_and_hold()
            .move_by_offset(8, 0)  # get past dnd-kit's activation distance
            .move_to_element(target_column)
            .move_by_offset(0, 10)  # a second move inside the target
            .pause(0.25)
            .release()
            .perform()
        )

    def open_an_open_ticket_from(self, list_path: str) -> None:
        """
        Opens a ticket that is still OPEN, and fails loudly rather than quietly picking a
        finished one.

        WHY THIS EXISTS. The entire action header - More Action, Change Status, the reply
        composer - is REMOVED from a Resolved or Closed ticket (`if (isClosed) return null` in
        TicketHeaderActions). That is correct: there is nothing left to do to a finished
        ticket. But it means any test that opens "the first row in the list" can land on a
        Resolved one and read "no actions" as "this role is not allowed", which is a false
        failure about permissions on a ticket where nobody has any. Three classes have now
        been caught by it.

        The board is the reliable source: New and In Progress are open by definition (Resolved
        is its own column and Closed is off the board entirely), so a card from either still
        has its actions.
        """
        self.open(list_path)
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(
                f"No tickets are visible at {list_path} for this user, so there is no "
                "ticket to open."
            )
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        column = (
            KanbanPage.IN_PROGRESS
            if self.kanban.card_count(KanbanPage.IN_PROGRESS) > 0
            else KanbanPage.NEW
        )
        if self.kanban.card_count(column) == 0:
            pytest.skip(
                f"No open (New or In Progress) ticket is visible at {list_path}, so there "
                "is no live ticket to act on."
            )
        self.kanban.open_card(self.kanban.first_card_in(column))
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def press_escape(self) -> None:
        """Presses Escape - cancels a drag, closes a menu, closes a modal."""
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()


def _looks_like_a_missing_account(message: str | None) -> bool:
    """
    True only for the API's own "this email has no account" answer.

    Deliberately narrow. Everything else - a dead browser, a site that is down, a rate
    limit - must fail rather than skip, because a skip reads as "nothing to see here".
    """
    return message is not None and "no matching account for this email" in message.lower()


def _looks_like_rate_limiting(message: str | None) -> bool:
    if message is None:
        return False
    lower = message.lower()
    return "429" in lower or "rate" in lower or "too many" in lower
