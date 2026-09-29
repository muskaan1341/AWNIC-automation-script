"""
REPLY TO CUSTOMER - the composer that drives the whole ticket lifecycle.

THIS IS THE PRIMARY WAY A TICKET MOVES, and it is easy to miss. The agent does not change
a status by hand: they type a reply here and press Send Reply, and the application does the
rest - the stage goes New -> In Progress, the 24-hour Tier 1 clock stops, and the audit
trail records what was said. "Change Status" is the manual override, not the main road.

SENDING FROM HERE SENDS A REAL EMAIL TO A REAL CUSTOMER. The send is threaded onto the
original conversation through Graph, from the watched mailbox the enquiry arrived on - not
from the agent's own. Nothing in this page object presses Send by accident, and the one
test that does is behind its own switch (see test_08b_reply_lifecycle.py).

The composer is always VISIBLE but goes DISABLED when the ticket is locked to somebody else
or is a merged duplicate, with the reason in a tooltip on the control itself. So "can this
person reply?" is answered by is_send_enabled(), never by whether the card is on the page.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class ReplyPage(BasePage):
    CARD = (
        By.XPATH,
        "//h3[translate(normalize-space(),"
        "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')='REPLY TO CUSTOMER']",
    )
    # Anchored on the ARIA LABEL, not the placeholder. The placeholder is dropped entirely
    # while the composer is locked (ReplyToCustomerCard passes placeholder={locked ?
    # undefined : ...}), so a placeholder locator finds nothing on exactly the tickets whose
    # lock behaviour is most worth testing - and reports "no composer" when the truth is
    # "composer present and correctly disabled". That cost this class its first run.
    #
    # Note also: components/ticket/ReplyBox.tsx has a "Type your reply here..." placeholder
    # and is NOT the component the app renders - nothing imports it but its own unit test.
    # Do not take locators from it.
    COMPOSER = (By.CSS_SELECTOR, "textarea[aria-label='Write a reply to the customer']")
    SEND_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Send Reply' or normalize-space()='Sending…']",
    )

    # ---- checks ----

    def is_card_displayed(self) -> bool:
        return self.exists(self.CARD)

    def is_composer_displayed(self) -> bool:
        return self.exists(self.COMPOSER)

    def is_composer_enabled(self) -> bool:
        return self.exists(self.COMPOSER) and self.driver.find_element(
            *self.COMPOSER
        ).is_enabled()

    def is_send_displayed(self) -> bool:
        return self.exists(self.SEND_BUTTON)

    def is_send_enabled(self) -> bool:
        return self.exists(self.SEND_BUTTON) and self.driver.find_element(
            *self.SEND_BUTTON
        ).is_enabled()

    def get_lock_tooltip(self) -> str:
        """The tooltip that says WHY the composer is disabled - the lock reason, in words."""
        if not self.exists(self.COMPOSER):
            return ""
        on_box = self.driver.find_element(*self.COMPOSER).get_attribute("title")
        return on_box or ""

    def names_the_sending_mailbox(self) -> bool:
        """The mailbox badge - replies go out from the watched alias, not the agent's own."""
        return self.exists((By.XPATH, "//*[@title[contains(.,'send from')]]"))

    def sending_mailbox(self) -> tuple[str, str]:
        """
        The mailbox badge in the composer's header: (the address it shows, its tooltip).

        ("", "") when there is no badge. ReplyToCustomerCard renders the address as the
        badge's text and repeats it in the tooltip ("Replies on this ticket send from X, not
        your own mailbox."), so a test can check the two name the SAME mailbox rather than
        only that some badge exists.
        """
        badges = self.driver.find_elements(
            By.XPATH, "//span[starts-with(@title, 'Replies on this ticket send from ')]"
        )
        if not badges:
            return "", ""
        return badges[0].text.strip(), badges[0].get_attribute("title") or ""

    # ---- actions (typing only; pressing Send is deliberately separate) ----

    def type_reply(self, text: str) -> None:
        self.type_into(self.COMPOSER, text)

    def clear_reply(self) -> None:
        self.clear_box(self.wait_visible(self.COMPOSER))

    def press_send_reply(self) -> None:
        """
        PRESSES SEND. This really emails the customer - see the module comment. Only call it
        from a test that has already checked it is allowed to write to this environment.
        """
        self.click(self.SEND_BUTTON)

    def is_sent(self) -> bool:
        """
        True once the send has been accepted.

        The button does NOT latch to "Sent" - it returns to "Send Reply" and a toast appears
        instead, because the real Graph send runs as a background task and the composer is
        deliberately freed straight away. So the honest signal is the toast, not the button.
        """
        return self.exists(self.innermost_containing("Reply sent"))
