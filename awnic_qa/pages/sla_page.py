"""
The SLA tab of a ticket - /tickets/{id}/sla.

Three cards: SLA STATUS, ESCALATION LADDER and MATRIX RULE.

The escalation ladder is not the same as the ticket's stages. It has these rungs, in order:
  CC Initiator, POC, L1 Escalation, L2 Escalation (motor tickets only), Final Escalation
Each rung has data-testid="ladder-rung-<label>", and its circle is marked
"ladder-rung-reached" or "ladder-rung-pending".
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class SlaPage(BasePage):
    # The rungs on a non-motor ticket (no L2).
    NON_MOTOR_RUNGS = ["CC Initiator", "POC", "L1 Escalation", "Final Escalation"]

    # The extra rung only motor tickets have.
    MOTOR_ONLY_RUNG = "L2 Escalation"

    # The rungs on a motor ticket, in order.
    MOTOR_RUNGS = ["CC Initiator", "POC", "L1 Escalation", "L2 Escalation", "Final Escalation"]

    # The three card titles (shown in capitals).
    CARD_TITLES = ["SLA STATUS", "ESCALATION LADDER", "MATRIX RULE"]

    ANY_RUNG = (By.CSS_SELECTOR, "[data-testid^='ladder-rung-']")
    REACHED_RUNGS = (By.CSS_SELECTOR, "[data-testid='ladder-rung-reached']")
    PENDING_RUNGS = (By.CSS_SELECTOR, "[data-testid='ladder-rung-pending']")

    # ---------------- Waits ----------------

    def wait_until_loaded(self):
        """Waits for the ESCALATION LADDER card (the heading shows before the tab loads)."""
        self.wait_visible((By.XPATH, "//*[normalize-space()='ESCALATION LADDER']"))

    # ---------------- Checks ----------------

    def has_card(self, title):
        return self.exists((By.XPATH, f"//*[normalize-space()='{title}']"))

    def has_rung(self, rung_label):
        """True when this rung is shown (reached or not)."""
        return self.exists((By.CSS_SELECTOR, f"[data-testid='ladder-rung-{rung_label}']"))

    def rung_labels(self):
        """Every rung on the ladder, in order."""
        labels = []
        for rung in self.driver.find_elements(*self.ANY_RUNG):
            test_id = rung.get_attribute("data-testid")
            # The circles inside a rung also start with "ladder-rung-", so skip them.
            if test_id and test_id not in ("ladder-rung-reached", "ladder-rung-pending"):
                labels.append(test_id[len("ladder-rung-"):])
        return labels

    def reached_count(self):
        return self.count(self.REACHED_RUNGS)

    def reached_rung_labels(self):
        """The labels of the rungs this ticket has reached, in order."""
        reached = []
        for label in self.rung_labels():
            reached_circle = (
                By.CSS_SELECTOR,
                f"[data-testid='ladder-rung-{label}'] [data-testid='ladder-rung-reached']",
            )
            if self.exists(reached_circle):
                reached.append(label)
        return reached

    def rung_text(self, rung_label):
        """All the text on one rung (label, TAT, people), or "" when the rung is not shown."""
        rungs = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='ladder-rung-{rung_label}']"
        )
        if rungs:
            return rungs[0].text
        return ""

    def pending_count(self):
        return self.count(self.PENDING_RUNGS)

    def rung_count(self):
        """How many rungs the ladder has."""
        return len(self.rung_labels())

    def value_of(self, label):
        """The value next to a label in any card. An empty value shows as an em dash."""
        return self.text_of(
            (
                By.XPATH,
                f"//span[normalize-space()='{label}']/following-sibling::span[1]",
            )
        )

    def has_row(self, label):
        return self.exists(
            (
                By.XPATH,
                f"//span[normalize-space()='{label}']/following-sibling::span[1]",
            )
        )
