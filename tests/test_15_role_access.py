"""
ACCESS CONTROL - who is allowed to see and do what.

THIS IS THE MOST VALUABLE CLASS IN THE SUITE, because getting it wrong means somebody reads a
customer's complaint they had no business reading. Everything else is a bug; this is a breach.

THE MODEL IN ONE PARAGRAPH. Visibility has TWO dimensions that both have to be satisfied. First
TYPE: which kinds of ticket may you see - enquiries, complaints, discarded? Second SCOPE: how
many of that kind - the whole organisation, only your department, or only the ones assigned to
you personally? A role needs at least one type AND one scope before it can see a single ticket.

THE RULE THESE TESTS EXIST TO PROVE: hiding a button is NOT protection. Every test that checks
a hidden menu item is paired with one that types the URL in directly, because that is what a
real attacker does.

The eight seeded roles:
  admin              user administration only - NO ticket queues at all
  head_of_department every queue, own-department user admin, but CANNOT create tickets
  manager            organisation-wide, can discard and configure
  cc_supervisor      all three queues, plus discard / reassign / escalate
  cc_initiator       all three queues, can create tickets
  complaint_handler  complaints ONLY, and only the ones assigned to them
  dept_poc           enquiries + complaints, but only their OWN department
  compliance_officer read-only oversight - audit trail yes, editing no
"""

from __future__ import annotations

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   C-P0 'Cross-scope ticket access returns 404, not data' + 'No-role users get 403 everywhere'
pytestmark = [pytest.mark.p0, pytest.mark.phase1, pytest.mark.regression]



