"""
The Investigation & Resolution tab of one complaint - /tickets/{id}/investigation.

MODULE 11 in the test-case pack (the Complaints Register). Until now the suite proved this tab
EXISTS on a complaint and does not 404, and nothing more - the 36 cases behind it were
untouched. This page object is what lets them be driven.

COMPLAINT-ONLY, AND IT 404s RATHER THAN EMPTIES. The page reads
`if (ticket.reference_type !== "Complaint") notFound()`, gating on reference_type - the source
of truth - not on the inquiry_type string. So typing this URL for an enquiry gives the
application's own not-found screen, which is a real behaviour worth asserting rather than a
gap to work around.

TWO CARDS, AND THEY BEHAVE DIFFERENTLY:

  INVESTIGATION & RESOLUTION   a field grid, editable in place. Three states:
        never filled + editable   -> the form opens straight away (no grid of dashes first)
        has data + editable       -> a read view with an "Edit" button that swaps the form in
        never filled + view-only  -> one line saying nothing has been recorded yet
  RESOLUTION REMARKS           APPEND-ONLY. A list of remarks, each stamped with who wrote it
        and when, plus a box to add another. There is no edit control and no delete control
        anywhere on it, and that absence is the point - see the tests.

WHO MAY WRITE. Editing the fields needs the edit capability AND an open ticket AND the
CC-Initiator action lock to allow it (`canEditInvestigation(me) && !isClosed && canActNow`).
Appending a remark has NO capability gate at all as of 2026-08-20 - the same as internal notes -
because AWNIC's own sheets log closure itself as a remark. A merged duplicate is the one case
that removes the box entirely, replacing it with "This merged ticket is read-only."
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class InvestigationPage(BasePage):
    #: The two card titles. Both render uppercase, so match without case.
    INVESTIGATION_CARD = "Investigation & Resolution"
    REMARKS_CARD = "Resolution Remarks"

    #: The exact sentences the tab produces. Asserting the words, not just "something showed",
    #: is what tells a real empty state apart from a card that failed to render.
    NOTHING_RECORDED = "No investigation or resolution details have been recorded yet."
    NO_REMARKS_YET = "No resolution remarks yet."
    MERGED_READ_ONLY = "This merged ticket is read-only."

    REMARK_BOX = (By.CSS_SELECTOR, "textarea[aria-label='Add a resolution remark']")
    ADD_REMARK_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Add Remark' or normalize-space()='Adding…']",
    )
    EDIT_BUTTON = (By.XPATH, "//button[normalize-space()='Edit']")
    CANCEL_BUTTON = (By.XPATH, "//button[normalize-space()='Cancel']")
    ERROR_ALERT = (By.CSS_SELECTOR, "p[role='alert']")

    #: One saved remark. The card renders them as <li>, each holding the author, the timestamp
    #: and the text - anchoring on the list keeps this independent of the styling around it.
    REMARK_ITEMS = (By.XPATH, "//*[@role='listitem'] | //ul/li")

    # ==================================================================
    # Waits
    # ==================================================================

    def wait_until_loaded(self) -> None:
        """
        Waits for the RESOLUTION REMARKS card, not merely for a heading.

        The heading belongs to the ticket-detail shell and is already on screen while this tab
        is still fetching, so waiting on it would let a test read an empty card and report it
        as missing. The remarks card is always rendered on a complaint whatever state the
        record is in, which makes it the honest signal that the tab itself has arrived.
        """
        self.wait_visible(self.text_ignoring_case(self.REMARKS_CARD))

    # ==================================================================
    # Checks - the cards
    # ==================================================================

    def has_investigation_card(self) -> bool:
        return self.exists(self.text_ignoring_case(self.INVESTIGATION_CARD))

    def has_remarks_card(self) -> bool:
        return self.exists(self.text_ignoring_case(self.REMARKS_CARD))

    def says_nothing_recorded_yet(self) -> bool:
        """The view-only empty state - a sentence, deliberately not a grid of em dashes."""
        return self.exists(self.innermost_containing(self.NOTHING_RECORDED))

    def says_no_remarks_yet(self) -> bool:
        return self.exists(self.innermost_containing(self.NO_REMARKS_YET))

    def says_merged_read_only(self) -> bool:
        return self.exists(self.innermost_containing(self.MERGED_READ_ONLY))

    # ==================================================================
    # Checks - the investigation field grid
    # ==================================================================

    def has_edit_button(self) -> bool:
        """The Edit affordance. Absent for a view-only role, and on a Resolved/Closed ticket."""
        return self.exists(self.EDIT_BUTTON)

    def start_editing(self) -> None:
        self.click(self.EDIT_BUTTON)

    def is_form_open(self) -> bool:
        """True once the field form has swapped in - it is the form that carries a Save."""
        return self.has_button("Save") or self.has_button("Save Changes")

    def field_value(self, label: str) -> str:
        """
        A field's value as the user reads it.

        The grid is DetailField pairs, the same component the Overview uses, so an empty field
        reads as an em dash rather than as blank.
        """
        return self.text_of(
            (
                By.XPATH,
                f"(//div[normalize-space(text())='{label}'])[1]"
                "/parent::div/following-sibling::div",
            )
        )

    def has_field(self, label: str) -> bool:
        return self.exists((By.XPATH, f"//div[normalize-space(text())='{label}']"))

    # ==================================================================
    # Checks - the resolution remarks (append-only)
    # ==================================================================

    def remark_count(self) -> int:
        return self.count(self.REMARK_ITEMS)

    def remark_texts(self) -> list[str]:
        return [text for text in self.texts_of(self.REMARK_ITEMS) if text]

    def remark_details(self) -> list[tuple[str, str, str]]:
        """
        Each saved remark as (author, when, body).

        remark_texts() returns one blob per remark, which cannot tell "written by Leila at
        14:05" apart from a body that happens to contain a name - so an attribution test built
        on it asserts nothing. Every remark renders the same three parts
        (ResolutionRemarksCard): two header spans, the author and the timestamp, then the body
        in a <p>. Missing parts come back empty rather than raising, so the test can say which
        one was missing.
        """
        details: list[tuple[str, str, str]] = []
        for item in self.driver.find_elements(*self.REMARK_ITEMS):
            spans = item.find_elements(By.TAG_NAME, "span")
            bodies = item.find_elements(By.TAG_NAME, "p")
            details.append(
                (
                    spans[0].text.strip() if len(spans) > 0 else "",
                    spans[1].text.strip() if len(spans) > 1 else "",
                    bodies[0].text.strip() if bodies else "",
                )
            )
        return details

    def shows_remark_containing(self, fragment: str) -> bool:
        return any(fragment in text for text in self.remark_texts())

    def is_remark_box_displayed(self) -> bool:
        return self.exists(self.REMARK_BOX)

    def is_remark_box_enabled(self) -> bool:
        return self.exists(self.REMARK_BOX) and self.driver.find_element(
            *self.REMARK_BOX
        ).is_enabled()

    def is_add_remark_enabled(self) -> bool:
        """
        Whether the remark can actually be added.

        The button is `disabled={saving || !draft.trim()}`, so this answers the whitespace
        question directly: a box holding only spaces leaves it disabled.
        """
        return self.exists(self.ADD_REMARK_BUTTON) and self.driver.find_element(
            *self.ADD_REMARK_BUTTON
        ).is_enabled()

    def type_remark(self, text: str) -> None:
        self.type_into(self.REMARK_BOX, text)

    def clear_remark(self) -> None:
        self.clear_box(self.wait_visible(self.REMARK_BOX))

    def add_remark(self) -> None:
        """PRESSES ADD. This really appends a row the register keeps forever."""
        self.click(self.ADD_REMARK_BUTTON)

    def remark_draft(self) -> str:
        return self.driver.find_element(*self.REMARK_BOX).get_attribute("value")

    def has_error(self) -> bool:
        return self.exists(self.ERROR_ALERT)

    def get_error(self) -> str:
        return self.text_of(self.ERROR_ALERT)

    # ==================================================================
    # The absence that matters
    # ==================================================================

    def offers_any_remark_edit_or_delete_control(self) -> bool:
        """
        True if ANYTHING on this tab offers to change or remove a saved remark.

        The register is append-only by design - the API exposes no update or delete, and the
        database grants block it - so the honest browser-level check is that the screen never
        even offers the controls. Deliberately broad: it sweeps for buttons, menu items and
        aria-labels alike, so a regression is caught whatever shape it arrives in.
        """
        return self.exists(
            (
                By.XPATH,
                "//button[normalize-space()='Delete' or normalize-space()='Remove'"
                " or normalize-space()='Edit Remark' or normalize-space()='Delete Remark']"
                " | //*[@aria-label[contains(.,'Delete remark') or contains(.,'Edit remark')]]"
                " | //*[@role='menuitem'][contains(normalize-space(),'Delete')"
                " or contains(normalize-space(),'Remove')]",
            )
        )
