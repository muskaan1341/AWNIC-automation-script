"""
SCOPE TIERS - does each role actually see the number of rows its permissions say it should?

WHAT THIS ADDS THAT test_15 DOES NOT
test_15_role_access and test_15_role_matrix ask "which SCREENS and ACTIONS is this role
offered". This class asks the different question underneath that: given the role can reach
the ticket list at all, HOW MANY of the rows does it get? A role can be offered every screen
and still be silently over- or under-scoped, and no screen-level test can see it.

The three tiers, from app/tickets/policy.py:

    view_tickets_org_wide        every row of the permitted types
    view_tickets_own_department  only rows whose Ticket.department == User.department
    view_tickets_own_assigned    only rows assigned to the caller

and a role holding NONE of them sees nothing at all - the gates fail closed.

HOW THE ASSERTIONS AVOID BEING VACUOUS
"An org-wide role sees a lot of rows" is not checkable - "a lot" depends on the data. What IS
checkable, and is the actual difference between the tiers, is HOW MANY DISTINCT DEPARTMENTS
appear: org-wide must span more than one, own-department exactly one. That holds whatever the
row count happens to be, and it fails if org-wide is ever accidentally narrowed.

The accounts come from awnic_qa.users, which was built from the user and user_roles exports.
Every account used here has already signed in, so no Admin Portal status changes.
"""

from __future__ import annotations

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P1 'Complaint Handler's scope is Complaints-only + own-assigned'
pytestmark = [pytest.mark.p1, pytest.mark.phase1]


#: Roles whose holders should see the whole organisation. Two accounts, not all five, keeps
#: this class inside the sign-in rate limit (10 a minute) with room to spare.
ORG_WIDE_ACCOUNTS = [users.CC_AGENT, users.HOD_BROKER_MOTOR]

#: Seeded accounts that sign in perfectly well and hold no role at all.
ROLELESS_ACCOUNTS = [
    users.UNGRANTED_HOD,
    users.UNGRANTED_COMPLAINTS_MANAGER,
    users.UNGRANTED_COMPLIANCE,
]

ENQUIRIES = "/tickets/enquiries"


