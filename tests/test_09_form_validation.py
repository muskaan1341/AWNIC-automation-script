"""
FORM VALIDATION - straight from QA/AWNIC-Form-QA-Documentation.xlsx.

That workbook documents every form in the application field by field: what is required, when
it becomes required, and - the useful part for automation - the EXACT sentence the form is
supposed to show when you get it wrong. This class works through its QA checklists for the
three typed-in forms:

  sheet "02 New Ticket - Enquiry"    /tickets/enquiries/new
  sheet "02 New Ticket - Complaint"  /tickets/complaints/new
  sheet "03 Edit Ticket"             /tickets/{id}/edit

WHY ASSERT ON THE WORDING AND NOT JUST THE DISABLED BUTTON?
test_08_create_ticket.py already proves the button stays disabled, which is the sturdier check
and the right one for "can this be submitted at all". But a form that blocks you with the
WRONG explanation is still a form nobody can get past - and the wording is exactly what the
documentation pins down. The two classes are complementary: that one asks "is it blocked?",
this one asks "is the person told why?".
"""

from __future__ import annotations

import pytest

from awnic_qa import customers
from awnic_qa.base_test import BaseTest
from awnic_qa.pages.new_ticket_page import NewTicketPage
from awnic_qa.pages.ticket_edit_page import TicketEditPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   Validation wording — a refusal that is correct but worded wrong
pytestmark = [pytest.mark.p2, pytest.mark.phase1, pytest.mark.regression]



