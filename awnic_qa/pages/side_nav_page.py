"""
The left-hand menu (the <aside> element), present on every signed-in page.

What appears here depends entirely on the signed-in user's role, so this page object is
mostly used to check that a role is offered only what its job needs.

THE MENU HAS THREE SHAPES, not one:
  - a role that can configure things (Head of Department, Complaints Manager) gets a
    collapsible "Tickets" GROUP holding Enquiries / Complaints / Discarded Tickets,
  - a role that sees several ticket types but configures nothing (CC Agent, Supervisor)
    gets FLAT entries labelled "Enquiries Tickets" / "Complaint Tickets" / "Discarded
    Tickets",
  - a role that sees exactly one type (Complaint Handler) gets a single "Tickets" link.

And nothing is greyed out any more. "Teams & SLA" used to be the one disabled entry and
is now a working page, so the expected count of disabled items is ZERO.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage, Locator


class SideNavPage(BasePage):
    SIDE_NAV = (By.TAG_NAME, "aside")
    DISABLED_ITEMS = (By.CSS_SELECTOR, "aside [aria-disabled='true']")
    NAV_LINKS = (By.CSS_SELECTOR, "aside nav a, aside nav button")
    TICKETS_GROUP_TOGGLE = (
        By.XPATH,
        "//aside//button[.//span[normalize-space()='Tickets']]",
    )

    @staticmethod
    def nav_item(label: str) -> Locator:
        """
        A menu entry whose visible text is exactly this label.
        Some entries are links wrapping a <span>, others are plain links, so this matches on
        TEXT rather than on the tag name.
        """
        return (By.XPATH, f"//aside//*[normalize-space(text())='{label}']")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.SIDE_NAV)
        # The menu's SHAPE comes from the signed-in user's permissions, which the browser
        # fetches after the first paint. Until they arrive the menu renders its
        # permission-less shape, so reading it too early reports the wrong one. Wait until
        # some ticket entry exists - by then the permissions have landed.
        self.wait.until(
            lambda d: self.has_tickets_group()
            or self.has_item("Tickets")
            or self.has_item("Enquiries Tickets")
            or self.has_item("Complaint Tickets")
            or self.has_no_ticket_queues()
        )

    def click_item(self, label: str) -> None:
        self.click(self.nav_item(label))

    def toggle_tickets_group(self) -> None:
        # Scroll first: on a short window the group header can sit below the fold, and a
        # click on an off-screen element is refused rather than scrolled to.
        self.scroll_to_middle(self.wait_visible(self.TICKETS_GROUP_TOGGLE))
        self.click(self.TICKETS_GROUP_TOGGLE)

    # ---------- CHECKS ----------

    def has_item(self, label: str) -> bool:
        """True if this role is offered the menu entry at all."""
        return self.exists(self.nav_item(label))

    def has_tickets_group(self) -> bool:
        """The collapsible "Tickets" group, shown only to the configuration tier."""
        return self.exists(self.TICKETS_GROUP_TOGGLE)

    def is_tickets_group_expanded(self) -> bool:
        toggles = self.driver.find_elements(*self.TICKETS_GROUP_TOGGLE)
        return bool(toggles) and toggles[0].get_attribute("aria-expanded") == "true"

    def disabled_item_count(self) -> int:
        """
        How many menu entries are greyed out.

        Kept as a sweep rather than a check on one named item: the app used to grey out
        "Teams & SLA" and no longer does, so the expected number is now zero. A sweep catches
        a regression whatever the item happens to be called.
        """
        return self.count(self.DISABLED_ITEMS)

    def disabled_item_labels(self) -> list[str]:
        return self.texts_of(self.DISABLED_ITEMS)

    def all_item_labels(self) -> list[str]:
        """Every entry in the menu, top to bottom - handy for "what does this role see?"."""
        return [text for text in self.texts_of(self.NAV_LINKS) if text]

    def dashboard_href(self) -> str:
        """Where the Dashboard entry points: "/admin" for a pure administrator, "/" otherwise."""
        return self.driver.find_element(
            By.XPATH, "//aside//a[.//span[normalize-space()='Dashboard']]"
        ).get_attribute("href")

    def has_no_ticket_queues(self) -> bool:
        """True when the menu offers no ticket queue of any kind."""
        return not (
            self.has_item("Enquiries Tickets")
            or self.has_item("Complaint Tickets")
            or self.has_item("Discarded Tickets")
            or self.has_item("Tickets")
        )
