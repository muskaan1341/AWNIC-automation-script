"""
The Edit Ticket form at /tickets/{id}/edit  (Form 3 in the Form QA documentation).

WHO CAN OPEN IT: only a role holding the edit capability, and only while the ticket is
still open - the server sends you straight back to the detail view for a Closed, Resolved
or duplicate ticket, so "I could not reach the form" is often correct behaviour rather
than a fault.

WHY THIS FORM IS EASY TO AUTOMATE: every control carries a real id, "edit-" plus the
field name (edit-department, edit-alternate_email, ...). That is the best kind of locator
there is, so nothing in this class depends on layout or styling.

THE THREE MESSAGES IT PRODUCES (from the documentation, asserted verbatim):
  "<Label> is required"          a required cascade level left blank
  "Enter a valid email address"  a malformed email
  "Enter a valid phone number"   a malformed phone number

NAMING NOTE: the Java class called its typing helper typeInto(fieldKey, text). Here that
would collide with BasePage.type_into(locator, text) through inheritance, so the
field-oriented one is called fill(). Same behaviour, unambiguous name.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage, Locator


class TicketEditPage(BasePage):
    BAD_EMAIL_MESSAGE = "Enter a valid email address"
    BAD_PHONE_MESSAGE = "Enter a valid phone number"

    # The submit button reads "Update Ticket" ("Saving…" while the PATCH is in flight) -
    # TicketEditForm.tsx. It never read "Save": the old locator waited for a button that does
    # not exist, so wait_until_loaded() timed out on EVERY ticket and no edit-form test ever
    # reached its own assertion.
    SAVE_BUTTON = (
        By.XPATH,
        "//button[@type='submit' and "
        "(normalize-space()='Update Ticket' or normalize-space()='Saving…')]",
    )
    CANCEL_BUTTON = (By.XPATH, "//button[normalize-space()='Cancel']")
    FORM_LEVEL_ERROR = (By.CSS_SELECTOR, "p[role='alert']")

    @staticmethod
    def field(field_key: str) -> Locator:
        """Every control on this form is "edit-" + the field name."""
        return (By.ID, f"edit-{field_key}")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.SAVE_BUTTON)

    def fill(self, field_key: str, text: str) -> None:
        self.type_into(self.field(field_key), text)

    def choose_first_value(self, field_key: str) -> str:
        return self.choose_first_option(self.field(field_key))

    def choose(self, field_key: str, option_label: str) -> None:
        self.choose_option(self.field(field_key), option_label)

    def save(self) -> None:
        self.click(self.SAVE_BUTTON)

    def cancel(self) -> None:
        self.click(self.CANCEL_BUTTON)

    #: The complaint cascade, as edit-form field keys (TicketEditForm.tsx CASCADE.Complaint,
    #: less sub_product_line, which is hidden where the taxonomy offers nothing for it).
    COMPLAINT_CASCADE_BELOW_DEPARTMENT = [
        "product_line",
        "complaint_category",
        "complaint_type",
        "complaint_sub_type",
    ]

    def choose_garage_sub_type_path(self, motor_department: str, garage_sub_types: list[str]) -> str:
        """Department = Motor Claims, then the first taxonomy path down to a garage sub-type."""
        self.choose("department", motor_department)
        return self.choose_cascade_path_to(
            [self.field(key) for key in self.COMPLAINT_CASCADE_BELOW_DEPARTMENT],
            garage_sub_types,
        )

    def options_of(self, field_key: str) -> list[str]:
        """A dropdown's options, once the form's async taxonomy fetch has landed."""
        return self.read_dropdown_options_when_loaded(self.field(field_key))

    # ---------- CHECKS ----------

    #: EditCustomerSection.tsx - its <h2> and the optional Data Mart shortcut.
    CUSTOMER_SECTION = (By.XPATH, "//section//h2[normalize-space()='Customer Details']")
    DATA_MART_LOOKUP = "Look up in Data Mart"

    def has_customer_section(self) -> bool:
        return self.exists(self.CUSTOMER_SECTION)

    def is_field_editable(self, field_key: str) -> bool:
        return self.driver.find_element(*self.field(field_key)).is_enabled()

    def is_field_present(self, field_key: str) -> bool:
        return self.exists(self.field(field_key))

    def value_of(self, field_key: str) -> str:
        return self.driver.find_element(*self.field(field_key)).get_attribute("value")

    def shown_value(self, field_key: str) -> str:
        """
        What one field is showing, "" when it is empty - for text boxes AND dropdowns.

        value_of() reads an <input>'s value attribute, which a dropdown does not have: every
        select on this form is a CustomSelect, a <button> whose TEXT is the chosen label, or
        the "Select an option" placeholder when nothing is chosen. Both come back here as
        the value the user sees, with the placeholder read as empty.
        """
        element = self.driver.find_element(*self.field(field_key))
        if element.tag_name.lower() == "input":
            return (element.get_attribute("value") or "").strip()
        shown = element.text.strip()
        return "" if shown == "Select an option" else shown

    def reference_number(self) -> str:
        """The reference in the form's "Enquiry/Complaint Reference Number" box - which ticket this is."""
        return self.text_of(
            (
                By.XPATH,
                "//div[normalize-space()='Enquiry Reference Number' or "
                "normalize-space()='Complaint Reference Number']/following-sibling::div[1]",
            )
        )

    def error_for(self, field_key: str) -> str:
        """The message shown directly under one field, or "" when the field is happy."""
        return self.field_error(f"edit-{field_key}")

    def shows_required_error_for(self, label: str) -> bool:
        return self.shows_message(f"{label} is required")

    def shows_bad_email_message(self) -> bool:
        return self.shows_message(self.BAD_EMAIL_MESSAGE)

    def shows_bad_phone_message(self) -> bool:
        return self.shows_message(self.BAD_PHONE_MESSAGE)

    def all_errors(self) -> list[str]:
        """Every inline message on the form right now - useful in a failure message."""
        return self.all_field_errors()

    def has_form_level_error(self) -> bool:
        return self.exists(self.FORM_LEVEL_ERROR)

    def is_save_enabled(self) -> bool:
        return self.driver.find_element(*self.SAVE_BUTTON).is_enabled()
