"""
The "create a ticket by hand" screen (/tickets/enquiries/new and /tickets/complaints/new).

It has two steps:
  step 1  search for an existing customer, OR press "Create ticket" to skip
  step 2  the form itself

The form's "Create ticket" button stays DISABLED until the required fields are filled in:
Source, Department, Priority (+ Reason for Walk-in when Source is "Walk-in",
+ Complaint Category on a complaint).
"""

import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from awnic_qa import customers
from awnic_qa.pages.base_page import BasePage


class NewTicketPage(BasePage):
    # Every channel an agent can pick, in the order the form lists them.
    SOURCE_OPTIONS = [
        "Walk-in",
        "Phone",
        "Email",
        "Website Callback",
        "Website Complaint",
        "SANADAK",
        "Social Media",
    ]

    # "Garage Name" is asked for only on these two complaint sub-types.
    GARAGE_SUB_TYPES = ["Garage Repair Delay", "Garage Repair Quality Issues"]
    # "Vehicle Plate" is asked for only when the department is this one.
    MOTOR_DEPARTMENT = "Motor Claims"
    WALK_IN = "Walk-in"
    # The form's section cards, top to bottom.
    SECTION_TITLES = [
        "Customer Details",
        "Ticket Information",
        "Priority & Severity",
        "Assignment",
        "Internal Notes",
    ]
    # Step 1: the page heading and the text above the search box.
    STEP_ONE_HEADING = "New Ticket"
    STEP_ONE_PROMPT = "Let's create a new ticket"
    # The complaint dropdowns below Department, in order.
    COMPLAINT_CASCADE_BELOW_DEPARTMENT = [
        "Product Line",
        "Complaint Category",
        "Complaint Type",
        "Complaint Sub-Type",
    ]

    # The exact inline messages the form shows for a bad email / phone.
    BAD_EMAIL_MESSAGE = "Enter a valid email address"
    BAD_PHONE_MESSAGE = "Enter a valid phone number"

    CREATE_TICKET_BUTTON = (By.XPATH, "//button[normalize-space()='Create ticket']")
    CANCEL_BUTTON = (By.XPATH, "//button[normalize-space()='Cancel']")
    FORM_LANDMARK = (By.XPATH, "//*[normalize-space()='Priority & Severity']")
    CUSTOMER_SEARCH_INPUT = (By.CSS_SELECTOR, "input[aria-label='Search for a customer']")
    # The first result row under the customer search box.
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
    def _label_xpath(field_label):
        """
        The <label> whose first <span> starts with the field name.
        starts-with, because optional fields show "(Optional)" after their name.
        """
        return f"//label[span[starts-with(normalize-space(.),'{field_label}')]]"

    @classmethod
    def dropdown_for(cls, field_label):
        return (
            By.XPATH,
            cls._label_xpath(field_label) + "//button[@aria-haspopup='listbox']",
        )

    @classmethod
    def textarea_for(cls, field_label):
        return (By.XPATH, cls._label_xpath(field_label) + "//textarea")

    @classmethod
    def input_for(cls, field_label):
        return (By.XPATH, cls._label_xpath(field_label) + "//input")

    @classmethod
    def label_for(cls, field_label):
        return (By.XPATH, cls._label_xpath(field_label))

    # ==================================================================
    # Actions
    # ==================================================================

    def continue_to_form(self):
        """Step 1 -> step 2: skip the customer search and go straight to the form."""
        self.click(self.CREATE_TICKET_BUTTON)
        self.wait_visible(self.FORM_LANDMARK)

    def search_customer(self, text):
        """Step 1: type into the customer search box."""
        self.type_into(self.CUSTOMER_SEARCH_INPUT, text)

    def pick_customer(self, search_term):
        """
        Searches for a customer, picks the first result and returns its label.
        The search accepts a policy number, claim number, phone, customer id or email.
        """
        self.search_customer(search_term)
        first = self.wait.until(
            EC.element_to_be_clickable(self.FIRST_CUSTOMER_RESULT)
        )
        label = first.text.strip().replace("\n", " | ")
        first.click()
        self.wait_visible(self.FORM_LANDMARK)
        return label

    def customer_search_found_nobody(self):
        """True when the search ran and found no customer."""
        return self.exists(self.NO_CUSTOMER_FOUND)

    def customer_lookup_is_unavailable(self):
        """True when the customer lookup service could not be reached."""
        return self.exists(self.LOOKUP_UNAVAILABLE)

    def select_option(self, field_label, option_label):
        self.choose_option(self.dropdown_for(field_label), option_label)

    def select_first_option(self, field_label):
        """Picks the first option of a dropdown and returns it (values come from the database)."""
        return self.choose_first_option(self.dropdown_for(field_label))

    def get_dropdown_options(self, field_label):
        return self.read_dropdown_options(self.dropdown_for(field_label))

    def get_loaded_dropdown_options(self, field_label):
        """Like get_dropdown_options(), but waits for the options to finish loading."""
        return self.read_dropdown_options_when_loaded(self.dropdown_for(field_label))

    def fill(self, field_label, text):
        self.type_into(self.input_for(field_label), text)

    def fill_textarea(self, field_label, text):
        self.type_into(self.textarea_for(field_label), text)

    def click_create_ticket(self):
        self.click(self.CREATE_TICKET_BUTTON)

    def click_cancel(self):
        self.click(self.CANCEL_BUTTON)

    def wait_for_customer_search_to_settle(self, seconds=20):
        """
        Waits for the customer search to finish (a result, "No customer found", or
        "lookup unavailable"). Returns False if it is still searching after `seconds`.
        """
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self.exists(self.FIRST_CUSTOMER_RESULT) or self.customer_search_found_nobody():
                return True
            if self.customer_lookup_is_unavailable():
                return True
            time.sleep(0.5)
        return False

    def fill_minimum_enquiry(self, scenario=None):
        """
        Fills the fewest fields that make an ENQUIRY submittable.
        With no customer picked, Alternate Email and Alternate Mobile become required.
        """
        scenario = scenario or customers.DEFAULT_SCENARIO
        self.select_option("Source", "Phone")
        self.select_first_option("Type")
        self.select_first_option("Department")
        self.select_first_option("Priority")
        # A QA email, and the scenario customer's real mobile number.
        self.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.fill("Alternate Mobile", scenario.customer.mobile)

    def fill_minimum_complaint(self, scenario=None):
        """Fills the fewest fields that make a COMPLAINT submittable."""
        scenario = scenario or customers.BROKER_CUSTOMER_COMPLAINT
        self.select_option("Source", "Phone")
        self.select_first_option("Department")
        self.select_first_option("Product Line")
        self.select_first_option("Complaint Category")
        self.select_first_option("Priority")
        self.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.fill("Alternate Mobile", scenario.customer.mobile)

    def choose_garage_sub_type_path(self):
        """
        Picks Motor Claims, then any Product Line / Category / Type path that leads to a
        garage sub-type. Returns the sub-type picked ("" if none).
        """
        self.select_option("Department", self.MOTOR_DEPARTMENT)
        triggers = []
        for label in self.COMPLAINT_CASCADE_BELOW_DEPARTMENT:
            triggers.append(self.dropdown_for(label))
        return self.choose_cascade_path_to(triggers, self.GARAGE_SUB_TYPES)

    def first_non_garage_sub_type(self):
        """The first sub-type that is not a garage one, or "" if there is none."""
        for option in self.get_dropdown_options("Complaint Sub-Type"):
            if option not in self.GARAGE_SUB_TYPES:
                return option
        return ""

    def section_titles(self):
        """
        The section cards on screen, top to bottom.
        Uses textContent because the titles are shown in uppercase.
        """
        titles = []
        for heading in self.driver.find_elements(By.TAG_NAME, "h3"):
            title = (heading.get_attribute("textContent") or "").strip()
            if title in self.SECTION_TITLES:
                titles.append(title)
        return titles

    def is_on_customer_search_step(self):
        """Step 1: the "New Ticket" heading and the search box are shown, the form is not."""
        return (
            self.exists((By.XPATH, f"//h1[normalize-space()='{self.STEP_ONE_HEADING}']"))
            and self.is_customer_search_displayed()
            and not self.exists(self.FORM_LANDMARK)
        )

    # ==================================================================
    # Checks
    # ==================================================================

    def shows_bad_email_message(self):
        return self.shows_message(self.BAD_EMAIL_MESSAGE)

    def shows_bad_phone_message(self):
        return self.shows_message(self.BAD_PHONE_MESSAGE)

    def selected_value(self, field_label):
        """What a dropdown is currently showing."""
        return self.text_of(self.dropdown_for(field_label))

    def is_dropdown_empty(self, field_label):
        """True when a dropdown shows nothing or its "Select an option" placeholder."""
        shown = self.selected_value(field_label)
        return shown == "" or shown.lower() == "select an option"

    def is_create_ticket_enabled(self):
        return self.driver.find_element(*self.CREATE_TICKET_BUTTON).is_enabled()

    def is_field_displayed(self, field_label):
        return self.exists(self.label_for(field_label))

    def is_customer_search_displayed(self):
        return self.exists(self.CUSTOMER_SEARCH_INPUT)

    def has_form_error(self):
        return self.exists(self.FORM_ERROR)

    def get_form_error(self):
        return self.text_of(self.FORM_ERROR)

    def get_field_value(self, field_label):
        """Reads back the value of a text field."""
        return self.driver.find_element(*self.input_for(field_label)).get_attribute("value")

    def get_textarea_value(self, field_label):
        return self.driver.find_element(*self.textarea_for(field_label)).get_attribute("value")

    def is_field_read_only(self, field_label):
        """True when a field is disabled or read-only."""
        control = self.driver.find_element(*self.input_for(field_label))
        return not control.is_enabled() or control.get_attribute("readonly") is not None

    # ---- the Assignment card: Channel -> CC Initiator ----

    # The two catch-all channels, always offered after the pool channels.
    CATCH_ALL_CHANNELS = ["All", "Others"]
    # Added to the name of an initiator who is at today's limit, e.g. "Name — at daily limit (4/4)".
    AT_LIMIT_SUFFIX = " — at daily limit"

    def channel_options_when_loaded(self):
        """
        The Channel options, once the CC Initiator pools have loaded.
        "All" and "Others" are there from the start, so wait for at least one pool channel too.
        Returns [] if the pools never arrive.
        """
        trigger = self.dropdown_for("Channel")

        def pools_loaded(driver):
            options = self.read_dropdown_options(trigger)
            if len(options) > len(self.CATCH_ALL_CHANNELS):
                return options
            return False

        try:
            return self.wait.until(pools_loaded)
        except TimeoutException:
            return []

    def choose_channel(self, channel_label):
        self.select_option("Channel", channel_label)

    def cc_initiator_options(self):
        """
        Every CC Initiator offered for the chosen channel, as (label, can be picked) pairs.
        Only reads the list - nothing is chosen.
        """
        trigger = self.dropdown_for("CC Initiator")
        self.open_dropdown(trigger)
        options = []
        for option in self.driver.find_elements(*self.OPEN_OPTIONS):
            options.append((option.text.strip(), option.is_enabled()))
        self._close_dropdown_if_still_open(trigger)
        return options

    @classmethod
    def initiator_name(cls, option_label):
        """The person's name from a picker label (drops the "at daily limit" note)."""
        return option_label.split(cls.AT_LIMIT_SUFFIX)[0].strip()

    def is_customer_summary_displayed(self):
        """True when the chosen customer's summary bar is shown."""
        return self.has_button("Change customer") or self.has_button("Change")
