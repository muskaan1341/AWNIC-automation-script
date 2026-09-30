"""
One ticket's detail screen and its tabs.

TABS ARE CONDITIONAL - four to six of them. Never assert "six tabs":
  always       Overview, Customer & Records, SLA, Audit
  complaints   + Investigation & Resolution   (the ticket type is Complaint)
  AI tickets   + Recommended Action Plan      (the AI pipeline actually ran)

A hand-typed enquiry therefore shows FOUR tabs, and that is CORRECT: the application
deliberately hides every AI surface on a ticket the AI never touched, so nobody mistakes an
empty template for a real AI recommendation.

ACTIONS all live behind one "More Action" menu (Resolve / Edit / Reassign / Assign the Ticket /
Manual Escalation / Reclassify as … / Move to Discarded), each item gated on its own permission
(apps/web/src/app/tickets/[id]/TicketHeaderActions.tsx). There is NO standalone "Change Status"
button any more (client requirement 1.24): In Progress is set automatically when the assigned CC
Initiator opens the ticket, and the only manual status move left is "Resolve" inside the menu.
Resolve is hidden on an escalated ticket; on a Complaint it routes to the Investigation &
Resolution tab instead of opening a box. The Resolve box on an Inquiry is still
StatusChangeConfirmModal, whose confirm button is still labelled "Change Status".
"""

from __future__ import annotations

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage, Locator

#: A DetailField renders its label in a <div> above the value, inside a two-div wrapper.
#: Anchoring on the label and stepping to its sibling is how a field's value is read.
_DETAIL_LABEL_XPATH = "//div[normalize-space(text())='{}']"

#: Every modal form gives its controls a real id, which is the sturdiest locator there is. These
#: helpers take a short name, so a test reads "Assign to" not the id. Sources:
#:   ManualEscalationModal.tsx  manual-escalation-action / -department / -target / -reason
#:   AssignDeptPocModal.tsx     assign-mode ("Assign to") / assign-another-dept / assign-copy
MODAL_FIELD_IDS = {
    "Action": "manual-escalation-action",
    "Escalation department": "manual-escalation-department",
    "Escalation target": "manual-escalation-target",
    "Escalation reason": "manual-escalation-reason",
    "Assign to": "assign-mode",
    "Person in another department": "assign-another-dept",
    "Copy": "assign-copy",
}

#: The free-text Reassign boxes REMOVED when the Reassign pickers landed (ReassignInitiatorModal /
#: ReassignPocModal choose from a list). Kept only so a test can prove they have not come back.
REMOVED_REASSIGN_FREE_TEXT_IDS = ("reassign-poc-name", "reassign-poc-email")


