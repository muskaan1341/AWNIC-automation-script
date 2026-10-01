"""
Access control as a grid: every role against every screen, and against the ticket actions.

Each row of the tables below is reported by pytest as its own test.
"Refused" means the "You don't have access" panel OR being redirected away
(the create-ticket form redirects instead of showing the panel).
"/admin/settings" is the System Settings screen (nav label "System Settings"). Its rows check
access only; what the screen shows is checked in test_20_admin_config.py.
"""

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

# The phase mark is added per row below (phase1, or phase2 for the System Settings rows).
pytestmark = [pytest.mark.p0, pytest.mark.regression]


# (account key, role name, screen, may they open it?)
# Grouped by role so each account signs in only once (sign-in is rate-limited).
ROLE_SCREENS = [
    # Head of Department: sees everything but cannot create tickets
    ("hodEmail", "Head of Department", "/tickets/enquiries", True),
    ("hodEmail", "Head of Department", "/tickets/complaints", True),
    ("hodEmail", "Head of Department", "/tickets/discarded", True),
    ("hodEmail", "Head of Department", "/tickets/enquiries/new", False),
    ("hodEmail", "Head of Department", "/reports", True),
    ("hodEmail", "Head of Department", "/audit-trail", True),
    ("hodEmail", "Head of Department", "/history", True),
    ("hodEmail", "Head of Department", "/teams-sla", True),
    # True on purpose: HOD manages users of their own department on this screen.
    ("hodEmail", "Head of Department", "/user-management", True),
    # PR #186: System Settings (/admin/settings) is gated on canConfigure; HOD holds configure_* keys.
    ("hodEmail", "Head of Department", "/admin/settings", True),
    # Complaints Manager: configures and creates
    ("managerEmail", "Complaints Manager", "/tickets/enquiries", True),
    ("managerEmail", "Complaints Manager", "/tickets/complaints", True),
    ("managerEmail", "Complaints Manager", "/tickets/discarded", True),
    ("managerEmail", "Complaints Manager", "/tickets/enquiries/new", True),
    ("managerEmail", "Complaints Manager", "/reports", True),
    ("managerEmail", "Complaints Manager", "/audit-trail", True),
    ("managerEmail", "Complaints Manager", "/history", True),
    ("managerEmail", "Complaints Manager", "/teams-sla", True),
    ("managerEmail", "Complaints Manager", "/user-management", True),
    # PR #186: manager holds configure_sla_priority_tiers etc., so canConfigure lets them in.
    ("managerEmail", "Complaints Manager", "/admin/settings", True),
    # CC Supervisor: Reports yes, Audit Trail no
    ("supervisorEmail", "CC Supervisor", "/tickets/enquiries", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/complaints", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/discarded", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/enquiries/new", True),
    ("supervisorEmail", "CC Supervisor", "/reports", True),
    ("supervisorEmail", "CC Supervisor", "/audit-trail", False),
    ("supervisorEmail", "CC Supervisor", "/history", True),
    ("supervisorEmail", "CC Supervisor", "/teams-sla", False),
    ("supervisorEmail", "CC Supervisor", "/user-management", False),
    # PR #186: cc_supervisor holds no configure_* key, so System Settings is refused.
    ("supervisorEmail", "CC Supervisor", "/admin/settings", False),
    # CC Initiator: no management screens
    ("ccInitiatorEmail", "CC Initiator", "/tickets/enquiries", True),
    ("ccInitiatorEmail", "CC Initiator", "/tickets/complaints", True),
    ("ccInitiatorEmail", "CC Initiator", "/tickets/discarded", True),
    ("ccInitiatorEmail", "CC Initiator", "/tickets/enquiries/new", True),
    ("ccInitiatorEmail", "CC Initiator", "/reports", False),
    ("ccInitiatorEmail", "CC Initiator", "/audit-trail", False),
    ("ccInitiatorEmail", "CC Initiator", "/history", True),
    ("ccInitiatorEmail", "CC Initiator", "/teams-sla", False),
    ("ccInitiatorEmail", "CC Initiator", "/user-management", False),
    ("ccInitiatorEmail", "CC Initiator", "/admin/settings", False),
    # Complaint Handler: complaints only
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/enquiries", False),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/complaints", True),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/discarded", False),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/enquiries/new", True),
    ("complaintHandlerEmail", "Complaint Handler", "/reports", False),
    ("complaintHandlerEmail", "Complaint Handler", "/audit-trail", False),
    ("complaintHandlerEmail", "Complaint Handler", "/history", False),
    ("complaintHandlerEmail", "Complaint Handler", "/teams-sla", False),
    ("complaintHandlerEmail", "Complaint Handler", "/user-management", False),
    ("complaintHandlerEmail", "Complaint Handler", "/admin/settings", False),
    # Compliance Officer: reads tickets, nothing else
    ("complianceEmail", "Compliance Officer", "/tickets/enquiries", True),
    ("complianceEmail", "Compliance Officer", "/tickets/complaints", True),
    ("complianceEmail", "Compliance Officer", "/tickets/discarded", True),
    ("complianceEmail", "Compliance Officer", "/tickets/enquiries/new", False),
    ("complianceEmail", "Compliance Officer", "/reports", False),
    ("complianceEmail", "Compliance Officer", "/audit-trail", False),
    ("complianceEmail", "Compliance Officer", "/history", True),
    ("complianceEmail", "Compliance Officer", "/teams-sla", False),
    ("complianceEmail", "Compliance Officer", "/user-management", False),
    ("complianceEmail", "Compliance Officer", "/admin/settings", False),
    # Department POC: own department's enquiries and complaints
    ("deptPocEmail", "Department POC", "/tickets/enquiries", True),
    ("deptPocEmail", "Department POC", "/tickets/complaints", True),
    ("deptPocEmail", "Department POC", "/tickets/discarded", False),
    ("deptPocEmail", "Department POC", "/tickets/enquiries/new", False),
    ("deptPocEmail", "Department POC", "/reports", False),
    ("deptPocEmail", "Department POC", "/audit-trail", False),
    ("deptPocEmail", "Department POC", "/history", True),
    ("deptPocEmail", "Department POC", "/teams-sla", False),
    ("deptPocEmail", "Department POC", "/user-management", False),
    ("deptPocEmail", "Department POC", "/admin/settings", False),
    # Admin: user administration and (migration 156) the system-config screens, no ticket screens
    ("adminEmail", "Admin", "/tickets/enquiries", False),
    ("adminEmail", "Admin", "/tickets/complaints", False),
    ("adminEmail", "Admin", "/tickets/discarded", False),
    ("adminEmail", "Admin", "/tickets/enquiries/new", False),
    ("adminEmail", "Admin", "/reports", False),
    ("adminEmail", "Admin", "/audit-trail", False),
    ("adminEmail", "Admin", "/history", False),
    ("adminEmail", "Admin", "/teams-sla", True),
    ("adminEmail", "Admin", "/user-management", True),
    # Migration 156: admin now holds configure_sla_priority_tiers / _escalation_contacts_tats /
    # _routing_named_lists (plus configure_business_hours_calendar), so canConfigure lets them in.
    ("adminEmail", "Admin", "/admin/settings", True),
]

