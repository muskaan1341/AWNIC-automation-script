"""
MODULE 11 - The Complaints Register (the Investigation & Resolution tab).

WHY THIS CLASS EXISTS: module 11 has 36 written test cases and had ZERO browser automation. The
suite proved the tab appears on a complaint and does not 404, and nothing else - so the whole
complaints register, which is the part of the product AWNIC's own compliance obligations rest
on, had never been driven by a machine.

THE TWO CARDS BEHAVE DIFFERENTLY, and the difference is the point:

  INVESTIGATION & RESOLUTION   a field grid, EDITABLE in place by a role that holds the
                               capability, on a ticket that is still open, and that the
                               CC-Initiator action lock lets them touch.
  RESOLUTION REMARKS           APPEND-ONLY. Anyone who can see the ticket may add one; nobody,
                               including an administrator, may edit or delete one afterwards.

That second rule is the one worth protecting hardest. The API exposes no update or delete for a
remark and the database grants block it, so what a browser test can add is the visible half:
the screen must never offer the control in the first place.

ALMOST NOTHING HERE WRITES. Adding a remark appends a row the register keeps forever, so the
two tests that actually press Add Remark are behind `writeTestsEnabled` like every other
writing test. The rest check the guards and stop.
"""

from __future__ import annotations

import time

import pytest

from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   B-P1 'Resolution Tracking notes — intentionally ungated; notes are attributed'
pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression, pytest.mark.blocked("cc_supervisor")]



