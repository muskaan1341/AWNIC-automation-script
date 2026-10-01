"""
One ticket's detail screen and its tabs.

The tabs depend on the ticket (four to six of them):
  always       Overview, Customer & Records, SLA, Audit
  complaints   + Investigation & Resolution
  AI tickets   + Recommended Action Plan
So a hand-typed enquiry correctly shows only FOUR tabs.

All actions (Resolve, Edit, Reassign, Manual Escalation, Reclassify, Move to Discarded, ...)
live behind the one "More Action" menu.
"""

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage

# A field's label is a <div>; its value is in the <div> next to the label's parent.
_DETAIL_LABEL_XPATH = "//div[normalize-space(text())='{}']"

# Short names for the ids of the controls inside the modals.
MODAL_FIELD_IDS = {
    "Action": "manual-escalation-action",
    "Escalation department": "manual-escalation-department",
    "Escalation target": "manual-escalation-target",
    "Escalation reason": "manual-escalation-reason",
    "Assign to": "assign-mode",
    "Person in another department": "assign-another-dept",
    "Copy": "assign-copy",
}

# Old free-text Reassign boxes that were removed. Tests check they have not come back.
REMOVED_REASSIGN_FREE_TEXT_IDS = ("reassign-poc-name", "reassign-poc-email")


