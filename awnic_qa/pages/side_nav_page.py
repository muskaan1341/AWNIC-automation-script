"""
The left-hand menu (the <aside> element) on every signed-in page.
Which items appear depends on the signed-in user's role.

The menu has three shapes:
  - Head of Department / Complaints Manager: a collapsible "Tickets" group
  - CC Agent / Supervisor: flat items "Enquiries Tickets", "Complaint Tickets", "Discarded Tickets"
  - Complaint Handler: a single "Tickets" link
No item is greyed out any more, so the expected number of disabled items is zero.
"""

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class SideNavPage(BasePage):
    SIDE_NAV = (By.TAG_NAME, "aside")
    DISABLED_ITEMS = (By.CSS_SELECTOR, "aside [aria-disabled='true']")
    NAV_LINKS = (By.CSS_SELECTOR, "aside nav a, aside nav button")
    TICKETS_GROUP_TOGGLE = (
        By.XPATH,
        "//aside//button[.//span[normalize-space()='Tickets']]",
    )

    @staticmethod
    def nav_item(label):
        """A menu item whose visible text is exactly this label."""
        return (By.XPATH, f"//aside//*[normalize-space(text())='{label}']")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self):
        self.wait_visible(self.SIDE_NAV)
        # The menu changes shape once the user's permissions load, so wait for a ticket item.
        self.wait.until(
            lambda d: self.has_tickets_group()
            or self.has_item("Tickets")
            or self.has_item("Enquiries Tickets")
            or self.has_item("Complaint Tickets")
            or self.has_no_ticket_queues()
        )

    def click_item(self, label):
        self.click(self.nav_item(label))

    def toggle_tickets_group(self):
        # Scroll first - on a short window the group can be below the fold.
        self.scroll_to_middle(self.wait_visible(self.TICKETS_GROUP_TOGGLE))
        self.click(self.TICKETS_GROUP_TOGGLE)

    # ---------- CHECKS ----------

    def has_item(self, label):
        return self.exists(self.nav_item(label))

    def has_tickets_group(self):
        """True when the collapsible "Tickets" group is shown."""
        return self.exists(self.TICKETS_GROUP_TOGGLE)

    def is_tickets_group_expanded(self):
        toggles = self.driver.find_elements(*self.TICKETS_GROUP_TOGGLE)
        return bool(toggles) and toggles[0].get_attribute("aria-expanded") == "true"

    def disabled_item_count(self):
        """How many menu items are greyed out (expected: zero)."""
        return self.count(self.DISABLED_ITEMS)

    def disabled_item_labels(self):
        return self.texts_of(self.DISABLED_ITEMS)

    def all_item_labels(self):
        """Every item in the menu, top to bottom."""
        labels = []
        for text in self.texts_of(self.NAV_LINKS):
            if text:
                labels.append(text)
        return labels

    def dashboard_href(self):
        """Where the Dashboard item points: "/admin" for a pure administrator, "/" otherwise."""
        return self.driver.find_element(
            By.XPATH, "//aside//a[.//span[normalize-space()='Dashboard']]"
        ).get_attribute("href")

    def has_no_ticket_queues(self):
        """True when the menu has no ticket item of any kind."""
        return not (
            self.has_item("Enquiries Tickets")
            or self.has_item("Complaint Tickets")
            or self.has_item("Discarded Tickets")
            or self.has_item("Tickets")
        )
