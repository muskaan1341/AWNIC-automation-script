"""
The "create a ticket by hand" screen (/tickets/enquiries/new and /tickets/complaints/new).

IT HAS TWO STEPS:
  step 1  search for an existing customer, OR press "Create ticket" to skip
  step 2  the actual form

The form's own "Create ticket" button stays DISABLED until the required fields are filled
in. That is what most of the validation tests assert, and it is a very reliable thing to
check: there is no error text to match, just enabled or disabled, so the test cannot pass by
accident on the wrong message.

WHAT IS ACTUALLY REQUIRED (from the app's own rule):
  Source, Department, Priority
  + Reason for Walk-in, but only when Source is "Walk-in"
  + Complaint Category, but only on a complaint
Subject and Description are optional. Department only offers values once a Type has been
chosen - it is a cascade.

NAMING NOTE: the Java class called its typing helpers typeInto / typeIntoTextarea. Here
those would collide with BasePage.type_into(locator, text) through inheritance, so the
label-oriented ones are called fill() and fill_textarea().
"""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from awnic_qa import customers
from awnic_qa.pages.base_page import BasePage, Locator


class NewTicketPage(BasePage):
    #: Every channel a hand-typed ticket can come from.
    #: Every channel an agent can log by hand, in the order the form lists them
    #: (NewTicketForm.tsx SOURCE_OPTIONS). SANADAK and Social Media were added on
    #: 2026-09-22 by "align ticket creation with the AWNIC spec" (c7afbdb0); this list
    #: had the five that preceded them, so the test read the addition as a fault.
    SOURCE_OPTIONS = [
        "Walk-in",
        "Phone",
        "Email",
        "Website Callback",
        "Website Complaint",
        "SANADAK",
        "Social Media",
    ]

    # ------------------------------------------------------------------
    # The two inline messages this form can show
    # ------------------------------------------------------------------
    # Wording taken from the Form QA documentation (sheet "02 New Ticket - Enquiry"). These
    # are the exact sentences the form is supposed to produce, so the tests assert on them
    # rather than only on the disabled button - a form that blocks you with the WRONG
    # explanation is still a form nobody can get past.
    # ------------------------------------------------------------------
    # R24 / R32 - conditional fields and the section layout (NewTicketForm.tsx)
    # ------------------------------------------------------------------
    #: "Garage Name" is asked for only on these two complaint sub-types (GARAGE_SUB_TYPES,
    #: NewTicketForm.tsx ~L64; the edit form's lib/ticketEdit.ts keeps the same list).
    GARAGE_SUB_TYPES = ["Garage Repair Delay", "Garage Repair Quality Issues"]
    #: "Vehicle Plate" is asked for only when the complaint's department is this one
    #: (NewTicketForm.tsx ~L642, ticketEdit.ts MOTOR_DEPARTMENT).
    MOTOR_DEPARTMENT = "Motor Claims"
    WALK_IN = "Walk-in"
    #: The form's section cards, top to bottom (the Card titles in NewTicketForm.tsx).
    SECTION_TITLES = [
        "Customer Details",
        "Ticket Information",
        "Priority & Severity",
        "Assignment",
        "Internal Notes",
    ]
    #: Step 1 of NewTicketFlow.tsx - the page heading and the invitation above the search.
    STEP_ONE_HEADING = "New Ticket"
    STEP_ONE_PROMPT = "Let's create a new ticket"
    #: Complaint cascade from Department down to Complaint Sub-Type. Sub-Product Line is left
    #: out: it only renders where the taxonomy has values for the chosen product line.
    COMPLAINT_CASCADE_BELOW_DEPARTMENT = [
        "Product Line",
        "Complaint Category",
        "Complaint Type",
        "Complaint Sub-Type",
    ]

    BAD_EMAIL_MESSAGE = "Enter a valid email address"
    BAD_PHONE_MESSAGE = "Enter a valid phone number"

    CREATE_TICKET_BUTTON = (By.XPATH, "//button[normalize-space()='Create ticket']")
    CANCEL_BUTTON = (By.XPATH, "//button[normalize-space()='Cancel']")
    FORM_LANDMARK = (By.XPATH, "//*[normalize-space()='Priority & Severity']")
    # The customer search box has no id, but it does have an aria-label - a stable hook that
    # exists for screen readers rather than for styling.
    CUSTOMER_SEARCH_INPUT = (By.CSS_SELECTOR, "input[aria-label='Search for a customer']")
    #: A result row in the suggestion panel. The rows are plain <button>s with no id or role
    #: of their own, so they are reached through the panel that holds them - which is itself
    #: identified by the layout classes the component gives it. Not ideal; there is no better
    #: hook on this component today. If it ever gains role="option" (as CustomSelect has),
    #: switch to that and delete this note.
    FIRST_CUSTOMER_RESULT = (
        By.XPATH,
        "(//input[@aria-label='Search for a customer']/ancestor::div[1]"
        "/following-sibling::div//button[@type='button'])[1]",
    )
    NO_CUSTOMER_FOUND = (By.XPATH, "//*[contains(normalize-space(.),'No customer found')]")
    LOOKUP_UNAVAILABLE = (
        By.XPATH,
        "//*[contains(normalize-space(.),'Customer lookup is temporarily unavailable')]",
    )
    FORM_ERROR = (By.CSS_SELECTOR, "p.text-danger, p.text-sm.text-danger")

    @staticmethod
    def _label_xpath(field_label: str) -> str:
        """
        Every field on this form is wrapped in a <label> whose first <span> is the field
        name. So "find the label that says X, then the control inside it" locates any field
        without depending on where it sits on the page.

        WHY starts-with AND NOT AN EXACT MATCH? An optional field's label is not just its
        name - the form appends a second span, so "Description" is really "Description
        (Optional)" on screen. An exact match therefore finds nothing at all for every
        optional field, which is most of them. Matching the START of the label finds both.
        """
        return f"//label[span[starts-with(normalize-space(.),'{field_label}')]]"

    @classmethod
    def dropdown_for(cls, field_label: str) -> Locator:
        return (
            By.XPATH,
            cls._label_xpath(field_label) + "//button[@aria-haspopup='listbox']",
        )

    @classmethod
    def textarea_for(cls, field_label: str) -> Locator:
        return (By.XPATH, cls._label_xpath(field_label) + "//textarea")

    @classmethod
    def input_for(cls, field_label: str) -> Locator:
        return (By.XPATH, cls._label_xpath(field_label) + "//input")

    @classmethod
    def label_for(cls, field_label: str) -> Locator:
        return (By.XPATH, cls._label_xpath(field_label))

    # ==================================================================
    # Actions
    # ==================================================================

    def continue_to_form(self) -> None:
        """Step 1 -> step 2: skip the customer search and go straight to the form."""
        self.click(self.CREATE_TICKET_BUTTON)
        self.wait_visible(self.FORM_LANDMARK)

    def search_customer(self, text: str) -> None:
        """Step 1: type into the customer search box."""
        self.type_into(self.CUSTOMER_SEARCH_INPUT, text)

    def pick_customer(self, search_term: str) -> str:
        """
        Step 1 done PROPERLY: find a real customer and choose them.

        WHY THIS MATTERS MORE THAN IT LOOKS. `continue_to_form()` skips this step, and a
        ticket created that way carries NO policy and NO claim - the form reads both straight
        off the chosen customer (`policy_number: customer?.policy_number ?? null` in
        NewTicketForm.tsx), there is no field to type them into. So every test that skipped
        the search was exercising the ticket form with those two fields permanently empty,
        and never touching the Customer Lookup / Data Mart path at all.

        The box accepts a policy number, claim number, phone number, customer id or email
        (its own placeholder says so), so any identifier from awnic_qa.customers works.

        Returns the label of the customer picked, so a test can assert the ticket ended up
        carrying that customer rather than trusting that the click landed.
        """
        self.search_customer(search_term)
        first = self.wait.until(
            EC.element_to_be_clickable(self.FIRST_CUSTOMER_RESULT)
        )
        label = first.text.strip().replace("\n", " | ")
        first.click()
        self.wait_visible(self.FORM_LANDMARK)
        return label

    def customer_search_found_nobody(self) -> bool:
        """
        True when the search ran and returned nothing.

        Distinguishes "this identifier is not in the Data Mart" from "the lookup service is
        down" - the component shows a different panel for each, and a test that treated them
        the same would report an outage as missing data.
        """
        return self.exists(self.NO_CUSTOMER_FOUND)

    def customer_lookup_is_unavailable(self) -> bool:
        """True when the Data Mart itself could not be reached (the degraded callout)."""
        return self.exists(self.LOOKUP_UNAVAILABLE)

    def select_option(self, field_label: str, option_label: str) -> None:
        self.choose_option(self.dropdown_for(field_label), option_label)

    def select_first_option(self, field_label: str) -> str:
        """
        Picks whatever the FIRST option happens to be, and returns it.
        Used for Department and Priority, whose values come from the database - hard-coding
        one would make the test fail whenever the seed data changes.
        """
        return self.choose_first_option(self.dropdown_for(field_label))

    def get_dropdown_options(self, field_label: str) -> list[str]:
        return self.read_dropdown_options(self.dropdown_for(field_label))

    def get_loaded_dropdown_options(self, field_label: str) -> list[str]:
        """get_dropdown_options() after the form's async taxonomy fetch has landed."""
        return self.read_dropdown_options_when_loaded(self.dropdown_for(field_label))

    def fill(self, field_label: str, text: str) -> None:
        self.type_into(self.input_for(field_label), text)

    def fill_textarea(self, field_label: str, text: str) -> None:
        self.type_into(self.textarea_for(field_label), text)

    def click_create_ticket(self) -> None:
        self.click(self.CREATE_TICKET_BUTTON)

    def click_cancel(self) -> None:
        self.click(self.CANCEL_BUTTON)

    def wait_for_customer_search_to_settle(self, seconds: int = 20) -> bool:
        """
        Waits for the customer search to STOP saying "Searching…". True if it settled.

        Exists because on 2026-09-09 it did not settle at all - the panel sat on "Searching…"
        for 45 seconds with no result, no "No customer found", and not even the component's
        own "lookup is temporarily unavailable" callout. A test that simply waited for a
        result row would report that as a locator problem; this reports it as what it is.
        """
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self.exists(self.FIRST_CUSTOMER_RESULT) or self.customer_search_found_nobody():
                return True
            if self.customer_lookup_is_unavailable():
                return True
            time.sleep(0.5)
        return False

    def fill_minimum_enquiry(self, scenario=None) -> None:
        """
        Fills in the smallest set of fields that makes an ENQUIRY submittable.

        NOTE THE LAST TWO. When no customer was picked in step 1 - which is what these tests
        do - the ticket has no contact details on it at all, so Alternate Email and Alternate
        Mobile become MANDATORY: they are the only way anyone could reach the customer back.
        They also lose their "(Optional)" suffix on screen in that case. The server enforces
        the same rule, so this is a real requirement, not a UI quirk.
        """
        scenario = scenario or customers.DEFAULT_SCENARIO
        self.select_option("Source", "Phone")
        self.select_first_option("Type")
        self.select_first_option("Department")
        self.select_first_option("Priority")
        # REAL contact details, not placeholders. The mobile is the actual Data Mart search
        # key for this scenario's customer (awnic_qa.customers), so the number on the ticket
        # is one that genuinely resolves to a policy and a claim - which "+971501234567"
        # never did. The email is a QA address: the Data Mart records carry no email at all,
        # so there is no real one to use, and inventing a customer's address would be worse
        # than an obviously-QA one.
        self.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.fill("Alternate Mobile", scenario.customer.mobile)

    def fill_minimum_complaint(self, scenario=None) -> None:
        """
        The smallest set that makes a COMPLAINT submittable.

        A complaint needs everything an enquiry needs, plus a Complaint Category. The
        category list is a cascade - it only fills up once a Product Line is chosen.
        """
        scenario = scenario or customers.BROKER_CUSTOMER_COMPLAINT
        self.select_option("Source", "Phone")
        self.select_first_option("Department")
        self.select_first_option("Product Line")
        self.select_first_option("Complaint Category")
        self.select_first_option("Priority")
        self.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.fill("Alternate Mobile", scenario.customer.mobile)

    def choose_garage_sub_type_path(self) -> str:
        """
        Motor Claims, then whatever Product Line / Category / Type path leads to a garage
        sub-type on this environment's taxonomy. Returns the sub-type picked ("" if none).
        """
        self.select_option("Department", self.MOTOR_DEPARTMENT)
        return self.choose_cascade_path_to(
            [self.dropdown_for(label) for label in self.COMPLAINT_CASCADE_BELOW_DEPARTMENT],
            self.GARAGE_SUB_TYPES,
        )

    def first_non_garage_sub_type(self) -> str:
        """Another sub-type offered under the SAME type, "" if the garage ones are all."""
        return next(
            (
                o
                for o in self.get_dropdown_options("Complaint Sub-Type")
                if o not in self.GARAGE_SUB_TYPES
            ),
            "",
        )

    def section_titles(self) -> list[str]:
        """
        The known section cards on screen, top to bottom.

        Read through textContent, not .text: the Card title is styled `uppercase`, so .text
        returns "CUSTOMER DETAILS" while the DOM - and NewTicketForm.tsx - say "Customer
        Details".
        """
        titles = [
            (h.get_attribute("textContent") or "").strip()
            for h in self.driver.find_elements(By.TAG_NAME, "h3")
        ]
        return [t for t in titles if t in self.SECTION_TITLES]

    def is_on_customer_search_step(self) -> bool:
        """Step 1: the "New Ticket" heading, the customer search box, no form yet."""
        return (
            self.exists((By.XPATH, f"//h1[normalize-space()='{self.STEP_ONE_HEADING}']"))
            and self.is_customer_search_displayed()
            and not self.exists(self.FORM_LANDMARK)
        )

    # ==================================================================
    # Checks
    # ==================================================================

    def shows_bad_email_message(self) -> bool:
        return self.shows_message(self.BAD_EMAIL_MESSAGE)

    def shows_bad_phone_message(self) -> bool:
        return self.shows_message(self.BAD_PHONE_MESSAGE)

    def selected_value(self, field_label: str) -> str:
        """
        What a dropdown is currently showing.

        Used to prove the cascade RESETS: changing Type has to clear Department, Enquiry and
        Sub Enquiry, otherwise a ticket can be saved carrying a department that does not
        belong to its type.
        """
        return self.text_of(self.dropdown_for(field_label))

    def is_dropdown_empty(self, field_label: str) -> bool:
        """
        True when a cascade level is showing nothing yet.

        An unchosen dropdown shows its placeholder, so "empty" means the trigger reads
        "Select an option" (or is blank), not that the element is missing.
        """
        shown = self.selected_value(field_label)
        return shown == "" or shown.lower() == "select an option"

    def is_create_ticket_enabled(self) -> bool:
        """The whole point of the validation tests: is the submit button usable yet?"""
        return self.driver.find_element(*self.CREATE_TICKET_BUTTON).is_enabled()

    def is_field_displayed(self, field_label: str) -> bool:
        return self.exists(self.label_for(field_label))

    def is_customer_search_displayed(self) -> bool:
        return self.exists(self.CUSTOMER_SEARCH_INPUT)

    def has_form_error(self) -> bool:
        return self.exists(self.FORM_ERROR)

    def get_form_error(self) -> str:
        return self.text_of(self.FORM_ERROR)

    def get_field_value(self, field_label: str) -> str:
        """Reads a text field back - proves what we typed really went in."""
        return self.driver.find_element(*self.input_for(field_label)).get_attribute("value")

    def get_textarea_value(self, field_label: str) -> str:
        return self.driver.find_element(*self.textarea_for(field_label)).get_attribute("value")

    def is_field_read_only(self, field_label: str) -> bool:
        """True when a field is on screen but greyed out (e.g. Policy Status is read-only)."""
        control = self.driver.find_element(*self.input_for(field_label))
        return not control.is_enabled() or control.get_attribute("readonly") is not None

    def is_customer_summary_displayed(self) -> bool:
        """True when the customer summary bar is showing a picked customer's details."""
        return self.has_button("Change customer") or self.has_button("Change")
