"""
One ticket's detail screen.

The tabs and buttons change with the ticket type and the user's role. For example, only a
complaint has the "Investigation & Resolution" tab.
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.ticket_detail_page import TicketDetailPage

pytestmark = [pytest.mark.p0, pytest.mark.phase1]


class TestTicketDetail(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_first_ticket_of(self, list_path):
        """Open the first ticket on a list and wait for the detail screen."""
        # Skips with a clear reason if the signed-in account has no role.
        self.require_ticket_access()
        self.open(list_path)
        self.list.wait_until_loaded()
        self.list.open_first_row()
        self.detail.wait_until_loaded()

    # ---------- what the screen shows ----------

    @pytest.mark.regression
    def test_opening_a_ticket_shows_its_reference_number_as_the_heading(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        expected = self.list.get_reference_numbers()[0]

        self.list.open_first_row()
        self.detail.wait_until_loaded()

        assert self.detail.get_reference_number() == expected, "The clicked ticket should open"

    @pytest.mark.regression
    def test_every_ticket_always_has_the_four_core_tabs(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Overview", "Customer & Records", "SLA", "Audit"]:
            assert self.detail.has_tab(tab), (
                f"Tab '{tab}' is missing. Tabs: {self.detail.get_tab_labels()}"
            )

    @pytest.mark.regression
    def test_an_enquiry_has_no_investigation_tab(self):
        self.open_first_ticket_of("/tickets/enquiries")

        assert not self.detail.has_tab("Investigation & Resolution"), (
            "Only a complaint should have the investigation tab"
        )

    @pytest.mark.regression
    def test_a_complaint_has_the_investigation_tab(self):
        self.open_first_ticket_of("/tickets/complaints")

        assert self.detail.has_tab("Investigation & Resolution"), (
            f"A complaint should have the investigation tab. Tabs: {self.detail.get_tab_labels()}"
        )

    @pytest.mark.regression
    def test_every_tab_opens_its_own_page(self):
        self.open_first_ticket_of("/tickets/enquiries")

        for tab in ["Customer & Records", "SLA", "Audit"]:
            self.detail.open_tab(tab)
            self.wait.until(lambda d: not self.is_page_not_found())
            assert not self.is_page_not_found(), f"The '{tab}' tab showed 'Page not found'"

    @pytest.mark.regression
    def test_the_overview_tab_shows_the_core_ticket_cards(self):
        self.open_first_ticket_of("/tickets/enquiries")

        assert self.detail.has_section("Ticket Information"), "Ticket Information card is missing"
        assert self.detail.has_internal_notes_card(), "Internal notes card is missing"

    @pytest.mark.regression
    def test_going_back_returns_to_the_list_you_came_from(self):
        self.open_first_ticket_of("/tickets/enquiries")
        self.detail.go_back_to_list()

        self.wait_for_url_containing("/tickets/enquiries")
        assert "/tickets/enquiries" in self.current_url(), (
            f"'Back to Tickets' should return to the list. Actual: {self.current_url()}"
        )

    # ---------- ticket information fields ----------

    @pytest.mark.regression
    def test_an_enquiry_shows_the_enquiry_taxonomy_in_its_ticket_information(self):
        """An enquiry shows Sub-Enquiry and not Complaint Category."""
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        assert self.detail.has_section("Ticket Information")
        assert self.detail.has_detail_field("Sub-Enquiry"), "An enquiry should show Sub-Enquiry"
        assert not self.detail.has_detail_field("Complaint Category"), (
            "An enquiry should not show Complaint Category"
        )

    @pytest.mark.regression
    def test_a_complaint_shows_the_complaint_field_set_instead_of_the_enquiry_one(self):
        """A complaint shows Complaint Category and not Enquiry Summary."""
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/complaints")

        assert self.detail.has_detail_field("Complaint Category"), (
            "A complaint should show Complaint Category"
        )
        assert not self.detail.has_detail_field("Enquiry Summary"), (
            "A complaint should not show Enquiry Summary"
        )

    # ---------- internal notes ----------

    @pytest.mark.regression
    def test_an_empty_internal_note_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        assert not self.detail.is_send_note_enabled(), "Send should be disabled for an empty note"

    @pytest.mark.regression
    def test_a_note_made_only_of_spaces_cannot_be_sent(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("     ")
        assert not self.detail.is_send_note_enabled(), "Send should be disabled for only spaces"

    @pytest.mark.regression
    def test_typing_a_note_enables_send(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        self.detail.type_internal_note("Called the customer, awaiting documents.")
        assert self.detail.is_send_note_enabled(), "Send should be enabled for a real note"

    # ---------- the More Action menu ----------
    # These tests only open the confirmation box and then cancel it. Nothing is changed.

    def _open_enquiry_offering_resolve(self):
        """Open an enquiry whose More Action menu offers Resolve, or skip."""
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")
        offered = self.detail.more_action_labels()
        if TicketDetailPage.RESOLVE_ITEM not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Resolve "
                f"(status '{self.detail.current_status()}', menu {offered})."
            )

    @pytest.mark.regression
    def test_marking_a_ticket_resolved_requires_a_resolution_note(self):
        """Resolve needs a resolution note before it can be confirmed."""
        self._open_enquiry_offering_resolve()
        status_before = self.detail.current_status()

        self.detail.open_resolve()
        self.detail.wait_for_modal()

        assert self.detail.get_modal_title() == TicketDetailPage.RESOLVE_MODAL_TITLE, (
            f"Wrong box title: {self.detail.get_modal_title()}"
        )
        assert self.detail.has_resolution_note_box(), "The box should ask for a resolution note"
        assert not self.detail.is_status_confirm_enabled(), "Confirm should be disabled without a note"
        self.detail.type_status_resolution_note(
            "Policy document was re-issued and emailed to the customer."
        )
        assert self.detail.is_status_confirm_enabled(), "Confirm should be enabled after writing a note"

        # Cancel - nothing is resolved.
        self.detail.close_modal()
        assert self.detail.current_status() == status_before, "Cancel should not change the status"

    @pytest.mark.regression
    def test_the_resolve_box_offers_an_unticked_customer_email_opt_in(self):
        self._open_enquiry_offering_resolve()

        self.detail.open_resolve()
        self.detail.wait_for_modal()

        assert self.detail.has_notify_customer_checkbox(), "The box should offer to email the customer"
        assert not self.detail.is_notify_customer_checked(), "The checkbox should start unticked"
        self.detail.close_modal()

    @pytest.mark.regression
    def test_the_only_manual_status_move_is_resolve_inside_more_action(self):
        """No 'Change Status' button, and no raw status items in More Action."""
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")

        assert not self.detail.has_legacy_change_status_button(), (
            "The old 'Change Status' button should not be shown"
        )
        offered = self.detail.more_action_labels()
        stale = []
        for item in ("Change Status", "In Progress", "Pending Department POC", "Resolved"):
            if item in offered:
                stale.append(item)
        assert not stale, f"More Action should not offer status items. Offered: {offered}"

    @pytest.mark.regression
    def test_resolving_a_complaint_goes_to_its_investigation_tab_not_a_box(self):
        """Resolve on a complaint opens the investigation tab instead of a box."""
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/complaints")
        offered = self.detail.more_action_labels()
        if TicketDetailPage.RESOLVE_ITEM not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Resolve (menu {offered})."
            )

        self.detail.open_resolve()
        self.wait_for_url_containing("/investigation")

        assert "from=resolve" in self.current_url(), (
            f"Should land on the investigation tab. At: {self.current_url()}"
        )
        assert not self.detail.is_modal_open(), "No confirmation box should open for a complaint"

    @pytest.mark.regression
    def test_discarding_asks_for_confirmation_and_never_offers_to_email_the_customer(self):
        """Discard asks for confirmation and does not offer to email the customer."""
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/enquiries")
        offered = self.detail.more_action_labels()
        if "Move to Discarded" not in offered:
            pytest.skip(
                f"{self.detail.get_reference_number()} does not offer Move to Discarded ({offered})."
            )

        self.detail.open_more_action_menu()
        self.detail.click_menu_item("Move to Discarded")
        self.detail.wait_for_modal()

        assert self.detail.is_modal_open(), "Discarding should ask for confirmation"
        assert not self.detail.has_notify_customer_checkbox(), (
            "Discarding should not offer to email the customer"
        )

        # Cancel - nothing is discarded.
        self.detail.close_modal()
        assert not self.detail.is_modal_open(), "Cancel should close the box"

    @pytest.mark.regression
    @pytest.mark.blocked("tier1_window")
    def test_reclassifying_offers_an_unticked_customer_email_opt_in(self):
        self.login_once(self.get("hodEmail"))
        self.open_first_ticket_of("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip("This role has no More Action menu here.")
        self.detail.open_more_action_menu()
        if "Reclassify as Complaint" not in self.detail.get_open_menu_labels():
            pytest.skip("Reclassify is not offered on this ticket.")
        self.detail.click_menu_item("Reclassify as Complaint")
        self.detail.wait_for_modal()

        assert self.detail.has_notify_customer_checkbox(), "The box should offer to email the customer"
        assert not self.detail.is_notify_customer_checked(), "The checkbox should start unticked"
        self.detail.close_modal()

    # ---------- a read-only role ----------

    @pytest.mark.quarantine("TKT-03")
    @pytest.mark.blocked("compliance_officer")
    def test_a_compliance_officer_is_not_offered_resolve(self):
        """Known defect TKT-03: expected to fail until the app is fixed."""
        self.login_once(self.get("complianceEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from("/tickets/complaints")

        offered = self.detail.more_action_labels()
        assert TicketDetailPage.RESOLVE_ITEM not in offered, (
            f"A compliance officer should not be offered Resolve. Offered: {offered}"
        )

    # ---------- reclassify and discard options ----------

    @pytest.mark.regression
    @pytest.mark.blocked("tier1_window")
    def test_a_blocked_swap_is_shown_greyed_out_with_its_reason_not_simply_hidden(self):
        """A blocked Reclassify item is shown disabled with a reason."""
        self.login_once(self.get("hodEmail"))
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.has_more_action_menu():
            pytest.skip("This ticket has no More Action menu for this role.")
        if not self.detail.offers_reclassify_in_any_state():
            pytest.skip("Reclassify is not on this role's menu at all.")

        self.detail.open_more_action_menu()
        disabled = self.detail.reclassify_item_is_disabled()
        reason = self.detail.reclassify_blocked_reason()
        self.press_escape()

        if not disabled:
            pytest.skip("This ticket can still be reclassified, so there is no block to check.")
        assert reason, "A disabled Reclassify item should show the reason"

    @pytest.mark.regression
    def test_the_discard_reason_list_offers_real_choices(self):
        self.login_once(self.get("supervisorEmail"))
        self.open_an_open_ticket_from("/tickets/enquiries")

        if not self.detail.offers_action("Move to Discarded"):
            pytest.skip("This role is not offered discarding on this ticket.")

        self.detail.open_action("Move to Discarded")
        reasons = self.detail.get_escalation_actions()  # the reason dropdown has the same shape
        self.detail.close_modal()

        assert reasons, "The discard box should offer at least one reason"
