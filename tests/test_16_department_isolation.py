"""
Department isolation - a Department POC must see only their own department's tickets.

Department POC is the only role scoped to one department, so only dept_poc accounts are used.
The two accounts (users.ISOLATION_PAIR) are in different departments and have signed in before.
"""

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1]


# Two Department POC accounts in different departments.
POC_A, POC_B = users.ISOLATION_PAIR

# The two lists a Department POC can open.
QUEUES = ["/tickets/enquiries", "/tickets/complaints"]


class TestDepartmentIsolation(BaseTest):
    # No class-level sign-in: the tests switch between the two accounts.

    def open_queue_as(self, account, queue):
        """Signs in, opens a list, and returns how many rows are showing."""
        self.login_once(account.email)
        self.open(queue)
        self.list.wait_until_loaded()
        # The "no tickets" message is itself a table row, so check for it first.
        if self.list.is_empty_state_displayed():
            return 0
        return self.list.get_row_count()

    def find_a_visible_ticket(self, account):
        """Returns (reference, detail URL) of any ticket this account can see, or skips."""
        for queue in QUEUES:
            if self.open_queue_as(account, queue) == 0:
                continue
            references = self.list.get_reference_numbers()
            self.list.open_first_row()
            self.wait_for_ticket_detail_url()
            self.detail.wait_until_loaded()
            return references[0], self.current_url()
        pytest.skip(
            f"{account.email} ({account.department}) can see no tickets on this environment."
        )

    # ---------- the list ----------

    @pytest.mark.parametrize("account", [POC_A, POC_B], ids=lambda a: a.department)
    @pytest.mark.parametrize("queue", QUEUES)
    @pytest.mark.phase1
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_a_dept_poc_sees_only_their_own_departments_tickets(self, account, queue):
        """Every row in the list has the POC's own department."""
        if self.open_queue_as(account, queue) == 0:
            pytest.skip(f"{account.email} sees no rows in {queue}, so there is nothing to check.")

        departments = self.list.get_column_values("Department")
        # Make sure the Department column was actually read.
        assert departments, (
            f"{queue} shows {self.list.get_row_count()} rows but no Department values were read"
        )

        # Collect any department that is not the POC's own.
        foreign_set = set()
        for d in departments:
            if d and d != account.department:
                foreign_set.add(d)
        foreign = sorted(foreign_set)

        assert not foreign, (
            f"{account.email} ({account.department!r}) should only see their own department "
            f"in {queue}. Also showing: {foreign}"
        )

    @pytest.mark.parametrize("account", [POC_A, POC_B], ids=lambda a: a.department)
    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_dept_poc_is_not_offered_the_organisation_wide_tab(self, account):
        """A Department POC gets no "Organization Tickets" tab."""
        self.open_queue_as(account, QUEUES[0])

        assert "Organization Tickets" not in self.list.get_tab_labels(), (
            f"{account.email} must not get an organisation-wide tab. "
            f"Tabs: {self.list.get_tab_labels()}"
        )

    # ---------- opening another department's ticket by URL ----------

    @pytest.mark.phase1
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_another_departments_ticket_is_refused_even_by_its_direct_url(self):
        """POC B opening POC A's ticket URL gets "not found"."""
        reference, ticket_url = self.find_a_visible_ticket(POC_A)

        self.login_once(POC_B.email)
        self.driver.get(ticket_url)
        # Wait for the real page content, not just the loading skeleton.
        self.wait_for_page_content()

        # "Not found" (not "forbidden") is expected, so ticket ids can't be probed.
        assert self.is_page_not_found(), (
            f"{POC_B.email} ({POC_B.department}) opened {reference} from "
            f"{POC_A.department}. The page showed: {self.page_text_snippet()}"
        )

    @pytest.mark.env_check
    def test_the_two_accounts_really_are_in_different_departments(self):
        """Test-data check: the two accounts are dept_poc in different departments."""
        assert POC_A.department and POC_B.department, "Both accounts need a department set"
        assert POC_A.department != POC_B.department, (
            f"The two accounts must be in different departments, got {POC_A.department!r} twice"
        )
        assert POC_A.role == POC_B.role == users.DEPT_POC, "Both accounts must be dept_poc"
