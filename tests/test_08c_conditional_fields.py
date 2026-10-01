"""
Conditional field tests on the create and edit forms.

Reason for Walk-in shows only for Source = Walk-in, Vehicle Plate only for Motor Claims,
Garage Name only for a garage sub-type. A hidden field must also be cleared. Nothing is saved.
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.new_ticket_page import NewTicketPage

pytestmark = [pytest.mark.phase2, pytest.mark.regression, pytest.mark.functional]

GARAGE = "Garage Name"
PLATE = "Vehicle Plate"
REASON = "Reason for Walk-in"


class TestConditionalFields(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_form(self, kind):
        self.login_once(self.get("agentEmail"))
        self.open(f"/tickets/{kind}/new")
        self.new_ticket.continue_to_form()

    def reach_garage_sub_type(self):
        sub_type = self.new_ticket.choose_garage_sub_type_path()
        if not sub_type:
            pytest.skip(f"No complaint path leads to a garage sub-type ({NewTicketPage.GARAGE_SUB_TYPES}).")
        return sub_type

    # ---------- the two-step create flow and section order ----------

    @pytest.mark.p1
    @pytest.mark.parametrize("kind", ["enquiries", "complaints"])
    def test_r32_customer_search_comes_first_then_the_form_in_its_five_sections(self, kind):
        """The customer search comes first, then the form with its five sections in order."""
        self.login_once(self.get("agentEmail"))
        self.open(f"/tickets/{kind}/new")
        self.wait.until(lambda d: self.new_ticket.is_customer_search_displayed())

        assert self.new_ticket.is_on_customer_search_step(), (
            "Step 1 should show only the customer search, not the form"
        )
        self.new_ticket.continue_to_form()
        assert self.new_ticket.section_titles() == NewTicketPage.SECTION_TITLES, (
            f"Expected sections {NewTicketPage.SECTION_TITLES}, "
            f"got {self.new_ticket.section_titles()}"
        )

    # ---------- the create form ----------

    @pytest.mark.p1
    @pytest.mark.parametrize("kind", ["enquiries", "complaints"])
    def test_r24_the_walk_in_reason_disappears_when_the_source_changes_away(self, kind):
        self.open_form(kind)
        self.new_ticket.select_option("Source", NewTicketPage.WALK_IN)
        assert self.new_ticket.is_field_displayed(REASON), f"Walk-in should ask why ({kind})"

        self.new_ticket.select_option("Source", "Phone")
        assert not self.new_ticket.is_field_displayed(REASON), (
            f"Changing Source away from Walk-in should hide the reason ({kind})"
        )

    @pytest.mark.p1
    def test_r24_vehicle_plate_is_asked_only_for_motor_claims_and_cleared_when_left(self):
        self.open_form("complaints")
        assert not self.new_ticket.is_field_displayed(PLATE), (
            "No department chosen yet, so no Vehicle Plate"
        )
        departments = self.new_ticket.get_loaded_dropdown_options("Department")
        if NewTicketPage.MOTOR_DEPARTMENT not in departments:
            pytest.skip("Motor Claims is not a complaint department on this environment.")
        # Any department other than Motor Claims.
        other = next(d for d in departments if d != NewTicketPage.MOTOR_DEPARTMENT)

        self.new_ticket.select_option("Department", other)
        assert not self.new_ticket.is_field_displayed(PLATE), (
            f"'{other}' is not Motor Claims, so Vehicle Plate must stay hidden"
        )
        self.new_ticket.select_option("Department", NewTicketPage.MOTOR_DEPARTMENT)
        assert self.new_ticket.is_field_displayed(PLATE), "Motor Claims should ask for the plate"
        self.new_ticket.fill(PLATE, "QA 12345")

        self.new_ticket.select_option("Department", other)
        assert not self.new_ticket.is_field_displayed(PLATE), (
            "Leaving Motor Claims should hide Vehicle Plate"
        )
        self.new_ticket.select_option("Department", NewTicketPage.MOTOR_DEPARTMENT)
        assert self.new_ticket.get_field_value(PLATE) == "", (
            "The plate should have been cleared when the department changed"
        )

    @pytest.mark.p1
    def test_r24_garage_name_appears_only_for_a_garage_sub_type(self):
        self.open_form("complaints")
        assert not self.new_ticket.is_field_displayed(GARAGE), "No sub-type yet, so no Garage"

        sub_type = self.reach_garage_sub_type()
        assert self.new_ticket.is_field_displayed(GARAGE), (
            f"Sub-type '{sub_type}' should show Garage Name"
        )
        other = self.new_ticket.first_non_garage_sub_type()
        if not other:
            pytest.skip("Every sub-type under this path is a garage one; cannot switch away.")
        self.new_ticket.select_option("Complaint Sub-Type", other)
        assert not self.new_ticket.is_field_displayed(GARAGE), (
            f"'{other}' is not a garage sub-type, so Garage Name should be hidden"
        )

    @pytest.mark.p2
    def test_r24_a_garage_chosen_then_hidden_is_cleared(self):
        """A garage chosen, then hidden by changing the sub-type, is cleared."""
        self.open_form("complaints")
        self.reach_garage_sub_type()
        garages = self.new_ticket.get_dropdown_options(GARAGE)
        if not garages:
            pytest.skip("No garages are configured on this environment.")
        self.new_ticket.select_option(GARAGE, garages[0])
        garage_sub_type = self.new_ticket.selected_value("Complaint Sub-Type")
        other = self.new_ticket.first_non_garage_sub_type()
        if not other:
            pytest.skip("Every sub-type under this path is a garage one; cannot switch away.")

        self.new_ticket.select_option("Complaint Sub-Type", other)
        self.new_ticket.select_option("Complaint Sub-Type", garage_sub_type)
        shown = self.new_ticket.selected_value(GARAGE)
        assert shown in ("", "Select the garage"), (
            f"The garage '{garages[0]}' should have been cleared; it shows '{shown}'"
        )

    # ---------- the edit form ----------

    def open_complaint_edit_form(self):
        """Opens the edit form of an open complaint, or skips if Edit is not offered."""
        # Supervisor, not the initiator: an initiator opening a New ticket would change its stage.
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/complaints")
        offered = self.detail.more_action_labels()
        if "Edit" not in offered:
            pytest.skip(f"Edit is not offered on {self.detail.get_reference_number()} ({offered}).")
        self.detail.open_more_action_menu()
        self.detail.click_menu_item("Edit")
        self.wait_for_url_containing("/edit")
        self.edit_ticket.wait_until_loaded()

    def leave_edit_form_unsaved(self):
        self.edit_ticket.cancel()
        self.wait_for_ticket_detail_url()

    @pytest.mark.p1
    def test_r24_edit_form_shows_vehicle_plate_only_for_motor_claims(self):
        """On the edit form, Vehicle Plate shows only for Motor Claims and is cleared when hidden."""
        self.open_complaint_edit_form()
        departments = self.edit_ticket.options_of("department")
        if NewTicketPage.MOTOR_DEPARTMENT not in departments:
            pytest.skip("Motor Claims is not offered on the complaint edit form here.")
        # Any department other than Motor Claims.
        other = next(d for d in departments if d != NewTicketPage.MOTOR_DEPARTMENT)
        try:
            self.edit_ticket.choose("department", other)
            assert not self.edit_ticket.is_field_present("vehicle_plate"), (
                f"Department '{other}' must not show Vehicle Plate"
            )
            self.edit_ticket.choose("department", NewTicketPage.MOTOR_DEPARTMENT)
            assert self.edit_ticket.is_field_present("vehicle_plate"), (
                "Motor Claims should show Vehicle Plate"
            )
            self.edit_ticket.fill("vehicle_plate", "QA 12345")
            self.edit_ticket.choose("department", other)
            assert not self.edit_ticket.is_field_present("vehicle_plate")
            self.edit_ticket.choose("department", NewTicketPage.MOTOR_DEPARTMENT)
            assert self.edit_ticket.value_of("vehicle_plate") == "", (
                "The plate should have been cleared while it was hidden"
            )
        finally:
            self.leave_edit_form_unsaved()

    @pytest.mark.p1
    def test_r24_edit_form_shows_garage_name_only_for_a_garage_sub_type(self):
        """On the edit form, Garage Name shows only for a garage sub-type and is cleared when hidden."""
        self.open_complaint_edit_form()
        try:
            sub_type = self.edit_ticket.choose_garage_sub_type_path(
                NewTicketPage.MOTOR_DEPARTMENT, NewTicketPage.GARAGE_SUB_TYPES
            )
            if not sub_type:
                pytest.skip("No taxonomy path to a garage sub-type on the edit form here.")
            assert self.edit_ticket.is_field_present("garage_name"), (
                f"Sub-type '{sub_type}' should show Garage Name"
            )
            self.edit_ticket.fill("garage_name", "QA Garage")

            # Find the first sub-type that is not a garage one.
            other = ""
            for option in self.edit_ticket.options_of("complaint_sub_type"):
                if option not in NewTicketPage.GARAGE_SUB_TYPES:
                    other = option
                    break
            if not other:
                pytest.skip("Every sub-type under this path is a garage one; cannot switch away.")
            self.edit_ticket.choose("complaint_sub_type", other)
            assert not self.edit_ticket.is_field_present("garage_name"), (
                f"'{other}' is not a garage sub-type, so Garage Name should be hidden"
            )
            self.edit_ticket.choose("complaint_sub_type", sub_type)
            assert self.edit_ticket.value_of("garage_name") == "", (
                "The garage should have been cleared while it was hidden"
            )
        finally:
            self.leave_edit_form_unsaved()
