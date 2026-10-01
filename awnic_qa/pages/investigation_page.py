"""
The Investigation & Resolution tab of a complaint - /tickets/{id}/investigation.

Only complaints have this tab; for an enquiry the URL shows the app's "not found" screen.

It has two cards:
  INVESTIGATION & RESOLUTION  fields that can be edited (with an "Edit" button once saved).
  RESOLUTION REMARKS          a list of remarks you can ADD to, but never edit or delete.
A merged duplicate shows "This merged ticket is read-only." instead of the remark box.
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class InvestigationPage(BasePage):
    # The two card titles (shown in uppercase, so matched ignoring case).
    INVESTIGATION_CARD = "Investigation & Resolution"
    REMARKS_CARD = "Resolution Remarks"

    # Exact messages the tab shows.
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

    # One saved remark (a list item).
    REMARK_ITEMS = (By.XPATH, "//*[@role='listitem'] | //ul/li")

    # ---------------- Waits ----------------

    def wait_until_loaded(self):
        """
        Waits for the RESOLUTION REMARKS card. (The page heading appears before the tab has
        loaded, so it is not a good signal.)
        """
        self.wait_visible(self.text_ignoring_case(self.REMARKS_CARD))

    # ---------------- Checks - the cards ----------------

    def has_investigation_card(self):
        return self.exists(self.text_ignoring_case(self.INVESTIGATION_CARD))

    def has_remarks_card(self):
        return self.exists(self.text_ignoring_case(self.REMARKS_CARD))

    def says_nothing_recorded_yet(self):
        """The "nothing recorded yet" message shown to a view-only user."""
        return self.exists(self.innermost_containing(self.NOTHING_RECORDED))

    def says_no_remarks_yet(self):
        return self.exists(self.innermost_containing(self.NO_REMARKS_YET))

    def says_merged_read_only(self):
        return self.exists(self.innermost_containing(self.MERGED_READ_ONLY))

    # ---------------- The investigation fields ----------------

    def has_edit_button(self):
        """The Edit button. Not shown to a view-only role or on a Resolved/Closed ticket."""
        return self.exists(self.EDIT_BUTTON)

    def start_editing(self):
        self.click(self.EDIT_BUTTON)

    def is_form_open(self):
        """True when the edit form (with a Save button) is showing."""
        return self.has_button("Save") or self.has_button("Save Changes")

    def field_value(self, label):
        """A field's value as shown. An empty field shows an em dash."""
        return self.text_of(
            (
                By.XPATH,
                f"(//div[normalize-space(text())='{label}'])[1]"
                "/parent::div/following-sibling::div",
            )
        )

    def has_field(self, label):
        return self.exists((By.XPATH, f"//div[normalize-space(text())='{label}']"))

    # ---------------- The resolution remarks ----------------

    def remark_count(self):
        return self.count(self.REMARK_ITEMS)

    def remark_texts(self):
        texts = []
        for text in self.texts_of(self.REMARK_ITEMS):
            if text:
                texts.append(text)
        return texts

    def remark_details(self):
        """
        Each saved remark as (author, when, body). The author and time are the first two
        <span>s, the body is the <p>. A missing part comes back as "".
        """
        details = []
        for item in self.driver.find_elements(*self.REMARK_ITEMS):
            spans = item.find_elements(By.TAG_NAME, "span")
            bodies = item.find_elements(By.TAG_NAME, "p")
            author = spans[0].text.strip() if len(spans) > 0 else ""
            when = spans[1].text.strip() if len(spans) > 1 else ""
            body = bodies[0].text.strip() if bodies else ""
            details.append((author, when, body))
        return details

    def shows_remark_containing(self, fragment):
        for text in self.remark_texts():
            if fragment in text:
                return True
        return False

    def is_remark_box_displayed(self):
        return self.exists(self.REMARK_BOX)

    def is_remark_box_enabled(self):
        if not self.exists(self.REMARK_BOX):
            return False
        return self.driver.find_element(*self.REMARK_BOX).is_enabled()

    def is_add_remark_enabled(self):
        """True when Add Remark can be pressed (it stays disabled for a blank remark)."""
        if not self.exists(self.ADD_REMARK_BUTTON):
            return False
        return self.driver.find_element(*self.ADD_REMARK_BUTTON).is_enabled()

    def type_remark(self, text):
        self.type_into(self.REMARK_BOX, text)

    def clear_remark(self):
        self.clear_box(self.wait_visible(self.REMARK_BOX))

    def add_remark(self):
        """Presses Add Remark. This really saves a remark that can never be deleted."""
        self.click(self.ADD_REMARK_BUTTON)

    def remark_draft(self):
        return self.driver.find_element(*self.REMARK_BOX).get_attribute("value")

    def has_error(self):
        return self.exists(self.ERROR_ALERT)

    def get_error(self):
        return self.text_of(self.ERROR_ALERT)

    # ---------------- No edit/delete for remarks ----------------

    def offers_any_remark_edit_or_delete_control(self):
        """True if anything on the tab offers to edit or delete a saved remark (it must not)."""
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
