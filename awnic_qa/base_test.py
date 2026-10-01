"""
The parent of every test class.

It holds the browser (opened/closed by conftest.py), builds every page object once, and
has the helpers every test needs: open(), login_as(), clear_session(), and so on.

    class TestSomething(BaseTest):
        @pytest.fixture(scope="class", autouse=True)
        def sign_in(self, request, browser):
            request.cls.login_class(request.cls.get("agentEmail"))

        def test_something(self):
            self.open("/")
"""

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

# A ticket detail URL ends in the ticket's UUID.
_TICKET_DETAIL_URL = re.compile(
    r".*/tickets/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# The "you don't have access" panel shown by every protected screen.
_ACCESS_DENIED = (
    By.XPATH,
    "//*[contains(normalize-space(.),\"You don't have access to\")"
    " and not(.//*[contains(normalize-space(.),\"You don't have access to\")])]",
)

# The app's own "not found" screen (also shown for a ticket this user may not see).
_PAGE_NOT_FOUND = (
    By.XPATH,
    "//h1[normalize-space()='Page not found' "
    "or normalize-space()='Ticket not available']",
)


class SignInError(RuntimeError):
    """Could not sign in. The message says why."""


class BaseTest:
    # Set by the `browser` fixture in conftest.py.
    driver = None
    wait = None
    base_url: str = ""

    # Who is signed in right now (None = nobody).
    signed_in_as: str | None = None

    # Page objects, built once per class by build_page_objects().
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

    # ------------------------------------------------------------------
    # Setup - called from conftest.py
    # ------------------------------------------------------------------

    @classmethod
    def build_page_objects(cls):
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
    def login_class(cls, email):
        """Signs in once for the whole class (for use in a class-scoped fixture)."""
        cls().login_as(email)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    @staticmethod
    def get(key):
        """A value from the settings file, e.g. get("agentEmail")."""
        return Config.get(key)

    @staticmethod
    def reference(prefix, tail):
        """A seeded reference number with this year in it, e.g. "COM-2026-0001"."""
        return f"{prefix}-{date.today().year}-{tail}"

    # ------------------------------------------------------------------
    # Navigation and waits
    # ------------------------------------------------------------------

    def open(self, path):
        """Opens a page of the app, e.g. open("/tickets/enquiries")."""
        self.driver.get(self.base_url + path)

    def open_and_wait(self, path):
        """
        Opens a page and waits until something real is on screen: the access-denied panel,
        the not-found screen, a redirect, or a heading/table/admin tile.
        Use this before checking "was I allowed in?" - an empty page must not count as a pass.
        """
        self.open(path)
        self.wait_for_page_load()

        def page_arrived(driver):
            if self.is_access_denied() or self.is_page_not_found():
                return True
            if path not in driver.current_url:
                return True
            content = driver.find_elements(
                By.CSS_SELECTOR,
                "h1, h2, table, [data-testid^='admin-stat-'], [data-testid^='user-stat-']",
            )
            return len(content) > 0

        self.wait.until(page_arrived)

    def wait_for_page_load(self):
        """Waits until the browser says the page has finished loading."""
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def wait_for_page_content(self):
        """Waits until the loading skeleton is gone and a heading has rendered."""
        self.wait.until(
            lambda d: not d.find_elements(By.CSS_SELECTOR, "[aria-busy='true']")
            and d.find_elements(By.TAG_NAME, "h1")
        )

    def page_text_snippet(self):
        """The first 400 characters of the page text, for failure messages."""
        text = self.driver.find_element(By.TAG_NAME, "body").text.replace("\n", " | ").strip()
        if len(text) > 400:
            return text[:400] + "…"
        return text

    def wait_for_ticket_detail_url(self):
        """Waits until a ticket detail page (/tickets/<uuid>) is open."""
        self.wait.until(lambda d: _TICKET_DETAIL_URL.match(d.current_url) is not None)

    def wait_for_url_containing(self, fragment):
        self.wait.until(EC.url_contains(fragment))

    def wait_for_url(self, path):
        """Waits until the URL is exactly base_url + path."""
        self.wait.until(lambda d: d.current_url == self.base_url + path)

    def current_url(self):
        return self.driver.current_url

    # ------------------------------------------------------------------
    # Sign-in
    # ------------------------------------------------------------------

    def login_as(self, email):
        """
        Signs in with the email-only dev login (signs the previous user out first).
        If the account does not exist and missingAccountsAreSkipped is true, skips the test.
        """
        try:
            self._login_or_retry_after_rate_limit(email)
        except SignInError as error:
            message = str(error).lower()
            account_missing = "no matching account for this email" in message
            if Config.get_bool("missingAccountsAreSkipped") and account_missing:
                pytest.skip(
                    f"No usable account for {email} on this environment, so this test "
                    f"cannot run here. ({error})"
                )
            raise
        type(self).signed_in_as = email

    def require_ticket_access(self, account_key=None):
        """
        Skips the test if the signed-in account has no role (every screen says "no access").
        Call it straight after signing in.
        """
        if account_key is not None:
            who = self.get(account_key)
        else:
            who = self.signed_in_as or "(nobody)"
        self.open("/tickets/enquiries")
        self.wait_for_page_load()
        if self.is_access_denied():
            pytest.skip(
                f"The account '{who}' can sign in but has NO ROLE granted, so every "
                "screen refuses it. This is missing seed data on this environment, "
                "not a fault in the product or in this test. Grant the role in "
                "user_roles and this test will run."
            )

    def require_write_tests(self):
        """Skips the test unless writeTestsEnabled is true (the test changes real data)."""
        if not Config.get_bool("writeTestsEnabled"):
            pytest.skip(
                "Write test disabled; enable writeTestsEnabled explicitly. This test changes "
                "real data and writeTestsEnabled is false for this environment. Run with "
                "-D writeTestsEnabled=true to include it."
            )

    def _login_or_retry_after_rate_limit(self, email):
        """Signs in. If rate-limited (10 per minute), waits 65 seconds and tries once more."""
        try:
            self._attempt_login(email)
        except SignInError as error:
            message = str(error).lower()
            rate_limited = "429" in message or "rate" in message or "too many" in message
            if not rate_limited:
                raise
            print("Sign-in was rate limited. Waiting a minute and trying once more.")
            time.sleep(65)
            self._attempt_login(email)

    def _attempt_login(self, email):
        self.clear_session()
        self.login.open()
        self.login.sign_in(email)
        try:
            self.wait.until_not(EC.url_contains("/login"))
        except TimeoutException as timeout:
            if self.login.has_error_message():
                reason = self.login.get_error_message()
            else:
                reason = "no error shown"
            raise SignInError(
                f"Could not sign in as {email} - still on the login page. Page says: {reason}"
            ) from timeout

    def login_once(self, email):
        """Signs in only if this email is not already signed in (saves sign-in requests)."""
        if email != self.signed_in_as:
            self.login_as(email)

    def clear_session(self):
        """
        Signs the browser out by deleting all cookies.
        Done on /api/v1/auth/me because only there are BOTH auth cookies visible
        (refresh_token lives on /api/v1/auth), and that page cannot sign us back in.
        """
        self.driver.get(self.base_url + "/api/v1/auth/me")
        self.driver.delete_all_cookies()

        self.login.open()
        type(self).signed_in_as = None

    # ------------------------------------------------------------------
    # Shared checks
    # ------------------------------------------------------------------

    def is_access_denied(self):
        """True when the page shows "You don't have access to ..."."""
        return len(self.driver.find_elements(*_ACCESS_DENIED)) > 0

    def is_page_not_found(self):
        """True when the page shows "Page not found" or "Ticket not available"."""
        return len(self.driver.find_elements(*_PAGE_NOT_FOUND)) > 0

    # ------------------------------------------------------------------
    # Kanban
    # ------------------------------------------------------------------

    def drag_card(self, card, target_column):
        """
        Drags a Kanban card onto a column.
        The board uses pointer events, so drag_and_drop() does not work; move in small steps.
        """
        actions = ActionChains(self.driver)
        actions.move_to_element(card)
        actions.click_and_hold()
        actions.move_by_offset(8, 0)  # small first move so it counts as a drag, not a click
        actions.move_to_element(target_column)
        actions.move_by_offset(0, 10)  # a second move inside the target
        actions.pause(0.25)
        actions.release()
        actions.perform()

    def open_an_open_ticket_from(self, list_path):
        """
        Opens a ticket that is still open (New or In Progress) from the Kanban board.
        Resolved/Closed tickets have no action buttons, so they must not be picked.
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

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) > 0:
            column = KanbanPage.IN_PROGRESS
        else:
            column = KanbanPage.NEW
        if self.kanban.card_count(column) == 0:
            pytest.skip(
                f"No open (New or In Progress) ticket is visible at {list_path}, so there "
                "is no live ticket to act on."
            )
        self.kanban.open_card(self.kanban.first_card_in(column))
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def press_escape(self):
        """Presses Escape - closes a menu or modal, cancels a drag."""
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