class TestRoleScope(BaseTest):
    def departments_visible_to(self, account: users.Account) -> list[str]:
        """
        Every REAL department appearing in this account's enquiry list.

        A ticket with no department renders its cell as an em dash (TruncatedText), and on
        this product that is common - an unmatched classification is deliberately left without
        one. Counting "—" as a department let both org-wide tests below pass on a list holding
        a single real department plus some blanks, which is exactly the narrowed scope they
        exist to catch. Blanks are therefore left out.
        """
        self.login_once(account.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        if self.list.is_empty_state_displayed():
            return []
        return [
            value
            for value in self.list.get_column_values("Department")
            if value and value != "\u2014"
        ]

    # ==================================================================
    # Fail closed - no role, no rows
    # ==================================================================

    @pytest.mark.parametrize("account", ROLELESS_ACCOUNTS, ids=lambda a: a.email)
    @pytest.mark.regression
    @pytest.mark.blocked("roleless_account")
    def test_an_account_holding_no_role_is_refused_the_ticket_list(self, account):
        """
        A user with no row in user_roles must be refused, not quietly shown an empty list.

        THIS IS ASSERTING CORRECT PRODUCT BEHAVIOUR, and it is worth saying so because these
        four accounts are the reason for a large share of this suite's skips. The gates fail
        CLOSED (app/tickets/policy.py can_view_any_tickets), so "no role" means "refused" -
        an empty list instead would be far worse, because it looks like "no tickets exist".

        The accounts being ungranted is missing seed data on this environment, not a fault.
        What this test pins is that the product handles it safely.
        """
        self.login_once(account.email)
        self.open_and_wait(ENQUIRIES)

        assert self.is_access_denied(), (
            f"{account.email} holds no role, so every ticket screen must refuse it outright "
            f"rather than render an empty list. The page showed: {self.page_text_snippet()}"
        )

    # ==================================================================
    # Org-wide really is org-wide
    # ==================================================================

    @pytest.mark.parametrize("account", ORG_WIDE_ACCOUNTS, ids=lambda a: a.role)
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_an_org_wide_role_sees_more_than_one_department(self, account):
        """
        The positive half of the isolation story (test_16 covers the negative half).

        A cc_initiator and a head_of_department both hold view_tickets_org_wide, so their
        list must span departments. If a future change accidentally applied departmental
        scoping to everybody, test_16 would still pass - every row would still match the
        viewer's own department - and only this test would catch it.
        """
        departments = self.departments_visible_to(account)
        if not departments:
            pytest.skip(
                f"{account.email} sees no enquiry with a department on this environment, so "
                "there is nothing to measure the scope with."
            )

        distinct = sorted(set(departments))
        assert len(distinct) > 1, (
            f"{account.email} holds {account.role} (view_tickets_org_wide) and should see "
            f"more than one department's tickets, but every visible row is {distinct}. "
            "Either the data has only one department, or org-wide scope has been narrowed."
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_an_org_wide_role_sees_a_department_that_is_not_its_own(self):
        """
        The sharpest form of the same check, and the one that cannot pass by accident.

        The HOD used here has their OWN department set, so "sees more than one department"
        could in principle be satisfied by rows that are all theirs plus blanks. Requiring a
        row from a department that is demonstrably NOT theirs is unambiguous.
        """
        account = users.HOD_BROKER_MOTOR
        departments = self.departments_visible_to(account)
        if not departments:
            pytest.skip(
                f"{account.email} sees no enquiry with a department, so there is nothing to "
                "measure."
            )

        foreign = sorted({d for d in departments if d != account.department})
        assert foreign, (
            f"{account.email} is org-wide but every row belongs to their own department "
            f"({account.department!r}). Org-wide scope looks narrowed to a department."
        )

    # ==================================================================
    # Scoped roles do not get the org-wide view offered to them
    # ==================================================================

    @pytest.mark.regression
    def test_a_scoped_role_is_offered_fewer_views_than_an_org_wide_one(self):
        """
        The scope tabs are CLIENT-SIDE (see TicketListPage's own note), so they are not
        authorisation - but offering an "Organization Tickets" tab to a departmental role
        would be an invitation to ask for rows it must not have. An org-wide role gets the
        tabs; a scoped one gets none.

        WHAT THIS REPLACED: `len(scoped) < len(org_wide)`. The org-wide role gets three tabs,
        so a scoped role offered "My Tickets" + "Organization Tickets" - the very tab this
        docstring warns about - still counted as "fewer" and passed. The product rule is
        stated exactly (TicketTypeListClient renders no tab strip when isRestrictedScope,
        docs/rbac.md 8.5), so it is asserted exactly: none for the scoped role, and the
        organisation-wide view present for the org-wide one.
        """
        self.login_once(users.CC_AGENT.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        org_wide_tabs = self.list.get_tab_labels()

        self.login_once(users.DEPT_POC_MEDICAL_OPS.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        scoped_tabs = self.list.get_tab_labels()

        assert "Organization Tickets" in org_wide_tabs, (
            "An org-wide cc_initiator should be offered the Organization Tickets view. "
            f"Tabs: {org_wide_tabs}"
        )
        assert scoped_tabs == [], (
            "A dept_poc has exactly one implicit view, so no scope tabs at all. "
            f"Offered: {scoped_tabs}"
        )

    # ==================================================================
    # A standing note about this environment, kept as a test so it is not forgotten
    # ==================================================================

    @pytest.mark.xfail(
        reason="compliance_officer has no holder in user_roles on UAT (re-checked "
        "2026-09-30; complaint_handler is now held by complaints.officer@awnic.ae), so that "
        "role cannot be exercised by any test. Missing seed data, not a product fault - "
        "grant the role and this turns green.",
        strict=False,
    )
    @pytest.mark.env_check
    def test_every_role_the_product_defines_has_an_account_to_test_it_with(self):
        """
        Not a product assertion - a standing statement about test COVERAGE.

        Two of the eight roles have nobody holding them, which means the suite cannot say
        anything about them at all. That is easy to forget once the skips become familiar,
        so it is recorded here as an expected failure rather than left in a report nobody
        re-reads. It turns green by itself the day the grants are made.
        """
        assert not users.ROLE_HAS_NO_HOLDER, (
            "No account holds these roles, so they are completely untested: "
            f"{sorted(users.ROLE_HAS_NO_HOLDER)}"
        )