class TicketDetailPage(BasePage):
    # Every tab the app can show, in the order it shows them.
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
    # The removed header "Change Status" button. The Resolve box has a button with the same
    # label, so buttons inside a dialog are excluded.
    LEGACY_CHANGE_STATUS_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Change Status'][not(ancestor::div[@role='dialog'])]",
    )
    RESOLVE_ITEM = "Resolve"
    # Title and confirm button of the Resolve box.
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
    def detail_field_label(label):
        return (By.XPATH, _DETAIL_LABEL_XPATH.format(label))

    # ---------------- Actions ----------------

    def wait_until_loaded(self):
        self.wait_visible(self.HEADING)
        self.wait_visible((By.XPATH, "//a[normalize-space()='Overview']"))

    def open_tab(self, label):
        self.click(self.link(label))

    def open_more_action_menu(self):
        self.click(self.MORE_ACTION_BUTTON)

    def click_menu_item(self, label):
        self.click((By.XPATH, f"//*[@role='menu']//*[normalize-space()='{label}']"))

    def go_back_to_list(self):
        self.click(self.BACK_LINK)

    # ---- internal notes ----

    def type_internal_note(self, text):
        self.type_into(self.NOTE_BOX, text)

    def send_internal_note(self):
        self.click(self.NOTE_SEND_BUTTON)

    # ---- the Resolve (status change) box ----

    def type_status_resolution_note(self, text):
        """Types the resolution note the Resolve box asks for."""
        self.type_into((By.CSS_SELECTOR, "div[role='dialog'] textarea"), text)

    def has_resolution_note_box(self):
        return self.exists((By.CSS_SELECTOR, "div[role='dialog'] textarea"))

    def is_status_confirm_enabled(self):
        """True when the Resolve box's "Change Status" button can be pressed."""
        return self.driver.find_element(*self.RESOLVE_CONFIRM).is_enabled()

    # ---- fields inside a modal ----

    @staticmethod
    def modal_field(short_name):
        field_id = MODAL_FIELD_IDS.get(short_name)
        if field_id is None:
            raise ValueError(
                f"No modal field called '{short_name}'. Known: {sorted(MODAL_FIELD_IDS)}"
            )
        return (By.ID, field_id)

    def type_modal_field(self, short_name, text):
        """Types into a modal field. An empty string just clears it."""
        box = self.wait_visible(self.modal_field(short_name))
        self.clear_box(box)
        if text:
            box.send_keys(text)

    def modal_field_value(self, short_name):
        return self.driver.find_element(*self.modal_field(short_name)).get_attribute("value")

    def confirm_modal_with(self, button_label_start):
        """Presses the modal button whose label STARTS with this text (e.g. "Restore")."""
        self.click(
            (
                By.XPATH,
                "//div[@role='dialog']//button"
                f"[starts-with(normalize-space(),'{button_label_start}')]",
            )
        )

    # ---- modals ----

    def wait_for_modal(self):
        self.wait_visible(self.MODAL)

    def close_modal(self):
        """Clicks Cancel if the modal has one, otherwise the X icon."""
        cancel_buttons = self.driver.find_elements(
            By.XPATH, "//div[@role='dialog']//button[normalize-space()='Cancel']"
        )
        if cancel_buttons:
            cancel_buttons[0].click()
        else:
            self.driver.find_element(
                By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']"
            ).click()
        self.wait_gone(self.MODAL)

    # ---------------- Checks ----------------

    def get_reference_number(self):
        """The reference number shown in the page heading."""
        return self.wait_visible(self.HEADING).text.strip()

    def email_conversation_message_count(self):
        """
        The message count from the Overview's EMAIL card ("3 in conversation"),
        or -1 when there is no EMAIL card.
        """
        subtitles = self.driver.find_elements(
            By.XPATH,
            "//h3[normalize-space()='EMAIL']"
            "/following-sibling::p[contains(normalize-space(), 'in conversation')]",
        )
        if not subtitles:
            return -1
        first_word = subtitles[0].text.strip().split(" ", 1)[0]
        if first_word.isdigit():
            return int(first_word)
        return -1

    def cc_initiator_email(self):
        """The CC Ticket Initiator's email from SMART ROUTING, or "" when Unassigned."""
        # The email is the <span> after the name <div>, so the "Unassigned" badge is never read.
        pills = self.driver.find_elements(
            By.XPATH,
            "//div[normalize-space(text())='CC Ticket Initiator']"
            "/following-sibling::div[1]/following-sibling::span[1]",
        )
        if pills:
            return pills[0].text.strip()
        return ""

    def department_poc_email(self):
        """The Department POC's email from SMART ROUTING, or "" when no POC is assigned."""
        pills = self.driver.find_elements(
            By.XPATH,
            "//div[normalize-space(text())='Department POC']"
            "/following-sibling::div[1]/following-sibling::span[1]",
        )
        if pills:
            return pills[0].text.strip()
        return ""

    def get_tab_labels(self):
        """
        The tabs shown, in order. Only known tab names are kept, because other parts of the
        page also contain /tickets/ links.
        """
        present = []
        for text in self.texts_of(self.TAB_LINKS):
            if text in self.ALL_TAB_LABELS and text not in present:
                present.append(text)
        return present

    def has_tab(self, label):
        return label in self.get_tab_labels()

    def has_more_action_menu(self):
        return self.exists(self.MORE_ACTION_BUTTON)

    def has_legacy_change_status_button(self):
        """True if the removed header "Change Status" button is back (it must not be)."""
        return self.exists(self.LEGACY_CHANGE_STATUS_BUTTON)

    def get_open_menu_labels(self):
        """The text of every item in the menu that is open now."""
        labels = []
        for text in self.texts_of(self.MENU_ITEMS):
            if text:
                labels.append(text)
        return labels

    def has_section(self, title):
        """A named card on the tab, e.g. "Ticket Information". Case does not matter."""
        return self.exists(self.text_ignoring_case(title))

    def is_completeness_banner_displayed(self):
        return self.exists(self.innermost_containing("requires additional information"))

    def is_duplicate_banner_displayed(self):
        return self.exists(self.innermost_containing("possible duplicate"))

    def is_merged(self):
        """The grey "Merged" badge next to the reference number."""
        return self.exists((By.XPATH, "//h1/../*[normalize-space()='Merged']"))

    def has_status_badge(self, status):
        return self.exists((By.XPATH, f"//h1/..//*[normalize-space()='{status}']"))

    def current_status(self):
        """The ticket's current status - the first badge after the heading."""
        return self.text_of((By.XPATH, "(//h1/following-sibling::span)[1]"))

    def has_ai_badge(self):
        """The "AI Generated" badge. It must never appear on a hand-typed ticket."""
        return self.exists(self.innermost_containing("AI Generated"))

    def has_ai_summary_card(self, title):
        """
        The AI summary CARD (an <h3> title). Not the TICKET INFORMATION field with the same
        name, whose label is a <div>.
        """
        return self.exists((By.XPATH, f"//h3[normalize-space()='{title}']"))

    def has_detail_field(self, label):
        """True when TICKET INFORMATION has a field with this label."""
        return self.exists(self.detail_field_label(label))

    def get_detail_field_value(self, label):
        """A field's value as shown. An empty field shows an em dash."""
        return self.text_of(
            (
                By.XPATH,
                f"({_DETAIL_LABEL_XPATH.format(label)})[1]"
                "/parent::div/following-sibling::div",
            )
        )

    # ---------------- Resolve (More Action -> Resolve) ----------------

    def more_action_labels(self):
        """Every item in More Action ([] when there is no menu). Closes the menu again."""
        if not self.has_more_action_menu():
            return []
        self.open_more_action_menu()
        labels = self.get_open_menu_labels()
        self._press_escape_on_menu()
        self.wait_gone((By.CSS_SELECTOR, "[role='menu']"))
        return labels

    def open_resolve(self):
        """More Action -> Resolve. A Complaint goes to the Investigation tab instead of a box."""
        self.open_more_action_menu()
        self.click_menu_item(self.RESOLVE_ITEM)

    def page_mentions(self, text):
        """True when this text appears anywhere on the ticket."""
        return self.exists((By.XPATH, f'//*[contains(normalize-space(.),"{text}")]'))

    # ---------------- More Action items (Reassign, Escalation, ...) ----------------

    def open_action(self, label):
        """Opens More Action, picks an item and waits for its modal."""
        self.open_more_action_menu()
        self.click_menu_item(label)
        self.wait_for_modal()

    def offers_action(self, label):
        """True when More Action exists and offers this item. Closes the menu again."""
        if not self.has_more_action_menu():
            return False
        self.open_more_action_menu()
        present = label in self.get_open_menu_labels()
        self._press_escape_on_menu()
        return present

    def _press_escape_on_menu(self):
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    # ---- Reclassify ----
    # The item can be: usable, shown but disabled (with a reason), or not shown at all.

    def reclassify_item_is_disabled(self, label="Reclassify as Complaint"):
        """True when the item is listed but disabled. The menu must already be open."""
        return self.exists(
            (
                By.XPATH,
                f"//*[@role='menu']//*[normalize-space()='{label}']"
                "[@disabled or @aria-disabled='true']"
                " | //*[@role='menu']//*[@disabled or @aria-disabled='true']"
                f"[.//*[normalize-space()='{label}'] or normalize-space()='{label}']",
            )
        )

    def reclassify_blocked_reason(self):
        """The reason shown on a disabled Reclassify item (title/aria text), or ""."""
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

    def offers_reclassify_in_any_state(self, label="Reclassify as Complaint"):
        """True when the item is in the menu at all, usable or not. Closes the menu again."""
        if not self.has_more_action_menu():
            return False
        self.open_more_action_menu()
        present = False
        for text in self.get_open_menu_labels():
            if label in text:
                present = True
                break
        self._press_escape_on_menu()
        return present

    # ---- the Reassign modal ----

    def has_removed_free_text_reassign_field(self):
        """True if either removed free-text Reassign box is back on screen."""
        for field_id in REMOVED_REASSIGN_FREE_TEXT_IDS:
            if self.exists((By.ID, field_id)):
                return True
        return False

    # ---- the "Assign the Ticket" modal ----

    def get_assign_modes(self):
        """The "Assign to" choices."""
        return self.read_dropdown_options(self.modal_field("Assign to"))

    # ---- the Manual Escalation modal ----

    def get_escalation_actions(self):
        """The actions the escalation modal offers."""
        return self.read_dropdown_options(
            (By.CSS_SELECTOR, "div[role='dialog'] button[aria-haspopup='listbox']")
        )

    # ---------------- Audit tab ----------------

    def open_audit_tab_and_wait(self):
        """
        Opens the Audit tab and waits for the URL, then for at least one entry or the
        "No audit events" message. (The tab is its own page and can be slow the first time.)
        """
        self.open_tab("Audit")
        self.wait.until(lambda d: "/audit" in d.current_url)
        self.wait.until(
            lambda d: self.get_audit_event_labels()
            or self.exists(self.innermost_containing("No audit events"))
        )

    def get_audit_event_labels(self):
        """The title (<h4>) of every audit entry, newest first."""
        labels = []
        for text in self.texts_of((By.CSS_SELECTOR, "h4")):
            if text:
                labels.append(text)
        return labels

    def audit_records(self, label):
        """True when an audit entry contains this text (case ignored)."""
        for entry in self.get_audit_event_labels():
            if label.lower() in entry.lower():
                return True
        return False

    def audit_entry_count(self):
        return len(self.get_audit_event_labels())

    def has_internal_notes_card(self):
        return self.exists(self.text_ignoring_case("Internal Notes"))

    def is_send_note_enabled(self):
        return self.driver.find_element(*self.NOTE_SEND_BUTTON).is_enabled()

    def internal_note_count(self):
        """How many internal notes are saved on this ticket."""
        return self.count(
            (
                By.XPATH,
                "//*[contains(translate(normalize-space(text()),"
                "'INTERNAL NOTES','internal notes'),'internal notes')]/ancestor::div[2]//li",
            )
        )

    # ---------------- ATTACHMENTS card and preview ----------------
    # The card only shows when the ticket has an attachment. Clicking a row opens a preview.

    _ATTACHMENTS_CARD = (
        "//h3[normalize-space()='ATTACHMENTS']/ancestor::div[contains(@class,'rounded-lg')][1]"
    )
    ATTACHMENT_ROWS = (By.XPATH, _ATTACHMENTS_CARD + "//div[@role='button']")
    ATTACHMENT_DOWNLOAD_LINKS = (
        By.XPATH, _ATTACHMENTS_CARD + "//a[starts-with(@aria-label,'Download ')]"
    )
    DOWNLOAD_ALL = (By.XPATH, _ATTACHMENTS_CARD + "//button[normalize-space()='Download all']")
    # The zoom text "100%" is split into two text nodes, so look for any text node with "%".
    PREVIEW_ZOOM_LEVEL = (By.XPATH, "//div[@role='dialog']//span[text()[contains(.,'%')]]")
    PREVIEW_IMAGE = (By.CSS_SELECTOR, "div[role='dialog'] img")
    PREVIEW_DOWNLOAD = (By.XPATH, "//div[@role='dialog']//a[@download]")

    def attachment_count(self):
        """Rows in the ATTACHMENTS card (0 when there is no card)."""
        return self.count(self.ATTACHMENT_ROWS)

    def has_download_all(self):
        return self.exists(self.DOWNLOAD_ALL)

    def attachment_download_labels(self):
        labels = []
        for link in self.driver.find_elements(*self.ATTACHMENT_DOWNLOAD_LINKS):
            labels.append(link.get_attribute("aria-label"))
        return labels

    def open_attachment_preview(self, index=0):
        rows = self.driver.find_elements(*self.ATTACHMENT_ROWS)
        self.scroll_to_middle(rows[index])
        rows[index].click()
        self.wait_for_modal()

    @staticmethod
    def preview_control(label):
        """A preview button by its aria-label: Zoom in / Zoom out / Rotate /
        Previous attachment / Next attachment."""
        return (By.CSS_SELECTOR, f"div[role='dialog'] button[aria-label='{label}']")

    def has_preview_control(self, label):
        return self.exists(self.preview_control(label))

    def is_preview_control_enabled(self, label):
        return self.driver.find_element(*self.preview_control(label)).is_enabled()

    def click_preview_control(self, label):
        self.click(self.preview_control(label), scroll=False)

    def preview_title(self):
        return self.get_modal_title()

    def preview_zoom_text(self):
        return self.text_of(self.PREVIEW_ZOOM_LEVEL)

    def preview_image_transform(self):
        """The image's inline style (holds rotate(...)), or "" when no image is shown."""
        images = self.driver.find_elements(*self.PREVIEW_IMAGE)
        if not images:
            return ""
        return images[0].get_attribute("style") or ""

    def has_preview_download(self):
        return self.exists(self.PREVIEW_DOWNLOAD)

    def close_preview(self):
        """The preview closes with a "Close" button (not Cancel)."""
        self.click((By.XPATH, "//div[@role='dialog']//button[normalize-space()='Close']"))
        self.wait_gone(self.MODAL)

    # ---------------- PRIORITY & RISK card ----------------

    def priority_card_has_clock(self, label):
        """True when PRIORITY & RISK shows an SLA clock with this label."""
        return self.exists(
            (
                By.XPATH,
                "//h3[normalize-space()='PRIORITY & RISK']"
                "/ancestor::div[contains(@class,'rounded-lg')][1]"
                f"//span[normalize-space(text())='{label}']",
            )
        )

    def has_attachment_download(self, file_name):
        return self.exists((By.CSS_SELECTOR, f"[aria-label='Download {file_name}']"))

    def is_modal_open(self):
        return self.exists(self.MODAL)

    def get_modal_title(self):
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def modal_warns_permanent(self):
        return self.exists(
            (By.XPATH, "//div[@role='dialog']//*[contains(normalize-space(.),'permanent')]")
        )

    def has_notify_customer_checkbox(self):
        """The "notify the customer" checkbox in a modal (unticked by default)."""
        return self.exists((By.CSS_SELECTOR, "div[role='dialog'] input[type='checkbox']"))

    def is_notify_customer_checked(self):
        boxes = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] input[type='checkbox']"
        )
        return bool(boxes) and boxes[0].is_selected()
