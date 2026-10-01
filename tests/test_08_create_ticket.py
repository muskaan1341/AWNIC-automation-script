"""
Manual ticket creation tests (walk-in or phone call).

Most tests check whether the "Create ticket" button is enabled.
No test presses it, so nothing is written to the database.

TestCcInitiatorPicker (Phase 2) reads the Assignment card's Channel -> CC Initiator picker
against the Teams & SLA > CC Initiator Pools roster. It only opens the dropdowns.
"""

import pytest

from awnic_qa import customers
from awnic_qa.base_test import BaseTest
from awnic_qa.pages.new_ticket_page import NewTicketPage

pytestmark = [pytest.mark.regression]


@pytest.mark.p0
@pytest.mark.phase1
class TestCreateTicket(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(request.cls.get("agentEmail"))

    def open_enquiry_form(self):
        """Opens the create screen and skips the customer search."""
        self.open("/tickets/enquiries/new")
        self.new_ticket.continue_to_form()

    def open_complaint_form(self):
        self.open("/tickets/complaints/new")
        self.new_ticket.continue_to_form()

    # ---------- getting to the form ----------

    @pytest.mark.smoke
    @pytest.mark.sanity
    def test_create_button_opens_the_new_ticket_screen(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        self.list.click_create_button("Create Enquiry")

        self.wait_for_url_containing("/tickets/enquiries/new")
        assert self.new_ticket.is_customer_search_displayed(), (
            "Step 1 should offer a customer search box before the form"
        )

    def test_the_form_can_be_reached_without_picking_a_customer(self):
        self.open_enquiry_form()

        # Not every walk-in is an existing customer, so skipping the search must be allowed.
        assert self.new_ticket.is_field_displayed("Source"), (
            "Skipping the customer search should still open the form"
        )

    # ---------- required fields ----------

    @pytest.mark.sanity
    def test_submit_is_disabled_on_an_empty_form(self):
        self.open_enquiry_form()

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "'Create ticket' must stay disabled until the required fields are filled in"
        )

    @pytest.mark.sanity
    def test_submit_stays_disabled_until_every_required_field_is_filled(self):
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Phone")
        assert not self.new_ticket.is_create_ticket_enabled(), "Source alone is not enough"

        # Department only offers values once a Type has been picked - it is a cascade.
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        assert not self.new_ticket.is_create_ticket_enabled(), "Priority is still missing"

        self.new_ticket.select_first_option("Priority")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A way to contact the customer back is still missing"
        )

        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With every required field filled in, the form should be submittable"
        )

    def test_subject_and_description_are_not_required(self):
        """Subject and Description are optional."""
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()

        assert self.new_ticket.is_create_ticket_enabled(), (
            "A ticket should be submittable without a subject or a description"
        )

    # ---------- the channel (Source) ----------

    def test_every_manual_channel_can_be_chosen(self):
        self.open_enquiry_form()

        assert self.new_ticket.get_dropdown_options("Source") == NewTicketPage.SOURCE_OPTIONS, (
            "The Source list should offer every channel an agent can log by hand"
        )

    def test_choosing_walk_in_reveals_the_reason_field(self):
        self.open_enquiry_form()

        assert not self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "The reason field should be hidden until Walk-in is chosen"
        )

        self.new_ticket.select_option("Source", "Walk-in")
        assert self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "Choosing Walk-in should reveal the 'Reason for Walk-in' field"
        )

    def test_choosing_phone_does_not_ask_for_a_walk_in_reason(self):
        self.open_enquiry_form()
        self.new_ticket.select_option("Source", "Phone")

        assert not self.new_ticket.is_field_displayed("Reason for Walk-in"), (
            "A phone enquiry should not ask why the customer walked in"
        )

    def test_walk_in_without_a_reason_cannot_be_submitted(self):
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Walk-in")
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A walk-in ticket must explain why the customer came in person"
        )

        self.new_ticket.fill_textarea(
            "Reason for Walk-in", "Customer came to the branch about a motor claim."
        )
        assert self.new_ticket.is_create_ticket_enabled(), (
            "Once the reason is given, the form should be submittable"
        )

    # ---------- complaints ask for more ----------

    @pytest.mark.sanity
    def test_a_complaint_cannot_be_saved_without_its_category(self):
        self.open_complaint_form()

        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")
        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A complaint must be categorised before it can be saved"
        )

        # Complaint Category only has values once a Product Line is chosen.
        if not self.new_ticket.get_dropdown_options("Product Line"):
            pytest.skip("No Product Line values on this environment - seed the complaint taxonomy.")
        self.new_ticket.select_first_option("Product Line")
        self.new_ticket.select_first_option("Complaint Category")
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With a category chosen, the complaint should be submittable"
        )

    def test_with_no_customer_chosen_the_alternate_contacts_become_compulsory(self):
        """Without a customer, Alternate Email and Alternate Mobile are both required."""
        self.open_enquiry_form()

        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.select_first_option("Type")
        self.new_ticket.select_first_option("Department")
        self.new_ticket.select_first_option("Priority")

        assert not self.new_ticket.is_create_ticket_enabled(), (
            "Without a customer, a way to contact them back is required"
        )

        self.new_ticket.fill("Alternate Email", customers.QA_CONTACT_EMAIL)
        assert not self.new_ticket.is_create_ticket_enabled(), "A phone number is needed too"

        self.new_ticket.fill("Alternate Mobile", customers.MOTOR_CLAIM_FOLLOW_UP.customer.mobile)
        assert self.new_ticket.is_create_ticket_enabled(), (
            "With both contact details given, the form should be submittable"
        )

    def test_the_complaint_form_asks_the_complaint_questions_not_the_enquiry_ones(self):
        self.open_complaint_form()

        assert self.new_ticket.is_field_displayed("Complaint Category"), (
            "A complaint form should ask for a complaint category"
        )
        assert not self.new_ticket.is_field_displayed("Sub Enquiry"), (
            "'Sub Enquiry' belongs to the enquiry form, not the complaint form"
        )

    # ---------- contact details ----------

    def test_an_invalid_email_address_blocks_the_save(self):
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()
        assert self.new_ticket.is_create_ticket_enabled(), "The form should start valid"

        self.new_ticket.fill("Alternate Email", "not-an-email")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A badly formed email address must block the save"
        )

    def test_an_invalid_phone_number_blocks_the_save(self):
        self.open_enquiry_form()
        self.new_ticket.fill_minimum_enquiry()

        self.new_ticket.fill("Alternate Mobile", "12")
        assert not self.new_ticket.is_create_ticket_enabled(), (
            "A number that is not a real UAE mobile must block the save"
        )

    # ---------- text that people actually paste in ----------

    def test_arabic_text_is_accepted_and_kept(self):
        self.open_enquiry_form()

        arabic = "العميل يطلب نسخة من وثيقة التأمين"
        self.new_ticket.fill("Subject", arabic)

        assert self.new_ticket.get_field_value("Subject") == arabic, (
            "Arabic text should be stored exactly as typed"
        )

    def test_quotes_ampersands_and_emoji_do_not_break_the_form(self):
        self.open_enquiry_form()

        awkward = 'Policy "A&B" renewal — urgent 🙂'
        self.new_ticket.fill("Subject", awkward)
        self.new_ticket.fill_minimum_enquiry()

        assert self.new_ticket.get_field_value("Subject") == awkward, (
            "Punctuation and emoji should survive unchanged"
        )
        assert self.new_ticket.is_create_ticket_enabled(), (
            "Odd characters should not block a valid form"
        )

    def test_a_very_long_description_is_kept_in_full(self):
        self.open_enquiry_form()

        long_text = "The customer explained at length. " * 60
        self.new_ticket.fill_textarea("Description", long_text)

        assert len(self.new_ticket.get_textarea_value("Description")) == len(long_text), (
            "A long description must not be silently trimmed"
        )

    # ---------- leaving without saving ----------

    def test_cancel_goes_back_to_the_list_without_creating_anything(self):
        self.open("/tickets/enquiries")
        self.list.wait_until_loaded()
        # Use the reported total - the list only shows ten rows per page.
        before = self.list.get_reported_result_count()

        self.open_enquiry_form()
        self.new_ticket.select_option("Source", "Phone")
        self.new_ticket.click_cancel()

        self.list.wait_until_loaded()
        assert self.current_url().endswith("/tickets/enquiries"), (
            f"Cancel should return to the list. Actual: {self.current_url()}"
        )
        assert self.list.get_reported_result_count() == before, (
            f"Cancelling must not create a ticket: {before} enquiries before, "
            f"{self.list.get_reported_result_count()} after"
        )


