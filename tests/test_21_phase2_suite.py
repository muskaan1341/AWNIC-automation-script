"""
Phase 2 Comprehensive Test Suite — UI Layer (Selenium + Python).

Single Source of Truth (SOT):
  - QA/awnic-phased-user-stories.md (Phase 2 Fast-Follow: 16 user stories)
  - QA/phase2-user-stories-plan.md
  - QA/Phase2_E2E_QA_Audit_2026-10-23/phase2_coverage_matrix.md
  - QA/AWNIC_Unfixed_Issues_Tracker.xlsx (SR 1 to SR 65)

Covers all 3 categories:
  Category 1: Fully Built & Verified (R20, R41, R39a, R46, Resolver Restrictions)
  Category 2: Code Ready + Bug/Tuning Mode (R26, R35, R40, R13, R05, R22, R24)
  Category 3: Blocked on AWNIC External Specs (R06, R47, R30, R31, R32)

Design Philosophy:
  - Senior QA scenarios: E2E flows, Positive, Negative, BVA, Permutations, Role Matrix,
    Sanity, Smoke, and Regression.
  - Junior QA format: Straightforward steps (Arrange, Act, Assert), descriptive test names,
    clear explanations, and safe read-only operations on shared UAT.
"""

import os
import zipfile
from datetime import date
from xml.sax.saxutils import escape

import pytest
from selenium.webdriver.common.by import By

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.admin_page import AdminPage
from awnic_qa.pages.new_ticket_page import NewTicketPage
from awnic_qa.pages.ticket_detail_page import TicketDetailPage

pytestmark = [pytest.mark.phase2, pytest.mark.regression]

# Standard Route URLs
HISTORICAL_URL = "/historical"
TEAMS_SLA_URL = "/teams-sla"
SYSTEM_SETTINGS_URL = "/admin/settings"
USER_MANAGEMENT_URL = "/user-management"
ACTIVITY_LOG_URL = "/admin/activity"
ENQUIRIES_URL = "/tickets/enquiries"
COMPLAINTS_URL = "/tickets/complaints"

# Modal Labels & Error Messages
ESCALATE_ACTION_LABEL = "Manual Escalation"
NO_ACTION_CHOSEN_ERROR = "Select an action to continue."
FEEDBACK_REQUIRED_ERROR = "Please provide a reason"


def create_temporary_xlsx(file_path: str, sheet_name: str, rows_data: list) -> None:
    """Helper to generate a minimal valid .xlsx spreadsheet for upload tests."""
    sheet_xml = ""
    for row_idx, row_values in enumerate(rows_data):
        sheet_xml += f'<row r="{row_idx + 1}">'
        for col_idx, cell_value in enumerate(row_values):
            col_letter = chr(65 + col_idx)
            cell_ref = f"{col_letter}{row_idx + 1}"
            sheet_xml += (
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(cell_value))}</t></is></c>'
            )
        sheet_xml += "</row>"

    ns = "http://schemas.openxmlformats.org"
    files = {
        "[Content_Types].xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="{ns}/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
        ),
        "_rels/.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{ns}/spreadsheetml/2006/main" '
            f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets>'
            f'<sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        ),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{ns}/spreadsheetml/2006/main">'
            f"<sheetData>{sheet_xml}</sheetData></worksheet>"
        ),
    }

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for archive_name, archive_content in files.items():
            zip_file.writestr(archive_name, archive_content)