# (account key, role name, action in the More Action menu, is it offered?)
ROLE_ACTIONS = [
    ("hodEmail", "Head of Department", "Reassign", True),
    ("hodEmail", "Head of Department", "Manual Escalation", True),
    ("hodEmail", "Head of Department", "Move to Discarded", False),
    ("managerEmail", "Complaints Manager", "Reassign", True),
    ("managerEmail", "Complaints Manager", "Manual Escalation", True),
    ("managerEmail", "Complaints Manager", "Move to Discarded", True),
    ("supervisorEmail", "CC Supervisor", "Reassign", True),
    ("supervisorEmail", "CC Supervisor", "Manual Escalation", True),
    ("supervisorEmail", "CC Supervisor", "Move to Discarded", True),
    ("ccInitiatorEmail", "CC Initiator", "Manual Escalation", False),
    ("ccInitiatorEmail", "CC Initiator", "Reassign", False),
    ("ccInitiatorEmail", "CC Initiator", "Move to Discarded", False),
    ("complianceEmail", "Compliance Officer", "Reassign", False),
    ("complianceEmail", "Compliance Officer", "Manual Escalation", False),
    ("complianceEmail", "Compliance Officer", "Move to Discarded", False),
    # Only "not offered" rows for Reclassify: when it IS offered also depends on the ticket's stage.
    ("managerEmail", "Complaints Manager", "Reclassify as Complaint", False),
    ("supervisorEmail", "CC Supervisor", "Reclassify as Complaint", False),
    ("complianceEmail", "Compliance Officer", "Reclassify as Complaint", False),
]


