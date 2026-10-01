"""
Form validation message tests.

Checks that the create and edit ticket forms show the right error message
for bad input (email, phone), and that dependent dropdowns reset correctly.
"""

import pytest

from awnic_qa import customers
from awnic_qa.base_test import BaseTest
from awnic_qa.pages.new_ticket_page import NewTicketPage
from awnic_qa.pages.ticket_edit_page import TicketEditPage

pytestmark = [pytest.mark.p2, pytest.mark.phase1, pytest.mark.regression]


class TestFormValidation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("ccInitiatorEmail"))

    def open_enquiry_form(self):
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/enquiries/new")
        self.new_ticket.continue_to_form()

    def open_complaint_form(self):
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/complaints/new")
        self.new_ticket.continue_to_form()

    # ---------- new enquiry form ----------

    def test_a_malformed_alternate_email_says_exactly_what_is_wrong(self):
        self.open_enquiry_form()
        self.new_ticket.fill("Alternate Email", "not-an-email")
        # Fill the next field so the email field loses focus and is checked.
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert self.new_ticket.shows_bad_email_message(), (
            f"The form should say '{NewTicketPage.BAD_EMAIL_MESSAGE}' under the field"
        )
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "Create ticket should be disabled while the email is wrong"
        )

    def test_a_malformed_alternate_phone_says_exactly_what_is_wrong(self):
        self.open_enquiry_form()
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", "12345")

        assert self.new_ticket.shows_bad_phone_message(), (
            f"The form should say '{NewTicketPage.BAD_PHONE_MESSAGE}' under the field"
        )
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "Create ticket should be disabled while the phone is wrong"
        )

    def test_fixing_the_email_clears_the_message_again(self):
        self.open_enquiry_form()
        self.new_ticket.fill("Alternate Email", "not-an-email")
        assert self.new_ticket.shows_bad_email_message(), "Precondition: the message is showing"

        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.wait.until(lambda d: not self.new_ticket.shows_bad_email_message())

        assert not self.new_ticket.shows_bad_email_message(), (
            "Once the address is valid the message must go away"
        )

    @pytest.mark.sanity
    def test_changing_the_type_clears_the_department_beneath_it(self):
        self.open_enquiry_form()

        types = self.new_ticket.get_dropdown_options("Type")
        if len(types) < 2:
            pytest.skip("Only one Type is configured here, so there is no parent change to make.")

        self.new_ticket.select_option("Type", types[0])
        chosen_department = self.new_ticket.select_first_option("Department")
        assert chosen_department, "Precondition: a department was chosen"

        self.new_ticket.select_option("Type", types[1])
        self.wait.until(lambda d: self.new_ticket.is_dropdown_empty("Department"))

        assert self.new_ticket.is_dropdown_empty("Department"), (
            f"Changing the Type should clear Department, but it still reads "
            f"'{self.new_ticket.selected_value('Department')}'"
        )

    # ---------- new complaint form ----------

    def test_sub_product_line_is_hidden_rather_than_shown_empty(self):
        """Sub-Product Line is either hidden or has options - never an empty dropdown."""
        self.open_complaint_form()

        # Product Line only has values once a Department is chosen.
        self.new_ticket.select_first_option("Department")
        if not self.new_ticket.get_loaded_dropdown_options("Product Line"):
            pytest.skip("The first complaint department offers no Product Line on this environment.")
        self.new_ticket.select_first_option("Product Line")

        if not self.new_ticket.is_field_displayed("Sub-Product Line"):
            return  # hidden - that is correct
        assert self.new_ticket.get_dropdown_options("Sub-Product Line"), (
            "Sub-Product Line is shown but has no options - it should be hidden instead"
        )

    # ---------- edit ticket form ----------

    def open_edit_form(self, read_first=()):
        """
        Opens the edit form of an open enquiry, or skips.
        Returns the reference number and the detail-page values of the labels in read_first.
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

        before = {"reference": self.detail.get_reference_number()}
        for label in read_first:
            before[label] = self.detail.get_detail_field_value(label)

        if not self.detail.has_more_action_menu():
            pytest.skip("This ticket offers no actions to this role.")
        self.detail.open_more_action_menu()
        if "Edit" not in self.detail.get_open_menu_labels():
            pytest.skip("Edit is not offered on this ticket.")
        self.detail.click_menu_item("Edit")
        self.wait_for_url_containing("/edit")
        self.edit_ticket.wait_until_loaded()
        return before

    def test_the_edit_form_opens_with_the_tickets_current_values(self):
        """The edit form shows the same ticket and the same Department / Enquiry / Sub-Enquiry."""
        # Detail-page label -> edit-form field key. ("Type" is left out: the page has two.)
        compared = {"Department": "department", "Enquiry": "enquiry", "Sub-Enquiry": "sub_enquiry"}
        before = self.open_edit_form(read_first=tuple(compared))

        assert self.edit_ticket.reference_number() == before["reference"], (
            f"Edit was opened from {before['reference']} but the form is for "
            f"{self.edit_ticket.reference_number()}"
        )
        for label, key in compared.items():
            # The detail page shows an empty value as an em dash; the form shows it empty.
            if before[label] == "—":
                expected = ""
            else:
                expected = before[label]
            assert self.edit_ticket.shown_value(key) == expected, (
                f"The ticket's {label} is '{before[label]}', but the edit form shows "
                f"'{self.edit_ticket.shown_value(key)}'"
            )
        assert not self.edit_ticket.has_form_level_error(), (
            "A freshly opened form should show no error"
        )

    def test_the_edit_form_rejects_a_malformed_email(self):
        """A bad alternate email shows the email error and the form is not saved."""
        self.open_edit_form()

        if not self.edit_ticket.is_field_present("alternate_email"):
            pytest.skip("This ticket's form has no alternate_email field.")
        self.edit_ticket.fill("alternate_email", "not-an-email")
        self.edit_ticket.save()

        assert self.edit_ticket.shows_bad_email_message(), (
            f"Expected '{TicketEditPage.BAD_EMAIL_MESSAGE}'. "
            f"Messages on screen: {self.edit_ticket.all_errors()}"
        )
        assert "/edit" in self.current_url(), "The form should not have been saved"

    def test_the_edit_form_rejects_a_malformed_phone(self):
        """A bad alternate phone shows the phone error and the form is not saved."""
        self.open_edit_form()

        if not self.edit_ticket.is_field_present("alternate_phone"):
            pytest.skip("This ticket's form has no alternate_phone field.")
        self.edit_ticket.fill("alternate_phone", "12345")
        self.edit_ticket.save()

        assert self.edit_ticket.shows_bad_phone_message(), (
            f"Expected '{TicketEditPage.BAD_PHONE_MESSAGE}'. "
            f"Messages on screen: {self.edit_ticket.all_errors()}"
        )
        assert "/edit" in self.current_url(), "The form should not have been saved"

    def test_cancelling_the_edit_returns_without_saving(self):
        """Cancel returns to the same ticket without saving."""
        before = self.open_edit_form()

        self.edit_ticket.cancel()
        self.wait.until(lambda d: "/edit" not in d.current_url)
        self.detail.wait_until_loaded()

        assert "updated=1" not in self.current_url(), (
            f"Cancel must not look like a save. URL: {self.current_url()}"
        )
        assert self.detail.get_reference_number() == before["reference"], (
            f"Cancel should return to {before['reference']}, not "
            f"{self.detail.get_reference_number()}"
        )
