"""
UAT regression - screen checks for the UAT items that were reopened (U11, U12/U17, U15, U16, U22/U24).

All tests are read-only: menus and forms are opened and then cancelled, nothing is downloaded.
Tickets are opened as the CC Supervisor, because opening a New ticket as its own CC Initiator
moves it to In Progress (a real change). Tests skip when UAT has no suitable ticket.
"""

import time

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage
from awnic_qa.pages.ticket_detail_page import TicketDetailPage
from awnic_qa.pages.ticket_edit_page import TicketEditPage
from awnic_qa.pages.ticket_list_page import TicketListPage

pytestmark = [pytest.mark.phase1, pytest.mark.regression]

ENQUIRIES = "/tickets/enquiries"
COMPLAINTS = "/tickets/complaints"

# Allowed working-day SLA ceilings: enquiries 2 or 3 WD, complaints 2, 3 or 4 WD.
ALLOWED_WORKING_DAYS = {ENQUIRIES: {2, 3}, COMPLAINTS: {2, 3, 4}}

# Email enquiries, 50 per page (attachments only arrive by email).
EMAIL_ENQUIRIES = ENQUIRIES + "?source=Email&pageSize=50"
# Maximum seconds to spend opening tickets while looking for test data.
ATTACHMENT_SCAN_SECONDS = 200

# More Action menu labels.
ASSIGN_THE_TICKET = "Assign the Ticket"
OLD_ASSIGN_LABEL = "Assign to Dept POC"
REASSIGN = "Reassign"
RESOLVE = TicketDetailPage.RESOLVE_ITEM
# "Assign to" options in the Assign the Ticket box.
ASSIGN_MODES = ["Assign to Dept POC", "Assign to Another Dept"]