@pytest.mark.p1
@pytest.mark.phase2
class TestCcInitiatorPicker(BaseTest):
    """
    Who the manual-create picker offers for each channel (CcInitiatorPicker.tsx):
    paused and deactivated initiators are left out, and someone at today's limit is
    listed but cannot be picked. UAT data is shared, so the roster is only READ - nobody
    is paused, capped or deactivated by these tests, and the form is never submitted.
    """

    # The roster's Status words (lib/ccInitiatorStatus.ts).
    AVAILABLE = "Available"
    AT_LIMIT = "At limit"
    PAUSED = "Paused"
    ACCOUNT_OFF = "Account off"

    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        # A Manager can both read the Teams & SLA roster and open the create form.
        request.cls.login_class(request.cls.get("managerEmail"))

    def read_roster(self):
        """{pool label: [(name, status), ...]} from Teams & SLA > CC Initiator Pools."""
        self.login_once(self.get("managerEmail"))
        self.open_and_wait("/teams-sla")
        self.wait_for_page_content()
        self.reports.open_teams_sla_tab("CC Initiator Pools")
        roster = {}
        for pool in self.reports.pool_labels():
            roster[pool] = self.reports.pool_roster(pool)
        return roster

    def open_form_channels(self):
        """Opens the enquiry form and returns its Channel options (once the pools have loaded)."""
        self.open("/tickets/enquiries/new")
        self.new_ticket.continue_to_form()
        channels = self.new_ticket.channel_options_when_loaded()
        if not channels:
            pytest.skip("The Channel dropdown never listed a CC Initiator pool on this environment.")
        return channels

    def offered_for(self, channel):
        """[(label, can be picked), ...] the CC Initiator dropdown offers for this channel."""
        self.new_ticket.choose_channel(channel)
        return self.new_ticket.cc_initiator_options()

    def find_member(self, wanted_status):
        """
        Reads the roster, opens the form, and returns (channel, name) of the first initiator
        with this status in a pool the form offers as a channel - or (None, None).
        """
        roster = self.read_roster()
        channels = self.open_form_channels()
        for pool, members in roster.items():
            if pool not in channels:
                continue  # e.g. "CCC Complaint Handler" is not a picker channel
            for name, status in members:
                if status == wanted_status:
                    return pool, name
        return None, None

    def skip_because_nobody_is(self, status):
        pytest.skip(
            f"No CC Initiator has the status '{status}' in any channel pool on Teams & SLA > "
            "CC Initiator Pools right now. Changing someone's status would change shared UAT "
            "data, so this case cannot be checked here."
        )

    def test_r40_each_channel_offers_exactly_its_in_rotation_initiators(self):
        """Each channel lists its Available and At-limit members, and only the At-limit ones are disabled."""
        roster = self.read_roster()
        channels = self.open_form_channels()
        checked = 0
        for pool, members in roster.items():
            if pool not in channels:
                continue
            expected = []
            expected_disabled = []
            for name, status in members:
                if status in (self.AVAILABLE, self.AT_LIMIT):
                    expected.append(name)
                if status == self.AT_LIMIT:
                    expected_disabled.append(name)
            offered = []
            disabled = []
            for label, enabled in self.offered_for(pool):
                offered.append(NewTicketPage.initiator_name(label))
                if not enabled:
                    disabled.append(NewTicketPage.initiator_name(label))
            assert sorted(offered) == sorted(expected), (
                f"Channel '{pool}' should offer {sorted(expected)}, offers {sorted(offered)}"
            )
            assert sorted(disabled) == sorted(expected_disabled), (
                f"Channel '{pool}': only at-limit people should be disabled. "
                f"Expected {sorted(expected_disabled)}, disabled {sorted(disabled)}"
            )
            checked += 1
        assert checked, f"No roster pool matched a Channel option. Pools: {list(roster)}"

    def test_r40_a_paused_initiator_is_not_offered(self):
        """A pool member switched off (Paused) is not in that channel's list."""
        channel, name = self.find_member(self.PAUSED)
        if channel is None:
            self.skip_because_nobody_is(self.PAUSED)
        offered = []
        for label, enabled in self.offered_for(channel):
            offered.append(NewTicketPage.initiator_name(label))
        assert name not in offered, f"Paused '{name}' must not be offered under '{channel}': {offered}"

    def test_r40_an_initiator_at_the_daily_limit_is_listed_but_disabled(self):
        """Someone at today's limit is shown greyed out, with an "at daily limit" note."""
        channel, name = self.find_member(self.AT_LIMIT)
        if channel is None:
            self.skip_because_nobody_is(self.AT_LIMIT)
        matches = []
        for label, enabled in self.offered_for(channel):
            if NewTicketPage.initiator_name(label) == name:
                matches.append((label, enabled))
        assert matches, f"'{name}' is at the limit but should still be listed under '{channel}'"
        label, enabled = matches[0]
        assert not enabled, f"'{name}' is at the daily limit and must not be selectable"
        assert NewTicketPage.AT_LIMIT_SUFFIX in label, f"The option should say why: '{label}'"

    def test_r40_a_deactivated_initiator_is_not_offered(self):
        """A pool member whose account is deactivated (Account off) is not in that channel's list."""
        channel, name = self.find_member(self.ACCOUNT_OFF)
        if channel is None:
            self.skip_because_nobody_is(self.ACCOUNT_OFF)
        offered = []
        for label, enabled in self.offered_for(channel):
            offered.append(NewTicketPage.initiator_name(label))
        assert name not in offered, (
            f"Deactivated '{name}' must not be offered under '{channel}': {offered}"
        )
