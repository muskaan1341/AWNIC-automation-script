"""
The bar across the top of every signed-in page: the notification bell, the user menu,
and Sign out.

Note: the notification panel's title gets cut off below ~800px wide, so the suite runs
the browser at 1600x1000.
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class TopBarPage(BasePage):
    # The user menu is the header button showing an email address; the bell is the one without.
    USER_MENU_BUTTON = (By.XPATH, "//header//button[.//div[contains(text(),'@')]]")
    SIGNED_IN_EMAIL = (By.XPATH, "//header//button//div[contains(text(),'@')]")
    SIGN_OUT_BUTTON = (By.XPATH, "//button[normalize-space()='Sign out']")
    NOTIFICATION_PANEL = (By.XPATH, "//*[normalize-space()='Notification']")
    NOTIFICATION_EMPTY_STATE = (By.XPATH, "//*[normalize-space()='No notifications yet']")
    MARK_ALL_READ = (By.XPATH, "//button[normalize-space()='Mark as read all']")

    # ---------- ACTIONS ----------

    def open_user_menu(self):
        self.click(self.USER_MENU_BUTTON)
        self.wait_visible(self.SIGN_OUT_BUTTON)

    def sign_out(self):
        self.open_user_menu()
        self.driver.find_element(*self.SIGN_OUT_BUTTON).click()

    def open_notifications(self):
        """Opens the notification bell (the header button without an email address)."""
        for header_button in self.driver.find_elements(By.CSS_SELECTOR, "header button"):
            if "@" not in header_button.text:
                header_button.click()
                break
        self.wait_visible(self.NOTIFICATION_PANEL)

    def close_notifications(self):
        """
        Closes the notification panel by clicking outside it.
        (Escape does not close this panel.)
        """
        self.click((By.CSS_SELECTOR, "div.fixed.inset-0"))

    def mark_all_notifications_read(self):
        self.click(self.MARK_ALL_READ)

    # ---------- CHECKS ----------

    def get_signed_in_email(self):
        """The email shown beside the avatar."""
        return self.wait_visible(self.SIGNED_IN_EMAIL).text

    def is_notification_panel_open(self):
        return self.exists(self.NOTIFICATION_PANEL)

    def shows_no_notifications(self):
        return self.exists(self.NOTIFICATION_EMPTY_STATE)

    def get_breadcrumb_labels(self):
        """The breadcrumb trail, e.g. ["Tickets", "Enquiries", "INQ-2026-0001"]."""
        trail = self.text_of((By.XPATH, "//header/div[1]/div[1]"))
        labels = []
        for piece in trail.split("/"):
            if piece.strip():
                labels.append(piece.strip())
        return labels

    # ---------- the notification panel ----------

    # The unread count on the bell. Not shown at zero, and shows "9+" above nine.
    UNREAD_BADGE = (
        By.XPATH,
        "//header//button[not(.//div[contains(text(),'@')])]"
        "//span[string-length(normalize-space())<=2 and normalize-space()!='']",
    )

    # Every row in the open panel that links to a ticket.
    NOTIFICATION_LINKS = (By.CSS_SELECTOR, "a[href*='/tickets/']")

    def unread_badge_text(self):
        """The number on the bell, or "" when there is no badge."""
        return self.text_of(self.UNREAD_BADGE)

    def has_unread_badge(self):
        return self.unread_badge_text() != ""

    def unread_badge_count(self):
        """The badge as a number. "9+" is returned as 10."""
        text = self.unread_badge_text()
        if not text:
            return 0
        if text == "9+":
            return 10
        digits = ""
        for character in text:
            if character.isdigit():
                digits += character
        if digits:
            return int(digits)
        return 0

    def notification_hrefs(self):
        """Where each notification row links to."""
        hrefs = []
        for link in self.driver.find_elements(*self.NOTIFICATION_LINKS):
            hrefs.append(link.get_attribute("href"))
        return hrefs

    def open_first_notification(self):
        """Clicks the newest notification."""
        links = self.driver.find_elements(*self.NOTIFICATION_LINKS)
        if not links:
            raise AssertionError("No notification rows are on screen to open.")
        self.scroll_to_middle(links[0])
        links[0].click()

    def has_mark_all_read(self):
        """The "Mark as read all" button is shown only when something is unread."""
        return self.exists(self.MARK_ALL_READ)

    def unread_notification_count(self):
        """
        How many rows in the open panel are unread.
        Unread rows differ from read ones only by their background class (bg-foundation-primary-10).
        """
        unread_rows = self.driver.find_elements(
            By.XPATH,
            "//span[normalize-space()='Notification']/../following-sibling::div[1]"
            "/div[contains(@class,'bg-foundation-primary-10')]",
        )
        return len(unread_rows)

    def has_notification_bell(self):
        """True when the header has the bell (a header button without an email address)."""
        for button in self.driver.find_elements(By.CSS_SELECTOR, "header button"):
            if "@" not in button.text:
                return True
        return False

    def notification_count(self):
        links = self.driver.find_elements(
            By.XPATH, "//*[normalize-space()='Notification']/ancestor::div[2]//a"
        )
        return len(links)
