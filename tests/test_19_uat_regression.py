"""
UAT REGRESSION - the UI half of the items the UAT tracker reopened (U11, U12/U17, U15, U16, U22/U24).

Every label asserted here is read from apps/web source, named in each test's docstring, never
guessed. Every test is READ-ONLY on the shared UAT environment:

  * menus and modals are opened and then closed / cancelled - nothing is confirmed,
  * attachments are previewed, never downloaded (links are only checked for presence),
  * tickets are opened as the CC SUPERVISOR wherever the role does not matter. Opening a "New"
    ticket as its ASSIGNED CC Initiator auto-advances it to In Progress (AutoAdvanceOnOpen /
    shouldAutoAdvanceOnOpen, client requirement 1.24) - a real write. The supervisor is never an
    assigned initiator, so browsing as them changes nothing. The one class of test that must be
    the initiator (U22) only ever opens that initiator's IN PROGRESS tickets, which the auto-advance
    no longer touches.

Data on UAT is discovered at runtime from the lists; when the shape a test needs is not there, the
test SKIPS naming the missing data rather than passing on nothing.
"""

from __future__ import annotations

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

#: TicketPriorityCell.tsx: the whole-ticket ceiling - Complaints 4/3/2 WD (Invalid / Regular /
#: Reputational or High), Enquiries 3 WD or 2 WD (reputational). Confirmed against the UAT
#: sla_matrix / non_motor_sla_policy working-day columns (read-only, 2026-09-30).
ALLOWED_WORKING_DAYS = {ENQUIRIES: {2, 3}, COMPLAINTS: {2, 3, 4}}

#: The email-sourced enquiry list, 50 to a page, via the list's own URL contract
#: (lib/ticket-query.ts - `source` multi-filter, `pageSize` in PAGE_SIZE_OPTIONS). Attachments on
#: UAT only ever arrive by email intake, so this is where they are.
EMAIL_ENQUIRIES = ENQUIRIES + "?source=Email&pageSize=50"
#: How long the attachment discovery may spend opening tickets before giving up with a data
#: skip - well inside pytest.ini's 300-second per-test backstop.
ATTACHMENT_SCAN_SECONDS = 200

#: TicketHeaderActions.tsx menu labels.
ASSIGN_THE_TICKET = "Assign the Ticket"
OLD_ASSIGN_LABEL = "Assign to Dept POC"
REASSIGN = "Reassign"
RESOLVE = TicketDetailPage.RESOLVE_ITEM
#: AssignDeptPocModal.tsx "Assign to" options.
ASSIGN_MODES = ["Assign to Dept POC", "Assign to Another Dept"]


