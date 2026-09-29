"""
The Kanban board - the second view on every ticket list (press the "Kanban" button).

FOUR COLUMNS, NEVER MORE: New, In Progress, Pending POC, Resolved.
  - the nine formal stages collapse into those four. The three "Escalated" stages all sit
    inside Pending POC and show as a badge on the card, not as a column of their own,
  - "Closed" is the end of the road and is OFF the board - a closed ticket is in no column,
  - "Discarded" is not a stage at all; it is a different kind of ticket, on its own list.

"New" is a SOURCE only, never a destination: a ticket cannot be dragged backwards into it.

The application gives us stable hooks here, so nothing in this class depends on styling:
    data-testid="kanban-column-New"   (and the other three)
    data-testid="kanban-card"

DRAGGING: use BaseTest.drag_card(...), never ActionChains.drag_and_drop - see the long
comment on that method for why. Assert on the OUTCOME (the column counts) rather than the
animation.
"""

from __future__ import annotations

import re

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage, Locator


class KanbanPage(BasePage):
    NEW = "New"
    IN_PROGRESS = "In Progress"
    PENDING_POC = "Pending POC"
    RESOLVED = "Resolved"

    #: The four columns, in the order the board renders them.
    COLUMNS = [NEW, IN_PROGRESS, PENDING_POC, RESOLVED]

    ANY_COLUMN = (By.CSS_SELECTOR, "[data-testid^='kanban-column-']")
    ANY_CARD = (By.CSS_SELECTOR, "[data-testid='kanban-card']")
    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")

    @staticmethod
    def column(title: str) -> Locator:
        return (By.CSS_SELECTOR, f"[data-testid='kanban-column-{title}']")

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.column(self.NEW))

    def column_element(self, title: str):
        return self.driver.find_element(*self.column(title))

    def cards_in(self, title: str) -> list:
        """The cards currently sitting in one column."""
        return self.driver.find_element(*self.column(title)).find_elements(*self.ANY_CARD)

    def first_card_in(self, title: str):
        cards = self.cards_in(title)
        if not cards:
            raise AssertionError(
                f"No cards in the '{title}' column - this test needs seeded data there. "
                "Run 'make seed-demo' before the suite."
            )
        return cards[0]

    def wait_for_card_count(self, title: str, expected: int) -> None:
        self.wait.until(lambda d: len(self.cards_in(title)) == expected)

    def open_card(self, card) -> None:
        """Opens a card's ticket by clicking it (a click and a drag are told apart by distance)."""
        card.click()

    # ==================================================================
    # Checks
    # ==================================================================

    def get_column_titles(self) -> list[str]:
        """Every column heading on the board, left to right."""
        return [
            col.get_attribute("data-testid")[len("kanban-column-") :]
            for col in self.driver.find_elements(*self.ANY_COLUMN)
        ]

    def card_count(self, title: str) -> int:
        return len(self.cards_in(title))

    def total_card_count(self) -> int:
        return self.count(self.ANY_CARD)

    def header_count(self, title: str) -> int:
        """The number in the column header badge, which must agree with the cards below it."""
        text = self.text_of(
            (By.XPATH, f"//h3[normalize-space()='{title}']/following-sibling::span[1]")
        )
        return 0 if not text else int(re.sub(r"\D+", "", text))

    def column_contains(self, title: str, text: str) -> bool:
        """True if any card in the column shows this text (a reference number, a badge, ...)."""
        return any(text in card.text for card in self.cards_in(title))

    def board_contains(self, reference: str) -> bool:
        """True if this reference number is anywhere on the board."""
        return any(
            reference in card.text for card in self.driver.find_elements(*self.ANY_CARD)
        )

    def column_of(self, reference: str) -> str:
        """Which column a reference number is currently in, or "" if it is not on the board."""
        for title in self.COLUMNS:
            if self.column_contains(title, reference):
                return title
        return ""

    def shows_drop_hint(self, title: str) -> bool:
        """The hint the app renders in an empty column instead of leaving a blank box."""
        return "Drop tickets here" in self.driver.find_element(*self.column(title)).text

    def is_card_draggable(self, card) -> bool:
        """
        True when a card can really be picked up.

        A card is NOT draggable when the signed-in user lacks the move-stage right (the board
        is read-only for them) or when the ticket is escalated (the escalation engine owns it
        from that point). The drag library removes its listeners in both cases; the attribute
        it leaves behind is the honest signal.
        """
        wrapper = card.find_element(By.XPATH, "..")
        # dnd-kit marks a live drag handle with a set of accessibility attributes. Which ones
        # it emits varies with the version, so accept any of them rather than pinning one and
        # reporting "not draggable" when it simply spelled it differently.
        role_description = wrapper.get_attribute("aria-roledescription")
        if role_description and "draggable" in role_description:
            return True
        return (
            wrapper.get_attribute("role") == "button"
            or wrapper.get_attribute("aria-describedby") is not None
        )

    def describe_card_wrapper(self, card) -> str:
        """Everything dnd-kit put on a card's wrapper - for a failure message worth reading."""
        wrapper = card.find_element(By.XPATH, "..")
        return (
            f"role={wrapper.get_attribute('role')}"
            f" aria-roledescription={wrapper.get_attribute('aria-roledescription')}"
            f" aria-describedby={wrapper.get_attribute('aria-describedby')}"
            f" tabindex={wrapper.get_attribute('tabindex')}"
        )

    def card_reference(self, card) -> str:
        """
        The reference number a card links to - i.e. WHICH ticket this card is.

        Read from the card's own ticket link rather than by scanning its text for a line
        beginning "INQ-", so a test can follow one named card across a drag and say where it
        ended up, instead of only counting how many cards a column holds.
        """
        return card.find_element(
            By.XPATH, ".//a[contains(@href, '/tickets/')]"
        ).text.strip()

    def card_customer_name(self, card) -> str:
        """
        The customer named on a card, or "" when the card shows no customer line at all.

        KanbanCard renders the "Customer" label and the name together or not at all (the whole
        row is conditional on ticket.customer_name), so an empty string here means the ticket
        has no customer name recorded - which is correct behaviour, not a missing element.
        """
        values = card.find_elements(
            By.XPATH, ".//span[normalize-space()='Customer']/following-sibling::span[1]"
        )
        return values[0].text.strip() if values else ""

    def is_card_escalated(self, card) -> bool:
        """
        True when the card carries the escalation badge ("Escalated L1" / "L2" / "Final").

        Read from the badge itself, not from the card's text: every card also carries an SLA
        pill, and an overdue one reads "Breached by 2h" - which the old `"breach" in text`
        check counted as escalated. A breached SLA and an escalated ticket are different
        facts; only the second takes the card out of human hands (breach_level > 0).
        """
        return bool(
            card.find_elements(By.XPATH, ".//div[starts-with(normalize-space(), 'Escalated ')]")
        )

    # ==================================================================
    # The board's own error banner
    # ==================================================================
    # A move the rules do not allow is not silently ignored - the board says why, in a red
    # callout titled "Status change not allowed". That is far better than the card just
    # snapping back with no explanation, and it is worth asserting on.

    def has_error_banner(self) -> bool:
        return self.exists(
            (
                By.XPATH,
                "//*[normalize-space(text())='Status change not allowed']"
                " | //*[normalize-space(text())='Action failed']"
                ' | //*[normalize-space(text())="Couldn\'t load the board"]',
            )
        )

    def shows_blocked_move_error(self) -> bool:
        return self.exists(
            (By.XPATH, "//*[normalize-space(text())='Status change not allowed']")
        )

    def error_message(self) -> str:
        """The explanation under the banner's title, e.g. "A ticket can't be moved back to New."."""
        return self.text_of(
            (
                By.XPATH,
                "//*[normalize-space(text())='Status change not allowed']/following::p[1]"
                " | //*[normalize-space(text())='Status change not allowed']"
                "/../following-sibling::*[1]",
            )
        )

    # ==================================================================
    # The two modals a drop can open
    # ==================================================================
    # Dropping onto "Resolved" asks for a resolution note first.
    # Dropping onto "Pending POC" asks which named contact should take it.

    def is_modal_open(self) -> bool:
        return self.exists(self.MODAL)

    def wait_for_modal(self) -> None:
        self.wait_visible(self.MODAL)

    def modal_title(self) -> str:
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def type_resolution_note(self, text: str) -> None:
        self.type_into((By.CSS_SELECTOR, "div[role='dialog'] textarea"), text)

    def select_poc_contact(self, index: int) -> None:
        self.open_dropdown(
            (By.CSS_SELECTOR, "div[role='dialog'] button[aria-haspopup='listbox']")
        )
        self.driver.find_elements(*self.OPEN_OPTIONS)[index].click()

    def is_modal_confirm_enabled(self, button_text: str) -> bool:
        """True when the modal's primary button is usable - it is disabled until valid."""
        return self.driver.find_element(
            By.XPATH, f"//div[@role='dialog']//button[normalize-space()='{button_text}']"
        ).is_enabled()

    def confirm_modal(self, button_text: str) -> None:
        self.click(
            (
                By.XPATH,
                f"//div[@role='dialog']//button[normalize-space()='{button_text}']",
            )
        )
        self.wait_gone(self.MODAL)

    def cancel_modal(self) -> None:
        self.click(
            (By.XPATH, "//div[@role='dialog']//button[normalize-space()='Cancel']")
        )
        self.wait_gone(self.MODAL)
