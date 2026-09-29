"""
DEPARTMENT ISOLATION - can a Department POC see another department's tickets?

WHY THIS CLASS ONLY EVER USES dept_poc, AND WHY THAT IS NOT A SHORTCUT
Ticket visibility has three mutually-exclusive SCOPE tiers (app/tickets/policy.py), and
exactly ONE of them is departmental:

    view_tickets_org_wide        every row            head_of_department, manager,
                                                      cc_supervisor, cc_initiator,
                                                      compliance_officer
    view_tickets_own_department  Ticket.department == User.department      dept_poc  <-- only
    view_tickets_own_assigned    only rows assigned to you                complaint_handler

So "department A cannot see department B's tickets" is a real rule for dept_poc and for
NOBODY ELSE. Signing in as, say, a CC Initiator of one department and expecting a narrowed
list would be testing something the product does not claim: a CC Initiator is org-wide by
design and correctly sees everything. Writing that test would produce a failure that is not
a bug, which is worse than not writing it.

The pair used here (awnic_qa.users.ISOLATION_PAIR) is two dept_poc holders in different
departments who have BOTH ALREADY SIGNED IN. That last part matters on a shared environment:
the Admin Portal derives "Pending Invitation" from last_login_at being NULL, so signing in as
someone who never has would permanently change what the portal shows about them.

WHAT IS DELIBERATELY *NOT* ASSERTED HERE
That a ticket reaches "the CC Initiator of its department". There is no such thing - the CC
Initiator round-robin pool is one flat, global pool regardless of department
(app/non_motor_sla/model.py RoundRobinPool, confirmed with AWNIC). AWNIC have said they
expect it to be department-specific; until that is settled, asserting either way would be
writing a guess into the suite.
"""

from __future__ import annotations

import pytest

from awnic_qa import users
from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P1 'Dept POC's scope is own-department, not own-assigned (migration 073)'
pytestmark = [pytest.mark.p1, pytest.mark.phase1]


#: The two dept_poc accounts, in different departments.
POC_A, POC_B = users.ISOLATION_PAIR

#: Both queues a dept_poc is allowed to see at all (they hold the enquiry AND complaint type
#: keys). Checking both means a leak in one is not hidden by the other being clean.
QUEUES = ["/tickets/enquiries", "/tickets/complaints"]