class TestRoleAccess(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def start_from_the_agent(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    # ==================================================================
    # Complaint handler - complaints only, and only their own
    # ==================================================================

    def test_complaint_handler_sees_only_complaints_assigned_to_them(self):
        """
        Every complaint a Complaint Handler can see is assigned to THEM.

        The rule (app/tickets/repository.py _visibility_clauses): a view_tickets_own_assigned
        role is filtered to `assigned_poc_email == the caller`. So each row is checked the
        same way - by opening it and reading its Department POC's email off the ticket's own
        Smart Routing card.

        WHAT THIS REPLACED: "the handler's row count is below the agent's row count". Both
        numbers were rows ON SCREEN, and the list shows ten a page - with more than ten
        complaints on each side that compared 10 with 10, and it never looked at WHOSE the
        rows were. A handler shown ten of somebody else's complaints would have passed
        whenever the agent could see more.

        The count survives only as a sanity bound, using the REPORTED totals: an own-assigned
        scope can never report more complaints than an organisation-wide one. It is not
        asserted to be strictly fewer - that would be a claim about this environment's data
        (a handler holding every complaint is legitimate), not about the product.
        """
        handler = self.get("complaintHandlerEmail")
        self.login_once(handler)
        self.require_ticket_access("complaintHandlerEmail")

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.is_empty_state_displayed():
            pytest.skip(
                f"{handler} has no complaints assigned, so there are no rows whose owner can "
                "be checked. That is consistent with the scope but does not prove it."
            )
        their_total = self.list.get_reported_result_count()
        references = self.list.get_reference_numbers()

        for row, reference in enumerate(references):
            if row:
                self.open("/tickets/complaints")
                self.list.wait_until_loaded()
            self.list.open_row(row)
            self.wait_for_ticket_detail_url()
            self.detail.wait_until_loaded()

            assert self.detail.get_reference_number() == reference, (
                f"Row {row} was {reference} but {self.detail.get_reference_number()} opened"
            )
            assert self.detail.department_poc_email() == handler, (
                f"{handler} can see {reference}, whose Department POC is "
                f"'{self.detail.department_poc_email()}'. An own-assigned role must see only "
                "complaints assigned to them."
            )

        self.login_once(self.get("agentEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        organisation_wide = self.list.get_reported_result_count()

        assert their_total <= organisation_wide, (
            f"An own-assigned role reports {their_total} complaints but an organisation-wide "
            f"role reports only {organisation_wide} - the narrower scope cannot hold more."
        )

    def test_complaint_handler_gets_no_scope_tabs(self):
        """
        A role whose scope is already narrow gets NO tab strip, because there is nothing to
        switch between - every ticket they can see is already "theirs".
        """
        self.login_once(self.get("complaintHandlerEmail"))
        self.require_ticket_access("complaintHandlerEmail")

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

        assert not self.list.has_tab_strip(), (
            "A restricted-scope role has one implicit view, so no tabs. "
            f"Tabs found: {self.list.get_tab_labels()}"
        )



    # ==================================================================
    # Head of department - sees everything, creates nothing
    # ==================================================================

    def test_head_of_department_sees_the_administration_entries(self):
        self.login_once(self.get("hodEmail"))

        self.open("/")
        self.nav.wait_until_loaded()

        assert self.nav.has_item("Access Management"), (
            "A Head of Department manages users inside their own department"
        )
        assert self.nav.has_item("Audit Trail"), (
            "A Head of Department can read configuration changes"
        )
        assert self.nav.has_tickets_group(), (
            "A configuring role gets the collapsible 'Tickets' group, not flat links"
        )

    @pytest.mark.sanity
    def test_head_of_department_does_not_get_the_organisation_wide_admin_screens(self):
        """
        The two doors to user administration are deliberately different. A Head of Department
        gets "Access Management" (their own department); only a platform administrator gets the
        organisation-wide "User Management" and "Role Management".
        """
        self.login_once(self.get("hodEmail"))

        self.open("/")
        self.nav.wait_until_loaded()

        assert not self.nav.has_item("User Management"), (
            "Organisation-wide user management belongs to the platform administrator"
        )
        assert not self.nav.has_item("Role Management"), (
            "Organisation-wide role management belongs to the platform administrator"
        )

    # ==================================================================
    # Platform administrator - people, not tickets
    # ==================================================================

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_admin_lands_on_the_user_admin_dashboard_instead_of_the_ticket_dashboard(self):
        self.login_once(self.get("adminEmail"))

        # Signing in always lands on "/" first; the server then forwards an administrator on to
        # "/admin". Wait for that SECOND hop rather than reading the URL too early.
        self.wait_for_url("/admin")

        assert self.current_url() == self.base_url + "/admin", (
            "An admin holds no ticket permission, so / should forward to /admin"
        )

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_admin_sees_user_statistics_and_no_ticket_queues(self):
        self.login_once(self.get("adminEmail"))

        self.open_and_wait("/admin")
        self.nav.wait_until_loaded()

        assert self.dashboard.is_kpi_displayed("Total Users"), (
            "The admin dashboard should count users"
        )
        assert self.nav.has_item("User Management"), "An admin manages users"
        assert self.nav.has_item("Role Management"), "An admin manages roles"
        assert self.nav.has_no_ticket_queues(), (
            f"An admin must be offered no ticket queue at all. Menu: {self.nav.all_item_labels()}"
        )

    @pytest.mark.blocked("compliance_officer")
    def test_compliance_officer_can_read_tickets_across_the_organisation(self):
        """What the role CAN do: read tickets across the whole organisation."""
        self.login_once(self.get("complianceEmail"))
        self.require_ticket_access("complianceEmail")

        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

        assert not self.is_access_denied(), (
            "A compliance officer holds organisation-wide ticket visibility"
        )
        assert self.list.get_row_count() > 0, (
            "They should see the organisation's complaints, not an empty list"
        )

    @pytest.mark.sanity
    def test_an_agent_is_refused_every_screen_their_role_does_not_cover(self):
        """
        One loop instead of a dozen near-identical tests: for each restricted screen, sign in as
        a role that should NOT have it and confirm the screen itself refuses - not just that the
        menu hides it.
        """
        self.login_once(self.get("agentEmail"))

        forbidden = [
            "/user-management",
            "/role-management",
            "/audit-trail",
            "/access-management",
            "/admin/activity",
        ]

        for path in forbidden:
            self.open_and_wait(path)
            assert (
                self.is_access_denied()
                or self.is_page_not_found()
                or path not in self.current_url()
            ), (
                f"A Customer Care agent reached {path}, which their role does not cover. "
                f"Actual URL: {self.current_url()} — page says: {self.page_text_snippet()}"
            )

    def test_every_tab_of_somebody_elses_ticket_is_refused(self):
        """
        Every sub-page of a ticket is protected separately, not just the ticket's main page. A
        missing check on one tab is exactly how data leaks in practice.
        """
        owned_by_them = self.reference("COM", self.get("complaintHandlerTicketTail"))

        # Step 1: as an account that can see everything, find a complaint that is NOT the one
        # belonging to the complaint handler.
        self.login_once(self.get("agentEmail"))
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()

        all_complaints = self.list.get_reference_numbers()
        row_of_someone_elses = next(
            (row for row, ref in enumerate(all_complaints) if ref != owned_by_them), -1
        )
        if row_of_someone_elses < 0:
            pytest.skip(
                "Only one complaint is seeded, so there is no 'somebody else's' ticket to try."
            )

        self.list.search(all_complaints[row_of_someone_elses])
        self.list.wait_for_row_count(1)
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        someone_elses_ticket = self.current_url()[len(self.base_url) :]

        # Step 2: as the complaint handler, every tab of it must be refused - and refused in a
        # way that does not even confirm the ticket exists.
        self.login_once(self.get("complaintHandlerEmail"))
        self.require_ticket_access("complaintHandlerEmail")
        for tab in ["", "/audit", "/sla", "/customer-records", "/investigation"]:
            # open_and_wait, NOT open - this is precisely the case BaseTest warns about. A plain
            # open() returns as soon as the browser STARTS loading, so asking "was I refused?"
            # on the next line reads a page that has not arrived yet. Here that produced a false
            # failure; on a differently-worded screen it would produce a false PASS on an
            # access-control test, which is worse.
            self.open_and_wait(someone_elses_ticket + tab)
            assert self.is_page_not_found() or self.is_access_denied(), (
                f"The '{tab}' tab of a ticket outside this user's scope must be refused, and "
                f"must hide that the ticket exists at all. Actual URL: {self.current_url()}"
            )