class TestUatRegression(BaseTest):
    # Filled once per class by the search helpers below, so the search runs only once.
    _attachment_tickets = None
    _own_in_progress = None

    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    # ---------- helpers ----------

    def as_supervisor(self):
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()

    def open_list(self, path):
        self.open(path)
        self.list.wait_until_loaded()

    def open_first_ticket(self, path):
        self.open_list(path)
        if self.list.get_row_count() == 0 or self.list.is_empty_state_displayed():
            pytest.skip(f"No tickets visible at {path}.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def discover_attachment_tickets(self):
        """Finds one email enquiry with 2+ attachments ("multi") and one with exactly 1 ("single").

        Returns a dict. A key is missing if no such ticket was found in time.
        """
        cls = type(self)
        if cls._attachment_tickets is not None:
            return cls._attachment_tickets
        self.open_list(EMAIL_ENQUIRIES)
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()
        # Look at worked tickets first; the New column is long.
        links = self.kanban.card_links(
            [KanbanPage.IN_PROGRESS, KanbanPage.PENDING_POC, KanbanPage.NEW, KanbanPage.RESOLVED]
        )
        found = {"scanned": 0}
        deadline = time.monotonic() + ATTACHMENT_SCAN_SECONDS
        for _, url in links:
            if time.monotonic() > deadline or ("multi" in found and "single" in found):
                break
            self.driver.get(url)
            self.detail.wait_until_loaded()
            found["scanned"] += 1
            count = self.detail.attachment_count()
            if count >= 2 and "multi" not in found:
                found["multi"] = url
            elif count == 1 and "single" not in found:
                found["single"] = url
        found["candidates"] = len(links)
        cls._attachment_tickets = found
        return found

    def open_attachment_ticket(self, key):
        found = self.discover_attachment_tickets()
        if key not in found:
            if key == "multi":
                wanted = "two or more attachments"
            else:
                wanted = "exactly one attachment"
            pytest.skip(
                f"No email enquiry with {wanted} among the {found['scanned']} of "
                f"{found['candidates']} opened within {ATTACHMENT_SCAN_SECONDS}s."
            )
        self.driver.get(found[key])
        self.detail.wait_until_loaded()

    def find_open_escalated_ticket(self):
        """Returns (reference, More Action labels) of an open escalated ticket, or None.

        Only tickets where the supervisor is offered Reassign count (others have all actions
        hidden, e.g. duplicate hold). At most 6 tickets are tried.
        """
        open_columns = [KanbanPage.NEW, KanbanPage.IN_PROGRESS, KanbanPage.PENDING_POC]
        tried = 0
        for queue in (ENQUIRIES, COMPLAINTS):
            position = 0
            while tried < 6:
                self.open_list(queue)
                self.list.switch_to_kanban()
                self.kanban.wait_until_loaded()
                escalated = []
                for column in open_columns:
                    for card in self.kanban.cards_in(column):
                        if self.kanban.is_card_escalated(card):
                            escalated.append(card)
                if position >= len(escalated):
                    break
                card = escalated[position]
                position += 1
                tried += 1
                reference = self.kanban.card_reference(card)
                self.kanban.open_card(card)
                self.wait_for_ticket_detail_url()
                self.detail.wait_until_loaded()
                labels = self.detail.more_action_labels()
                if REASSIGN in labels:
                    return reference, labels
        return None

    def discover_own_in_progress(self):
        """Returns up to 3 (reference, url, menu labels) for In Progress tickets owned by the CC Initiator.

        Only In Progress tickets are opened - opening your own New ticket would change it.
        """
        cls = type(self)
        if cls._own_in_progress is not None:
            return cls._own_in_progress
        initiator_email = self.get("ccInitiatorEmail").lower()
        candidates = []
        for queue in (ENQUIRIES, COMPLAINTS):
            self.open_list(queue)
            self.list.switch_to_kanban()
            self.kanban.wait_until_loaded()
            candidates += self.kanban.card_links([KanbanPage.IN_PROGRESS])
        owned = []
        deadline = time.monotonic() + ATTACHMENT_SCAN_SECONDS
        for reference, url in candidates:
            if len(owned) >= 3 or time.monotonic() > deadline:
                break
            self.driver.get(url)
            self.detail.wait_until_loaded()
            if self.detail.cc_initiator_email().lower() != initiator_email:
                continue
            owned.append((reference, url, self.detail.more_action_labels()))
        cls._own_in_progress = owned
        return owned

    # ---------- U11: SLA columns and clocks ----------

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u11_lists_carry_the_sla_and_current_level_sla_columns(self, path):
        """U11: both lists have an "SLA" and a "Current-Level SLA" column."""
        self.as_supervisor()
        self.open_list(path)
        headers = self.list.get_column_headers()

        for column in (TicketListPage.SLA_COLUMN, TicketListPage.CURRENT_LEVEL_SLA_COLUMN):
            assert column in headers, f"{path} should have a '{column}' column. Columns: {headers}"

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u11_the_priority_cell_shows_the_working_day_ceiling(self, path):
        """U11: each Priority cell ends in "<n> WD", and n is an allowed value once a department is set."""
        self.as_supervisor()
        self.open_list(path)
        lines = self.list.priority_working_day_lines()
        if not lines:
            pytest.skip(f"No rows at {path} to read a Priority cell from.")

        malformed = []
        for _, wd in lines:
            if not TicketListPage.WORKING_DAYS_LINE.match(wd):
                malformed.append(wd)
        assert not malformed, (
            f"Every Priority cell on {path} should end in '<n> WD'. Malformed: {malformed}"
        )

        # Only rows with a department have the working-day ceiling.
        allowed = ALLOWED_WORKING_DAYS[path]
        with_department = []
        for dept, wd in lines:
            if dept and dept != "—":
                days = int(TicketListPage.WORKING_DAYS_LINE.match(wd).group(1))
                with_department.append((dept, days))
        if not with_department:
            pytest.skip(f"No row on {path} has a department yet.")

        outside = []
        for d, n in with_department:
            if n not in allowed:
                outside.append((d, n))
        assert not outside, (
            f"On {path} the working days must be one of {sorted(allowed)}. "
            f"Rows outside it (department, WD): {outside}"
        )

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize(
        "path,total_label", [(ENQUIRIES, "Total SLA"), (COMPLAINTS, "Priority SLA")]
    )
    def test_u11_the_priority_and_risk_card_shows_both_sla_clocks(self, path, total_label):
        """U11: PRIORITY & RISK shows Current-Level SLA plus Total SLA (enquiry) or Priority SLA (complaint)."""
        self.as_supervisor()
        self.open_first_ticket(path)

        assert self.detail.has_section("PRIORITY & RISK"), "The PRIORITY & RISK card is missing"
        assert self.detail.priority_card_has_clock("Current-Level SLA"), (
            "PRIORITY & RISK should show the Current-Level SLA clock"
        )
        assert self.detail.priority_card_has_clock(total_label), (
            f"PRIORITY & RISK on a ticket from {path} should show '{total_label}'"
        )
        if total_label == "Total SLA":
            other = "Priority SLA"
        else:
            other = "Total SLA"
        assert not self.detail.priority_card_has_clock(other), (
            f"'{other}' should not be shown on a ticket from {path}"
        )

    # ---------- U12 / U17: attachments ----------

    @pytest.mark.p1
    def test_u12_the_viewer_pages_through_attachments_and_resets_zoom_and_rotation(self):
        """U12/U17: the preview pages between files, and zoom/rotation reset per file."""
        self.as_supervisor()
        self.open_attachment_ticket("multi")

        self.detail.open_attachment_preview(0)
        assert self.detail.has_preview_control("Next attachment"), "Next arrow missing"
        assert self.detail.has_preview_control("Previous attachment"), "Previous arrow missing"
        assert not self.detail.is_preview_control_enabled("Previous attachment"), (
            "On the first file the Previous arrow should be disabled"
        )
        assert self.detail.is_preview_control_enabled("Next attachment"), (
            "The Next arrow should be enabled"
        )
        assert self.detail.has_preview_download(), "The preview should offer a Download link"

        # Zoom and Rotate only exist for images.
        image_first = self.detail.has_preview_control("Rotate")
        if image_first:
            for control in ("Zoom in", "Zoom out", "Rotate"):
                assert self.detail.has_preview_control(control), f"'{control}' missing"
            assert self.detail.preview_zoom_text() == "100%"
            self.detail.click_preview_control("Zoom in")
            self.wait.until(lambda d: self.detail.preview_zoom_text() == "125%")
            self.detail.click_preview_control("Rotate")
            self.wait.until(lambda d: "rotate(90deg)" in self.detail.preview_image_transform())

        # The position is read from the arrows (two files may have the same name).
        self.detail.click_preview_control("Next attachment")
        self.wait.until(lambda d: self.detail.is_preview_control_enabled("Previous attachment"))
        if self.detail.has_preview_control("Rotate"):
            assert self.detail.preview_zoom_text() == "100%", (
                "The next file must open at 100% zoom"
            )

        self.detail.click_preview_control("Previous attachment")
        self.wait.until(
            lambda d: not self.detail.is_preview_control_enabled("Previous attachment")
        )
        if image_first:
            assert self.detail.preview_zoom_text() == "100%", (
                "Going back to a file must show it at 100% zoom"
            )
            assert "rotate(0deg)" in self.detail.preview_image_transform(), (
                f"Going back to a file must show it unrotated. Style: "
                f"{self.detail.preview_image_transform()}"
            )
        self.detail.close_preview()
        if not image_first:
            pytest.skip("Paging checked; the first file is not an image, so zoom/rotate was not checked.")

    @pytest.mark.p1
    def test_u12_download_all_is_offered_only_with_two_or_more_attachments(self):
        """U12/U17: "Download all" only with 2+ attachments; every file has its own download link."""
        self.as_supervisor()
        self.open_attachment_ticket("multi")
        count = self.detail.attachment_count()
        assert self.detail.has_download_all(), (
            f"With {count} attachments the card should offer 'Download all'"
        )
        assert len(self.detail.attachment_download_labels()) == count, (
            "Every attachment should have its own download link"
        )

        self.open_attachment_ticket("single")
        assert self.detail.attachment_count() == 1
        assert not self.detail.has_download_all(), (
            "A single attachment must not offer 'Download all'"
        )
        assert len(self.detail.attachment_download_labels()) == 1, (
            "The single attachment should still have its own download link"
        )

    # ---------- U15: Refresh button, merged rows ----------

    @pytest.mark.p2
    @pytest.mark.parametrize("path", ["/", ENQUIRIES, COMPLAINTS])
    def test_u15_refresh_is_offered_on_the_dashboard_and_both_lists(self, path):
        """U15: the dashboard and both lists have a Refresh button."""
        self.as_supervisor()
        self.open_and_wait(path)
        self.wait_for_page_content()
        assert self.list.has_refresh_button(), f"{path} should offer a Refresh button"

    @pytest.mark.p1
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u15_a_merged_row_says_where_it_went_and_cannot_be_opened(self, path):
        """U15: a merged row says which ticket it was merged into and cannot be clicked."""
        self.as_supervisor()
        self.open_list(path + "?duplicate=merged")
        merged = self.list.merged_rows()
        if not merged:
            pytest.skip(f"No merged duplicate visible at {path} on UAT.")

        row = merged[0]
        assert row["inert"] and not row["clickable"], (
            f"Merged row {row['reference']} must not be clickable"
        )
        tooltip = self.list.reference_tooltip(row["index"])
        assert tooltip.startswith("This ticket has been merged into "), (
            f"Merged row {row['reference']} should say where it was merged. Tooltip: '{tooltip}'"
        )
        target = tooltip.removeprefix("This ticket has been merged into ").rstrip(".")
        assert target and target != row["reference"], (
            f"The tooltip should name another ticket. Got '{target}'"
        )

    # ---------- U16: customer details ----------

    @pytest.mark.p1
    def test_u16_the_ticket_shows_customer_details_and_the_edit_form_can_change_them(self):
        """U16: Customer Details shows on the ticket and can be edited on the Edit form (then cancelled)."""
        self.as_supervisor()
        self.open_an_open_ticket_from(ENQUIRIES)
        assert self.detail.has_section("CUSTOMER DETAILS"), (
            "The ticket Overview should show the Customer Details card"
        )

        offered = self.detail.more_action_labels()
        if "Edit" not in offered:
            pytest.skip(
                f"Edit is not offered on {self.detail.get_reference_number()} ({offered}) - "
                "it is hidden while required fields are missing."
            )
        self.detail.open_more_action_menu()
        self.detail.click_menu_item("Edit")
        self.wait_for_url_containing("/edit")
        self.edit_ticket.wait_until_loaded()

        assert self.edit_ticket.has_customer_section(), (
            "The edit form should have a Customer Details section"
        )
        for key in ("customer_name", "contact_email", "contact_phone", "alternate_email"):
            assert self.edit_ticket.is_field_present(key), f"The {key} field is missing"
            assert self.edit_ticket.is_field_editable(key), f"edit-{key} should be editable"
        assert self.edit_ticket.has_button(TicketEditPage.DATA_MART_LOOKUP), (
            "The edit form should offer the Data Mart look-up"
        )

        self.edit_ticket.cancel()
        self.wait_for_ticket_detail_url()

    # ---------- U22 / U24: the More Action menu ----------

    @pytest.mark.p1
    @pytest.mark.escalation
    def test_u22_an_escalated_ticket_offers_no_resolve(self):
        """U22: an escalated ticket does not offer Resolve."""
        # Note: the API does allow resolving an escalated ticket; this checks the screen only.
        self.as_supervisor()
        found = self.find_open_escalated_ticket()
        if found is None:
            pytest.skip("No escalated open ticket with a working action menu on UAT.")
        reference, offered = found

        assert not self.detail.has_legacy_change_status_button()
        assert RESOLVE not in offered, (
            f"{reference} is escalated, so Resolve must be hidden. Offered: {offered}"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_u22_the_cc_initiator_menu_on_their_own_ticket(self):
        """U22/U24: the CC Initiator's own ticket offers Assign the Ticket and Resolve, but not Reassign."""
        # Signed in as the CC Initiator: this checks the menu of the ticket's own CC Initiator.
        self.login_once(self.get("ccInitiatorEmail"))
        self.require_ticket_access()
        owned = self.discover_own_in_progress()
        if not owned:
            pytest.skip(f"No In Progress ticket on UAT has {self.get('ccInitiatorEmail')} as its CC Initiator.")

        with_assign = []
        for reference, url, labels in owned:
            if ASSIGN_THE_TICKET in labels:
                with_assign.append((reference, url, labels))
        if not with_assign:
            pytest.skip(f"None of the CC Initiator's In Progress tickets offers Assign the Ticket. Menus: {owned}")
        reference, url, offered = with_assign[0]
        self.driver.get(url)
        self.detail.wait_until_loaded()

        assert not self.detail.has_legacy_change_status_button(), (
            "There should be no separate Change Status button"
        )
        assert OLD_ASSIGN_LABEL not in offered, (
            f"The item should be called '{ASSIGN_THE_TICKET}', not '{OLD_ASSIGN_LABEL}': {offered}"
        )
        assert RESOLVE in offered, f"The CC Initiator should be offered Resolve: {offered}"
        assert REASSIGN not in offered, (
            f"Reassign must NOT be offered to a CC Initiator ({reference}): {offered}"
        )

    @pytest.mark.p2
    @pytest.mark.rbac
    def test_u22_the_cc_initiator_is_offered_reclassify_inside_the_window(self):
        """U22: the CC Initiator is offered the swap to the other type (enquiry <-> complaint)."""
        self.login_once(self.get("ccInitiatorEmail"))
        self.require_ticket_access()
        owned = self.discover_own_in_progress()
        if not owned:
            pytest.skip(f"No In Progress ticket on UAT is owned by {self.get('ccInitiatorEmail')}.")

        swaps = ("Reclassify as Complaint", "Reclassify as Enquiry")
        reclassifiable = []
        for ticket in owned:
            labels = ticket[2]
            for label in swaps:
                if label in labels:
                    reclassifiable.append(ticket)
                    break
        if not reclassifiable:
            pytest.skip(f"None of the CC Initiator's tickets can be reclassified now. Menus: {owned}")

        reference, _, offered = reclassifiable[0]
        prefix = reference[:3]
        if prefix == "INQ":
            expected = "Reclassify as Complaint"
        else:
            expected = "Reclassify as Enquiry"
        assert expected in offered, f"{reference} should offer '{expected}': {offered}"

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_u22_assign_the_ticket_offers_both_modes_and_a_copy_field(self):
        """U22: the Assign the Ticket box offers both "Assign to" options and a Copy field (then cancelled)."""
        self.login_once(self.get("ccInitiatorEmail"))
        self.require_ticket_access()
        owned = []
        for ticket in self.discover_own_in_progress():
            if ASSIGN_THE_TICKET in ticket[2]:
                owned.append(ticket)
        if not owned:
            pytest.skip("No In Progress ticket owned by the CC Initiator offers Assign the Ticket.")
        self.driver.get(owned[0][1])
        self.detail.wait_until_loaded()

        self.detail.open_action(ASSIGN_THE_TICKET)
        assert self.detail.get_modal_title() == ASSIGN_THE_TICKET
        assert self.detail.get_assign_modes() == ASSIGN_MODES, (
            f"'Assign to' should offer {ASSIGN_MODES}"
        )
        assert self.detail.exists(self.detail.modal_field("Copy")), (
            "The Assign the Ticket box should have a Copy field"
        )
        self.detail.close_modal()
        assert not self.detail.is_modal_open(), "Cancel should close the box"
