"""
Scope tiers - does each role see the right range of tickets?

Org-wide roles must see more than one department; a role with no role at all is refused.
Accounts come from awnic_qa.users and have all signed in before.
"""

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


# Two org-wide accounts (kept to two because sign-in is rate-limited).
ORG_WIDE_ACCOUNTS = [users.CC_INITIATOR_ACCOUNT, users.HOD_BROKER_MOTOR]

# Accounts that can sign in but hold no role.
ROLELESS_ACCOUNTS = [
    users.UNGRANTED_HOD,
    users.UNGRANTED_COMPLAINTS_MANAGER,
    users.UNGRANTED_COMPLIANCE,
]

ENQUIRIES = "/tickets/enquiries"


class TestRoleScope(BaseTest):
    def departments_visible_to(self, account):
        """Returns the Department value of every enquiry row this account sees.

        Blank departments (shown as a dash) are left out.
        """
        self.login_once(account.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        if self.list.is_empty_state_displayed():
            return []
        departments = []
        for value in self.list.get_column_values("Department"):
            if value and value != "—":
                departments.append(value)
        return departments

    # ---------- no role, no tickets ----------

    @pytest.mark.parametrize("account", ROLELESS_ACCOUNTS, ids=lambda a: a.email)
    @pytest.mark.regression
    @pytest.mark.blocked("roleless_account")
    def test_an_account_holding_no_role_is_refused_the_ticket_list(self, account):
        """A user with no role is refused the ticket list (not shown an empty one)."""
        self.login_once(account.email)
        self.open_and_wait(ENQUIRIES)

        assert self.is_access_denied(), (
            f"{account.email} holds no role, so the ticket list must be refused. "
            f"The page showed: {self.page_text_snippet()}"
        )

    # ---------- org-wide roles ----------

    @pytest.mark.parametrize("account", ORG_WIDE_ACCOUNTS, ids=lambda a: a.role)
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_an_org_wide_role_sees_more_than_one_department(self, account):
        """An org-wide role sees tickets from more than one department."""
        departments = self.departments_visible_to(account)
        if not departments:
            pytest.skip(f"{account.email} sees no enquiry with a department on this environment.")

        distinct = sorted(set(departments))
        assert len(distinct) > 1, (
            f"{account.email} ({account.role}) should see more than one department, "
            f"but every row is {distinct}"
        )

    @pytest.mark.regression
    @pytest.mark.sanity
    def test_an_org_wide_role_sees_a_department_that_is_not_its_own(self):
        """The HOD (org-wide) sees at least one ticket from another department."""
        account = users.HOD_BROKER_MOTOR
        departments = self.departments_visible_to(account)
        if not departments:
            pytest.skip(f"{account.email} sees no enquiry with a department.")

        foreign_set = set()
        for d in departments:
            if d != account.department:
                foreign_set.add(d)
        foreign = sorted(foreign_set)
        assert foreign, (
            f"{account.email} is org-wide but every row is their own department "
            f"({account.department!r})"
        )

    # ---------- scope tabs ----------

    @pytest.mark.regression
    def test_a_scoped_role_is_offered_fewer_views_than_an_org_wide_one(self):
        """The org-wide CC Initiator gets "Organization Tickets"; a Department POC gets no tabs."""
        self.login_once(users.CC_INITIATOR_ACCOUNT.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        org_wide_tabs = self.list.get_tab_labels()

        self.login_once(users.DEPT_POC_MEDICAL_OPS.email)
        self.open(ENQUIRIES)
        self.list.wait_until_loaded()
        scoped_tabs = self.list.get_tab_labels()

        assert "Organization Tickets" in org_wide_tabs, (
            f"The CC Initiator should get the Organization Tickets tab. Tabs: {org_wide_tabs}"
        )
        assert scoped_tabs == [], f"A dept_poc should get no tabs. Offered: {scoped_tabs}"

    # ---------- test-data coverage note ----------

    @pytest.mark.xfail(
        reason="compliance_officer has no holder in user_roles on UAT (re-checked "
        "2026-09-30; complaint_handler is now held by complaints.officer@awnic.ae), so that "
        "role cannot be exercised by any test. Missing seed data, not a product fault - "
        "grant the role and this turns green.",
        strict=False,
    )
    @pytest.mark.env_check
    def test_every_role_the_product_defines_has_an_account_to_test_it_with(self):
        """Test-data check: every role has at least one account holding it."""
        assert not users.ROLE_HAS_NO_HOLDER, (
            f"No account holds these roles: {sorted(users.ROLE_HAS_NO_HOLDER)}"
        )
