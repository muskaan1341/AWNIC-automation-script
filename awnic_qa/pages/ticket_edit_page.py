"""
The Edit Ticket form - /tickets/{id}/edit.

Only a role with the edit permission can open it, and only while the ticket is open. For a
Closed, Resolved or duplicate ticket the app sends you back to the detail page.

Every control has an id "edit-" + field name (edit-department, edit-alternate_email, ...).

Messages the form shows:
  "<Label> is required"          a required field left blank
  "Enter a valid email address"  a bad email
  "Enter a valid phone number"   a bad phone number

Note: the typing helper is called fill(), because type_into() already exists in BasePage.
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class TicketEditPage(BasePage):
    BAD_EMAIL_MESSAGE = "Enter a valid email address"
    BAD_PHONE_MESSAGE = "Enter a valid phone number"

    # The submit button says "Update Ticket" ("Saving…" while saving).
    SAVE_BUTTON = (
        By.XPATH,
        "//button[@type='submit' and "
        "(normalize-space()='Update Ticket' or normalize-space()='Saving…')]",
    )
    CANCEL_BUTTON = (By.XPATH, "//button[normalize-space()='Cancel']")
    FORM_LEVEL_ERROR = (By.CSS_SELECTOR, "p[role='alert']")

    @staticmethod
    def field(field_key):
        """The locator of a form control: id "edit-" + the field name."""
        return (By.ID, f"edit-{field_key}")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self):
        self.wait_visible(self.SAVE_BUTTON)

    def fill(self, field_key, text):
        self.type_into(self.field(field_key), text)

    def choose_first_value(self, field_key):
        return self.choose_first_option(self.field(field_key))

    def choose(self, field_key, option_label):
        self.choose_option(self.field(field_key), option_label)

    def save(self):
        self.click(self.SAVE_BUTTON)

    def cancel(self):
        self.click(self.CANCEL_BUTTON)

    # The complaint dropdowns below Department, top to bottom.
    COMPLAINT_CASCADE_BELOW_DEPARTMENT = [
        "product_line",
        "complaint_category",
        "complaint_type",
        "complaint_sub_type",
    ]

    def choose_garage_sub_type_path(self, motor_department, garage_sub_types):
        """Picks the Motor department, then the first path down to a garage sub-type."""
        self.choose("department", motor_department)
        dropdowns = []
        for key in self.COMPLAINT_CASCADE_BELOW_DEPARTMENT:
            dropdowns.append(self.field(key))
        return self.choose_cascade_path_to(dropdowns, garage_sub_types)

    def options_of(self, field_key):
        """A dropdown's options, after they have finished loading."""
        return self.read_dropdown_options_when_loaded(self.field(field_key))

    # ---------- CHECKS ----------

    CUSTOMER_SECTION = (By.XPATH, "//section//h2[normalize-space()='Customer Details']")
    DATA_MART_LOOKUP = "Look up in Data Mart"

    def has_customer_section(self):
        return self.exists(self.CUSTOMER_SECTION)

    def is_field_editable(self, field_key):
        return self.driver.find_element(*self.field(field_key)).is_enabled()

    def is_field_present(self, field_key):
        return self.exists(self.field(field_key))

    def value_of(self, field_key):
        return self.driver.find_element(*self.field(field_key)).get_attribute("value")

    def shown_value(self, field_key):
        """
        What a field shows, or "" when empty. Works for text boxes and for dropdowns
        (a dropdown is a <button>; its placeholder "Select an option" counts as empty).
        """
        element = self.driver.find_element(*self.field(field_key))
        if element.tag_name.lower() == "input":
            return (element.get_attribute("value") or "").strip()
        shown = element.text.strip()
        if shown == "Select an option":
            return ""
        return shown

    def reference_number(self):
        """The ticket's reference number shown on the form."""
        return self.text_of(
            (
                By.XPATH,
                "//div[normalize-space()='Enquiry Reference Number' or "
                "normalize-space()='Complaint Reference Number']/following-sibling::div[1]",
            )
        )

    def error_for(self, field_key):
        """The error shown under one field, or "" when there is none."""
        return self.field_error(f"edit-{field_key}")

    def shows_required_error_for(self, label):
        return self.shows_message(f"{label} is required")

    def shows_bad_email_message(self):
        return self.shows_message(self.BAD_EMAIL_MESSAGE)

    def shows_bad_phone_message(self):
        return self.shows_message(self.BAD_PHONE_MESSAGE)

    def all_errors(self):
        """Every error message on the form (handy in a failure message)."""
        return self.all_field_errors()

    def has_form_level_error(self):
        return self.exists(self.FORM_LEVEL_ERROR)

    def is_save_enabled(self):
        return self.driver.find_element(*self.SAVE_BUTTON).is_enabled()
