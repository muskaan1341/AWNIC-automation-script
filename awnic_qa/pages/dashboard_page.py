"""
The dashboard. TWO of them share this one page object, because the KPI tile is the same
component on both screens:

  "/"       the operational ticket dashboard - Total Ticket, Open Cases, High Priority,
            Reputational Risk, SLA Breaches. Everyone with a ticket-view right lands here.

  "/admin"  the user-administration dashboard - Total Users, Active Users,
            Pending Invitation, Deactivated Users. A pure administrator, who has no ticket
            rights at all, is redirected here from "/".

NOTE the fourth admin tile is "Deactivated Users". It used to be called "Suspended Users";
the whole application was renamed, so an old test asserting "Suspended" fails for the wrong
reason.

PERSONAL vs ORGANISATION LABELS: a role that only sees its own work (a complaint handler, a
department contact) gets four tiles prefixed "My …" instead of the five organisation tiles.
That is intentional, so never assert "always five tiles" for every role.
"""

from __future__ import annotations

import re

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage, Locator


class DashboardPage(BasePage):
    #: The five tiles an organisation-wide role sees on "/".
    ORG_KPIS = [
        "Total Ticket",
        "Open Cases",
        "High Priority",
        "Reputational Risk",
        "SLA Breaches",
    ]

    #: The four tiles a personal-queue role sees instead.
    PERSONAL_KPIS = [
        "My Open Cases",
        "My High Priority",
        "My Reputational Risk",
        "My SLA Breaches",
    ]

    #: The four tiles on "/admin". Note "Deactivated", not "Suspended".
    ADMIN_KPIS = [
        "Total Users",
        "Active Users",
        "Pending Invitation",
        "Deactivated Users",
    ]

    RECENT_TICKETS_CARD = (By.XPATH, "//*[normalize-space()='Recent Ticket']")
    VIEW_ALL_LINK = (By.XPATH, "//a[normalize-space()='View All']")
    GREETING = (By.TAG_NAME, "h1")

    @staticmethod
    def kpi_value(label: str) -> Locator:
        """
        The locator for one KPI tile's NUMBER.

        A tile is laid out like this:
          <div>                        the card
            <div>                      a row holding the label and the icon
              <div>Total Ticket</div>  the label
              <div>icon</div>
            </div>
            <div>12</div>              the value we want
          </div>

        So: find the label, step UP to its row, then take the row's NEXT sibling.
        """
        return (
            By.XPATH,
            f"//div[normalize-space()='{label}']/parent::div/following-sibling::div",
        )

    @staticmethod
    def kpi_label(label: str) -> Locator:
        return (By.XPATH, f"//div[normalize-space()='{label}']")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self) -> None:
        """Waits until the ticket dashboard has really rendered before anything is asserted."""
        self.wait.until(
            lambda d: self.exists(self.kpi_label("Total Ticket"))
            or self.exists(self.kpi_label("My Open Cases"))
        )

    def wait_until_admin_loaded(self) -> None:
        self.wait_visible(self.kpi_label("Total Users"))

    def click_view_all(self) -> None:
        self.click(self.VIEW_ALL_LINK)

    def open_recent_tickets_tab(self, label: str) -> None:
        """The Recent Ticket card's own tabs: Enquiry / Complaint / Discarded."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def click_kpi(self, label: str) -> None:
        """Clicks a KPI tile - the whole tile is a link that drills into its filtered list."""
        self.click((By.XPATH, f"//a[.//div[normalize-space()='{label}']]"))

    # ---------- CHECKS ----------

    def is_kpi_displayed(self, label: str) -> bool:
        return self.exists(self.kpi_label(label))

    def get_kpi_value(self, label: str) -> str:
        """The number on a tile, e.g. get_kpi_value("Total Ticket") -> "15"."""
        return self.wait_visible(self.kpi_value(label)).text

    def get_kpi_number(self, label: str) -> int:
        return int(re.sub(r"\D+", "", self.get_kpi_value(label)))

    def is_kpi_clickable(self, label: str) -> bool:
        """True when the tile is a clickable drill-down link rather than a plain box."""
        return self.exists((By.XPATH, f"//a[.//div[normalize-space()='{label}']]"))

    def get_kpi_href(self, label: str) -> str:
        return self.driver.find_element(
            By.XPATH, f"//a[.//div[normalize-space()='{label}']]"
        ).get_attribute("href")

    def is_recent_tickets_card_displayed(self) -> bool:
        return self.exists(self.RECENT_TICKETS_CARD)

    def view_all_href(self) -> str:
        """Where "View All" points. Must be a real list, never the retired "/tickets" route."""
        return self.driver.find_element(*self.VIEW_ALL_LINK).get_attribute("href")

    def has_recent_tickets_tab(self, label: str) -> bool:
        return self.exists((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def get_greeting(self) -> str:
        """The "Good morning, <name>" line - proves the page knows who is signed in."""
        return self.text_of(self.GREETING)

    def is_card_displayed(self, card_title: str) -> bool:
        return self.exists((By.XPATH, f"//*[normalize-space()='{card_title}']"))

    def is_recent_activity_card_displayed(self) -> bool:
        return self.is_card_displayed("Recent Activity")
