"""
R46 / R40 - THE ADMIN AND CONFIGURATION SCREENS (Phase 2).

  /historical       R46 - the Historical Complaints archive (HistoricalArchiveClient.tsx).
                    Viewing: VIEW_HISTORICAL_COMPLAINTS (HOD, Manager, CC Supervisor).
                    Importing: IMPORT_HISTORICAL_COMPLAINTS - head_of_department ONLY
                    (apps/api app/teams/seed_data.py ROLE_PERMISSIONS).
  /teams-sla        R40 - seven tabs (TeamsSlaClient.tsx). Reached by canViewTeamsSla (a
                    configure_* key or org-wide user admin). Inside, each tab's edit controls
                    follow their OWN key: holidays CONFIGURE_BUSINESS_HOURS_CALENDAR (admin +
                    HOD), the daily limit CONFIGURE_CC_INITIATOR_DAILY_CAP and availability
                    MANAGE_CC_INITIATOR_AVAILABILITY (admin + HOD) - so a Manager sees them
                    read-only.
  /role-management  the "Ticket Export Access" matrix (RoleExportAccessMatrix.tsx): editable only
                    with MANAGE_USERS_ORG_WIDE, view-only for an own-department user admin (HOD).

READ-ONLY, with ONE deliberate exception: the R46 test uploads files the API REJECTS WHOLESALE
before anything is stored. apps/api app/complaints/routes.py refuses a non-.xlsx name outright,
and app/complaints/import_historical.py raises ImportFileError for an unreadable workbook or one
missing the required columns - "validate-then-commit, all-or-nothing", no audit row on failure.
Both files were checked offline against _open_sheet/_column_index before this test was written,
and the test asserts the archive row count is unchanged afterwards. Nothing is ever saved,
added, removed or toggled here: controls are asserted present/enabled only.
"""

from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.reports_page import ReportsPage

pytestmark = [pytest.mark.phase2, pytest.mark.regression]

HISTORICAL = "/historical"
TEAMS_SLA = "/teams-sla"

#: The two file-level refusals, verbatim from apps/api (routes.py / import_historical.py).
NOT_XLSX = "Upload the .xlsx import template (not .xlsm/.csv)."
MISSING_COLUMNS = "Template is missing required column(s):"
#: The import template's sheet name (app/complaints/register_columns.py SHEET_TITLE), so the
#: wrong-headers workbook fails on its HEADERS, not on a missing sheet.
REGISTER_SHEET = "Complaints Register"

READ_ONLY_TABS = ["SLA Policy", "Escalation Ladder", "Working Hours", "Classification"]