class TicketDetailPage(BasePage):
    #: The six labels the app can render, in the order it renders them.
    ALL_TAB_LABELS = [
        "Overview",
        "Investigation & Resolution",
        "Customer & Records",
        "Recommended Action Plan",
        "SLA",
        "Audit",
    ]

    HEADING = (By.TAG_NAME, "h1")
    TAB_LINKS = (By.CSS_SELECTOR, "a[href*='/tickets/']")
    MORE_ACTION_BUTTON = (By.XPATH, "//button[normalize-space()='More Action']")
    #: The old header "Change Status" button - a button with that label OUTSIDE any dialog. The
    #: Resolve confirm box's own button carries the same words, so the dialog is excluded.
    LEGACY_CHANGE_STATUS_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Change Status'][not(ancestor::div[@role='dialog'])]",
    )
    RESOLVE_ITEM = "Resolve"
    #: StatusChangeConfirmModal's title and confirm label.
    RESOLVE_MODAL_TITLE = "Change status"
    RESOLVE_CONFIRM = (
        By.XPATH, "//div[@role='dialog']//button[normalize-space()='Change Status']"
    )
    MENU_ITEMS = (
        By.CSS_SELECTOR,
        "[role='menu'] [role='menuitem'], [role='menu'] a, [role='menu'] button",
    )
    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")
    BACK_LINK = (By.XPATH, "//a[normalize-space()='Back to Tickets']")

    NOTE_BOX = (By.CSS_SELECTOR, "textarea[aria-label='Write an internal note']")
    NOTE_SEND_BUTTON = (By.XPATH, "//button[normalize-space()='Send']")

    @staticmethod
    def detail_field_label(label: str) -> Locator:
        return (By.XPATH, _DETAIL_LABEL_XPATH.format(label))

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.HEADING)
        self.wait_visible((By.XPATH, "//a[normalize-space()='Overview']"))

    def open_tab(self, label: str) -> None:
        self.click(self.link(label))

    def open_more_action_menu(self) -> None:
        self.click(self.MORE_ACTION_BUTTON)

    def click_menu_item(self, label: str) -> None:
        self.click((By.XPATH, f"//*[@role='menu']//*[normalize-space()='{label}']"))

    def go_back_to_list(self) -> None:
        self.click(self.BACK_LINK)

    # ---- internal notes ----

    def type_internal_note(self, text: str) -> None:
        self.type_into(self.NOTE_BOX, text)

    def send_internal_note(self) -> None:
        self.click(self.NOTE_SEND_BUTTON)

    # ---- the status-change modal ----

    def type_status_resolution_note(self, text: str) -> None:
        """
        Types the resolution note the modal asks for when the new status is "Resolved".

        The application never lets a ticket be marked resolved without somebody writing HOW it
        was resolved - the same rule the Kanban board enforces when a card is dropped into the
        Resolved column, and the API rejects the change without it.
        """
        self.type_into((By.CSS_SELECTOR, "div[role='dialog'] textarea"), text)

    def has_resolution_note_box(self) -> bool:
        return self.exists((By.CSS_SELECTOR, "div[role='dialog'] textarea"))

    def is_status_confirm_enabled(self) -> bool:
        """True when the Resolve box's confirm button ("Change Status") is usable."""
        return self.driver.find_element(*self.RESOLVE_CONFIRM).is_enabled()

    # ---- fields inside a modal ----

    @staticmethod
    def modal_field(short_name: str) -> Locator:
        field_id = MODAL_FIELD_IDS.get(short_name)
        if field_id is None:
            raise ValueError(
                f"No modal field called '{short_name}'. Known: {sorted(MODAL_FIELD_IDS)}"
            )
        return (By.ID, field_id)

    def type_modal_field(self, short_name: str, text: str) -> None:
        """Types into a modal field. An empty string clears it - how "left blank" is tested."""
        box = self.wait_visible(self.modal_field(short_name))
        self.clear_box(box)
        if text:
            box.send_keys(text)

    def modal_field_value(self, short_name: str) -> str:
        return self.driver.find_element(*self.modal_field(short_name)).get_attribute("value")

    def confirm_modal_with(self, button_label_start: str) -> None:
        """
        Presses the modal's confirm button.

        Matched on the START of the label, because the wording changes with what is being
        confirmed - "Restore Enquiry" / "Restore Complaint" are both a "Restore", and the
        reclassify box relabels its button per target type.
        """
        self.click(
            (
                By.XPATH,
                "//div[@role='dialog']//button"
                f"[starts-with(normalize-space(),'{button_label_start}')]",
            )
        )

    # ---- modals ----

    def wait_for_modal(self) -> None:
        self.wait_visible(self.MODAL)

    def close_modal(self) -> None:
        cancel = self.driver.find_elements(
            By.XPATH, "//div[@role='dialog']//button[normalize-space()='Cancel']"
        )
        if cancel:
            cancel[0].click()
        else:
            self.driver.find_element(
                By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']"
            ).click()
        self.wait_gone(self.MODAL)

    # ==================================================================
    # Checks
    # ==================================================================

    def get_reference_number(self) -> str:
        """The reference number in the page heading - proves the right ticket opened."""
        return self.wait_visible(self.HEADING).text.strip()

    def email_conversation_message_count(self) -> int:
        """
        How many messages the Overview's EMAIL card says the conversation holds, or -1 when
        there is no EMAIL card at all.

        TicketDetailContent renders that card only for a ticket whose source is Email, and
        its first entry is the inbound email the ticket was made from - so a count of at
        least one means the arriving email is actually on the ticket. Anchored on the exact
        title AND its "... in conversation" subtitle, because "Email" alone is also the label
        of a Customer Details field.
        """
        subtitles = self.driver.find_elements(
            By.XPATH,
            "//h3[normalize-space()='EMAIL']"
            "/following-sibling::p[contains(normalize-space(), 'in conversation')]",
        )
        if not subtitles:
            return -1
        digits = subtitles[0].text.strip().split(" ", 1)[0]
        return int(digits) if digits.isdigit() else -1

    def cc_initiator_email(self) -> str:
        """
        The CC Ticket Initiator's email from the Overview's SMART ROUTING card, or "" when
        the ticket is Unassigned (a red badge instead of a person - deliberate since
        2026-08-23 when no pool matches, see SmartRoutingPanel).
        """
        # The email pill is the span AFTER the name <div>. The "Unassigned" badge is also a
        # <span> sibling of the label, but with no name div before it - so anchoring on the
        # name div keeps the badge from being read back as an address.
        pills = self.driver.find_elements(
            By.XPATH,
            "//div[normalize-space(text())='CC Ticket Initiator']"
            "/following-sibling::div[1]/following-sibling::span[1]",
        )
        return pills[0].text.strip() if pills else ""

    def department_poc_email(self) -> str:
        """
        The Department POC's email from the Overview's SMART ROUTING card, or "" when no POC
        is assigned (the card then shows only a "—" name and no email pill).

        This is the ticket's assigned_poc_email - the exact field the own-assigned scope
        (complaint_handler) is filtered on server-side, so it is the honest per-ticket answer
        to "is this one theirs?".
        """
        pills = self.driver.find_elements(
            By.XPATH,
            "//div[normalize-space(text())='Department POC']"
            "/following-sibling::div[1]/following-sibling::span[1]",
        )
        return pills[0].text.strip() if pills else ""

    def get_tab_labels(self) -> list[str]:
        """
        The tabs actually rendered, in order.

        Filtered against the known six rather than scraping every /tickets/ link on the page,
        because the customer-history panel and the audit trail also render ticket links.
        """
        present: list[str] = []
        for text in self.texts_of(self.TAB_LINKS):
            if text in self.ALL_TAB_LABELS and text not in present:
                present.append(text)
        return present

    def has_tab(self, label: str) -> bool:
        return label in self.get_tab_labels()

    def has_more_action_menu(self) -> bool:
        return self.exists(self.MORE_ACTION_BUTTON)

    def has_legacy_change_status_button(self) -> bool:
        """True if the REMOVED header "Change Status" button is back (it must not be)."""
        return self.exists(self.LEGACY_CHANGE_STATUS_BUTTON)

    def get_open_menu_labels(self) -> list[str]:
        """Everything currently offered inside whichever menu is open."""
        return [text for text in self.texts_of(self.MENU_ITEMS) if text]

    def has_section(self, title: str) -> bool:
        """A named card on the tab, e.g. "Ticket Information". Case does not matter."""
        return self.exists(self.text_ignoring_case(title))

    def is_completeness_banner_displayed(self) -> bool:
        return self.exists(self.innermost_containing("requires additional information"))

    def is_duplicate_banner_displayed(self) -> bool:
        return self.exists(self.innermost_containing("possible duplicate"))

    def is_merged(self) -> bool:
        """The grey "Merged" badge next to the reference number on a confirmed duplicate."""
        return self.exists((By.XPATH, "//h1/../*[normalize-space()='Merged']"))

    def has_status_badge(self, status: str) -> bool:
        return self.exists((By.XPATH, f"//h1/..//*[normalize-space()='{status}']"))

    def current_status(self) -> str:
        """
        The status this ticket is in RIGHT NOW, read from the badge beside the reference.

        has_status_badge() can only confirm a status you already suspect; a test that has to
        say "the menu must not offer whatever it is in" needs to read it. The badge is the
        first <span> after the <h1> (TicketDetailHeader renders StatusBadge there, and Badge
        renders a span), which is also why the duplicate/needs-review badges beside it are
        never mistaken for it.
        """
        return self.text_of((By.XPATH, "(//h1/following-sibling::span)[1]"))

    def has_ai_badge(self) -> bool:
        """
        The "AI Generated" badge.

        It must NEVER appear on a ticket typed in by hand. That is the whole point of the
        ai_processed flag: a manual ticket has no AI content, so showing an AI label on it
        would be telling the user something untrue.
        """
        return self.exists(self.innermost_containing("AI Generated"))

    def has_ai_summary_card(self, title: str) -> bool:
        """
        The AI's own narrative summary CARD - not the field of the same name.

        There are now TWO things called "Enquiry Summary" on an enquiry, and they are not
        interchangeable:

          the CARD   a standalone section carrying the AI Generated badge, holding the Intent
                     Classifier's one or two sentence read on what the customer wants. Pure AI
                     output, so it appears ONLY on a ticket the AI actually processed.
          the FIELD  a label-and-value pair inside TICKET INFORMATION, added in September. It
                     is part of the classified field set and renders on EVERY enquiry, showing
                     an em dash when there is nothing in it.

        Asking "is the text 'Enquiry Summary' on the page?" cannot tell them apart, and a test
        that did exactly that started failing the moment the field was added. The card's title
        is an h3; the field's label is a div, so the tag is what separates them.
        """
        return self.exists((By.XPATH, f"//h3[normalize-space()='{title}']"))

    def has_detail_field(self, label: str) -> bool:
        """True when TICKET INFORMATION carries a field with this label."""
        return self.exists(self.detail_field_label(label))

    def get_detail_field_value(self, label: str) -> str:
        """
        A field's value as the user reads it. An empty field reads as an em dash, which is the
        application's honest way of saying "nothing here" rather than leaving a blank.
        """
        return self.text_of(
            (
                By.XPATH,
                f"({_DETAIL_LABEL_XPATH.format(label)})[1]"
                "/parent::div/following-sibling::div",
            )
        )

    # ==================================================================
    # Resolve - More Action -> Resolve -> a confirmation box (Inquiry only)
    # ==================================================================
    #
    # The old "Change Status" MENU (In Progress / Pending Department POC / Resolved) is gone.
    # Resolve is the only manual status move, and it lives in More Action. On an Inquiry it
    # opens StatusChangeConfirmModal (title "Change status", a Resolution note box, an unticked
    # notify-customer checkbox, confirm "Change Status" disabled until a note is written). On a
    # Complaint it navigates to /tickets/{id}/investigation?from=resolve instead.

    def more_action_labels(self) -> list[str]:
        """Every item More Action offers right now ([] when there is no menu). Closes it again."""
        if not self.has_more_action_menu():
            return []
        self.open_more_action_menu()
        labels = self.get_open_menu_labels()
        self._press_escape_on_menu()
        self.wait_gone((By.CSS_SELECTOR, "[role='menu']"))
        return labels

    def open_resolve(self) -> None:
        """More Action -> Resolve. On an Inquiry waits for the box; a Complaint navigates away."""
        self.open_more_action_menu()
        self.click_menu_item(self.RESOLVE_ITEM)

    def page_mentions(self, text: str) -> bool:
        """True when this text appears anywhere on the ticket - for "was the POC recorded?"."""
        return self.exists((By.XPATH, f'//*[contains(normalize-space(.),"{text}")]'))

    # ==================================================================
    # The escalation ladder: More Action -> Reassign / Manual Escalation
    # ==================================================================
    #
    # WHO IS ALLOWED WHAT (app/teams/seed_data.py ROLE_PERMISSIONS - the authority):
    #
    #   Reassign            REASSIGN_TICKET        HOD, Manager, CC Supervisor
    #   Manual Escalation   MANUAL_ESCALATION_EARLY HOD, Manager, CC Supervisor
    #                       ^ deliberately NOT the CC Initiator. The 2026-08-12 amendment
    #                         flipped that cell Y->N, reversing an earlier spec, so it is
    #                         exactly the kind of grant that silently comes back on a bad
    #                         merge from stale seed data.
    #   Reclassify          RECLASSIFY_TICKET_TYPE HOD and CC Initiator ONLY
    #   Move to Discarded   DISCARD_TICKET         Manager and CC Supervisor ONLY
    #
    # Reclassify and Discard are DIFFERENT tiers on purpose - holding one never implies the
    # other.

    def open_action(self, label: str) -> None:
        """Opens More Action and picks an item, e.g. open_action("Manual Escalation")."""
        self.open_more_action_menu()
        self.click_menu_item(label)
        self.wait_for_modal()

    def offers_action(self, label: str) -> bool:
        """True when More Action exists AND offers this item. Closes the menu again."""
        if not self.has_more_action_menu():
            return False
        self.open_more_action_menu()
        present = label in self.get_open_menu_labels()
        self._press_escape_on_menu()
        return present

    def _press_escape_on_menu(self) -> None:
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    # ------------------------------------------------------------------
    # The proactive reclassification window (module 07)
    # ------------------------------------------------------------------
    # The swap between Inquiry and Complaint is only legal while the ticket is still with the
    # CC Initiator, has not already been swapped once, and has no complaints-register row. Rather
    # than let a user press the button and collect a 409, the API tells the screen up front
    # through two advisory read fields (`can_reclassify_now` / `reclassify_blocked_reason`), and
    # the menu renders the item DISABLED with that reason on it. The 409 stays the backstop.
    #
    # So "is the swap offered?" has THREE answers here, not two: offered and usable, offered but
    # disabled with a reason, or absent because the role holds no reclassify capability at all.

    def reclassify_item_is_disabled(self, label: str = "Reclassify as Complaint") -> bool:
        """
        True when the swap is listed but greyed out - the window has closed.

        Assumes the More Action menu is already open. A disabled menu item can be marked either
        way depending on whether it renders as a button or a menuitem, so both are accepted.
        """
        return self.exists(
            (
                By.XPATH,
                f"//*[@role='menu']//*[normalize-space()='{label}']"
                "[@disabled or @aria-disabled='true']"
                f" | //*[@role='menu']//*[@disabled or @aria-disabled='true']"
                f"[.//*[normalize-space()='{label}'] or normalize-space()='{label}']",
            )
        )

    def reclassify_blocked_reason(self) -> str:
        """
        The one-line explanation shown on a blocked swap, or "" when there is none.

        Read from the item's own tooltip/title first, then from any text beside it - the reason
        is the whole point of surfacing the block proactively, so a disabled item with no
        explanation is worse than no item at all.
        """
        items = self.driver.find_elements(
            By.XPATH,
            "//*[@role='menu']//*[contains(normalize-space(),'Reclassify')]",
        )
        for item in items:
            for attribute in ("title", "aria-label", "aria-describedby"):
                value = item.get_attribute(attribute)
                if value and value.strip() and "Reclassify" not in value:
                    return value.strip()
        return ""

    def offers_reclassify_in_any_state(self, label: str = "Reclassify as Complaint") -> bool:
        """True when the item is on the menu at all, usable or not. Closes the menu again."""
        if not self.has_more_action_menu():
            return False
        self.open_more_action_menu()
        present = any(
            label in text for text in self.get_open_menu_labels()
        )
        self._press_escape_on_menu()
        return present

    # ---- the Reassign modal ----

    def has_removed_free_text_reassign_field(self) -> bool:
        """True if either removed free-text Reassign box (name / email) is back on screen."""
        return any(self.exists((By.ID, i)) for i in REMOVED_REASSIGN_FREE_TEXT_IDS)

    # ---- the "Assign the Ticket" modal (AssignDeptPocModal) ----

    def get_assign_modes(self) -> list[str]:
        """The "Assign to" choices (Assign to Dept POC / Assign to Another Dept)."""
        return self.read_dropdown_options(self.modal_field("Assign to"))

    # ---- the Manual Escalation modal ----

    def get_escalation_actions(self) -> list[str]:
        """The actions the escalation modal offers (Escalate to next level, straight to Final…)."""
        return self.read_dropdown_options(
            (By.CSS_SELECTOR, "div[role='dialog'] button[aria-haspopup='listbox']")
        )

    # ==================================================================
    # The Audit tab
    # ==================================================================

    def open_audit_tab_and_wait(self) -> None:
        """
        Opens the Audit tab and waits for it to have genuinely arrived.

        The Audit tab is its OWN ROUTE (/tickets/{id}/audit), so on a development server the
        first visit compiles it - which can take most of the wait budget on its own. Waiting
        straight away for "at least one entry" therefore spends the whole timeout on a page
        that has not started rendering, and fails a ticket whose trail is perfectly fine.

        So this waits in stages: the route first, then the page load, and only then the
        content - and it accepts the honest "no audit events" message as an arrival too, so a
        genuinely empty trail is reported by the assertion rather than by a timeout.
        """
        self.open_tab("Audit")
        self.wait.until(lambda d: "/audit" in d.current_url)
        self.wait.until(
            lambda d: self.get_audit_event_labels()
            or self.exists(self.innermost_containing("No audit events"))
        )

    def get_audit_event_labels(self) -> list[str]:
        """
        Every audit entry's title, newest first.

        An entry is a block with an <h4> heading, NOT a table row and not a list item - the
        same shape the organisation-wide trail uses (see ReportsPage.has_audit_entries).
        """
        return [text for text in self.texts_of((By.CSS_SELECTOR, "h4")) if text]

    def audit_records(self, label: str) -> bool:
        """True when the ticket's own history records this event. Substring, not exact."""
        return any(
            label.lower() in entry.lower() for entry in self.get_audit_event_labels()
        )

    def audit_entry_count(self) -> int:
        return len(self.get_audit_event_labels())

    def has_internal_notes_card(self) -> bool:
        return self.exists(self.text_ignoring_case("Internal Notes"))

    def is_send_note_enabled(self) -> bool:
        return self.driver.find_element(*self.NOTE_SEND_BUTTON).is_enabled()

    def internal_note_count(self) -> int:
        """How many internal notes are already saved on this ticket."""
        return self.count(
            (
                By.XPATH,
                "//*[contains(translate(normalize-space(text()),"
                "'INTERNAL NOTES','internal notes'),'internal notes')]/ancestor::div[2]//li",
            )
        )

    # ==================================================================
    # U12 / U17 - the ATTACHMENTS card and its preview (AttachmentsPanel / AttachmentPreviewModal)
    # ==================================================================
    # The card only renders when the ticket has at least one attachment. Each row is a
    # role="button" (opens the preview) holding a per-file <a aria-label="Download <name>">.
    # "Download all" sits in the card header only when there are two or more.

    _ATTACHMENTS_CARD = (
        "//h3[normalize-space()='ATTACHMENTS']/ancestor::div[contains(@class,'rounded-lg')][1]"
    )
    ATTACHMENT_ROWS = (By.XPATH, _ATTACHMENTS_CARD + "//div[@role='button']")
    ATTACHMENT_DOWNLOAD_LINKS = (
        By.XPATH, _ATTACHMENTS_CARD + "//a[starts-with(@aria-label,'Download ')]"
    )
    DOWNLOAD_ALL = (By.XPATH, _ATTACHMENTS_CARD + "//button[normalize-space()='Download all']")
    #: `{Math.round(zoom * 100)}%` renders as TWO text nodes ("100", "%"), so ask whether ANY
    #: text node holds the "%" (README pitfall 8 - the same shape as "6 results").
    PREVIEW_ZOOM_LEVEL = (By.XPATH, "//div[@role='dialog']//span[text()[contains(.,'%')]]")
    PREVIEW_IMAGE = (By.CSS_SELECTOR, "div[role='dialog'] img")
    PREVIEW_DOWNLOAD = (By.XPATH, "//div[@role='dialog']//a[@download]")

    def attachment_count(self) -> int:
        """Rows in the ATTACHMENTS card; 0 when the card is absent (no attachments)."""
        return self.count(self.ATTACHMENT_ROWS)

    def has_download_all(self) -> bool:
        return self.exists(self.DOWNLOAD_ALL)

    def attachment_download_labels(self) -> list[str]:
        return [
            e.get_attribute("aria-label")
            for e in self.driver.find_elements(*self.ATTACHMENT_DOWNLOAD_LINKS)
        ]

    def open_attachment_preview(self, index: int = 0) -> None:
        rows = self.driver.find_elements(*self.ATTACHMENT_ROWS)
        self.scroll_to_middle(rows[index])
        rows[index].click()
        self.wait_for_modal()

    @staticmethod
    def preview_control(label: str) -> Locator:
        """An IconButton in the preview (aria-label): Zoom in / Zoom out / Rotate /
        Previous attachment / Next attachment."""
        return (By.CSS_SELECTOR, f"div[role='dialog'] button[aria-label='{label}']")

    def has_preview_control(self, label: str) -> bool:
        return self.exists(self.preview_control(label))

    def is_preview_control_enabled(self, label: str) -> bool:
        return self.driver.find_element(*self.preview_control(label)).is_enabled()

    def click_preview_control(self, label: str) -> None:
        self.click(self.preview_control(label), scroll=False)

    def preview_title(self) -> str:
        return self.get_modal_title()

    def preview_zoom_text(self) -> str:
        return self.text_of(self.PREVIEW_ZOOM_LEVEL)

    def preview_image_transform(self) -> str:
        """The inline rotate(...) the image renderer applies ("" when no image is shown)."""
        images = self.driver.find_elements(*self.PREVIEW_IMAGE)
        return (images[0].get_attribute("style") or "") if images else ""

    def has_preview_download(self) -> bool:
        return self.exists(self.PREVIEW_DOWNLOAD)

    def close_preview(self) -> None:
        """The preview has a "Close" button in its header (not Cancel)."""
        self.click((By.XPATH, "//div[@role='dialog']//button[normalize-space()='Close']"))
        self.wait_gone(self.MODAL)

    # ==================================================================
    # U11 - PRIORITY & RISK card (PriorityCard.tsx)
    # ==================================================================

    def priority_card_has_clock(self, label: str) -> bool:
        """
        True when PRIORITY & RISK shows an SLA clock with this label - "Current-Level SLA" on
        every ticket, then "Total SLA" (enquiry) or "Priority SLA" (complaint). The label is a
        <span> holding the text plus an info-icon tooltip, hence contains() on its own text.
        """
        return self.exists(
            (
                By.XPATH,
                "//h3[normalize-space()='PRIORITY & RISK']"
                "/ancestor::div[contains(@class,'rounded-lg')][1]"
                f"//span[normalize-space(text())='{label}']",
            )
        )

    def has_attachment_download(self, file_name: str) -> bool:
        return self.exists((By.CSS_SELECTOR, f"[aria-label='Download {file_name}']"))

    def is_modal_open(self) -> bool:
        return self.exists(self.MODAL)

    def get_modal_title(self) -> str:
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def modal_warns_permanent(self) -> bool:
        return self.exists(
            (By.XPATH, "//div[@role='dialog']//*[contains(normalize-space(.),'permanent')]")
        )

    def has_notify_customer_checkbox(self) -> bool:
        """Every write modal carries a "notify the customer" opt-in, unticked by default."""
        return self.exists((By.CSS_SELECTOR, "div[role='dialog'] input[type='checkbox']"))

    def is_notify_customer_checked(self) -> bool:
        boxes = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] input[type='checkbox']"
        )
        return bool(boxes) and boxes[0].is_selected()