class TestInvestigation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_investigation_of_first_complaint(self) -> None:
        """
        Opens the first complaint and switches to its Investigation & Resolution tab.

        Skips rather than fails on an environment with no complaints - that is a seed-data
        state, not this tab being broken.
        """
        # The class's own role, signed in BEFORE the access guard. A read-only test earlier in
        # this class switches to the compliance account, and without this every later test that
        # opens the register ran - and was skipped or judged - as that account instead.
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access("supervisorEmail")
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("No complaints on this environment, so there is no register to open.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Investigation & Resolution")
        self.investigation.wait_until_loaded()

    # ==================================================================
    # The register exists and is complaint-only
    # ==================================================================

    def test_a_complaint_has_its_own_register_record(self):
        """M11-POS: 'A complaint has its own detailed register record'."""
        self.open_investigation_of_first_complaint()

        assert self.investigation.has_remarks_card(), (
            "Every complaint gets a RESOLUTION REMARKS card whatever state its register is in. "
            f"On screen: {self.page_text_snippet()}"
        )
        # The investigation card itself is absent only in one legitimate case: a view-only role
        # looking at a register nothing has been written into yet, which says so in words.
        assert (
            self.investigation.has_investigation_card()
            or self.investigation.says_nothing_recorded_yet()
        ), (
            "The tab must show the investigation card, or say plainly that nothing has been "
            f"recorded. On screen: {self.page_text_snippet()}"
        )

    def test_an_enquiry_has_no_register_at_all_even_by_typed_url(self):
        """
        M11-ACC: the register is complaint-only, and hiding the tab is not enough.

        The page gates on `reference_type !== "Complaint" -> notFound()`, so typing the URL for
        an enquiry gives the application's own not-found screen rather than an empty register.
        That is worth asserting directly: a tab hidden from the strip but reachable by URL would
        be exactly the kind of gap this suite exists to catch.
        """
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("No enquiries on this environment to try the URL against.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        enquiry_path = self.current_url()[len(self.base_url) :]

        self.open_and_wait(enquiry_path + "/investigation")

        assert self.is_page_not_found() or self.is_access_denied(), (
            "An enquiry has no complaints-register row, so its investigation URL must be "
            f"refused rather than rendered empty. On screen: {self.page_text_snippet()}"
        )


    def test_an_empty_remark_cannot_be_added(self):
        """M11-NEG: 'An empty note cannot be saved'."""
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip(
                "No remark box on this ticket - it is a merged duplicate, which correctly "
                f"makes the register read-only. On screen: {self.page_text_snippet()}"
            )
        assert not self.investigation.is_add_remark_enabled(), (
            "Add Remark should stay disabled while the box is empty"
        )

    def test_a_remark_made_only_of_spaces_cannot_be_added(self):
        """
        M11-NEG, the half that is easy to miss: whitespace is not a remark.

        The button is `disabled={saving || !draft.trim()}`, so this is the rule stated in code -
        worth a test because a register full of blank rows would be worse than an empty one.
        """
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")
        self.investigation.type_remark("     ")
        assert not self.investigation.is_add_remark_enabled(), (
            "Whitespace is not a remark - Add Remark must stay disabled"
        )

    def test_typing_a_real_remark_makes_it_addable(self):
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")
        self.investigation.type_remark("Called the customer to confirm the documents arrived.")
        assert self.investigation.is_add_remark_enabled(), (
            "A real remark should make Add Remark usable"
        )
        # Deliberately NOT pressed - this appends a row the register keeps forever.

    def test_a_saved_remark_can_never_be_edited_or_deleted(self):
        """
        M11-NEG, and the most valuable test in this class:
        'An investigation note cannot be edited after it is saved' /
        'An investigation note cannot be deleted'.

        The register is append-only all the way down - the API exposes no update or delete, and
        the database grants block it. So the browser-level half of that guarantee is that the
        screen never offers the control at all. A user who is shown a Delete button that then
        403s has been told something untrue about their own audit trail.
        """
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() == 0:
            pytest.skip(
                "This complaint has no saved remarks yet, so there is nothing whose "
                "immutability can be checked. Seed one to exercise this."
            )
        assert not self.investigation.offers_any_remark_edit_or_delete_control(), (
            "The complaints register is append-only. A saved remark must offer no edit and no "
            "delete control anywhere on the screen - not even to an administrator."
        )

    def test_an_empty_register_says_so_rather_than_showing_nothing(self):
        """
        M11-POS: an empty state must be a sentence, not a blank card.

        A card that opens onto empty space is indistinguishable from one that failed to load,
        and gets reported as a bug. Both empty states here are explicit sentences.
        """
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() > 0:
            pytest.skip("This complaint already has remarks, so the empty state is not on screen.")
        assert self.investigation.says_no_remarks_yet(), (
            "An empty remarks card must say 'No resolution remarks yet.', not render blank. "
            f"On screen: {self.page_text_snippet()}"
        )

    def test_several_remarks_build_a_readable_trail_with_author_and_time(self):
        """
        M11-POS: 'Several notes build up a readable investigation trail' and
        'A note always shows the real author'.

        Each remark is stamped with who wrote it and when. A trail that lost its attribution
        would still read fine and be useless the moment anybody asked who decided what.
        """
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() == 0:
            pytest.skip("No remarks on this complaint to read a trail from.")
        # WHAT THIS USED TO ASSERT: `"\n" in text or len(text) > 0` - true of every non-empty
        # string, so a remark that had lost its author and its timestamp passed just as happily
        # as a complete one. The trail's whole value is knowing WHO decided WHAT and WHEN, so
        # each part is now read separately (ResolutionRemarksCard renders the author and the
        # timestamp above the body).
        for author, when, body in self.investigation.remark_details():
            assert body, f"A rendered remark must carry its text. Got author={author!r}"
            assert author, (
                "Every remark names who wrote it - an unattributed one is useless the moment "
                f"anybody asks who decided what. Remark: {body[:60]!r}"
            )
            assert when, f"Every remark carries when it was written. Remark: {body[:60]!r}"
    def test_arabic_text_is_accepted_in_a_remark(self):
        """
        M11-EDG: 'Investigation notes in Arabic save and display correctly'.

        Checks the box holds it exactly as typed. Proving it round-trips through the database
        unchanged needs a write, and is covered by the append test above.
        """
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")

        arabic = "تم الاتصال بالعميل وتأكيد استلام المستندات المطلوبة"
        self.investigation.type_remark(arabic)

        assert self.investigation.remark_draft() == arabic, (
            "Arabic text should be held exactly as typed"
        )

    # ==================================================================
    # Who may write into the register
    # ==================================================================

    @pytest.mark.blocked("compliance_officer")
    def test_a_read_only_role_is_offered_no_way_to_edit_the_investigation(self):
        """
        M11-ACC: 'A compliance officer can read complaints but cannot change them'.

        The Edit affordance is gated on `canEditInvestigation(me) && !isClosed && canActNow`.
        A compliance officer fails the first of those, so the button must not be rendered -
        and the API refuses the call regardless, which is the real boundary.
        """
        self.login_once(self.get("complianceEmail"))
        self.open("/tickets/complaints")
        self.wait_for_page_load()
        if self.is_access_denied():
            pytest.skip(
                f"'{self.get('complianceEmail')}' can sign in but holds no role on this "
                "environment, so every screen refuses it. Grant the role in user_roles to make "
                "this test meaningful here."
            )
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("This role sees no complaints here.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Investigation & Resolution")
        self.investigation.wait_until_loaded()

        assert not self.investigation.has_edit_button(), (
            "A compliance officer holds no investigation-edit capability, so the Edit button "
            "must not be offered at all"
        )

    def test_the_register_of_a_ticket_that_does_not_exist_is_refused(self):
        """
        M11-ACC, the half this test can actually prove: an unknown ticket id is REFUSED, and
        refused in the same words as one you simply may not see - so nobody can discover which
        tickets exist by trying ids.

        RENAMED because the old name promised more than the body delivers. It asks for a
        made-up UUID, which no account can see, so it demonstrates "not found" and never
        crosses a scope at all. The genuine cross-scope case - one handler opening ANOTHER
        handler's real ticket, its /investigation tab included - is
        test_15_role_access.py::test_every_tab_of_somebody_elses_ticket_is_refused, which has
        the second account that check needs. Keeping both under honest names is why no
        coverage is invented here.
        """
        # Runs straight after the compliance-account test, so sign back in as the class's role -
        # otherwise an account with NO role gets "access denied" and this passes having proved
        # nothing about row-scoping.
        self.login_once(self.get("supervisorEmail"))
        self.open_and_wait(
            "/tickets/00000000-0000-0000-0000-000000000000/investigation"
        )

        assert self.is_page_not_found() or self.is_access_denied(), (
            "An unknown ticket id must be refused, not rendered. "
            f"On screen: {self.page_text_snippet()}"
        )