class TestUatRegression(BaseTest):
    #: Filled once per class by the discovery helpers - opening ~50 tickets once is fine, twice
    #: is not.
    _attachment_tickets: dict | None = None
    _own_in_progress: list | None = None

    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def as_supervisor(self) -> None:
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()

    def open_list(self, path: str) -> None:
        self.open(path)
        self.list.wait_until_loaded()

    def open_first_ticket(self, path: str) -> None:
        self.open_list(path)
        if self.list.get_row_count() == 0 or self.list.is_empty_state_displayed():
            pytest.skip(f"No tickets visible at {path}.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def discover_attachment_tickets(self) -> dict:
        """
        {"multi": url, "single": url} - one email enquiry with >= 2 attachments and one with
        exactly 1, found by OPENING tickets as the supervisor (read-only). Either key is absent
        when the time budget runs out without one; "scanned" says how many were opened.

        One board load harvests every email enquiry's ticket link (the board honours the list's
        ?source=Email filter), then each ticket is visited directly - reloading the list per
        ticket blew the suite's 300-second per-test backstop on the first UAT run.
        """
        cls = type(self)
        if cls._attachment_tickets is not None:
            return cls._attachment_tickets
        self.open_list(EMAIL_ENQUIRIES)
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()
        # Worked tickets first: New holds the long tail of untouched intake (136 email
        # enquiries on UAT on 2026-09-30, most of them New), and 200 seconds opens ~50.
        links = self.kanban.card_links(
            [KanbanPage.IN_PROGRESS, KanbanPage.PENDING_POC, KanbanPage.NEW, KanbanPage.RESOLVED]
        )
        found: dict = {"scanned": 0}
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

    def open_attachment_ticket(self, key: str) -> None:
        found = self.discover_attachment_tickets()
        if key not in found:
            wanted = "two or more attachments" if key == "multi" else "exactly one attachment"
            pytest.skip(
                f"No email enquiry with {wanted} among the {found['scanned']} of "
                f"{found['candidates']} email enquiries opened within the "
                f"{ATTACHMENT_SCAN_SECONDS}s discovery budget on UAT."
            )
        self.driver.get(found[key])
        self.detail.wait_until_loaded()

    def find_open_escalated_ticket(self) -> tuple[str, list[str]] | None:
        """
        (reference, More Action labels) of an ESCALATED open ticket whose header is NOT frozen,
        or None. Every open column is searched: escalation is a breach_level badge, not a column
        (app/stages/mapping.py), so an escalated ticket can still sit in New or In Progress.

        "Not frozen" = the supervisor is offered Reassign there. A ticket on duplicate hold or
        still pending classification hides EVERY action, so Resolve's absence would prove
        nothing about escalation; such tickets are passed over. At most 6 are tried.
        """
        open_columns = [KanbanPage.NEW, KanbanPage.IN_PROGRESS, KanbanPage.PENDING_POC]
        tried = 0
        for queue in (ENQUIRIES, COMPLAINTS):
            position = 0
            while tried < 6:
                self.open_list(queue)
                self.list.switch_to_kanban()
                self.kanban.wait_until_loaded()
                cards = [c for column in open_columns for c in self.kanban.cards_in(column)]
                escalated = [c for c in cards if self.kanban.is_card_escalated(c)]
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

    def discover_own_in_progress(self) -> list:
        """
        [(reference, url, menu labels)] for In Progress tickets - enquiries AND complaints -
        whose CC Ticket Initiator is the signed-in agent. ONLY In Progress: opening one's own
        NEW ticket would auto-advance it (a write). Every In Progress card's link is harvested
        from one board load per queue, then visited directly; at most 3 owned tickets are kept.
        """
        cls = type(self)
        if cls._own_in_progress is not None:
            return cls._own_in_progress
        agent = self.get("agentEmail").lower()
        candidates: list[tuple[str, str]] = []
        for queue in (ENQUIRIES, COMPLAINTS):
            self.open_list(queue)
            self.list.switch_to_kanban()
            self.kanban.wait_until_loaded()
            candidates += self.kanban.card_links([KanbanPage.IN_PROGRESS])
        owned: list = []
        deadline = time.monotonic() + ATTACHMENT_SCAN_SECONDS
        for reference, url in candidates:
            if len(owned) >= 3 or time.monotonic() > deadline:
                break
            self.driver.get(url)
            self.detail.wait_until_loaded()
            if self.detail.cc_initiator_email().lower() != agent:
                continue
            owned.append((reference, url, self.detail.more_action_labels()))
        cls._own_in_progress = owned
        return owned

    # ==================================================================
    # U11 - the two SLA columns, the working-day line, the PRIORITY & RISK clocks
    # ==================================================================

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u11_lists_carry_the_sla_and_current_level_sla_columns(self, path):
        """
        UAT U11. TicketTypeListClient.tsx declares BOTH clocks as columns: "SLA" (the whole-ticket
        outer ceiling, Total/Priority SLA) and "Current-Level SLA" (the current holder's
        deadline, which resets on escalation). One without the other hides half the SLA story.
        """
        self.as_supervisor()
        self.open_list(path)
        headers = self.list.get_column_headers()

        for column in (TicketListPage.SLA_COLUMN, TicketListPage.CURRENT_LEVEL_SLA_COLUMN):
            assert column in headers, f"{path} should have a '{column}' column. Columns: {headers}"

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u11_the_priority_cell_shows_the_working_day_ceiling(self, path):
        """
        UAT U11. TicketPriorityCell.tsx renders "<n> WD" under the priority pill - the whole-ticket
        working-day ceiling (Complaints 4/3/2, Enquiries 3/2). Before a department is assigned it
        falls back to sla_days (the Dept-POC TAT, 0/1 day), so the range check covers only rows
        that HAVE a department; the "<n> WD" shape is checked on every row. No deadline
        arithmetic here - that belongs to the API tier.
        """
        self.as_supervisor()
        self.open_list(path)
        lines = self.list.priority_working_day_lines()
        if not lines:
            pytest.skip(f"No rows at {path} to read a Priority cell from.")

        malformed = [wd for _, wd in lines if not TicketListPage.WORKING_DAYS_LINE.match(wd)]
        assert not malformed, (
            f"Every Priority cell on {path} should end in '<n> WD'. Malformed: {malformed}"
        )
        allowed = ALLOWED_WORKING_DAYS[path]
        with_department = [
            (dept, int(TicketListPage.WORKING_DAYS_LINE.match(wd).group(1)))
            for dept, wd in lines
            if dept and dept != "—"
        ]
        if not with_department:
            pytest.skip(f"No row on {path} has a department yet, so no ceiling has started.")
        outside = [(d, n) for d, n in with_department if n not in allowed]
        assert not outside, (
            f"On {path} the working-day ceiling must be one of {sorted(allowed)}. "
            f"Rows outside it (department, WD): {outside}"
        )

    @pytest.mark.p1
    @pytest.mark.sla
    @pytest.mark.parametrize(
        "path,total_label", [(ENQUIRIES, "Total SLA"), (COMPLAINTS, "Priority SLA")]
    )
    def test_u11_the_priority_and_risk_card_shows_both_sla_clocks(self, path, total_label):
        """
        UAT U11. PriorityCard.tsx (PRIORITY & RISK) shows "Current-Level SLA" on every ticket and
        the whole-ticket clock beneath it, labelled "Total SLA" on an enquiry and "Priority SLA"
        on a complaint (its budget varies with priority/risk).
        """
        self.as_supervisor()
        self.open_first_ticket(path)

        assert self.detail.has_section("PRIORITY & RISK"), "The PRIORITY & RISK card is missing"
        assert self.detail.priority_card_has_clock("Current-Level SLA"), (
            "PRIORITY & RISK should show the Current-Level SLA clock"
        )
        assert self.detail.priority_card_has_clock(total_label), (
            f"PRIORITY & RISK on a ticket from {path} should label the whole-ticket clock "
            f"'{total_label}'"
        )
        other = "Priority SLA" if total_label == "Total SLA" else "Total SLA"
        assert not self.detail.priority_card_has_clock(other), (
            f"'{other}' belongs to the other ticket type, not to a ticket from {path}"
        )

    # ==================================================================
    # U12 / U17 - attachments: the panel, the viewer, Download all
    # ==================================================================

    @pytest.mark.p1
    def test_u12_the_viewer_pages_through_attachments_and_resets_zoom_and_rotation(self):
        """
        UAT U12/U17. AttachmentPreviewModal.tsx: arrows "Previous attachment"/"Next attachment"
        flank the preview when there is more than one file (Previous disabled on the first,
        Next on the last); an image gets "Zoom out"/"Zoom in"/"Rotate" and a percentage
        readout; moving to another file resets zoom to 100% and rotation to 0 (`go()` sets both
        back). Nothing is downloaded - the modal is closed.

        Position is read from the arrows, not the title: two attachments may share a file name
        (UAT's 2-file ticket holds two "image.png"), so the title cannot tell them apart.
        """
        self.as_supervisor()
        self.open_attachment_ticket("multi")

        self.detail.open_attachment_preview(0)
        assert self.detail.has_preview_control("Next attachment"), "Next arrow missing"
        assert self.detail.has_preview_control("Previous attachment"), "Previous arrow missing"
        assert not self.detail.is_preview_control_enabled("Previous attachment"), (
            "On the first file the Previous arrow should be disabled"
        )
        assert self.detail.is_preview_control_enabled("Next attachment"), (
            "With more files to see, the Next arrow should be usable"
        )
        assert self.detail.has_preview_download(), "The preview should offer a Download link"

        image_first = self.detail.has_preview_control("Rotate")
        if image_first:
            for control in ("Zoom in", "Zoom out", "Rotate"):
                assert self.detail.has_preview_control(control), f"'{control}' missing"
            assert self.detail.preview_zoom_text() == "100%"
            self.detail.click_preview_control("Zoom in")
            self.wait.until(lambda d: self.detail.preview_zoom_text() == "125%")
            self.detail.click_preview_control("Rotate")
            self.wait.until(lambda d: "rotate(90deg)" in self.detail.preview_image_transform())

        self.detail.click_preview_control("Next attachment")
        self.wait.until(lambda d: self.detail.is_preview_control_enabled("Previous attachment"))
        if self.detail.has_preview_control("Rotate"):
            assert self.detail.preview_zoom_text() == "100%", (
                "The next file must open at 100%, not inherit the previous file's zoom"
            )

        self.detail.click_preview_control("Previous attachment")
        self.wait.until(
            lambda d: not self.detail.is_preview_control_enabled("Previous attachment")
        )
        if image_first:
            assert self.detail.preview_zoom_text() == "100%", (
                "Coming back to a file must show it at 100%, not the zoom it was left at"
            )
            assert "rotate(0deg)" in self.detail.preview_image_transform(), (
                "Coming back to a file must show it unrotated. Style: "
                f"{self.detail.preview_image_transform()}"
            )
        self.detail.close_preview()
        if not image_first:
            pytest.skip(
                "Paging checked; the first attachment is not an image, so the zoom/rotate "
                "controls (image-only by design) could not be exercised on this ticket."
            )

    @pytest.mark.p1
    def test_u12_download_all_is_offered_only_with_two_or_more_attachments(self):
        """
        UAT U12/U17. AttachmentsPanel.tsx puts "Download all" (one ZIP) in the card header only
        when attachments.length > 1; every row keeps its own per-file download link
        (AttachmentRow.tsx, aria-label "Download <name>"). Presence only - nothing downloaded.
        """
        self.as_supervisor()
        self.open_attachment_ticket("multi")
        count = self.detail.attachment_count()
        assert self.detail.has_download_all(), (
            f"With {count} attachments the card should offer 'Download all'"
        )
        assert len(self.detail.attachment_download_labels()) == count, (
            "Every attachment row should carry its own download link"
        )

        self.open_attachment_ticket("single")
        assert self.detail.attachment_count() == 1
        assert not self.detail.has_download_all(), (
            "A lone attachment must not offer 'Download all' - its own link already does that"
        )
        assert len(self.detail.attachment_download_labels()) == 1, (
            "The single attachment should still have its per-file download link"
        )

    # ==================================================================
    # U15 - Refresh everywhere, merged rows labelled and inert
    # ==================================================================

    @pytest.mark.p2
    @pytest.mark.parametrize("path", ["/", ENQUIRIES, COMPLAINTS])
    def test_u15_refresh_is_offered_on_the_dashboard_and_both_lists(self, path):
        """
        UAT U15. RefreshButton.tsx ("Refresh") sits on the Dashboard (app/page.tsx) and on both
        ticket lists (TicketTypeListClient.tsx). Only its presence is asserted.
        """
        self.as_supervisor()
        self.open_and_wait(path)
        self.wait_for_page_content()
        assert self.list.has_refresh_button(), f"{path} should offer a Refresh button"

    @pytest.mark.p1
    @pytest.mark.parametrize("path", [ENQUIRIES, COMPLAINTS])
    def test_u15_a_merged_row_says_where_it_went_and_cannot_be_opened(self, path):
        """
        UAT U15. TicketReferenceCell.tsx labels a merged duplicate with a "Merged" badge and a
        hover "This ticket has been merged into <ref>." (duplicateTooltipLabel); the per-type
        list renders the row inert (rowDisabled={(t) => t.is_duplicate} -> cursor-not-allowed).
        Found through the list's own Duplicate=Merged filter (?duplicate=merged).
        Deliberately NOT asserted: inline photos in an email body - they are attachment chips
        by design.
        """
        self.as_supervisor()
        self.open_list(path + "?duplicate=merged")
        merged = self.list.merged_rows()
        if not merged:
            pytest.skip(f"No merged duplicate visible at {path} on UAT.")

        row = merged[0]
        assert row["inert"] and not row["clickable"], (
            f"Merged row {row['reference']} must be rendered inert, not clickable"
        )
        tooltip = self.list.reference_tooltip(row["index"])
        assert tooltip.startswith("This ticket has been merged into "), (
            f"Merged row {row['reference']} should say which ticket it was merged into. "
            f"Tooltip: '{tooltip}'"
        )
        target = tooltip.removeprefix("This ticket has been merged into ").rstrip(".")
        assert target and target != row["reference"], (
            f"The merged-into label should name ANOTHER ticket. Got '{target}'"
        )

    # ==================================================================
    # U16 - customer details on the ticket and on its edit form
    # ==================================================================

    @pytest.mark.p1
    def test_u16_the_ticket_shows_customer_details_and_the_edit_form_can_change_them(self):
        """
        UAT U16. The Overview carries CustomerDetailsCard ("CUSTOMER DETAILS"), and the Edit form
        (TicketEditForm.tsx) carries EditCustomerSection: heading "Customer Details", the
        hand-editable identity fields (edit-customer_name / edit-contact_email /
        edit-contact_phone ...) and the optional "Look up in Data Mart" shortcut. The form is
        opened and left through its Cancel link - never saved.
        """
        self.as_supervisor()
        self.open_an_open_ticket_from(ENQUIRIES)
        assert self.detail.has_section("CUSTOMER DETAILS"), (
            "The ticket Overview should show the Customer Details card"
        )

        offered = self.detail.more_action_labels()
        if "Edit" not in offered:
            pytest.skip(
                f"Edit is not offered on {self.detail.get_reference_number()} ({offered}) - "
                "it is hidden while required fields are missing, which is correct."
            )
        self.detail.open_more_action_menu()
        self.detail.click_menu_item("Edit")
        self.wait_for_url_containing("/edit")
        self.edit_ticket.wait_until_loaded()

        assert self.edit_ticket.has_customer_section(), (
            "The edit form should have a Customer Details section"
        )
        for key in ("customer_name", "contact_email", "contact_phone", "alternate_email"):
            assert self.edit_ticket.is_field_present(key), (
                f"The Customer Details section should let the {key} be edited"
            )
            assert self.edit_ticket.is_field_editable(key), (
                f"edit-{key} should be editable, not read-only"
            )
        assert self.edit_ticket.has_button(TicketEditPage.DATA_MART_LOOKUP), (
            "The Data Mart look-up shortcut should be offered on the edit form"
        )

        self.edit_ticket.cancel()
        self.wait_for_ticket_detail_url()

    # ==================================================================
    # U22 / U24 - the More Action menu by role
    # ==================================================================

    @pytest.mark.p1
    @pytest.mark.escalation
    def test_u22_an_escalated_ticket_offers_no_resolve(self):
        """
        UAT U22. TicketHeaderActions.tsx:77 hides Resolve while `isEscalated` (breach_level > 0),
        and there is no header Change Status button at all.

        MISMATCH: API allows resolving escalated tickets. apps/api/app/stages/state_machine.py
        (module docstring and validate_stage_transition, "breach_level is accepted but no longer
        consulted") deliberately stopped blocking a move on an escalated ticket on 2026-09-07,
        while the web comment at TicketHeaderActions.tsx:24 still says "the API 409s a manual
        move on an escalated ticket". This test pins the UI as built; the two need reconciling.
        """
        self.as_supervisor()
        found = self.find_open_escalated_ticket()
        if found is None:
            pytest.skip(
                "No escalated open ticket with a live (unfrozen) header on either board on UAT."
            )
        reference, offered = found

        assert not self.detail.has_legacy_change_status_button()
        assert RESOLVE not in offered, (
            f"{reference} is escalated, so Resolve must be hidden. More Action offered: {offered}"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_u22_the_cc_initiator_menu_on_their_own_ticket(self):
        """
        UAT U22/U24. For the ASSIGNED CC Initiator on their own in-Tier-1 ticket, More Action
        (TicketHeaderActions.tsx) offers "Assign the Ticket" (the old "Assign to Dept POC" label
        is gone), and Resolve; there is no standalone Change Status button, and NO "Reassign" -
        that item is supervisory (REASSIGN_TICKET: HOD / Manager / CC Supervisor). Whether the
        supervisor and HOD ARE offered Reassign is already a cell of test_15_role_matrix's action
        grid, so it is not repeated here.
        """
        self.login_once(self.get("agentEmail"))
        self.require_ticket_access()
        owned = self.discover_own_in_progress()
        if not owned:
            pytest.skip(
                f"No In Progress ticket on UAT has {self.get('agentEmail')} as its CC Ticket "
                "Initiator (only In Progress ones are opened - a New one would auto-advance)."
            )
        with_assign = [o for o in owned if ASSIGN_THE_TICKET in o[2]]
        if not with_assign:
            pytest.skip(
                "None of the agent's In Progress tickets is still in its Tier-1 window "
                f"(Assign the Ticket is gated on in_tier_1_stage). Menus seen: {owned}"
            )
        reference, url, offered = with_assign[0]
        self.driver.get(url)
        self.detail.wait_until_loaded()

        assert not self.detail.has_legacy_change_status_button(), (
            "No standalone Change Status button any more (requirement 1.24)"
        )
        assert OLD_ASSIGN_LABEL not in offered, (
            f"The item is now called '{ASSIGN_THE_TICKET}', not '{OLD_ASSIGN_LABEL}': {offered}"
        )
        assert RESOLVE in offered, f"The assigned initiator should be offered Resolve: {offered}"
        assert REASSIGN not in offered, (
            f"Reassign is supervisory and must NOT be offered to a CC Initiator ({reference}): "
            f"{offered}"
        )

    @pytest.mark.p2
    @pytest.mark.rbac
    def test_u22_the_cc_initiator_is_offered_reclassify_inside_the_window(self):
        """
        UAT U22. buildReclassifyMenu (reclassifyMenu.ts) shows the one-time Inquiry<->Complaint
        swap - "Reclassify as Complaint" on an enquiry, "Reclassify as Enquiry" on a complaint
        (RECLASSIFY_OPTIONS) - to a RECLASSIFY_TICKET_TYPE holder who may act, has not used the
        swap, and whose ticket is still reclassifiable (can_reclassify_now). Checked on the
        agent's own In Progress tickets; skips when every one has legitimately left the window.
        """
        self.login_once(self.get("agentEmail"))
        self.require_ticket_access()
        owned = self.discover_own_in_progress()
        if not owned:
            pytest.skip(f"No In Progress ticket on UAT is owned by {self.get('agentEmail')}.")
        swaps = ("Reclassify as Complaint", "Reclassify as Enquiry")
        reclassifiable = [o for o in owned if any(label in o[2] for label in swaps)]
        if not reclassifiable:
            pytest.skip(
                "Every In Progress ticket the agent owns has used its swap or left the window, "
                f"where the item is hidden by design. Menus seen: {owned}"
            )
        reference, _, offered = reclassifiable[0]
        prefix = reference[:3]
        expected = "Reclassify as Complaint" if prefix == "INQ" else "Reclassify as Enquiry"
        assert expected in offered, (
            f"{reference} should offer '{expected}' (the swap to the OTHER type): {offered}"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_u22_assign_the_ticket_offers_both_modes_and_a_copy_field(self):
        """
        UAT U22. AssignDeptPocModal.tsx ("Assign the Ticket"): an "Assign to" choice between
        "Assign to Dept POC" and "Assign to Another Dept", plus the "Copy" people picker
        (assign-copy). Opened and CANCELLED - nothing is assigned.
        """
        self.login_once(self.get("agentEmail"))
        self.require_ticket_access()
        owned = [o for o in self.discover_own_in_progress() if ASSIGN_THE_TICKET in o[2]]
        if not owned:
            pytest.skip("No In Progress ticket owned by the agent offers Assign the Ticket.")
        self.driver.get(owned[0][1])
        self.detail.wait_until_loaded()

        self.detail.open_action(ASSIGN_THE_TICKET)
        assert self.detail.get_modal_title() == ASSIGN_THE_TICKET
        assert self.detail.get_assign_modes() == ASSIGN_MODES, (
            f"'Assign to' should offer {ASSIGN_MODES}"
        )
        assert self.detail.exists(self.detail.modal_field("Copy")), (
            "The Copy field (assign-copy) should be on the Assign the Ticket box"
        )
        self.detail.close_modal()
        assert not self.detail.is_modal_open(), "Cancel should close the box without assigning"
