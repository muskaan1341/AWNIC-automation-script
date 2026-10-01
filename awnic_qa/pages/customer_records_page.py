"""
The Customer & Records tab of one ticket - /tickets/{id}/customer-records.

It shows three record tables (policies, claims, quotations) plus the customer's case history.
The important difference to test:
  "no records"     the lookup ran and the customer has nothing (a fact)
  "lookup failed"  the lookup did not complete, so an empty table means nothing (an error)
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class CustomerRecordsPage(BasePage):
    # The record cards, in screen order (shown in uppercase).
    POLICY_CARD = "Policy Details"
    CLAIM_CARD = "Claim Details"
    QUOTATION_CARD = "Quotation Details"
    RECORD_CARDS = [POLICY_CARD, CLAIM_CARD, QUOTATION_CARD]

    CUSTOMER_DETAILS_CARD = "Customer Details"

    # The eight fields in CUSTOMER DETAILS.
    CUSTOMER_FIELDS = [
        "Customer Name",
        "Type",
        "Email",
        "Phone Number",
        "Alternate Email",
        "Alternate Phone",
        "Policy Number",
        "Claim Number",
    ]

    # The messages this tab can show.
    NOTHING_LOOKED_UP = "No customer records have been looked up for this ticket yet."
    NO_LINKED_RECORDS = "No linked records found for this customer."
    LOOKUP_FAILED = "Couldn’t load customer records"
    RECORDS_INCOMPLETE = "These records may be incomplete"

    # The message inside each table when it has no rows.
    TABLE_EMPTY_STATES = {
        POLICY_CARD: "No policies found",
        CLAIM_CARD: "No claims found",
        QUOTATION_CARD: "No quotations found",
    }

    POLICY_TABLE = (By.CSS_SELECTOR, "[data-testid='policy-table']")
    CLAIM_TABLE = (By.CSS_SELECTOR, "[data-testid='claim-table']")
    QUOTATION_TABLE = (By.CSS_SELECTOR, "[data-testid='quotation-table']")

    # The "Customer History" card (it is on the ticket's Overview tab).
    # Found through its <h3> title so the side-menu item of the same name is not matched.
    _HISTORY_CARD = (
        "//h3[normalize-space()='Customer History']/ancestor::div[contains(@class,'rounded-lg')][1]"
    )
    HISTORY_PANEL = (By.XPATH, "//h3[normalize-space()='Customer History']")
    # PR #301 (CustomerHistoryPanel.tsx) renamed this message: "tickets" -> "records".
    NO_OTHER_TICKETS = "No other records found for this customer."

    # Card title -> the table's data-testid.
    _TABLE_IDS = {
        POLICY_CARD: "policy-table",
        CLAIM_CARD: "claim-table",
        QUOTATION_CARD: "quotation-table",
    }

    # ==================================================================
    # Waits
    # ==================================================================

    def wait_until_loaded(self):
        """Waits until the tab shows the tables, or one of its "no records" / "failed" messages."""
        self.wait.until(
            lambda d: self.exists(self.POLICY_TABLE)
            or self.says_nothing_looked_up()
            or self.says_no_linked_records()
            or self.says_lookup_failed()
        )

    # ==================================================================
    # Checks - the record cards
    # ==================================================================

    def has_card(self, title):
        return self.exists(self.text_ignoring_case(title))

    def table_for(self, card_title):
        table_id = self._TABLE_IDS.get(card_title)
        if table_id is None:
            raise ValueError(
                f"No record table called '{card_title}'. Known: {sorted(self._TABLE_IDS)}"
            )
        return (By.CSS_SELECTOR, f"[data-testid='{table_id}']")

    def has_table(self, card_title):
        return self.exists(self.table_for(card_title))

    def row_count(self, card_title):
        """
        How many real rows a table has.
        An empty table still has one row holding its "No ... found" message; that row is not counted.
        """
        self.table_for(card_title)  # raises ValueError for an unknown card title
        rows = self.driver.find_elements(
            By.XPATH,
            f"//*[@data-testid='{self._TABLE_IDS[card_title]}']//tbody/tr",
        )
        if not rows:
            return 0
        empty_sentence = self.TABLE_EMPTY_STATES[card_title]
        count = 0
        for row in rows:
            if empty_sentence not in row.text:
                count += 1
        return count

    def column_values(self, card_title, column_name):
        """Every row's value in one column (found by its header name), top to bottom."""
        table_id = self._TABLE_IDS[card_title]
        headers = []
        for header in self.texts_of((By.XPATH, f"//*[@data-testid='{table_id}']//thead//th")):
            headers.append(header.strip())
        if column_name not in headers:
            raise ValueError(
                f"'{card_title}' has no '{column_name}' column. Columns: {headers}"
            )
        index = headers.index(column_name)
        values = []
        for row in self.driver.find_elements(
            By.XPATH, f"//*[@data-testid='{table_id}']//tbody/tr"
        ):
            cells = row.find_elements(By.TAG_NAME, "td")
            if index < len(cells):
                values.append(cells[index].text.strip())
        return values

    def shows_table_empty_state(self, card_title):
        return self.exists(
            self.innermost_containing(self.TABLE_EMPTY_STATES[card_title])
        )

    # ==================================================================
    # Checks - "no records" versus "the lookup failed"
    # ==================================================================

    def says_nothing_looked_up(self):
        """No lookup has been run for this ticket yet."""
        return self.exists(self.innermost_containing(self.NOTHING_LOOKED_UP))

    def says_no_linked_records(self):
        """The lookup ran and the customer has nothing linked."""
        return self.exists(self.innermost_containing(self.NO_LINKED_RECORDS))

    def says_lookup_failed(self):
        """The lookup failed (an error, not "no records")."""
        return self.exists(self.innermost_containing(self.LOOKUP_FAILED))

    def says_records_may_be_incomplete(self):
        """Old rows are shown, but the latest lookup did not finish."""
        return self.exists(self.innermost_containing(self.RECORDS_INCOMPLETE))

    # ==================================================================
    # Checks - the customer's case history
    # ==================================================================

    def has_history_panel(self):
        return self.exists(self.HISTORY_PANEL)

    def says_no_other_tickets(self):
        return self.exists(self.innermost_containing(self.NO_OTHER_TICKETS))

    def history_ticket_links(self):
        """The ticket links inside the Customer History card."""
        return self.driver.find_elements(
            By.XPATH, self._HISTORY_CARD + "//a[contains(@href,'/tickets/')]"
        )

    def history_archive_links(self):
        """Archive rows in the Customer History card (PR #301: they link to /historical/<id>)."""
        return self.driver.find_elements(
            By.XPATH, self._HISTORY_CARD + "//a[contains(@href,'/historical/')]"
        )

    def history_references(self):
        """The reference numbers in the history, in the order shown."""
        references = []
        for link in self.history_ticket_links():
            for line in link.text.split("\n"):
                token = line.strip()
                if token[:3] in ("INQ", "COM", "JNK") and "-" in token:
                    references.append(token)
                    break
        return references
