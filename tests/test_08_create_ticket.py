"""
MODULE 04 - Creating a ticket by hand (a walk-in or a phone call).

Most of these tests check VALIDATION, and they all do it the same way: by looking at whether
the "Create ticket" button is enabled. That is a very stable thing to assert - there is no
error text to match, so the test cannot pass by accident on the wrong message, and it cannot
break when the wording is polished.

WHAT THE FORM ACTUALLY REQUIRES: Source, Department and Priority. Plus a reason when the
source is Walk-in, and a category when it is a complaint. Subject and Description are optional
- which surprises people, so it is asserted below rather than assumed.

NOTHING HERE WRITES TO THE DATABASE. Every test stops before "Create ticket" is pressed. The
one test that did submit a real enquiry was removed on 2026-09-09 with the other data-writing
tests, so this class is safe against a shared environment.
"""

from __future__ import annotations

import re
import time

import pytest

from awnic_qa import customers
from awnic_qa.base_test import BaseTest
from awnic_qa.pages.new_ticket_page import NewTicketPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P0 'Manual ticket creation — creates a real, correctly-numbered ticket'
pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]



class TestCreateTicket(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiry_form(self) -> None:
        """Opens the create screen and steps past the customer search onto the form itself."""
        self.open("/tickets/enquiries/new")
        self.new_ticket.continue_to_form()

    def open_complaint_form(self) -> None:
        self.open("/tickets/complaints/new")
        self.new_ticket.continue_to_form()

    # ---------- getting to the form ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_create_button_opens_the_new_ticket_screen(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.click_create_button("Create Enquiry")

        self.wait_for_url_containing("/tickets/enquiries/new")
        assert self.new_ticket.is_customer_search_displayed(), (
            "Step 1 should offer a customer search box before the form"
        )

    def test_the_form_can_be_reached_without_picking_a_customer(self):
        self.open_enquiry_form()

        # Not every walk-in is an existing customer, so skipping the search must be allowed.
        assert self.new_ticket.is_field_displayed("Source"), (
            "Skipping the customer search should still open the form"
        )

    # ---------- required fields ----------

    @pytest.mark.sanity
    def test_submit_is_disabled_on_an_empty_form(self):
        self.open_enquiry_form()

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "'Create ticket' must stay disabled until the required fields are filled in"
        )

    @pytest.mark.sanity
    def test_submit_stays_disabled_until_every_required_field_is_filled(self):
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Phone")
        assert not self.new_ticket.is_create_ticket_enabled(), "Source alone is not enough"

        # Department only offers values once a Type has been picked - it is a cascade.
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        assert not self.new_ticket.is_create_ticket_enabled(), "Priority is still missing"

        self.new_ticket.select_first_option("Priority")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A way to contact the customer back is still missing"
        )

        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With every required field filled in, the form should be submittable"
        )

    def test_subject_and_description_are_not_required(self):
        """Subject and Description are optional - worth pinning down so nobody "fixes" it."""
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()

        assert self.new_ticket.is_create_ticket_enabled(), (
            "A ticket should be submittable without a subject or a description"
        )

    # ---------- the channel (Source) ----------

    def test_every_manual_channel_can_be_chosen(self):
        self.open_enquiry_form()

        assert self.new_ticket.get_dropdown_options("Source") == NewTicketPage.SOURCE_OPTIONS, (
            "The Source list should offer every channel an agent can log by hand"
        )

    def test_choosing_walk_in_reveals_the_reason_field(self):
        self.open_enquiry_form()

        assert not self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "The reason field should be hidden until Walk-in is chosen"
        )

        self.new_ticket.select_option("Source", "Walk-in")
        assert self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "Choosing Walk-in should reveal the 'Reason for Walk-in' field"
        )

    def test_choosing_phone_does_not_ask_for_a_walk_in_reason(self):
        self.open_enquiry_form()
        self.new_ticket.select_option("Source", "Phone")

        assert not self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "A phone enquiry should not ask why the customer walked in"
        )

    def test_walk_in_without_a_reason_cannot_be_submitted(self):
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Walk-in")
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A walk-in ticket must explain why the customer came in person"
        )

        self.new_ticket.fill_textarea(
            "Reason for Walk-in", "Customer came to the branch about a motor claim."
        )
        assert self.new_ticket.is_create_ticket_enabled(), (
            "Once the reason is given, the form should be submittable"
        )

    # ---------- complaints ask for more ----------

    @pytest.mark.sanity
    def test_a_complaint_cannot_be_saved_without_its_category(self):
        self.open_complaint_form()

        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A complaint must be categorised before it can be saved"
        )

        # The category list is a cascade - it only fills up once a Product Line is chosen.
        if not self.new_ticket.get_dropdown_options("Product Line"):
            pytest.skip(
                "No Product Line values are configured on this environment, so the complaint "
                "cascade cannot be exercised. Seed the complaint taxonomy first."
            )
        self.new_ticket.select_first_option("Product Line")
        self.new_ticket.select_first_option("Complaint Category")
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With a category chosen, the complaint should be submittable"
        )

    def test_with_no_customer_chosen_the_alternate_contacts_become_compulsory(self):
        """
        When no customer was picked, the two alternate contact fields are the ONLY way to reach
        the person back - so the form makes them compulsory and drops the "(Optional)" from
        their labels. Worth pinning down, because it is easy to "simplify" away.
        """
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "Without a customer, a way to contact them back is required"
        )

        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        assert not self.new_ticket.is_create_ticket_enabled(), "A phone number is needed too"

        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With both contact details given, the form should be submittable"
        )

    def test_the_complaint_form_asks_the_complaint_questions_not_the_enquiry_ones(self):
        self.open_complaint_form()

        assert self.new_ticket.is_field_displayed("Complaint Category"), (
            "A complaint form should ask for a complaint category"
        )
        assert not self.new_ticket.is_field_displayed("Sub Enquiry"), (
            "'Sub Enquiry' belongs to the enquiry form, not the complaint form"
        )

    # ---------- contact details ----------

    def test_an_invalid_email_address_blocks_the_save(self):
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()
        assert self.new_ticket.is_create_ticket_enabled(), "The form should start valid"

        self.new_ticket.fill("Alternate Email", "not-an-email")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A badly formed email address must block the save"
        )

    def test_an_invalid_phone_number_blocks_the_save(self):
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()

        self.new_ticket.fill("Alternate Mobile", "12")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A number that is not a real UAE mobile must block the save"
        )

    # ---------- text that people actually paste in ----------

    def test_arabic_text_is_accepted_and_kept(self):
        self.open_enquiry_form()

        arabic = "العميل يطلب نسخة من وثيقة التأمين"
        self.new_ticket.fill("Subject", arabic)

        assert self.new_ticket.get_field_value("Subject") == arabic, (
            "Arabic text should be stored exactly as typed"
        )

    def test_quotes_ampersands_and_emoji_do_not_break_the_form(self):
        self.open_enquiry_form()

        awkward = 'Policy "A&B" renewal — urgent 🙂'
        self.new_ticket.fill("Subject", awkward)
        self.new_ticket.fill_minimum_enquiry()

        assert self.new_ticket.get_field_value("Subject") == awkward, (
            "Punctuation and emoji should survive unchanged"
        )
        assert self.new_ticket.is_create_ticket_enabled(), (
            "Odd characters should not block a valid form"
        )

    def test_a_very_long_description_is_kept_in_full(self):
        self.open_enquiry_form()

        long_text = "The customer explained at length. " * 60
        self.new_ticket.fill_textarea("Description", long_text)

        assert len(self.new_ticket.get_textarea_value("Description")) == len(long_text), (
            "A long description must not be silently trimmed"
        )

    # ---------- leaving without saving ----------

    def test_cancel_goes_back_to_the_list_without_creating_anything(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        # The REPORTED total: the list shows ten a page, so with more than ten enquiries a new
        # ticket would not change the row count on screen at all.
        before = self.list.get_reported_result_count()

        self.open_enquiry_form()
        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.click_cancel()

        self.list.wait_until_loaded()
        assert self.current_url().endswith("/tickets/enquiries"), (
            f"Cancel should return to the list. Actual: {self.current_url()}"
        )
        assert self.list.get_reported_result_count() == before, (
            f"Cancelling must not create a ticket: {before} enquiries before, "
            f"{self.list.get_reported_result_count()} after"
        )

    # ---------- the happy path ----------