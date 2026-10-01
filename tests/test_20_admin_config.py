"""
Phase 2 admin and configuration screens (R46 / R40).

/historical - the Historical Complaints archive (only the Head of Department may import).
/teams-sla - the seven Teams & SLA tabs, and who can edit what on them.
/role-management - the Ticket Export Access matrix (editable only by the administrator).
PR #186 editors (TestConfigEditors): Working Hours Edit, the Escalation Ladder add-contact modal,
the Activity Log detail drawer and System Settings > Ticket Numbering. Every modal is closed with
Cancel - nothing is ever saved, added or removed.
"""

import zipfile
from datetime import date
from xml.sax.saxutils import escape

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.admin_page import AdminPage
from awnic_qa.pages.reports_page import ReportsPage

pytestmark = [pytest.mark.phase2, pytest.mark.regression]

HISTORICAL = "/historical"
TEAMS_SLA = "/teams-sla"
SYSTEM_SETTINGS = "/admin/settings"

# The two error messages shown when an import file is refused.
NOT_XLSX = "Upload the .xlsx import template (not .xlsm/.csv)."
MISSING_COLUMNS = "Template is missing required column(s):"
# The template's sheet name, so the wrong-headers file fails on its headers, not the sheet name.
REGISTER_SHEET = "Complaints Register"

# PR #186 made "Escalation Ladder" and "Working Hours" editable for the config tier
# (EscalationLadderSteps.tsx Add/Remove, TeamWorkingHoursCard.tsx Edit), so they moved to EDITOR_TABS.
READ_ONLY_TABS = ["SLA Policy", "Classification"]
EDITOR_TABS = ["Escalation Ladder", "Working Hours"]


def write_minimal_xlsx(path, sheet, rows):
    """Writes a tiny .xlsx file (one sheet of text cells) using only zipfile."""
    # Build the <row> XML for the sheet: row 1 = rows[0], columns A, B, C...
    body = ""
    for i, row in enumerate(rows):
        body += f'<row r="{i + 1}">'
        for j, value in enumerate(row):
            ref = f"{chr(65 + j)}{i + 1}"
            body += f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
        body += "</row>"

    # The fixed XML files every .xlsx needs.
    ns = "http://schemas.openxmlformats.org"
    parts = {
        "[Content_Types].xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="{ns}/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/'
            'sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.worksheet+xml"/></Types>'
        ),
        "_rels/.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/'
            f'relationships"><Relationship Id="rId1" Type="{ns}/officeDocument/2006/'
            'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{ns}/spreadsheetml/2006/'
            f'main" xmlns:r="{ns}/officeDocument/2006/relationships"><sheets><sheet name="'
            f'{escape(sheet)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{ns}/package/2006/'
            f'relationships"><Relationship Id="rId1" Type="{ns}/officeDocument/2006/'
            'relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        ),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{ns}/spreadsheetml/2006/'
            f'main"><sheetData>{body}</sheetData></worksheet>'
        ),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)


