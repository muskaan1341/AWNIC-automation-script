"""
The Kanban board - the second view on every ticket list (the "Kanban" button).

It has exactly four columns: New, In Progress, Pending POC, Resolved.
Escalated tickets sit in Pending POC with a badge; Closed and Discarded tickets are not on
the board. A ticket can never be dragged back into "New".

To drag a card use BaseTest.drag_card(...), not ActionChains.drag_and_drop.
"""

import re

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class KanbanPage(BasePage):
    NEW = "New"
    IN_PROGRESS = "In Progress"
    PENDING_POC = "Pending POC"
    RESOLVED = "Resolved"

    # The four columns, left to right.
    COLUMNS = [NEW, IN_PROGRESS, PENDING_POC, RESOLVED]

    ANY_COLUMN = (By.CSS_SELECTOR, "[data-testid^='kanban-column-']")
    ANY_CARD = (By.CSS_SELECTOR, "[data-testid='kanban-card']")
    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")

    @staticmethod
    def column(title):
        return (By.CSS_SELECTOR, f"[data-testid='kanban-column-{title}']")

    # ---------------- Actions ----------------

    def wait_until_loaded(self):
        self.wait_visible(self.column(self.NEW))

    def column_element(self, title):
        return self.driver.find_element(*self.column(title))

    def cards_in(self, title):
        """The cards in one column."""
        return self.driver.find_element(*self.column(title)).find_elements(*self.ANY_CARD)

    def first_card_in(self, title):
        cards = self.cards_in(title)
        if not cards:
            raise AssertionError(
                f"No cards in the '{title}' column - this test needs seeded data there. "
                "Run 'make seed-demo' before the suite."
            )
        return cards[0]

    def wait_for_card_count(self, title, expected):
        self.wait.until(lambda d: len(self.cards_in(title)) == expected)

    def card_links(self, columns=None):
        """A (reference, ticket URL) pair for every card in these columns (default: all four)."""
        pairs = []
        for column in columns or self.COLUMNS:
            for card in self.cards_in(column):
                links = card.find_elements(By.CSS_SELECTOR, "a[href*='/tickets/']")
                if links:
                    pairs.append((links[0].text.strip(), links[0].get_attribute("href")))
        return pairs

    def open_card(self, card):
        """Opens a card's ticket by clicking it."""
        card.click()

    # ---------------- Checks ----------------

    def get_column_titles(self):
        """Every column title on the board, left to right."""
        titles = []
        for column in self.driver.find_elements(*self.ANY_COLUMN):
            test_id = column.get_attribute("data-testid")
            titles.append(test_id[len("kanban-column-"):])
        return titles

    def card_count(self, title):
        return len(self.cards_in(title))

    def total_card_count(self):
        return self.count(self.ANY_CARD)

    def header_count(self, title):
        """The number in a column's header badge."""
        text = self.text_of(
            (By.XPATH, f"//h3[normalize-space()='{title}']/following-sibling::span[1]")
        )
        if not text:
            return 0
        return int(re.sub(r"\D+", "", text))

    def column_contains(self, title, text):
        """True if any card in the column shows this text."""
        for card in self.cards_in(title):
            if text in card.text:
                return True
        return False

    def board_contains(self, reference):
        """True if this reference number is anywhere on the board."""
        for card in self.driver.find_elements(*self.ANY_CARD):
            if reference in card.text:
                return True
        return False

    def column_of(self, reference):
        """The column a reference number is in, or "" if it is not on the board."""
        for title in self.COLUMNS:
            if self.column_contains(title, reference):
                return title
        return ""

    def shows_drop_hint(self, title):
        """The "Drop tickets here" hint shown in an empty column."""
        return "Drop tickets here" in self.driver.find_element(*self.column(title)).text

    def is_card_draggable(self, card):
        """
        True when a card can be dragged. (Not draggable when the user may not move tickets,
        or the ticket is escalated.) The drag library marks the card's wrapper with one of
        several attributes, so any of them counts.
        """
        wrapper = card.find_element(By.XPATH, "..")
        role_description = wrapper.get_attribute("aria-roledescription")
        if role_description and "draggable" in role_description:
            return True
        if wrapper.get_attribute("role") == "button":
            return True
        return wrapper.get_attribute("aria-describedby") is not None

    def describe_card_wrapper(self, card):
        """The drag attributes on a card's wrapper, for a failure message."""
        wrapper = card.find_element(By.XPATH, "..")
        return (
            f"role={wrapper.get_attribute('role')}"
            f" aria-roledescription={wrapper.get_attribute('aria-roledescription')}"
            f" aria-describedby={wrapper.get_attribute('aria-describedby')}"
            f" tabindex={wrapper.get_attribute('tabindex')}"
        )

    def card_reference(self, card):
        """The reference number of the ticket this card links to."""
        return card.find_element(
            By.XPATH, ".//a[contains(@href, '/tickets/')]"
        ).text.strip()

    def card_customer_name(self, card):
        """The customer name on a card, or "" when the card shows no customer."""
        values = card.find_elements(
            By.XPATH, ".//span[normalize-space()='Customer']/following-sibling::span[1]"
        )
        if values:
            return values[0].text.strip()
        return ""

    def is_card_escalated(self, card):
        """
        True when the card has an "Escalated ..." badge. (A "Breached by 2h" SLA pill is
        NOT the same thing, so the badge itself is checked, not the card text.)
        """
        badges = card.find_elements(
            By.XPATH, ".//div[starts-with(normalize-space(), 'Escalated ')]"
        )
        return bool(badges)

    # ---------------- The board's error banner ----------------
    # A move that is not allowed shows a red "Status change not allowed" message.

    def has_error_banner(self):
        return self.exists(
            (
                By.XPATH,
                "//*[normalize-space(text())='Status change not allowed']"
                " | //*[normalize-space(text())='Action failed']"
                ' | //*[normalize-space(text())="Couldn\'t load the board"]',
            )
        )

    def shows_blocked_move_error(self):
        return self.exists(
            (By.XPATH, "//*[normalize-space(text())='Status change not allowed']")
        )

    def error_message(self):
        """The text under the banner's title, e.g. "A ticket can't be moved back to New."."""
        return self.text_of(
            (
                By.XPATH,
                "//*[normalize-space(text())='Status change not allowed']/following::p[1]"
                " | //*[normalize-space(text())='Status change not allowed']"
                "/../following-sibling::*[1]",
            )
        )

    # ---------------- Modals opened by a drop ----------------
    # Dropping on "Resolved" asks for a resolution note; on "Pending POC" it asks for a contact.

    def is_modal_open(self):
        return self.exists(self.MODAL)

    def wait_for_modal(self):
        self.wait_visible(self.MODAL)

    def modal_title(self):
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def type_resolution_note(self, text):
        self.type_into((By.CSS_SELECTOR, "div[role='dialog'] textarea"), text)

    def select_poc_contact(self, index):
        self.open_dropdown(
            (By.CSS_SELECTOR, "div[role='dialog'] button[aria-haspopup='listbox']")
        )
        self.driver.find_elements(*self.OPEN_OPTIONS)[index].click()

    def is_modal_confirm_enabled(self, button_text):
        """True when the modal's main button can be pressed."""
        return self.driver.find_element(
            By.XPATH, f"//div[@role='dialog']//button[normalize-space()='{button_text}']"
        ).is_enabled()

    def confirm_modal(self, button_text):
        self.click(
            (
                By.XPATH,
                f"//div[@role='dialog']//button[normalize-space()='{button_text}']",
            )
        )
        self.wait_gone(self.MODAL)

    def cancel_modal(self):
        self.click(
            (By.XPATH, "//div[@role='dialog']//button[normalize-space()='Cancel']")
        )
        self.wait_gone(self.MODAL)
