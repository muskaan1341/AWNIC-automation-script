"""
The REPLY TO CUSTOMER card on a ticket.

Sending a reply is the main way a ticket moves forward (New -> In Progress, and the Tier 1
clock stops).

WARNING: pressing Send Reply sends a REAL email to a REAL customer. Only
press_send_reply() does that, and only one test calls it.

The composer is always shown, but is disabled (with the reason in a tooltip) when the ticket
is locked to someone else or is a merged duplicate - so use is_send_enabled() to ask
"can this user reply?".
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage


class ReplyPage(BasePage):
    CARD = (
        By.XPATH,
        "//h3[translate(normalize-space(),"
        "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')='REPLY TO CUSTOMER']",
    )
    # The composer is a rich-text editor (a contenteditable div), not a <textarea>.
    # Found by its aria-label because the placeholder disappears when it is locked.
    COMPOSER = (
        By.CSS_SELECTOR, "[role='textbox'][aria-label='Write a reply to the customer']"
    )
    SEND_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Send Reply' or normalize-space()='Sending…']",
    )

    # ---- checks ----

    def is_card_displayed(self):
        return self.exists(self.CARD)

    def is_composer_displayed(self):
        return self.exists(self.COMPOSER)

    def is_composer_enabled(self):
        if not self.exists(self.COMPOSER):
            return False
        composer = self.driver.find_element(*self.COMPOSER)
        return composer.get_attribute("contenteditable") == "true"

    def is_send_displayed(self):
        return self.exists(self.SEND_BUTTON)

    def is_send_enabled(self):
        if not self.exists(self.SEND_BUTTON):
            return False
        return self.driver.find_element(*self.SEND_BUTTON).is_enabled()

    def get_lock_tooltip(self):
        """The tooltip saying why the composer is disabled ("" if none)."""
        if not self.exists(self.COMPOSER):
            return ""
        # The reason is in the title of the editor's wrapper <div>.
        wrappers = self.driver.find_element(*self.COMPOSER).find_elements(
            By.XPATH, "ancestor::div[@title][1]"
        )
        if not wrappers:
            return ""
        return wrappers[0].get_attribute("title") or ""

    def names_the_sending_mailbox(self):
        """True when the badge naming the mailbox replies are sent from is shown."""
        return self.exists((By.XPATH, "//*[@title[contains(.,'send from')]]"))

    def sending_mailbox(self):
        """The mailbox badge as (address shown, tooltip), or ("", "") when there is none."""
        badges = self.driver.find_elements(
            By.XPATH, "//span[starts-with(@title, 'Replies on this ticket send from ')]"
        )
        if not badges:
            return "", ""
        return badges[0].text.strip(), badges[0].get_attribute("title") or ""

    # ---- actions ----

    def type_reply(self, text):
        self.type_into(self.COMPOSER, text)

    def clear_reply(self):
        """Empties the editor with Backspace (clear_box does not work on this editor)."""
        box = self.wait_visible(self.COMPOSER)
        box.click()
        box.send_keys(Keys.END)
        for _ in range(len(box.text) + 1):
            box.send_keys(Keys.BACK_SPACE)

    def press_send_reply(self):
        """PRESSES SEND - this really emails the customer."""
        self.click(self.SEND_BUTTON)

    def is_sent(self):
        """True once the "Reply sent" message appears (the button itself goes back to normal)."""
        return self.exists(self.innermost_containing("Reply sent"))