class TestAdminConfig(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("hodEmail"))

    def as_(self, key):
        """Signs in as the account stored under this settings key."""
        self.login_once(self.get(key))

    # ---------- R46: the Historical Complaints archive ----------

    def open_archive(self):
        self.open_and_wait(HISTORICAL)
        self.wait_for_page_content()

    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_r46_the_head_of_department_sees_the_archive_with_import_and_template(self):
        """R46: the HOD sees the archive with Download template and Import (nothing is pressed)."""
        self.as_("hodEmail")
        self.open_archive()

        assert not self.is_access_denied(), f"HOD should reach {HISTORICAL}"
        assert self.reports.get_heading() == ReportsPage.HISTORICAL_HEADING
        assert self.reports.has_import_controls(), (
            "The HOD holds IMPORT_HISTORICAL_COMPLAINTS and should see Download template + Import"
        )
        assert self.driver.find_element(*ReportsPage.TEMPLATE_BUTTON).is_enabled()
        self.nav.wait_until_loaded()
        assert self.nav.has_item("Historical Complaints"), "The HOD should see the Historical Complaints nav item"

    @pytest.mark.p1
    @pytest.mark.negative
    @pytest.mark.parametrize(
        "file_name,expected",
        [("not-a-template.txt", NOT_XLSX), ("wrong-headers.xlsx", MISSING_COLUMNS)],
    )
    def test_r46_an_invalid_file_is_refused_and_nothing_is_imported(
        self, tmp_path, file_name, expected
    ):
        """R46: a bad file is refused with a reason and the archive row count does not change."""
        self.as_("hodEmail")
        self.open_archive()
        before = self.reports.archive_row_count()

        # The only upload in this suite: the server refuses these files before storing anything.
        path = tmp_path / file_name
        if file_name.endswith(".xlsx"):
            write_minimal_xlsx(path, REGISTER_SHEET, [["Not A Real Column", "Another"], ["x", "y"]])
        else:
            path.write_text("This is a plain text file, not the import template.\n")
        self.reports.upload_import_file(str(path))

        headline = self.reports.wait_for_import_rejection()
        assert headline.startswith(expected), (
            f"Uploading {file_name} should be refused with '{expected}...'. Callout: '{headline}'"
        )
        assert self.reports.archive_row_count() == before, "A refused file must add no rows"
        self.open_archive()
        assert self.reports.archive_row_count() == before, (
            "After a reload the archive must still hold the same rows - nothing was stored"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r46_a_manager_views_the_archive_but_cannot_import(self):
        """R46: a Manager can view the archive but gets no Import controls."""
        self.as_("managerEmail")
        self.open_archive()

        assert not self.is_access_denied(), "A manager may view the archive"
        assert self.reports.get_heading() == ReportsPage.HISTORICAL_HEADING
        assert not self.reports.has_import_controls(), (
            "Only the Head of Department may import historical complaints"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.negative
    def test_r46_a_cc_initiator_has_no_archive_at_all(self):
        """R46: a CC Initiator gets no archive nav item and is refused the page."""
        self.as_("ccInitiatorEmail")
        self.open_and_wait("/")
        self.nav.wait_until_loaded()
        assert not self.nav.has_item("Historical Complaints"), (
            "The CC Initiator should not be shown the Historical Complaints nav item"
        )
        self.open_and_wait(HISTORICAL)
        assert self.is_access_denied(), (
            f"A CC Initiator must be refused {HISTORICAL}. Page: {self.page_text_snippet()}"
        )

    # ---------- R46: archive search, filter and detail (PR #301) - read only ----------

    def open_non_empty_archive(self):
        self.as_("hodEmail")
        self.open_archive()
        if self.reports.archive_row_count() == 0:
            pytest.skip("The historical archive is empty here, so there is nothing to search.")

    @pytest.mark.p1
    def test_r46_the_filter_drawer_narrows_the_archive_to_the_chosen_value(self):
        """R46: the Filter drawer offers the four filters; applying one Final Status lists only that status."""
        self.open_non_empty_archive()
        before = self.reports.archive_row_count()

        self.reports.open_archive_filter()
        assert self.reports.archive_filter_labels() == list(ReportsPage.ARCHIVE_FILTERS), (
            f"Filter fields: {self.reports.archive_filter_labels()}"
        )
        statuses = self.reports.archive_filter_options("Final Status")
        if not statuses:
            self.reports.close_drawer()
            pytest.skip("No Final Status values are offered for this archive.")
        wanted = statuses[0]
        self.reports.tick_archive_filter("Final Status", wanted)
        self.reports.apply_archive_filter()

        self.wait_for_url_containing("final_status=")
        self.wait.until(lambda d: set(self.reports.archive_cells("Final Status")) <= {wanted})
        shown = self.reports.archive_cells("Final Status")
        assert shown, f"Filtering on a status the drawer offered ('{wanted}') should list rows"
        assert set(shown) == {wanted}, f"Only '{wanted}' rows should be listed, got {sorted(set(shown))}"
        assert self.reports.archive_row_count() <= before, "A filter can never add complaints"

    @pytest.mark.p2
    def test_r46_searching_a_complaint_id_finds_that_complaint(self):
        """R46: searching the first row's Complaint ID (Enter) keeps that complaint in the list."""
        self.open_non_empty_archive()
        wanted = self.reports.archive_cells("Complaint ID")[0]

        self.reports.search_archive(wanted)
        self.wait_for_url_containing("search=")
        self.wait.until(lambda d: wanted in self.reports.archive_cells("Complaint ID"))
        assert wanted in self.reports.archive_cells("Complaint ID"), (
            f"Searching '{wanted}' should list that complaint"
        )

    @pytest.mark.p1
    def test_r46_a_row_opens_its_read_only_detail_page(self):
        """R46: a row opens /historical/<id> with its ID as the title and no Action Plan, Audit or edit."""
        self.open_non_empty_archive()

        complaint_id = self.reports.open_first_archive_row()
        self.wait_for_page_content()
        assert self.reports.get_heading() == complaint_id, (
            f"The detail title should be the Complaint ID '{complaint_id}'"
        )
        tabs = self.reports.historical_detail_tabs()
        assert tabs == ["Overview", "Investigation & Resolution", "Customer & Records", "SLA"], (
            f"An archive complaint shows these tabs only (no Action Plan, no Audit). Got: {tabs}"
        )
        for button in ["Edit", "Resolve", "More Action"]:
            assert not self.reports.has_button(button), f"The archive detail is read-only, but offers {button}"

    # ---------- R40: Teams & SLA ----------

    def open_teams_sla(self):
        self.open_and_wait(TEAMS_SLA)
        self.wait_for_page_content()
        assert not self.is_access_denied(), f"{self.signed_in_as} should reach {TEAMS_SLA}"

    @pytest.mark.p1
    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_r40_every_teams_and_sla_tab_renders(self):
        """R40: all seven Teams & SLA tabs are shown in order and each has content."""
        self.as_("hodEmail")
        self.open_teams_sla()
        assert self.reports.teams_sla_tab_labels() == list(ReportsPage.TEAMS_SLA_TABS), (
            f"Teams & SLA should offer {list(ReportsPage.TEAMS_SLA_TABS)}, "
            f"got {self.reports.teams_sla_tab_labels()}"
        )
        for label in ReportsPage.TEAMS_SLA_TABS:
            panel = self.reports.open_teams_sla_tab(label)
            assert panel.text.strip(), f"The '{label}' tab opened an empty panel"

    @pytest.mark.p1
    @pytest.mark.parametrize("label", READ_ONLY_TABS)
    def test_r40_the_policy_tabs_are_read_only(self, label):
        """R40: the policy tabs have no edit controls, even for the HOD (search boxes do not count)."""
        self.as_("hodEmail")
        self.open_teams_sla()
        panel = self.reports.open_teams_sla_tab(label)
        editable = ReportsPage.enabled_edit_controls(panel)
        assert not editable, f"'{label}' should be read-only, but offers: {editable}"

    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.parametrize("label", EDITOR_TABS)
    def test_r40_the_ladder_and_working_hours_tabs_offer_editing_to_the_hod(self, label):
        """R40: the HOD gets edit controls on these two tabs (nothing is pressed)."""
        # Was part of the read-only check: PR #186 added the editors, gated on
        # configure_escalation_contacts_tats / configure_business_hours_calendar, both held by HOD.
        self.as_("hodEmail")
        self.open_teams_sla()
        panel = self.reports.open_teams_sla_tab(label)
        editable = ReportsPage.enabled_edit_controls(panel)
        assert editable, f"'{label}' should offer the HOD its Edit/Add controls, but offers none"

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r40_holidays_offers_add_and_remove_to_the_head_of_department(self):
        """R40: the HOD gets Date/Name boxes, a disabled Add, and Remove per holiday (nothing is changed)."""
        self.as_("hodEmail")
        self.open_teams_sla()
        panel = self.reports.open_teams_sla_tab("Holidays")
        if "No business-hours calendar configured yet." in panel.text:
            pytest.skip("No business-hours calendar on this environment, so no holiday list.")

        controls = ReportsPage.holiday_controls(panel)
        assert controls["date_inputs"], "No Date box"
        add = controls["add_buttons"]
        assert add and not add[0].is_enabled(), (
            "Add should be offered, and disabled while Date and Name are empty"
        )
        if "No holidays added yet." not in panel.text:
            assert controls["remove_buttons"], (
                "Each listed holiday should carry a Remove button for the HOD"
            )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r40_cc_initiator_pools_offers_the_cap_and_availability_to_the_hod(self):
        """R40: the HOD gets the daily limit box, a disabled Save and availability switches (nothing is changed)."""
        self.as_("hodEmail")
        self.open_teams_sla()
        panel = self.reports.open_teams_sla_tab("CC Initiator Pools")

        assert "Daily ticket limit" in panel.text
        controls = ReportsPage.pool_controls(panel)
        assert controls["limit_inputs"], "The HOD should get an editable daily-limit box"
        save = controls["save_buttons"]
        assert save and not save[0].is_enabled(), "Save should be there, disabled until changed"
        switches = controls["switches"]
        if not switches:
            pytest.skip("No pool member rows are rendered, so there is no availability switch.")
        assert any(s.is_enabled() for s in switches), (
            "The HOD holds MANAGE_CC_INITIATOR_AVAILABILITY and should get usable switches"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r40_a_manager_is_offered_holidays_the_daily_limit_and_availability(self):
        """R40: a Manager gets the holiday, daily-limit and availability controls (nothing is changed)."""
        # Requirement changed: migration 156 gave manager configure_business_hours_calendar,
        # configure_cc_initiator_daily_cap and manage_cc_initiator_availability (was read-only).
        self.as_("managerEmail")
        self.open_teams_sla()

        holidays = self.reports.open_teams_sla_tab("Holidays")
        controls = ReportsPage.holiday_controls(holidays)
        assert controls["date_inputs"], "A manager should now get the holiday Date box"
        add = controls["add_buttons"]
        assert add and not add[0].is_enabled(), (
            "Add should be offered, and disabled while Date and Name are empty"
        )
        pools = ReportsPage.pool_controls(self.reports.open_teams_sla_tab("CC Initiator Pools"))
        assert pools["limit_inputs"], "A manager should now get an editable daily-limit box"
        save = pools["save_buttons"]
        assert save and not save[0].is_enabled(), "Save should be there, disabled until changed"
        if not pools["switches"]:
            pytest.skip("No pool member rows are rendered, so there is no availability switch.")
        assert any(s.is_enabled() for s in pools["switches"]), (
            "A manager holds MANAGE_CC_INITIATOR_AVAILABILITY and should get usable switches"
        )

    # ---------- /role-management: the Ticket Export Access matrix ----------

    @pytest.mark.p2
    @pytest.mark.rbac
    def test_r40_the_export_access_matrix_is_view_only_for_the_head_of_department(self):
        """The HOD sees the Ticket Export Access matrix as view-only, all checkboxes disabled."""
        self.as_("hodEmail")
        self.open_and_wait("/role-management")
        boxes = self.admin.export_access_checkboxes()
        assert boxes, "The export-access matrix should list its checkboxes"
        assert self.admin.export_access_is_view_only(), (
            "The HOD should be told the matrix is view-only"
        )
        assert not any(b.is_enabled() for b in boxes), "Every checkbox should be disabled for HOD"

    @pytest.mark.p2
    @pytest.mark.rbac
    def test_r40_the_export_access_matrix_is_editable_for_the_administrator(self):
        """The administrator can edit the Ticket Export Access matrix (nothing is ticked)."""
        self.as_("adminEmail")
        self.open_and_wait("/role-management")
        boxes = self.admin.export_access_checkboxes()
        assert boxes and any(b.is_enabled() for b in boxes), (
            "The administrator should be able to edit the export-access matrix"
        )
        assert not self.admin.export_access_is_view_only(), (
            "The administrator's matrix is not view-only"
        )


class TestConfigEditors(BaseTest):
    """PR #186 (R40/R41) editors - opened and cancelled only, never saved."""

    # Who holds configure_business_hours_calendar since migration 156.
    BUSINESS_HOURS_EDITORS = ["hodEmail", "managerEmail", "adminEmail"]
    NON_MOTOR_LEVELS = ["Dept POC", "First Escalation", "Final Escalation"]
    MOTOR_LEVELS = ["Dept POC", "First Escalation", "Second Escalation", "Final Escalation"]
    NUMBERING_TYPES = ["Complaint", "Inquiry", "Discarded"]

    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("hodEmail"))

    def open_tab(self, account_key, label):
        """Signs in as this account, opens Teams & SLA and switches to one tab."""
        self.login_once(self.get(account_key))
        self.open_and_wait(TEAMS_SLA)
        self.wait_for_page_content()
        assert not self.is_access_denied(), f"{self.signed_in_as} should reach {TEAMS_SLA}"
        return self.reports.open_teams_sla_tab(label)

    # ---------- Working Hours ----------

    @pytest.mark.p1
    def test_r40_the_working_hours_editor_opens_and_cancel_closes_it_unsaved(self):
        """R40: Edit opens "Edit Working Hours" with the current values; Cancel closes it and nothing changes."""
        self.open_tab("hodEmail", "Working Hours")
        if not self.reports.has_working_hours_edit():
            pytest.skip("No working-hours calendar is linked here, so there is no Edit button.")
        before = self.reports.working_hours_on_card()

        self.reports.open_working_hours_editor()
        assert self.reports.modal_title() == "Edit Working Hours"
        shown = [self.reports.modal_box_value("wh-start"), self.reports.modal_box_value("wh-end")]
        assert shown == before, f"The editor should start from the card's hours {before}, got {shown}"
        assert self.reports.modal_has_button("Save Changes"), "The editor should offer Save Changes"

        self.reports.cancel_open_modal()
        assert not self.reports.is_modal_open(), "Cancel should close the editor"
        assert self.reports.working_hours_on_card() == before, "Cancel must not change the hours"

    # ---------- Escalation Ladder ----------

    @pytest.mark.p1
    @pytest.mark.sanity
    @pytest.mark.smoke
    def test_r40_the_escalation_ladder_shows_the_non_motor_and_motor_chains(self):
        """R18/R19: Non-Motor shows a 3-rung chain, Motor a 4-rung chain."""
        self.open_tab("hodEmail", "Escalation Ladder")
        if "No escalation contacts configured yet." in self.reports.ladder_text():
            pytest.skip("No escalation contacts are configured on this environment.")
        assert self.reports.ladder_level_labels() == self.NON_MOTOR_LEVELS, (
            f"Non-Motor rungs: {self.reports.ladder_level_labels()}"
        )

        self.reports.choose_ladder_scope("Motor")
        self.wait.until(lambda d: "Motor ticket" in self.reports.ladder_text())
        assert self.reports.ladder_level_labels() == self.MOTOR_LEVELS, (
            f"Motor rungs: {self.reports.ladder_level_labels()}"
        )

    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.parametrize("scope", ["Non-Motor", "Motor"])
    def test_r40_the_escalation_ladder_add_contact_modal_opens_and_cancels(self, scope):
        """R40: a rung's Add opens the add-contact modal; Cancel closes it and no contact changes."""
        self.open_tab("hodEmail", "Escalation Ladder")
        self.reports.choose_ladder_scope(scope)
        add_labels = self.reports.ladder_add_labels()
        if not add_labels:
            pytest.skip(f"The {scope} ladder has no contacts here, so no rung offers Add.")
        contacts_before = self.reports.ladder_remove_count()

        # The aria-label is "Add <level> contact for <scope>"; the modal title is "Add <level> — <scope>".
        first = add_labels[0]
        level, _, where = first[len("Add "):].partition(" contact for ")
        self.reports.open_ladder_add_modal(first)
        assert self.reports.modal_title() == f"Add {level} — {where}"
        assert self.reports.modal_has_button("Platform user")
        assert self.reports.modal_has_button("Shared mailbox")
        assert not self.reports.modal_button_is_enabled("Add"), (
            "The modal's Add must stay disabled until a user is chosen"
        )

        self.reports.cancel_open_modal()
        assert not self.reports.is_modal_open(), "Cancel should close the modal"
        assert self.reports.ladder_remove_count() == contacts_before, "Cancel must not change contacts"

    # ---------- System Settings > Ticket Numbering (R41) ----------

    # Verified product defect on UAT 2026-10-01: GET /api/v1/admin/ticket-numbering returns 500
    # for admin and HOD, so /admin/settings shows "Something went wrong".
    @pytest.mark.quarantine("SETTINGS-500")
    @pytest.mark.p1
    def test_r41_system_settings_shows_each_ticket_numbering_series(self):
        """R41: System Settings lists each numbering series with a consistent "Next" preview (Edit is never pressed)."""
        self.login_once(self.get("hodEmail"))
        self.open_and_wait(SYSTEM_SETTINGS)
        self.admin.wait_for_settings()
        assert not self.admin.shows_error_screen(), (
            f"{SYSTEM_SETTINGS} failed to load. Page: {self.page_text_snippet()}"
        )
        assert self.admin.get_heading() == AdminPage.SETTINGS_HEADING

        rows = self.admin.numbering_rows()
        assert rows, "Ticket Numbering should list at least one series"
        this_year = str(date.today().year)
        for row in rows:
            assert row["type"] in self.NUMBERING_TYPES, f"Unknown series: {row}"
            assert row["year"] == this_year, f"Year should be {this_year}: {row}"
            assert row["next"].startswith(f"{row['prefix']}-{row['year']}-"), f"Bad preview: {row}"
            next_number = int(row["next"].split("-")[-1])
            allowed = [int(row["current"]) + 1, int(row["starts"])]
            assert next_number in allowed, (
                f"Next should be Current + 1 (or Starts at, in a new year): {row}"
            )

    # ---------- who gets the Working Hours Edit button ----------

    @pytest.mark.p1
    @pytest.mark.rbac
    @pytest.mark.parametrize("account_key", BUSINESS_HOURS_EDITORS)
    def test_r40_working_hours_edit_is_shown_to_each_role_holding_the_key(self, account_key):
        """R40: HOD, Manager and Admin hold configure_business_hours_calendar, so each sees Edit."""
        panel = self.open_tab(account_key, "Working Hours")
        if "No working hours calendar linked yet." in panel.text:
            pytest.skip("No working-hours calendar is linked here, so there is no Edit button.")
        assert self.reports.has_working_hours_edit(), (
            f"{self.signed_in_as} holds configure_business_hours_calendar and should see Edit"
        )

    # ---------- Activity Log detail drawer ----------

    @pytest.mark.p2
    def test_r40_an_activity_log_row_opens_its_read_only_detail_drawer(self):
        """A click on an Activity Log row opens "Activity detail" for that row, with no edit buttons."""
        self.login_once(self.get("adminEmail"))
        self.open_and_wait("/admin/activity")
        self.admin.wait_until_loaded()
        if not self.admin.has_activity_rows():
            pytest.skip("The activity log is empty here, so there is no row to open.")
        by = self.admin.activity_cell(1, "By")
        action = self.admin.activity_cell(1, "Action")

        self.admin.open_activity_row(1)
        assert self.admin.drawer_title() == AdminPage.DRAWER_TITLE
        labels = self.admin.drawer_labels()
        for expected in ["Action", "When", "User", "Role", "By"]:
            assert expected in labels, f"The drawer is missing '{expected}'. Labels: {labels}"
        assert "Details" in labels or "Setting" in labels, f"No change details shown. Labels: {labels}"
        assert by in self.admin.drawer_text() and action in self.admin.drawer_text(), (
            f"The drawer should describe the clicked row (by '{by}', action '{action}')"
        )
        for button in ["Save", "Edit", "Delete"]:
            assert not self.admin.drawer_has_button(button), f"The drawer is read-only, but offers {button}"

        self.admin.close_drawer()