def write_minimal_xlsx(path, sheet: str, rows: list[list[str]]) -> None:
    """The smallest workbook openpyxl will read: one sheet of inline strings, nothing else."""

    def cell(ref: str, value: str) -> str:
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'

    body = "".join(
        f'<row r="{i + 1}">'
        + "".join(cell(f"{chr(65 + j)}{i + 1}", v) for j, v in enumerate(row))
        + "</row>"
        for i, row in enumerate(rows)
    )
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

    def as_(self, key: str) -> None:
        self.login_once(self.get(key))

    # ==================================================================
    # R46 - the Historical Complaints archive
    # ==================================================================

    def open_archive(self) -> None:
        self.open_and_wait(HISTORICAL)
        self.wait_for_page_content()

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r46_the_head_of_department_sees_the_archive_with_import_and_template(self):
        """
        R46. HOD holds both keys, so HistoricalArchiveClient renders the "Historical Complaints"
        page with "Download template" and "Import" (canImport). Presence only - the template
        button navigates to a download, so it is not pressed.
        """
        self.as_("hodEmail")
        self.open_archive()

        assert not self.is_access_denied(), f"HOD should reach {HISTORICAL}"
        assert self.reports.get_heading() == ReportsPage.HISTORICAL_HEADING
        assert self.reports.has_import_controls(), (
            "The HOD holds IMPORT_HISTORICAL_COMPLAINTS and should see Download template + Import"
        )
        assert self.driver.find_element(*ReportsPage.TEMPLATE_BUTTON).is_enabled()
        self.nav.wait_until_loaded()
        assert self.nav.has_item("Historical Complaints"), "...and the nav item for it"

    @pytest.mark.p1
    @pytest.mark.negative
    @pytest.mark.parametrize(
        "file_name,expected",
        [("not-a-template.txt", NOT_XLSX), ("wrong-headers.xlsx", MISSING_COLUMNS)],
    )
    def test_r46_an_invalid_file_is_refused_and_nothing_is_imported(
        self, tmp_path, file_name, expected
    ):
        """
        R46. An unusable upload is refused with the API's reason shown in the danger Callout and
        "Nothing was imported." beneath it, and the archive is unchanged (row count read before,
        after, and again after a reload). The files are REJECTED by the API before any row is
        parsed (see the module note) - this is the one sanctioned upload.
        """
        self.as_("hodEmail")
        self.open_archive()
        before = self.reports.archive_row_count()

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
        """
        R46. The manager holds VIEW_HISTORICAL_COMPLAINTS but not IMPORT_HISTORICAL_COMPLAINTS:
        the archive renders, the Import/Download template controls do not.
        """
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
        """
        R46. cc_initiator holds neither archive key: no "Historical Complaints" nav item
        (SideNav requires VIEW_HISTORICAL_COMPLAINTS) and the page refuses with AccessDenied.
        """
        self.as_("agentEmail")
        self.open_and_wait("/")
        self.nav.wait_until_loaded()
        assert not self.nav.has_item("Historical Complaints"), (
            "The CC Initiator should not be shown the Historical Complaints nav item"
        )
        self.open_and_wait(HISTORICAL)
        assert self.is_access_denied(), (
            f"A CC Initiator must be refused {HISTORICAL}. Page: {self.page_text_snippet()}"
        )

    # ==================================================================
    # R40 - Teams & SLA
    # ==================================================================

    def open_teams_sla(self) -> None:
        self.open_and_wait(TEAMS_SLA)
        self.wait_for_page_content()
        assert not self.is_access_denied(), f"{self.signed_in_as} should reach {TEAMS_SLA}"

    @pytest.mark.p1
    def test_r40_every_teams_and_sla_tab_renders(self):
        """
        R40. TeamsSlaClient.tsx's seven tabs, in order, each opening its own tabpanel
        (Tabs.tsx: id="tabpanel-<key>") with something in it.
        """
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
        """
        R40. SLA Policy (KPI tiles), Escalation Ladder (a department picker + read-only steps),
        Working Hours (inputs `disabled readOnly`) and Classification (a TreeView) offer nothing
        that edits - even to the HOD, the broadest configure role. A search box is navigation
        and is not counted.
        """
        self.as_("hodEmail")
        self.open_teams_sla()
        panel = self.reports.open_teams_sla_tab(label)
        editable = ReportsPage.enabled_edit_controls(panel)
        assert not editable, f"'{label}' should be read-only, but offers: {editable}"

    @pytest.mark.p1
    @pytest.mark.rbac
    def test_r40_holidays_offers_add_and_remove_to_the_head_of_department(self):
        """
        R40. HolidaysCard.tsx with canEdit (CONFIGURE_BUSINESS_HOURS_CALENDAR - HOD): a Date and a
        Name box and an "Add" button that stays disabled until both are filled, plus a "Remove"
        per holiday. Nothing is typed, added or removed.
        """
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
        """
        R40. CcInitiatorPoolsPanel: the "Daily ticket limit" as a number box with a Save that is
        disabled until changed (CcInitiatorDailyLimit, canEdit = CONFIGURE_CC_INITIATOR_DAILY_CAP)
        and an availability Switch per initiator (CcInitiatorMembersTable, canManageAvailability).
        Nothing is changed or saved.
        """
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
    @pytest.mark.negative
    def test_r40_a_manager_sees_holidays_and_the_daily_limit_read_only(self):
        """
        R40. The manager reaches Teams & SLA (three configure_* keys) but NOT the holiday,
        daily-cap or availability keys (migration 151 / seed_data.py): no Add/Remove on Holidays,
        the daily limit as plain text, no availability switches.
        """
        self.as_("managerEmail")
        self.open_teams_sla()

        holidays = self.reports.open_teams_sla_tab("Holidays")
        assert not ReportsPage.enabled_edit_controls(holidays), (
            f"A manager must not be able to edit holidays: "
            f"{ReportsPage.enabled_edit_controls(holidays)}"
        )
        pools = ReportsPage.pool_controls(self.reports.open_teams_sla_tab("CC Initiator Pools"))
        assert not pools["limit_inputs"], (
            "A manager must see the daily limit as a value, not an input"
        )
        assert not pools["switches"], "A manager must not be offered availability switches"

    # ==================================================================
    # /role-management - the Ticket Export Access matrix
    # ==================================================================

    @pytest.mark.p2
    @pytest.mark.rbac
    def test_r40_the_export_access_matrix_is_view_only_for_the_head_of_department(self):
        """
        role-management/page.tsx: an own-department user admin (HOD, MANAGE_USERS_OWN_DEPT) sees
        the "Ticket Export Access" matrix with the note "(View-only — editing requires an
        administrator.)" and every checkbox disabled.
        """
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
        """
        role-management/page.tsx: only MANAGE_USERS_ORG_WIDE (admin) gets canEdit - the same
        matrix with enabled checkboxes and no view-only note. Nothing is ticked.
        """
        self.as_("adminEmail")
        self.open_and_wait("/role-management")
        boxes = self.admin.export_access_checkboxes()
        assert boxes and any(b.is_enabled() for b in boxes), (
            "The administrator should be able to edit the export-access matrix"
        )
        assert not self.admin.export_access_is_view_only(), (
            "The administrator's matrix is not view-only"
        )
