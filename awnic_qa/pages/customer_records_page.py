"""
The Customer & Records tab of one ticket - /tickets/{id}/customer-records.

MODULE 13 in the test-case pack (Customer Information). Like the investigation tab, the suite
proved this one opens and does not 404, and nothing more - the 31 cases behind it were
untouched.

WHAT IS ON IT: three record tables fed from the Data Mart cache, plus the customer's own case
history. Each table carries a real `data-testid` (`policy-table`, `claim-table`,
`quotation-table`), which is the stable hook - the card titles above them are styled uppercase
and are matched without case.

THE DISTINCTION THIS TAB IS BUILT AROUND, and the one worth testing hardest:

  "no records"     a fact. The lookup ran and the customer genuinely has no policies.
  "lookup failed"  an ERROR. The cache is untrustworthy, and an empty result means nothing.

The component is explicit about it (`an empty cache after a *failed* lookup is not 'no
records'`): a failed lookup with nothing cached shows a red "Couldn't load customer records"
callout, and a failed lookup WITH cached rows shows an amber "These records may be incomplete"
caveat above them. Reporting a failure as "this customer has no policies" would send an agent
away believing something false, which is worse than an error.

NOTHING HERE IS LIVE. R22 is a local join against `tickets` + `customer_lookup_cache`, never a
re-fetch, so these tables read what was cached at intake. The browser never talks to AWNIC's
Data Mart directly and must not be made to - `apps/api` is the single node for that.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage, Locator


class CustomerRecordsPage(BasePage):
    #: The record cards, in the order the tab renders them. Uppercase on screen.
    POLICY_CARD = "Policy Details"
    CLAIM_CARD = "Claim Details"
    QUOTATION_CARD = "Quotation Details"
    RECORD_CARDS = [POLICY_CARD, CLAIM_CARD, QUOTATION_CARD]

    #: The customer identity block, which lives on the Overview and is repeated here.
    CUSTOMER_DETAILS_CARD = "Customer Details"

    #: The eight fields CUSTOMER DETAILS is specified to carry.
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

    #: The exact sentences this tab produces. The first two are FACTS; the third is an ERROR,
    #: and telling them apart is most of what these tests are for.
    NOTHING_LOOKED_UP = "No customer records have been looked up for this ticket yet."
    NO_LINKED_RECORDS = "No linked records found for this customer."
    LOOKUP_FAILED = "Couldn’t load customer records"
    RECORDS_INCOMPLETE = "These records may be incomplete"

    #: Per-table empty states, shown inside a table that rendered but holds no rows.
    TABLE_EMPTY_STATES = {
        POLICY_CARD: "No policies found",
        CLAIM_CARD: "No claims found",
        QUOTATION_CARD: "No quotations found",
    }

    POLICY_TABLE = (By.CSS_SELECTOR, "[data-testid='policy-table']")
    CLAIM_TABLE = (By.CSS_SELECTOR, "[data-testid='claim-table']")
    QUOTATION_TABLE = (By.CSS_SELECTOR, "[data-testid='quotation-table']")

    #: The customer's own case history.
    HISTORY_PANEL = (By.XPATH, "//*[normalize-space()='Customer History']")
    NO_OTHER_TICKETS = "No other tickets found for this customer."

    _TABLE_IDS = {
        POLICY_CARD: "policy-table",
        CLAIM_CARD: "claim-table",
        QUOTATION_CARD: "quotation-table",
    }

    # ==================================================================
    # Waits
    # ==================================================================

    def wait_until_loaded(self) -> None:
        """
        Waits until the tab has genuinely arrived, in ANY of its legitimate shapes.

        There are four, and all of them are correct answers: the three record tables, the
        "nothing looked up yet" line, the "no linked records" line, or the failed-lookup
        callout. Waiting only for a table would time out on a ticket whose customer was never
        looked up - which is a normal state, not a fault.
        """
        self.wait.until(
            lambda d: self.exists(self.POLICY_TABLE)
            or self.says_nothing_looked_up()
            or self.says_no_linked_records()
            or self.says_lookup_failed()
        )

    # ==================================================================
    # Checks - the record cards
    # ==================================================================

    def has_card(self, title: str) -> bool:
        return self.exists(self.text_ignoring_case(title))

    def table_for(self, card_title: str) -> Locator:
        table_id = self._TABLE_IDS.get(card_title)
        if table_id is None:
            raise ValueError(
                f"No record table called '{card_title}'. Known: {sorted(self._TABLE_IDS)}"
            )
        return (By.CSS_SELECTOR, f"[data-testid='{table_id}']")

    def has_table(self, card_title: str) -> bool:
        return self.exists(self.table_for(card_title))

    def row_count(self, card_title: str) -> int:
        """
        How many real rows a record table holds.

        An empty table still renders ONE row - the one holding its empty-state sentence - so
        that row is discounted here. Otherwise "no policies found" would read as one policy.
        """
        table = self.table_for(card_title)
        rows = self.driver.find_elements(
            By.XPATH,
            f"//*[@data-testid='{self._TABLE_IDS[card_title]}']//tbody/tr",
        )
        if not rows:
            return 0
        empty_sentence = self.TABLE_EMPTY_STATES[card_title]
        return sum(1 for row in rows if empty_sentence not in row.text)

    def column_values(self, card_title: str, column_name: str) -> list[str]:
        """
        Every row's value in ONE named column of a record table, in page order.

        By NAME, not by index: these tables differ in width per record type, so "the policy
        number is the first cell" is one refactor away from being quietly wrong - and a
        scoping or duplication check that reads the wrong column passes while proving nothing.
        """
        table_id = self._TABLE_IDS[card_title]
        headers = self.texts_of(
            (By.XPATH, f"//*[@data-testid='{table_id}']//thead//th")
        )
        stripped = [h.strip() for h in headers]
        if column_name not in stripped:
            raise ValueError(
                f"'{card_title}' has no '{column_name}' column. Columns: {stripped}"
            )
        index = stripped.index(column_name)
        values: list[str] = []
        for row in self.driver.find_elements(
            By.XPATH, f"//*[@data-testid='{table_id}']//tbody/tr"
        ):
            cells = row.find_elements(By.TAG_NAME, "td")
            if index < len(cells):
                values.append(cells[index].text.strip())
        return values

    def shows_table_empty_state(self, card_title: str) -> bool:
        return self.exists(
            self.innermost_containing(self.TABLE_EMPTY_STATES[card_title])
        )

    # ==================================================================
    # Checks - "no records" versus "the lookup failed"
    # ==================================================================

    def says_nothing_looked_up(self) -> bool:
        """A FACT: no lookup has been run for this ticket."""
        return self.exists(self.innermost_containing(self.NOTHING_LOOKED_UP))

    def says_no_linked_records(self) -> bool:
        """A FACT: the lookup ran and this customer has nothing linked."""
        return self.exists(self.innermost_containing(self.NO_LINKED_RECORDS))

    def says_lookup_failed(self) -> bool:
        """An ERROR: the lookup did not complete, so an empty result proves nothing."""
        return self.exists(self.innermost_containing(self.LOOKUP_FAILED))

    def says_records_may_be_incomplete(self) -> bool:
        """The softer caveat: rows are cached, but a newer lookup did not finish."""
        return self.exists(self.innermost_containing(self.RECORDS_INCOMPLETE))

    # ==================================================================
    # Checks - the customer's own case history
    # ==================================================================

    def has_history_panel(self) -> bool:
        return self.exists(self.HISTORY_PANEL)

    def says_no_other_tickets(self) -> bool:
        return self.exists(self.innermost_containing(self.NO_OTHER_TICKETS))

    def history_ticket_links(self) -> list:
        """Every past case the history offers as a link through to its ticket."""
        return self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/tickets/']")

    def history_references(self) -> list[str]:
        """The reference numbers the history is showing, in the order it lists them."""
        references: list[str] = []
        for link in self.history_ticket_links():
            for line in link.text.split("\n"):
                token = line.strip()
                if token[:3] in ("INQ", "COM", "JNK") and "-" in token:
                    references.append(token)
                    break
        return references
