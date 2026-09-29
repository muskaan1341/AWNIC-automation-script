"""
The bar across the top of every signed-in page: the notification bell, the user menu,
and Sign out.

WORTH KNOWING before you widen a failure here into a bug report: the notification panel's
title is clipped by the main column at around 800px wide. The suite runs the browser at
1600x1000 for exactly this reason.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class TopBarPage(BasePage):
    # The user menu is the header button that shows an email address; the bell is the one
    # that does not. Locating them by that difference survives an icon or styling change.
    USER_MENU_BUTTON = (By.XPATH, "//header//button[.//div[contains(text(),'@')]]")
    SIGNED_IN_EMAIL = (By.XPATH, "//header//button//div[contains(text(),'@')]")
    SIGN_OUT_BUTTON = (By.XPATH, "//button[normalize-space()='Sign out']")
    NOTIFICATION_PANEL = (By.XPATH, "//*[normalize-space()='Notification']")
    NOTIFICATION_EMPTY_STATE = (By.XPATH, "//*[normalize-space()='No notifications yet']")
    #: The panel's own control, by the text TopBar renders: "Mark as read all". It was
    #: matched on "Mark all" before, which that sentence does not contain - so the control
    #: was never found and "is it offered?" always answered no.
    MARK_ALL_READ = (By.XPATH, "//button[normalize-space()='Mark as read all']")

    # ---------- ACTIONS ----------

    def open_user_menu(self) -> None:
        self.click(self.USER_MENU_BUTTON)
        self.wait_visible(self.SIGN_OUT_BUTTON)

    def sign_out(self) -> None:
        self.open_user_menu()
        self.driver.find_element(*self.SIGN_OUT_BUTTON).click()

    def open_notifications(self) -> None:
        """Opens the notification bell - the header button that carries no email address."""
        for header_button in self.driver.find_elements(By.CSS_SELECTOR, "header button"):
            if "@" not in header_button.text:
                header_button.click()
                break
        self.wait_visible(self.NOTIFICATION_PANEL)

    def close_notifications(self) -> None:
        """
        Closes the notification panel THE WAY THE PRODUCT CLOSES IT - by clicking away.

        TopBar renders a full-screen catcher behind the open panel
        (`<div className="fixed inset-0 z-30" onClick={() => setNotifOpen(false)} />`) and
        carries no key handling at all, so Escape does nothing here: a test that pressed it
        waited out the full timeout on a panel that was never going to close. Clicking the
        catcher is the same gesture a user makes when they click off the panel.
        """
        self.click((By.CSS_SELECTOR, "div.fixed.inset-0"))

    def mark_all_notifications_read(self) -> None:
        self.click(self.MARK_ALL_READ)

    # ---------- CHECKS ----------

    def get_signed_in_email(self) -> str:
        """The email beside the avatar - the honest proof of who is signed in."""
        return self.wait_visible(self.SIGNED_IN_EMAIL).text

    def is_notification_panel_open(self) -> bool:
        return self.exists(self.NOTIFICATION_PANEL)

    def shows_no_notifications(self) -> bool:
        return self.exists(self.NOTIFICATION_EMPTY_STATE)

    def get_breadcrumb_labels(self) -> list[str]:
        """
        The breadcrumb trail, e.g. ["Tickets", "Enquiries", "INQ-2026-0001"].

        It lives in the top bar, as the FIRST thing inside the header, with "/" between the
        crumbs. Worth testing because it is now ROLE-AWARE: it mirrors whatever shape the
        left-hand menu takes for this user, so a Head of Department sees "Tickets / Enquiries"
        while an agent sees just "Enquiries Tickets".
        """
        trail = self.text_of((By.XPATH, "//header/div[1]/div[1]"))
        return [piece.strip() for piece in trail.split("/") if piece.strip()]

    # ------------------------------------------------------------------
    # The notification panel's own detail (module 14)
    # ------------------------------------------------------------------
    # The bell carries an unread BADGE, and each row is a link through to the ticket it is
    # about. Read and unread rows use the same text treatment and differ only by background
    # (`bg-foundation-primary-10` unread, `bg-white` read), which is why these read the count
    # and the links rather than the styling.

    #: The unread badge. Absent entirely at zero, and capped at "9+" above nine.
    UNREAD_BADGE = (
        By.XPATH,
        "//header//button[not(.//div[contains(text(),'@')])]"
        "//span[string-length(normalize-space())<=2 and normalize-space()!='']",
    )

    #: Every row in the open panel that links through to a ticket.
    NOTIFICATION_LINKS = (By.CSS_SELECTOR, "a[href*='/tickets/']")

    def unread_badge_text(self) -> str:
        """The number on the bell, or "" when nothing is unread (the badge is not rendered)."""
        return self.text_of(self.UNREAD_BADGE)

    def has_unread_badge(self) -> bool:
        return self.unread_badge_text() != ""

    def unread_badge_count(self) -> int:
        """
        The badge as a number. "9+" means "more than nine", which is reported as 10.

        The cap is deliberate in the product - a two-character badge keeps the header from
        reflowing - so a test must never expect an exact figure above nine.
        """
        text = self.unread_badge_text()
        if not text:
            return 0
        if text == "9+":
            return 10
        digits = "".join(c for c in text if c.isdigit())
        return int(digits) if digits else 0

    def notification_hrefs(self) -> list[str]:
        """Where each notification row points. Every one must name a real ticket."""
        return [
            link.get_attribute("href")
            for link in self.driver.find_elements(*self.NOTIFICATION_LINKS)
        ]

    def open_first_notification(self) -> None:
        """Clicks through to the ticket the newest notification is about."""
        links = self.driver.find_elements(*self.NOTIFICATION_LINKS)
        if not links:
            raise AssertionError("No notification rows are on screen to open.")
        self.scroll_to_middle(links[0])
        links[0].click()

    def has_mark_all_read(self) -> bool:
        """Offered only when something is unread - a control that does nothing teaches nothing."""
        return self.exists(self.MARK_ALL_READ)

    def unread_notification_count(self) -> int:
        """
        How many rows in the open panel are UNREAD.

        The product's only read/unread cue is the row background - `bg-foundation-primary-10`
        when unread, `bg-white` when read (TopBar) - with identical text either way, so this is
        the one honest way to count them from a browser. Kept here rather than in a test: it is
        knowledge about how the panel renders, and it is the only reason a badge assertion can
        be more than "a badge exists".
        """
        # Scoped to the panel's own row list (the block after its "Notification" header), and
        # NOT restricted to rows with a ticket link: the badge counts every unread row
        # (`notifications.filter(n => !n.read_at)`), and a notification with no ticket has no
        # link but is still unread.
        return len(
            self.driver.find_elements(
                By.XPATH,
                "//span[normalize-space()='Notification']/../following-sibling::div[1]"
                "/div[contains(@class,'bg-foundation-primary-10')]",
            )
        )

    def has_notification_bell(self) -> bool:
        """
        True when the header carries the bell at all.

        The bell lives in the app shell, which a signed-out visitor never gets - so its absence
        is what "no bell" means, and it is different from "the panel did not open".
        """
        return any(
            "@" not in button.text
            for button in self.driver.find_elements(By.CSS_SELECTOR, "header button")
        )

    def notification_count(self) -> int:
        return len(
            self.driver.find_elements(
                By.XPATH, "//*[normalize-space()='Notification']/ancestor::div[2]//a"
            )
        )
