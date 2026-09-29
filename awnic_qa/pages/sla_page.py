"""
The SLA tab of one ticket - /tickets/{id}/sla.

WHAT IS ON THIS SCREEN
Three cards and nothing else:

  SLA STATUS         the deadline this ticket has to meet and how many days that is
  ESCALATION LADDER  the rungs this ticket can climb, and how far up it currently is
  MATRIX RULE        WHERE those numbers came from - the row in the SLA matrix that
                     department + enquiry type resolved to

THE ONE IDEA WORTH UNDERSTANDING: THE LADDER IS NOT A LIST OF STAGES.
The ticket pipeline has nine stages; this ladder has four rungs (five for a motor ticket).
They are different things. A ticket does not move onto an "Escalated" stage - escalation is
recorded separately and shown here as how far up the ladder it has got. So never assert
"the stage is Escalated L1"; assert which rung is REACHED.

THE RUNGS, in order:
  CC Initiator      the first response clock (R37 tier 1)
  POC               the department point of contact
  L1 Escalation     first escalation
  L2 Escalation     MOTOR TICKETS ONLY - a non-motor ticket goes L1 straight to Final
  Final Escalation  the department head

Each rung carries data-testid="ladder-rung-<label>", and its circle carries either
ladder-rung-reached or ladder-rung-pending. Those testids are the stable hook; the colours
next to them are a design choice that may change.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class SlaPage(BasePage):
    #: The rungs a NON-MOTOR ticket shows. Note: no L2 - that is the motor-only one.
    NON_MOTOR_RUNGS = ["CC Initiator", "POC", "L1 Escalation", "Final Escalation"]

    #: The extra rung that only a motor ticket gets.
    MOTOR_ONLY_RUNG = "L2 Escalation"

    #: The rungs a MOTOR ticket shows, in order - the non-motor ladder with L2 inserted
    #: before Final. Kept here beside NON_MOTOR_RUNGS so the two orders are stated once.
    MOTOR_RUNGS = NON_MOTOR_RUNGS[:-1] + [MOTOR_ONLY_RUNG] + NON_MOTOR_RUNGS[-1:]

    #: The three card titles. The app renders them in capitals, and so does the DOM.
    CARD_TITLES = ["SLA STATUS", "ESCALATION LADDER", "MATRIX RULE"]

    ANY_RUNG = (By.CSS_SELECTOR, "[data-testid^='ladder-rung-']")
    REACHED_RUNGS = (By.CSS_SELECTOR, "[data-testid='ladder-rung-reached']")
    PENDING_RUNGS = (By.CSS_SELECTOR, "[data-testid='ladder-rung-pending']")

    # ==================================================================
    # Waits
    # ==================================================================

    def wait_until_loaded(self) -> None:
        """
        Waits until the tab has actually rendered.

        Waits for the LADDER, not merely for a heading. The heading belongs to the ticket
        detail shell and is already on screen while this tab is still fetching - so a test
        that only waited for the heading could read an empty card and report it as missing.
        """
        self.wait_visible((By.XPATH, "//*[normalize-space()='ESCALATION LADDER']"))

    # ==================================================================
    # Checks
    # ==================================================================

    def has_card(self, title: str) -> bool:
        return self.exists((By.XPATH, f"//*[normalize-space()='{title}']"))

    def has_rung(self, rung_label: str) -> bool:
        """True when this rung is drawn at all - says nothing about whether it is reached."""
        return self.exists((By.CSS_SELECTOR, f"[data-testid='ladder-rung-{rung_label}']"))

    def rung_labels(self) -> list[str]:
        """Every rung on the ladder, in the order the page draws them."""
        labels: list[str] = []
        for rung in self.driver.find_elements(*self.ANY_RUNG):
            test_id = rung.get_attribute("data-testid")
            # The circles INSIDE a rung also start with "ladder-rung-", so skip those two.
            if test_id and test_id not in ("ladder-rung-reached", "ladder-rung-pending"):
                labels.append(test_id[len("ladder-rung-") :])
        return labels

    def reached_count(self) -> int:
        return self.count(self.REACHED_RUNGS)

    def reached_rung_labels(self) -> list[str]:
        """
        The labels of the rungs this ticket has REACHED, in the order the page draws them.

        reached_count() only says how many circles are green; it cannot say WHICH, so it
        cannot answer the question the ladder actually has to get right - that the green ones
        run from the bottom with no gap. Each rung element holds exactly one state circle
        (ladder-rung-reached or ladder-rung-pending, see SlaEscalationLadder), so the state is
        read per rung here rather than counted globally.
        """
        return [
            label
            for label in self.rung_labels()
            if self.exists(
                (
                    By.CSS_SELECTOR,
                    f"[data-testid='ladder-rung-{label}'] [data-testid='ladder-rung-reached']",
                )
            )
        ]

    def rung_text(self, rung_label: str) -> str:
        """
        Everything one rung shows: its label, tier badge, TAT ("24h", or "—" when no policy
        supplies one) and the people named against it. "" when the rung is not drawn.

        The CC Initiator rung names the ticket's OWN assigned initiator (SlaEscalationLadder's
        initiatorEmails is ticket.assigned_initiator_email), which is what lets a test tie
        the clock to a named person rather than only to a rung existing.
        """
        rungs = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='ladder-rung-{rung_label}']"
        )
        return rungs[0].text if rungs else ""

    def pending_count(self) -> int:
        return self.count(self.PENDING_RUNGS)

    def rung_count(self) -> int:
        """How many rungs the ladder has. Every rung is exactly one reached OR one pending."""
        return len(self.rung_labels())

    def value_of(self, label: str) -> str:
        """
        The value beside a label in any of the three cards.

        A DetailRow is a <div> holding two spans: the label, then the value. Anchoring on the
        label and stepping to its next sibling is how the pair is read. An empty value renders
        as an em dash, NOT as blank - so "—" is a real answer, not a missing one.
        """
        return self.text_of(
            (
                By.XPATH,
                f"//span[normalize-space()='{label}']/following-sibling::span[1]",
            )
        )

    def has_row(self, label: str) -> bool:
        return self.exists(
            (
                By.XPATH,
                f"//span[normalize-space()='{label}']/following-sibling::span[1]",
            )
        )
