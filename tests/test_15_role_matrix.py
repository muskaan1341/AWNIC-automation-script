"""
ACCESS CONTROL AS A GRID - every role against every screen, and every role against every
contested action on a ticket.

===================================================================================
WHY A GRID AND NOT MORE INDIVIDUAL TESTS
===================================================================================
test_15_role_access.py already checks the cases somebody thought to write down. The trouble
with that approach is the cells nobody thought about: "can a Compliance Officer reach Teams &
SLA?" is only ever tested if a person remembered to ask. A grid asks EVERY question, including
the ones that are obvious right up until the day they are wrong.

Each row below is one cell of the matrix, and pytest reports it as its own result - so a
failure names the exact role and the exact screen rather than "the role tests failed".

===================================================================================
WHERE THE EXPECTED ANSWERS COME FROM
===================================================================================
`ROLE_PERMISSIONS` in apps/api/app/teams/seed_data.py, which is the authority - not from
running the app and writing down what it did, which would only ever prove the app agrees with
itself. The four that are easiest to get backwards, and therefore the most valuable rows here:

  * A Head of Department CANNOT create a ticket. The most senior role does not hold
    CREATE_TICKET_MANUAL, which is counter-intuitive and regresses easily.
  * A CC Supervisor CAN open Reports but CANNOT open the Audit Trail. Two management screens,
    two different grants (the report was widened to the management tier on 2026-08-27; the
    audit trail was not).
  * The platform Admin holds user administration and NOTHING else - no ticket queue at all. It
    is a narrow user-administrator role, not a superuser.
  * A Complaint Handler sees Complaints only. No enquiries, no discarded, no history.

===================================================================================
TWO WAYS A SCREEN SAYS NO, AND BOTH COUNT
===================================================================================
Most refuse with the shared "You don't have access to ..." panel. The create-ticket form does
not - it REDIRECTS back to the list instead, because a form you may not submit is not worth
rendering. So "denied" here means the panel OR being sent somewhere else, and "allowed" means
genuinely landing on the screen asked for.
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest
from awnic_qa.pages.kanban_page import KanbanPage

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P0/C-P1 the full role x screen x action grid
pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]


# ==================================================================
# The screen grid
# ==================================================================
#
# role, screen, may-they-open-it.
#
# ORDERED BY ROLE ON PURPOSE. pytest runs parametrized cases in the order given, and
# `login_once` only signs in when the account actually changes - so grouping by role means
# eight sign-ins for eighty checks. Interleaving them would mean eighty sign-ins and would trip
# the ten-per-minute rate limit within seconds.
ROLE_SCREENS = [
    # --- Head of Department: sees everything, configures everything, creates nothing
    ("hodEmail", "Head of Department", "/tickets/enquiries", True),
    ("hodEmail", "Head of Department", "/tickets/complaints", True),
    ("hodEmail", "Head of Department", "/tickets/discarded", True),
    ("hodEmail", "Head of Department", "/tickets/enquiries/new", False),
    ("hodEmail", "Head of Department", "/reports", True),
    ("hodEmail", "Head of Department", "/audit-trail", True),
    ("hodEmail", "Head of Department", "/history", True),
    ("hodEmail", "Head of Department", "/teams-sla", True),
    # Reachable, and deliberately so. The page gates on canManageUsers - org-wide OR
    # own-department - and HOD holds MANAGE_USERS_OWN_DEPT. What they may actually DO there is
    # scoped by the API to their own department; the screen itself is not the boundary. Do not
    # "tighten" this to False: the page's own comment records the decision, and
    # test_15_role_access.py separately proves HOD is kept out of the org-wide admin screens.
    ("hodEmail", "Head of Department", "/user-management", True),
    # --- Complaints Manager: the only role that both configures AND creates
    ("managerEmail", "Complaints Manager", "/tickets/enquiries", True),
    ("managerEmail", "Complaints Manager", "/tickets/complaints", True),
    ("managerEmail", "Complaints Manager", "/tickets/discarded", True),
    ("managerEmail", "Complaints Manager", "/tickets/enquiries/new", True),
    ("managerEmail", "Complaints Manager", "/reports", True),
    ("managerEmail", "Complaints Manager", "/audit-trail", True),
    ("managerEmail", "Complaints Manager", "/history", True),
    ("managerEmail", "Complaints Manager", "/teams-sla", True),
    # own-dept manager, see the HOD note
    ("managerEmail", "Complaints Manager", "/user-management", True),
    # --- CC Supervisor: Reports YES, Audit Trail NO. The pair worth staring at.
    ("supervisorEmail", "CC Supervisor", "/tickets/enquiries", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/complaints", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/discarded", True),
    ("supervisorEmail", "CC Supervisor", "/tickets/enquiries/new", True),
    ("supervisorEmail", "CC Supervisor", "/reports", True),
    ("supervisorEmail", "CC Supervisor", "/audit-trail", False),
    ("supervisorEmail", "CC Supervisor", "/history", True),
    ("supervisorEmail", "CC Supervisor", "/teams-sla", False),
    ("supervisorEmail", "CC Supervisor", "/user-management", False),
    # --- CC Initiator: the working agent. No management screens at all.
    ("agentEmail", "CC Initiator", "/tickets/enquiries", True),
    ("agentEmail", "CC Initiator", "/tickets/complaints", True),
    ("agentEmail", "CC Initiator", "/tickets/discarded", True),
    ("agentEmail", "CC Initiator", "/tickets/enquiries/new", True),
    ("agentEmail", "CC Initiator", "/reports", False),
    ("agentEmail", "CC Initiator", "/audit-trail", False),
    ("agentEmail", "CC Initiator", "/history", True),
    ("agentEmail", "CC Initiator", "/teams-sla", False),
    ("agentEmail", "CC Initiator", "/user-management", False),
    # --- Complaint Handler: the narrowest queue in the product
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/enquiries", False),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/complaints", True),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/discarded", False),
    ("complaintHandlerEmail", "Complaint Handler", "/tickets/enquiries/new", True),
    ("complaintHandlerEmail", "Complaint Handler", "/reports", False),
    ("complaintHandlerEmail", "Complaint Handler", "/audit-trail", False),
    ("complaintHandlerEmail", "Complaint Handler", "/history", False),
    ("complaintHandlerEmail", "Complaint Handler", "/teams-sla", False),
    ("complaintHandlerEmail", "Complaint Handler", "/user-management", False),
    # --- Compliance Officer: reads tickets org-wide, writes and administers nothing
    ("complianceEmail", "Compliance Officer", "/tickets/enquiries", True),
    ("complianceEmail", "Compliance Officer", "/tickets/complaints", True),
    ("complianceEmail", "Compliance Officer", "/tickets/discarded", True),
    ("complianceEmail", "Compliance Officer", "/tickets/enquiries/new", False),
    ("complianceEmail", "Compliance Officer", "/reports", False),
    ("complianceEmail", "Compliance Officer", "/audit-trail", False),
    ("complianceEmail", "Compliance Officer", "/history", True),
    ("complianceEmail", "Compliance Officer", "/teams-sla", False),
    ("complianceEmail", "Compliance Officer", "/user-management", False),
    # --- Department POC: their own department's two queues, nothing else
    ("deptPocEmail", "Department POC", "/tickets/enquiries", True),
    ("deptPocEmail", "Department POC", "/tickets/complaints", True),
    ("deptPocEmail", "Department POC", "/tickets/discarded", False),
    ("deptPocEmail", "Department POC", "/tickets/enquiries/new", False),
    ("deptPocEmail", "Department POC", "/reports", False),
    ("deptPocEmail", "Department POC", "/audit-trail", False),
    ("deptPocEmail", "Department POC", "/history", True),
    ("deptPocEmail", "Department POC", "/teams-sla", False),
    ("deptPocEmail", "Department POC", "/user-management", False),
    # --- Admin: user administration ONLY. Not a superuser - this is the row that surprises
    #     people, so it is spelled out in full.
    ("adminEmail", "Admin", "/tickets/enquiries", False),
    ("adminEmail", "Admin", "/tickets/complaints", False),
    ("adminEmail", "Admin", "/tickets/discarded", False),
    ("adminEmail", "Admin", "/tickets/enquiries/new", False),
    ("adminEmail", "Admin", "/reports", False),
    ("adminEmail", "Admin", "/audit-trail", False),
    ("adminEmail", "Admin", "/history", False),
    ("adminEmail", "Admin", "/teams-sla", True),
    ("adminEmail", "Admin", "/user-management", True),
]

# ==================================================================
# The action grid
# ==================================================================
#
# role, action, is-it-offered - for the four actions whose grants are DIFFERENT tiers and are
# routinely assumed to be the same one.
#
#   Reassign / Manual Escalation   HOD, Manager, CC Supervisor
#   Reclassify                     HOD and CC Initiator only
#   Move to Discarded              Manager and CC Supervisor only
#
# Read down the columns and no two roles have the same shape. That is the point: holding one of
# these never implies holding another, and a merge from stale seed data that flattens them
# would light up several cells here at once.
#
# Only roles that can see a ticket org-wide appear - a role that cannot open the ticket cannot
# be asked what it is offered on it.
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
    # The reversal worth a dedicated row: the 2026-08-12 amendment took manual escalation AWAY
    # from the CC Initiator. An earlier spec said the opposite, so this is exactly the grant
    # that creeps back on a bad merge.
    ("agentEmail", "CC Initiator", "Manual Escalation", False),
    ("agentEmail", "CC Initiator", "Reassign", False),
    ("agentEmail", "CC Initiator", "Move to Discarded", False),
    # Read-only means read-only: not one of the four.
    ("complianceEmail", "Compliance Officer", "Reassign", False),
    ("complianceEmail", "Compliance Officer", "Manual Escalation", False),
    ("complianceEmail", "Compliance Officer", "Move to Discarded", False),
    # Reclassify, NEGATIVES ONLY - and deliberately so. Whether the swap is offered to a holder
    # also depends on the ticket still being inside its Tier-1 window, which is ticket state
    # this grid does not control. A negative has no such dependency: a role without
    # RECLASSIFY_TICKET_TYPE is never offered it, in the window or out of it. The positive
    # needs a ticket known to be inside that window, which nothing in the suite sets up:
    # test_06_ticket_detail.py and test_10_modal_form_validation.py exercise Reclassify as a
    # Head of Department, but SKIP when it is not offered. (test_08a_ticket_lifecycle.py,
    # which this comment used to point at, no longer exists.)
    ("managerEmail", "Complaints Manager", "Reclassify as Complaint", False),
    ("supervisorEmail", "CC Supervisor", "Reclassify as Complaint", False),
    ("complianceEmail", "Compliance Officer", "Reclassify as Complaint", False),
]


# ==================================================================
# Execution state, per CELL
# ==================================================================
# The grid is the one place where "can this run here?" varies row by row rather than file by
# file, so the blocked marker is attached to the individual cases: the accounts for
# cc_supervisor and compliance_officer hold no role on the deployed environment, so those
# rows skip themselves (require_ticket_access / the denial they would read is not the
# product's answer). Marking them keeps `-m "regression and not blocked"` honest without
# hiding them from the repository. The CC Initiator screen rows double as the Sanity slice:
# one verified account, nine screens, the whole allow/deny contract in one pass.
_BLOCKED_ACCOUNT = {
    "supervisorEmail": "cc_supervisor",
    "complianceEmail": "compliance_officer",
}
_SANITY_ACCOUNT = "agentEmail"


def _screen_cases():
    """ROLE_SCREENS as parametrize cases, carrying their own execution-state marks."""
    for account_key, role_name, path, allowed in ROLE_SCREENS:
        marks = []
        if account_key in _BLOCKED_ACCOUNT:
            marks.append(pytest.mark.blocked(_BLOCKED_ACCOUNT[account_key]))
        if account_key == _SANITY_ACCOUNT:
            marks.append(pytest.mark.sanity)
        yield pytest.param(
            account_key, role_name, path, allowed, marks=marks, id=f"{role_name}:{path}"
        )


def _action_cases():
    """ROLE_ACTIONS as parametrize cases, carrying their own execution-state marks."""
    for account_key, role_name, action, offered in ROLE_ACTIONS:
        marks = []
        if account_key in _BLOCKED_ACCOUNT:
            marks.append(pytest.mark.blocked(_BLOCKED_ACCOUNT[account_key]))
        yield pytest.param(
            account_key, role_name, action, offered, marks=marks, id=f"{role_name}:{action}"
        )


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
        self, account_key: str, role_name: str, path: str, should_be_allowed: bool
    ):
        self.login_once(self.get(account_key))
        self.open_and_wait(path)

        # Two ways to be refused, and both count - see the module comment.
        refused = self.is_access_denied() or path not in self.current_url()
        allowed = not refused

        if should_be_allowed:
            assert allowed, (
                f"{role_name} should be able to open {path}, but was refused. Landed on "
                f"{self.current_url()}. Page says: {self.page_text_snippet()}"
            )
            # Not being refused is not the same as getting in. The app's own "Page not found"
            # screen (app/not-found.tsx - "doesn't exist, or you don't have access to it")
            # renders AT THE REQUESTED URL with no access panel, so without this an allowed
            # cell passed on a screen that had vanished or been hidden behind notFound().
            assert not self.is_page_not_found(), (
                f"{role_name} should be able to open {path}, but it showed 'Page not found'. "
                f"Landed on {self.current_url()}"
            )
        else:
            assert refused, (
                f"{role_name} must NOT be able to open {path}, but got in. Landed on "
                f"{self.current_url()}. Page says: {self.page_text_snippet()}"
            )

    def open_an_open_ticket(self, role_name: str) -> None:
        """
        Opens a ticket that is still OPEN - and this detail matters more than it looks.

        The whole action header, More Action menu included, is REMOVED from a Resolved or Closed
        ticket (`if (isClosed) return null` in TicketHeaderActions). That is correct behaviour -
        there is nothing left to do to a finished ticket - but it means a grid that opens
        whatever happens to be first in the list can end up asking "is a supervisor offered
        Reassign?" on a ticket where NOBODY is offered anything, and read the answer as a
        permissions failure. That is exactly what the first run of this class did, and the
        product was right and the test was wrong.

        The board is the reliable way to avoid it: the New and In Progress columns are open
        tickets by definition (Resolved is its own column, and Closed is off the board
        entirely), so a card taken from either is guaranteed to still have its actions.
        """
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip(
                f"No enquiries visible to {role_name}, so there is no ticket to inspect the "
                "actions on."
            )
        self.list.switch_to_kanban()
        self.kanban.wait_until_loaded()

        column = (
            KanbanPage.IN_PROGRESS
            if self.kanban.card_count(KanbanPage.IN_PROGRESS) > 0
            else KanbanPage.NEW
        )
        if self.kanban.card_count(column) == 0:
            pytest.skip(
                f"No open (New or In Progress) enquiry is visible to {role_name}, so there is "
                "no live ticket to inspect the actions on."
            )
        self.kanban.open_card(self.kanban.first_card_in(column))
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()

    def describe_menu(self) -> str:
        """The whole More Action menu, for a failure message that explains itself."""
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
        self, account_key: str, role_name: str, action: str, should_be_offered: bool
    ):
        self.login_once(self.get(account_key))

        self.open_an_open_ticket(role_name)

        offered = self.detail.offers_action(action)
        assert offered == should_be_offered, (
            f"{role_name}"
            + (" should be offered '" if should_be_offered else " must NOT be offered '")
            + f"{action}'. Menu actually holds: {self.describe_menu()}"
        )