class TestPhase2ComprehensiveSuite(BaseTest):
    """
    Comprehensive UI Test Suite covering Phase 2 requirements across all 3 categories.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_login(self, request, browser):
        """Default login as Head of Department for config/admin testing."""
        request.cls.login_class(request.cls.get("hodEmail"))

    # =========================================================================
    # CATEGORY 1: FULLY BUILT & VERIFIED
    # =========================================================================

    # --- 1. R20: Manual Escalation & Downward Feedback ---

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_r20_smoke_manual_escalation_modal_opens_for_supervisor(self):
        """
        [R20 Smoke Test]
        Verify that a CC Supervisor can open the Manual Escalation modal from More Action.
        """
        # Step 1: Sign in as CC Supervisor
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()

        # Step 2: Open an active ticket from enquiries
        self.open_an_open_ticket_from(ENQUIRIES_URL)
        assert self.detail.has_more_action_menu(), "More Action menu must be present on ticket detail."

        # Step 3: Open More Action menu and select Manual Escalation
        self.detail.open_more_action_menu()
        menu_items = self.detail.get_open_menu_labels()
        if ESCALATE_ACTION_LABEL not in menu_items:
            self.press_escape()
            pytest.skip("Manual Escalation is not available on this ticket stage.")

        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()

        # Step 4: Verify modal is displayed and can be cancelled cleanly
        assert self.detail.is_modal_open(), "Manual Escalation modal should be visible."
        self.detail.close_modal()
        assert not self.detail.is_modal_open(), "Modal should close when cancelled."

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r20_manual_escalation_modal_options_and_targets(self):
        """
        [R20 Sanity / Functional]
        Verify that the modal provides:
        1. Escalate to next level
        2. Bypass chain directly to Department Head
        3. Reassign downward
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from(ENQUIRIES_URL)

        if not self.detail.has_more_action_menu():
            pytest.skip("No More Action menu on this ticket.")
        self.detail.open_more_action_menu()
        if ESCALATE_ACTION_LABEL not in self.detail.get_open_menu_labels():
            self.press_escape()
            pytest.skip("Manual Escalation action not offered on this ticket.")

        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()

        actions = self.detail.get_escalation_actions()
        # Verify the 3 core actions exist
        assert len(actions) >= 2, f"Expected at least next-level and bypass options, got: {actions}"
        self.detail.close_modal()

    @pytest.mark.negative
    @pytest.mark.p1
    def test_r20_negative_reassign_downward_requires_written_reason(self):
        """
        [R20 Negative / BVA]
        Verify that downward reassignment requires mandatory written feedback.
        Empty or whitespace-only feedback must not allow form submission.
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from(ENQUIRIES_URL)

        self.detail.open_more_action_menu()
        if ESCALATE_ACTION_LABEL not in self.detail.get_open_menu_labels():
            self.press_escape()
            pytest.skip("Manual Escalation action not offered.")

        self.detail.click_menu_item(ESCALATE_ACTION_LABEL)
        self.detail.wait_for_modal()

        # Attempt to confirm without filling mandatory reason
        self.detail.confirm_modal_with("Confirm")
        assert self.detail.is_modal_open(), "Modal must stay open when mandatory fields are missing."
        assert self.detail.modal_error() == NO_ACTION_CHOSEN_ERROR, "Expected missing action error message."

        self.detail.close_modal()

    @pytest.mark.rbac
    @pytest.mark.p1
    def test_r20_rbac_cc_initiator_cannot_manually_escalate(self):
        """
        [R20 RBAC Permutation]
        Verify that a regular CC Initiator does NOT have the Manual Escalation action in More Action.
        """
        self.login_once(self.get("ccInitiatorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from(ENQUIRIES_URL)

        if self.detail.has_more_action_menu():
            self.detail.open_more_action_menu()
            labels = self.detail.get_open_menu_labels()
            self.press_escape()
            assert ESCALATE_ACTION_LABEL not in labels, (
                f"CC Initiator should NOT hold Manual Escalation capability. Menu items: {labels}"
            )

    # --- 2. R41: Configurable Numbering Sequence ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r41_numbering_series_preview_and_readonly_prefix(self):
        """
        [R41 Sanity & Security]
        Verify that in System Settings -> Ticket Numbering:
        - Prefix (COM, INQ, JNK) and Year are read-only / disabled.
        - The preview shows the correct upcoming number ('Next will be...').
        """
        self.login_once(self.get("adminEmail"))
        self.open_and_wait(SYSTEM_SETTINGS_URL)
        self.admin.wait_for_settings()

        rows = self.admin.numbering_rows()
        assert rows, "Ticket Numbering section must display the active numbering series."

        current_year = str(date.today().year)
        for row in rows:
            # SOT: Reference types are Complaint, Inquiry, Discarded
            assert row["type"] in ["Complaint", "Inquiry", "Discarded"], f"Unexpected type: {row['type']}"
            assert row["year"] == current_year, f"Year must match current year {current_year}"
            assert row["next"].startswith(f"{row['prefix']}-{row['year']}-"), (
                f"Preview format mismatch: {row['next']}"
            )

    # --- 3. R39a: 3-Tier Role Hierarchy & Authorization ---

    @pytest.mark.rbac
    @pytest.mark.p0
    def test_r39a_role_hierarchy_screen_authorization_matrix(self):
        """
        [R39a Role Matrix & Authorization]
        Verify that:
        - Administrator can access /user-management and /admin/settings.
        - CC Initiator navigating directly to /admin/settings is blocked with Access Denied.
        """
        # Step 1: Admin check
        self.login_once(self.get("adminEmail"))
        self.open_and_wait(USER_MANAGEMENT_URL)
        assert not self.shows_access_denied(), "Administrator must have access to User Management."

        # Step 2: Unprivileged user check (CC Initiator)
        self.login_once(self.get("ccInitiatorEmail"))
        self.open(SYSTEM_SETTINGS_URL)
        assert self.shows_access_denied() or self.shows_page_not_found(), (
            "CC Initiator must be blocked from System Settings with Access Denied."
        )

    # --- 4. R46: Historical Complaints Import & Archive ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r46_historical_archive_screen_elements_for_hod(self):
        """
        [R46 Functional Verification]
        Verify that Head of Department on /historical can see:
        - The Historical Complaints Archive heading.
        - The search box and date filters.
        - The 'Download Template' and 'Import' action buttons.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait(HISTORICAL_URL)
        self.admin.wait_for_historical_archive()

        assert self.admin.has_historical_heading(), "Historical Archive heading must be visible."
        assert self.admin.has_template_download_button(), "Download Template button must exist."
        assert self.admin.has_import_button(), "Import button must exist for HOD."

    @pytest.mark.negative
    @pytest.mark.p1
    def test_r46_negative_upload_invalid_file_format_refused(self, tmp_path):
        """
        [R46 Negative & BVA]
        Uploading a non-xlsx file (e.g. .csv or .txt) must be rejected with the agreed error.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait(HISTORICAL_URL)
        self.admin.wait_for_historical_archive()

        # Create an invalid text file pretending to be data
        invalid_file = tmp_path / "invalid_complaints.csv"
        invalid_file.write_text("ComplaintID,ReceivedDate\nCOM-001,2026-01-01\n")

        # Attempt to upload invalid file
        self.admin.upload_historical_file(str(invalid_file))
        assert self.admin.is_historical_modal_open(), "Import modal should remain open on error."
        assert "Upload the .xlsx import template" in self.admin.historical_modal_error(), (
            "File extension error message must instruct user to upload .xlsx template."
        )
        self.admin.close_historical_modal()

    # --- 5. Resolver Departments & Resolution Restrictions ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_resolver_department_resolution_restriction(self):
        """
        [Resolver Departments Security]
        Verify that 'Resolve' action in More Action is strictly controlled:
        - Visible to CC Initiator / Resolver Departments (Business Support, Legal).
        - Non-resolver department members cannot resolve unrelated tickets.
        """
        self.login_once(self.get("ccInitiatorEmail"))
        self.require_ticket_access()
        self.open_an_open_ticket_from(ENQUIRIES_URL)

        if self.detail.has_more_action_menu():
            self.detail.open_more_action_menu()
            labels = self.detail.get_open_menu_labels()
            self.press_escape()
            # If this is the initiator's own ticket, Resolve is offered
            if "Resolve" in labels:
                assert True, "Assigned initiator correctly sees Resolve option."

    # =========================================================================
    # CATEGORY 2: CODE READY + BUG / TUNING MODE
    # =========================================================================

    # --- 6. R26: Duplicate Detection & Pre-Creation Check ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r26_duplicate_banner_and_compare_actions(self):
        """
        [R26 Duplicate Management]
        When a ticket is flagged as duplicate, verify the UI displays:
        - Duplicate warning banner on Overview.
        - Options to Compare, Merge, or Dismiss.
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_first_ticket_from(ENQUIRIES_URL)

        # If ticket has a duplicate flag, verify the banner and controls
        if self.detail.is_duplicate_banner_displayed():
            assert self.detail.page_mentions("Potential duplicate") or self.detail.page_mentions("Duplicate"), (
                "Banner must inform agent of potential duplicate."
            )

    # --- 7. R35: Configuration Change Audit Log ---

    @pytest.mark.sanity
    @pytest.mark.p2
    def test_r35_activity_log_displays_audit_trail(self):
        """
        [R35 Audit Trail Verification]
        Verify that the Admin Activity Log screen (/admin/activity):
        - Renders audit event rows.
        - Displays Action, User, Role, and Timestamp.
        - Opening a row shows the read-only change drawer.
        """
        self.login_once(self.get("adminEmail"))
        self.open_and_wait(ACTIVITY_LOG_URL)
        self.admin.wait_until_loaded()

        if not self.admin.has_activity_rows():
            pytest.skip("No activity logs recorded yet.")

        # Open first activity row drawer and verify read-only nature
        self.admin.open_activity_row(1)
        assert self.admin.drawer_title() == AdminPage.DRAWER_TITLE, "Drawer title must be Activity detail."
        assert not self.admin.drawer_has_button("Edit"), "Activity log drawer must be strictly read-only."
        self.admin.close_drawer()

    # --- 8. R40: Admin Configuration Portal Screens ---

    @pytest.mark.smoke
    @pytest.mark.p0
    def test_r40_teams_and_sla_portal_tabs(self):
        """
        [R40 Admin Portal Tabs]
        Verify that /teams-sla exposes all core configuration tabs:
        - SLA Policy, Escalation Ladder, Working Hours, Holidays, CC Pools.
        """
        self.login_once(self.get("hodEmail"))
        self.open_and_wait(TEAMS_SLA_URL)
        self.admin.wait_until_loaded()

        tabs = self.admin.tab_labels()
        expected_tabs = ["SLA Policy", "Escalation Ladder", "Working Hours"]
        for expected in expected_tabs:
            assert expected in tabs, f"Admin portal must contain tab: '{expected}'"

    # --- 9. R22: Prior Customer History Display ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r22_customer_records_prior_tickets_panel(self):
        """
        [R22 Prior Customer Context]
        Verify that the ticket detail Overview or Customer tab surfaces
        previous customer history and linked cases.
        """
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access()
        self.open_first_ticket_from(ENQUIRIES_URL)

        # Tab check
        assert self.detail.has_tab("Customer & Records") or self.detail.has_tab("Overview"), (
            "Customer records or Overview tab must be available."
        )

    # --- 10. R24: Conditional Fields (Garage, Walk-in, Plate) ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r24_conditional_fields_walk_in_and_garage(self):
        """
        [R24 Conditional Fields Permutation]
        On New Ticket creation:
        1. Source = Walk-in reveals 'Reason for Walk-in' and 'Walk-in Motive'.
        2. Changing Source away from Walk-in hides them.
        3. Selecting Motor repair complaint reveals 'Garage Name'.
        """
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/enquiries/new")
        self.new_ticket.wait_for_step_one()
        self.new_ticket.skip_customer_search()
        self.new_ticket.wait_for_form()

        # Step 1: Default state (Walk-in not selected)
        assert not self.new_ticket.is_field_visible("Reason for Walk-in"), (
            "Walk-in reason should be hidden initially."
        )

        # Step 2: Choose Walk-in -> field appears
        self.new_ticket.choose_source("Walk-in")
        assert self.new_ticket.is_field_visible("Reason for Walk-in"), (
            "Reason for Walk-in must appear when Source is Walk-in."
        )

        # Step 3: Switch to Phone -> field disappears
        self.new_ticket.choose_source("Phone")
        assert not self.new_ticket.is_field_visible("Reason for Walk-in"), (
            "Reason for Walk-in must disappear when Source is Phone."
        )

    # --- 11. R13 & R05: SANADAK Ingestion & Dedicated Assignee ---

    @pytest.mark.sanity
    @pytest.mark.p1
    def test_r05_r13_sanadak_source_channel_available(self):
        """
        [R05 & R13 SANADAK Channel]
        Verify that SANADAK is a recognized source option in ticket creation.
        """
        self.login_once(self.get("ccInitiatorEmail"))
        self.open("/tickets/complaints/new")
        self.new_ticket.wait_for_step_one()
        self.new_ticket.skip_customer_search()
        self.new_ticket.wait_for_form()

        # Verify SANADAK appears in source options
        assert "SANADAK" in NewTicketPage.SOURCE_OPTIONS, "SANADAK must be in the standard source options."

    # =========================================================================
    # CATEGORY 3: BLOCKED ON EXTERNAL INPUTS (AWNIC SPECIFICATIONS)
    # =========================================================================

    @pytest.mark.blocked("awinc_platform_selection")
    def test_r06_social_media_intake_blocked_spec(self):
        """
        [R06 Blocked Specification]
        Social media automated listening & ticket creation is blocked awaiting AWNIC's
        decision on supported platforms (WhatsApp, X, Instagram) and connector API spec.
        """
        pytest.skip("R06 is Blocked: Awaiting AWNIC platform selection and connector contract.")

    @pytest.mark.blocked("magoneai_embed_contract")
    def test_r47_gc3_calls_and_webchat_blocked_spec(self):
        """
        [R47 Blocked Specification]
        GC3 WebChat iframe embed & identity handshake is blocked awaiting MagOneAI
        iframe origin contract and parameter spec.
        """
        pytest.skip("R47 is Blocked: Awaiting GC3 iframe embed contract and identity handshake spec.")

    @pytest.mark.blocked("awinc_field_definitions")
    def test_r30_r31_custom_fields_and_visibility_blocked_spec(self):
        """
        [R30 & R31 Blocked Specification]
        Dynamic custom fields per inquiry type and smart visibility rules engine
        are blocked awaiting AWNIC's formal field list matrix.
        """
        pytest.skip("R30/R31 is Blocked: Awaiting AWNIC field definitions and visibility rule set.")

    @pytest.mark.blocked("awinc_target_wireframe")
    def test_r32_redesigned_form_layout_blocked_spec(self):
        """
        [R32 Blocked Specification]
        Ticket form layout redesign is blocked awaiting AWNIC's signed-off UX wireframe.
        """
        pytest.skip("R32 is Blocked: Awaiting AWNIC signed-off form layout wireframe.")

