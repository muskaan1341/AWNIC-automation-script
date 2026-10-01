"""
The Investigation & Resolution tab of a complaint.

Resolution remarks can be added but never edited or deleted.
These tests do not add any remark; they only check the screen.
"""

import pytest

from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


class TestInvestigation(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("supervisorEmail"))

    def open_investigation_of_first_complaint(self):
        """Open the first complaint's Investigation & Resolution tab."""
        # Sign in again as the supervisor, because one test in this class switches accounts.
        self.login_once(self.get("supervisorEmail"))
        self.require_ticket_access("supervisorEmail")
        self.open("/tickets/complaints")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("No complaints on this environment.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Investigation & Resolution")
        self.investigation.wait_until_loaded()

    # ---------- the register exists and is complaint-only ----------

    def test_a_complaint_has_its_own_register_record(self):
        self.open_investigation_of_first_complaint()

        assert self.investigation.has_remarks_card(), (
            f"The Resolution Remarks card is missing. On screen: {self.page_text_snippet()}"
        )
        # The investigation card may be missing only if the page says nothing is recorded yet.
        assert (
            self.investigation.has_investigation_card()
            or self.investigation.says_nothing_recorded_yet()
        ), (
            f"Expected the investigation card or a 'nothing recorded' message. "
            f"On screen: {self.page_text_snippet()}"
        )

    def test_an_enquiry_has_no_register_at_all_even_by_typed_url(self):
        """Typing the investigation URL of an enquiry is refused."""
        self.require_ticket_access()
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("No enquiries on this environment.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        enquiry_path = self.current_url()[len(self.base_url) :]

        self.open_and_wait(enquiry_path + "/investigation")

        assert self.is_page_not_found() or self.is_access_denied(), (
            f"An enquiry's investigation URL should be refused. On screen: {self.page_text_snippet()}"
        )

    def test_an_empty_remark_cannot_be_added(self):
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip(
                f"No remark box on this ticket (merged duplicate). On screen: {self.page_text_snippet()}"
            )
        assert not self.investigation.is_add_remark_enabled(), (
            "Add Remark should be disabled while the box is empty"
        )

    def test_a_remark_made_only_of_spaces_cannot_be_added(self):
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")
        self.investigation.type_remark("     ")
        assert not self.investigation.is_add_remark_enabled(), (
            "Add Remark should be disabled for only spaces"
        )

    def test_typing_a_real_remark_makes_it_addable(self):
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")
        self.investigation.type_remark("Called the customer to confirm the documents arrived.")
        assert self.investigation.is_add_remark_enabled(), "Add Remark should be enabled"
        # Not pressed on purpose - a saved remark can never be removed.

    def test_a_saved_remark_can_never_be_edited_or_deleted(self):
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() == 0:
            pytest.skip("This complaint has no saved remarks to check.")
        assert not self.investigation.offers_any_remark_edit_or_delete_control(), (
            "A saved remark should have no edit or delete control"
        )

    def test_an_empty_register_says_so_rather_than_showing_nothing(self):
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() > 0:
            pytest.skip("This complaint already has remarks.")
        assert self.investigation.says_no_remarks_yet(), (
            f"Expected 'No resolution remarks yet.' On screen: {self.page_text_snippet()}"
        )

    def test_several_remarks_build_a_readable_trail_with_author_and_time(self):
        """Every remark shows its author, time and text."""
        self.open_investigation_of_first_complaint()

        if self.investigation.remark_count() == 0:
            pytest.skip("No remarks on this complaint.")
        for author, when, body in self.investigation.remark_details():
            assert body, f"A remark has no text. Author: {author!r}"
            assert author, f"A remark has no author. Remark: {body[:60]!r}"
            assert when, f"A remark has no time. Remark: {body[:60]!r}"

    def test_arabic_text_is_accepted_in_a_remark(self):
        self.open_investigation_of_first_complaint()

        if not self.investigation.is_remark_box_displayed():
            pytest.skip("No remark box on this ticket (merged duplicate).")

        arabic = "تم الاتصال بالعميل وتأكيد استلام المستندات المطلوبة"
        self.investigation.type_remark(arabic)

        assert self.investigation.remark_draft() == arabic, "Arabic text should stay exactly as typed"

    # ---------- who may write into the register ----------

    @pytest.mark.blocked("compliance_officer")
    def test_a_read_only_role_is_offered_no_way_to_edit_the_investigation(self):
        """A compliance officer does not see the Edit button."""
        self.login_once(self.get("complianceEmail"))
        self.open("/tickets/complaints")
        self.wait_for_page_load()
        if self.is_access_denied():
            pytest.skip(f"'{self.get('complianceEmail')}' has no role on this environment.")
        self.list.wait_until_loaded()
        if self.list.get_row_count() == 0:
            pytest.skip("This role sees no complaints here.")
        self.list.open_first_row()
        self.wait_for_ticket_detail_url()
        self.detail.wait_until_loaded()
        self.detail.open_tab("Investigation & Resolution")
        self.investigation.wait_until_loaded()

        assert not self.investigation.has_edit_button(), (
            "A compliance officer should not see the Edit button"
        )

    def test_the_register_of_a_ticket_that_does_not_exist_is_refused(self):
        # Sign back in as the supervisor, because the previous test used another account.
        self.login_once(self.get("supervisorEmail"))
        self.open_and_wait(
            "/tickets/00000000-0000-0000-0000-000000000000/investigation"
        )

        assert self.is_page_not_found() or self.is_access_denied(), (
            f"An unknown ticket id should be refused. On screen: {self.page_text_snippet()}"
        )