# Rows for these accounts are marked blocked (no UAT user holds the role yet).
_BLOCKED_ACCOUNT = {
    "complianceEmail": "compliance_officer",
}
# The CC Initiator's screen rows are also part of the sanity run.
_SANITY_ACCOUNT = "ccInitiatorEmail"
# Screens added by Phase 2 (PR #186). Every other row is Phase 1.
_PHASE2_SCREENS = ["/admin/settings"]


def _screen_cases():
    """Turns ROLE_SCREENS into pytest params, with blocked/sanity marks."""
    cases = []
    for account_key, role_name, path, allowed in ROLE_SCREENS:
        marks = []
        if path in _PHASE2_SCREENS:
            marks.append(pytest.mark.phase2)
        else:
            marks.append(pytest.mark.phase1)
        if account_key in _BLOCKED_ACCOUNT:
            marks.append(pytest.mark.blocked(_BLOCKED_ACCOUNT[account_key]))
        if account_key == _SANITY_ACCOUNT:
            marks.append(pytest.mark.sanity)
        cases.append(
            pytest.param(account_key, role_name, path, allowed, marks=marks, id=f"{role_name}:{path}")
        )
    return cases


def _action_cases():
    """Turns ROLE_ACTIONS into pytest params, with blocked marks."""
    cases = []
    for account_key, role_name, action, offered in ROLE_ACTIONS:
        marks = [pytest.mark.phase1]
        if account_key in _BLOCKED_ACCOUNT:
            marks.append(pytest.mark.blocked(_BLOCKED_ACCOUNT[account_key]))
        cases.append(
            pytest.param(account_key, role_name, action, offered, marks=marks, id=f"{role_name}:{action}")
        )
    return cases


class TestRoleMatrix(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("hodEmail"))

    @pytest.mark.roles
    @pytest.mark.parametrize(
        "account_key,role_name,path,should_be_allowed",
        list(_screen_cases()),
    )
    def test_each_role_reaches_exactly_the_screens_its_permissions_allow(
        self, account_key, role_name, path, should_be_allowed
    ):
        self.login_once(self.get(account_key))
        self.open_and_wait(path)

        refused = self.is_access_denied() or path not in self.current_url()
        allowed = not refused

        if should_be_allowed:
            assert allowed, (
                f"{role_name} should be able to open {path}, but was refused. Landed on "
                f"{self.current_url()}. Page says: {self.page_text_snippet()}"
            )
            # "Page not found" is shown at the same URL, so check for it too.
            assert not self.is_page_not_found(), (
                f"{role_name} should be able to open {path}, but it showed 'Page not found'"
            )
        else:
            assert refused, (
                f"{role_name} must NOT be able to open {path}, but got in. Landed on "
                f"{self.current_url()}. Page says: {self.page_text_snippet()}"
            )

    def open_an_open_ticket(self, role_name):
        """Opens a New or In Progress ticket from the Kanban board.

        Resolved/Closed tickets have no action menu at all, so they can't be used here.
        """
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(f"No enquiries visible to {role_name}, so there is no ticket to check.")
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        if self.kanban.card_count(KanbanPage.IN_PROGRESS) > 0:
            column = KanbanPage.IN_PROGRESS
        else:
            column = KanbanPage.NEW
        if self.kanban.card_count(column) == 0:
            pytest.skip(f"No New or In Progress enquiry is visible to {role_name}.")
        self.kanban.open_card(self.kanban.first_card_in(column))
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def describe_menu(self):
        """Returns the More Action menu items as text, for failure messages."""
        if not self.detail.has_more_action_menu():
            return "<no More Action menu at all>"
        self.detail.open_more_action_menu()
        labels = str(self.detail.get_open_menu_labels())
        self.press_escape()
        return labels

    @pytest.mark.roles
    @pytest.mark.parametrize(
        "account_key,role_name,action,should_be_offered",
        list(_action_cases()),
    )
    def test_each_role_is_offered_exactly_the_ticket_actions_its_permissions_allow(
        self, account_key, role_name, action, should_be_offered
    ):
        self.login_once(self.get(account_key))

        self.open_an_open_ticket(role_name)

        if should_be_offered:
            expected = "should be offered"
        else:
            expected = "must NOT be offered"
        offered = self.detail.offers_action(action)
        assert offered == should_be_offered, (
            f"{role_name} {expected} '{action}'. Menu holds: {self.describe_menu()}"
        )