class TestFormValidation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiry_form(self) -> None:
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/enquiries/new")
        self.new_ticket.continue_to_form()

    def open_complaint_form(self) -> None:
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/complaints/new")
        self.new_ticket.continue_to_form()

    # ==================================================================
    # Sheet "02 New Ticket - Enquiry"
    # ==================================================================

    def test_a_malformed_alternate_email_says_exactly_what_is_wrong(self):
        """Checklist: "Malformed alternate email -> 'Enter a valid email address' inline"."""
        self.open_enquiry_form()
        self.new_ticket.fill("Alternate Email", "not-an-email")
        # Move focus on, so the form has a chance to judge what was typed.
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert self.new_ticket.shows_bad_email_message(), (
            f"The form should say '{NewTicketPage.BAD_EMAIL_MESSAGE}' under the field"
        )
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "...and refuse the save while it is wrong"
        )

    def test_a_malformed_alternate_phone_says_exactly_what_is_wrong(self):
        """Checklist: "Malformed alternate phone -> 'Enter a valid phone number' inline"."""
        self.open_enquiry_form()
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", "12345")

        assert self.new_ticket.shows_bad_phone_message(), (
            f"The form should say '{NewTicketPage.BAD_PHONE_MESSAGE}' under the field"
        )
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "...and refuse the save while it is wrong"
        )

    def test_fixing_the_email_clears_the_message_again(self):
        """Correcting the value must clear the message - an error that sticks is its own bug."""
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
        """
        Checklist: "Cascading selects (Type -> Department -> Enquiry -> Sub Enquiry) reset
        children on parent change".

        This one matters more than it looks. If changing the Type left the old Department
        behind, a ticket could be saved carrying a department that does not belong to its type -
        and it would route to the wrong team with nothing on screen looking wrong.
        """
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
            "Changing the Type must clear the Department under it, but it still reads "
            f"'{self.new_ticket.selected_value('Department')}'"
        )

    # ==================================================================
    # Sheet "02 New Ticket - Complaint"
    # ==================================================================

    def test_sub_product_line_is_hidden_rather_than_shown_empty(self):
        """
        Checklist: "Sub-Product Line only shown when the taxonomy has options for the chosen
        Product Line (else hidden, not an empty dropdown)".

        An empty dropdown looks like a screen that failed to load, and gets reported as one.
        """
        self.open_complaint_form()

        if not self.new_ticket.get_dropdown_options("Product Line"):
            pytest.skip("No Product Line values are configured on this environment.")
        self.new_ticket.select_first_option("Product Line")

        if not self.new_ticket.is_field_displayed("Sub-Product Line"):
            return  # correctly hidden - that is the rule working
        assert self.new_ticket.get_dropdown_options("Sub-Product Line"), (
            "Sub-Product Line is on screen, so it must actually offer something - an empty "
            "dropdown should be hidden instead"
        )


    def open_edit_form(self, read_first: tuple[str, ...] = ()) -> dict[str, str]:
        """
        Opens the edit form of the first ticket a supervisor can edit, or skips.

        Returns what the detail page said BEFORE leaving for the form: always the reference
        number (key "reference"), plus each field named in `read_first`, so a test can compare
        the form - or wherever Cancel lands - against the ticket it started from.
        """
        self.login_once(self.get("supervisorEmail"))
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.open_first_row()
        self.detail.wait_until_loaded()

        before = {"reference": self.detail.get_reference_number()}
        for label in read_first:
            before[label] = self.detail.get_detail_field_value(label)

        if not self.detail.has_more_action_menu():
            pytest.skip(
                "This ticket offers no actions to this role - it may be closed or resolved, "
                "which correctly makes it read-only."
            )
        self.detail.open_more_action_menu()
        if "Edit" not in self.detail.get_open_menu_labels():
            pytest.skip(
                "Edit is not offered here. The form is hidden for a ticket with unfilled "
                "required fields, and for a Closed/Resolved one - both correct."
            )
        self.detail.click_menu_item("Edit")
        self.wait_for_url_containing("/edit")
        self.edit_ticket.wait_until_loaded()
        return before

    @pytest.mark.blocked("cc_supervisor")
    def test_the_edit_form_opens_with_the_tickets_current_values(self):
        """
        WHAT THIS REPLACED: "the form has an email_subject OR a department field". Both are
        rendered by the field spec on every enquiry whatever they hold, so a form that opened
        blank - or opened another ticket's values - passed. The name promised the ticket's
        CURRENT VALUES; nothing compared a single one.

        Now it reads the ticket's classification off the detail page, opens Edit, and
        requires the form to be the same ticket showing the same values. These are the
        required cascade levels (TicketEditForm always renders them) and the ones where a
        wrong pre-fill does real damage: saving would silently re-route the ticket.
        """
        # Detail-page label -> edit-form field key. "Type" is deliberately left out: the
        # detail page also has a Customer Details field labelled "Type" (customer type), so
        # reading it by label would compare the wrong field.
        compared = {"Department": "department", "Enquiry": "enquiry", "Sub-Enquiry": "sub_enquiry"}
        before = self.open_edit_form(read_first=tuple(compared))

        assert self.edit_ticket.reference_number() == before["reference"], (
            f"Edit was opened from {before['reference']} but the form is for "
            f"{self.edit_ticket.reference_number()}"
        )
        for label, key in compared.items():
            # The detail page shows an empty field as an em dash; the form shows it empty.
            expected = "" if before[label] == "\u2014" else before[label]
            assert self.edit_ticket.shown_value(key) == expected, (
                f"The ticket's {label} is '{before[label]}', but the edit form opened showing "
                f"'{self.edit_ticket.shown_value(key)}'"
            )
        assert not self.edit_ticket.has_form_level_error(), (
            "A freshly opened form should not be complaining about anything yet"
        )

    @pytest.mark.blocked("cc_supervisor")
    def test_the_edit_form_rejects_a_malformed_email(self):
        """
        Checklist: "Malformed email in contact_email or alternate_email -> 'Enter a valid email address'".

        Aimed at ALTERNATE email. contact_email is editable too (edit-contact_email, since
        commit 9f99225), but both fields go through the SAME check - one branch in
        validateTicketEdit keyed on "contact_email or alternate_email", one EMAIL_RE, one
        message, mirrored server-side in form_spec.py - so one malformed field proves the
        rule. The alternate field is used because it is optional and usually empty, so the
        test does not depend on what the ticket's main contact address currently holds.
        """
        self.open_edit_form()

        if not self.edit_ticket.is_field_present("alternate_email"):
            pytest.skip("This ticket's form has no alternate_email field.")
        self.edit_ticket.fill("alternate_email", "not-an-email")
        self.edit_ticket.save()

        assert self.edit_ticket.shows_bad_email_message(), (
            f"Saving a malformed email should show '{TicketEditPage.BAD_EMAIL_MESSAGE}'. "
            f"Messages on screen: {self.edit_ticket.all_errors()}"
        )
        assert "/edit" in self.current_url(), (
            "...and keep us on the form rather than saving"
        )

    @pytest.mark.blocked("cc_supervisor")
    def test_the_edit_form_rejects_a_malformed_phone(self):
        """
        Checklist: "Malformed phone -> 'Enter a valid phone number'".

        Aimed at ALTERNATE phone, for the same reason as the email test above: contact_phone
        is editable too, but every field of kind "phone" goes through the same PHONE_RE check
        and message, so the one rule is proved once.
        """
        self.open_edit_form()

        if not self.edit_ticket.is_field_present("alternate_phone"):
            pytest.skip("This ticket's form has no alternate_phone field.")
        self.edit_ticket.fill("alternate_phone", "12345")
        self.edit_ticket.save()

        assert self.edit_ticket.shows_bad_phone_message(), (
            f"Saving a malformed phone should show '{TicketEditPage.BAD_PHONE_MESSAGE}'. "
            f"Messages on screen: {self.edit_ticket.all_errors()}"
        )
        assert "/edit" in self.current_url(), "...and keep us on the form"

    @pytest.mark.blocked("cc_supervisor")
    def test_cancelling_the_edit_returns_without_saving(self):
        """
        Cancel must leave without saving - and go back to THE SAME TICKET.

        The only check here used to be "the URL has no updated=1", which also holds if Cancel
        dropped the user on the list, the dashboard or somebody else's ticket. It now also
        requires landing on this ticket's own detail page.
        """
        before = self.open_edit_form()

        self.edit_ticket.cancel()
        self.wait.until(lambda d: "/edit" not in d.current_url)
        self.detail.wait_until_loaded()

        assert "updated=1" not in self.current_url(), (
            f"Cancel must not look like a save. Actual: {self.current_url()}"
        )
        assert self.detail.get_reference_number() == before["reference"], (
            f"Cancel on {before['reference']}'s form should return to that ticket, not "
            f"{self.detail.get_reference_number()}"
        )