class TestDepartmentIsolation(BaseTest):
    # No class-level sign-in: this class moves between accounts on purpose, and login_once
    # keeps that to one round trip per switch rather than one per test (the sign-in endpoint
    # allows 10 a minute).

    def open_queue_as(self, account: users.Account, queue: str) -> int:
        """Signs in, opens a queue, and returns how many rows are showing."""
        self.login_once(account.email)
        self.open(queue)
        self.list.wait_until_loaded()
        # get_row_count() counts <tr>s, and the EMPTY STATE is itself a <tr> holding one
        # <td> that spans the table - so an empty queue reports ONE row, not zero. Asking
        # the empty state directly is the only honest way to tell "no tickets" from "one
        # ticket", and getting this wrong is what made this test pass while reading nothing.
        if self.list.is_empty_state_displayed():
            return 0
        return self.list.get_row_count()

    def find_a_visible_ticket(self, account: users.Account) -> tuple[str, str]:
        """
        The reference and detail URL of any ticket this person can see.

        Skips rather than fails when they can see nothing: an empty queue is a statement
        about this environment's data, not about the product's scoping.
        """
        for queue in QUEUES:
            if self.open_queue_as(account, queue) == 0:
                continue
            references = self.list.get_reference_numbers()
            self.list.open_first_row()
            self.wait_for_ticket_detail_url()
            self.detail.wait_until_loaded()
            return references[0], self.current_url()
        pytest.skip(
            f"{account.email} ({account.department}) can see no tickets in either queue on "
            "this environment, so there is nothing to test isolation with."
        )

    # ==================================================================
    # The scope itself
    # ==================================================================

    @pytest.mark.parametrize("account", [POC_A, POC_B], ids=lambda a: a.department)
    @pytest.mark.parametrize("queue", QUEUES)
    @pytest.mark.phase1
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_a_dept_poc_sees_only_their_own_departments_tickets(self, account, queue):
        """
        The rule itself: every row a Department POC can see belongs to THEIR department.

        This asserts on the Department column of every visible row rather than on a count,
        because a count only proves the list is short - it does not prove the rows are the
        right ones.
        """
        if self.open_queue_as(account, queue) == 0:
            pytest.skip(
                f"{account.email} sees no rows in {queue}, so there is nothing to check. "
                "That is consistent with the scoping, but it does not prove it."
            )

        departments = self.list.get_column_values("Department")
        # Without this, a table that rendered no Department cells at all would give an empty
        # `foreign` and the assertion below would "pass" having checked nothing. The row count
        # above is already non-zero, so an empty read here means the column moved, not that
        # the scoping held.
        assert departments, (
            f"{queue} shows {self.list.get_row_count()} rows but no Department values could "
            "be read - the column has moved or renamed, so this test proved nothing."
        )
        foreign = sorted({d for d in departments if d and d != account.department})

        assert not foreign, (
            f"{account.email} holds view_tickets_own_department for "
            f"{account.department!r}, so every row in {queue} should be that department. "
            f"Also showing: {foreign}"
        )

    @pytest.mark.parametrize("account", [POC_A, POC_B], ids=lambda a: a.department)
    @pytest.mark.phase1
    @pytest.mark.regression
    def test_a_dept_poc_is_not_offered_the_organisation_wide_tab(self, account):
        """
        A restricted scope gets no scope tabs at all - there is only one view to offer.
        Worth pinning: the tabs are CLIENT-SIDE, so an "Organization Tickets" tab appearing
        for a scoped role would be a way to ask for rows the role should never see.
        """
        self.open_queue_as(account, QUEUES[0])

        assert "Organization Tickets" not in self.list.get_tab_labels(), (
            f"{account.email} is scoped to {account.department!r} and must not be offered "
            f"an organisation-wide view. Tabs: {self.list.get_tab_labels()}"
        )

    # ==================================================================
    # The cross-department check - the one that can actually catch a leak
    # ==================================================================

    @pytest.mark.phase1
    @pytest.mark.regression
    @pytest.mark.sanity
    def test_another_departments_ticket_is_refused_even_by_its_direct_url(self):
        """
        THE REAL TEST. Hiding a row from a list is presentation; refusing it when the URL is
        typed in directly is authorisation. A leak here is the difference between the two.

        The expected answer is NOT-FOUND rather than forbidden, and that is deliberate: the
        application answers "Ticket not available" for a ticket that does not exist AND for
        one you may not see, so nobody can discover which tickets exist by probing ids.
        """
        reference, ticket_url = self.find_a_visible_ticket(POC_A)

        self.login_once(POC_B.email)
        self.driver.get(ticket_url)
        # The RESOLVED page, not merely a finished network load: readyState goes "complete"
        # while the route skeleton is still up, and asking "was I refused?" then reads the
        # skeleton rather than the answer.
        self.wait_for_page_content()

        assert self.is_page_not_found(), (
            f"{POC_B.email} ({POC_B.department}) opened {reference}, which belongs to "
            f"{POC_A.department}. A Department POC must not reach another department's "
            f"ticket by its URL. The page showed: {self.page_text_snippet()}"
        )

    @pytest.mark.env_check
    def test_the_two_accounts_really_are_in_different_departments(self):
        """
        A guard on the test data, not on the product.

        Every assertion above is meaningless if these two turn out to share a department -
        the cross-department test would pass by simply never crossing one. Roles come from a
        user_roles export whose role NAMES were inferred, so this pins the one fact the class
        depends on and fails loudly if somebody edits the pair.
        """
        assert POC_A.department and POC_B.department, "Both accounts need a department set"
        assert POC_A.department != POC_B.department, (
            f"The isolation pair must span two departments, got {POC_A.department!r} twice"
        )
        assert POC_A.role == POC_B.role == users.DEPT_POC, (
            "Both must be dept_poc - it is the only department-scoped role in the product"
        )
