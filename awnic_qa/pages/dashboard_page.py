"""
The dashboard. Two screens share this page object:

  "/"       the ticket dashboard (Total Ticket, Open Cases, High Priority, ...)
  "/admin"  the user-administration dashboard (Total Users, Active Users, ...)

A role that sees only its own work gets four "My ..." tiles instead of the five
organisation tiles.
"""

import re

from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class DashboardPage(BasePage):
    # The five tiles an organisation-wide role sees on "/".
    ORG_KPIS = [
        "Total Ticket",
        "Open Cases",
        "High Priority",
        "Reputational Risk",
        "SLA Breaches",
    ]

    # The four tiles a role that sees only its own work gets instead.
    PERSONAL_KPIS = [
        "My Open Cases",
        "My High Priority",
        "My Reputational Risk",
        "My SLA Breaches",
    ]

    # The four tiles on "/admin". Note "Deactivated", not the old name "Suspended".
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
    def kpi_value(label):
        """
        The locator for a tile's number.
        The label sits in a row; the number is the div right after that row.
        """
        return (
            By.XPATH,
            f"//div[normalize-space()='{label}']/parent::div/following-sibling::div",
        )

    @staticmethod
    def kpi_label(label):
        return (By.XPATH, f"//div[normalize-space()='{label}']")

    # ---------- ACTIONS ----------

    def wait_until_loaded(self):
        """Waits until the ticket dashboard tiles are shown."""
        self.wait.until(
            lambda d: self.exists(self.kpi_label("Total Ticket"))
            or self.exists(self.kpi_label("My Open Cases"))
        )

    def wait_until_admin_loaded(self):
        self.wait_visible(self.kpi_label("Total Users"))

    def click_view_all(self):
        self.click(self.VIEW_ALL_LINK)

    def open_recent_tickets_tab(self, label):
        """Opens one of the Recent Ticket tabs: Enquiry / Complaint / Discarded."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def click_kpi(self, label):
        """Clicks a tile (each tile is a link to its filtered list)."""
        self.click((By.XPATH, f"//a[.//div[normalize-space()='{label}']]"))

    # ---------- CHECKS ----------

    def is_kpi_displayed(self, label):
        return self.exists(self.kpi_label(label))

    def get_kpi_value(self, label):
        """The number on a tile, e.g. get_kpi_value("Total Ticket") -> "15"."""
        return self.wait_visible(self.kpi_value(label)).text

    def get_kpi_number(self, label):
        return int(re.sub(r"\D+", "", self.get_kpi_value(label)))

    def is_kpi_clickable(self, label):
        """True when the tile is a link."""
        return self.exists((By.XPATH, f"//a[.//div[normalize-space()='{label}']]"))

    def get_kpi_href(self, label):
        return self.driver.find_element(
            By.XPATH, f"//a[.//div[normalize-space()='{label}']]"
        ).get_attribute("href")

    def is_recent_tickets_card_displayed(self):
        return self.exists(self.RECENT_TICKETS_CARD)

    def view_all_href(self):
        """Where the "View All" link points."""
        return self.driver.find_element(*self.VIEW_ALL_LINK).get_attribute("href")

    def has_recent_tickets_tab(self, label):
        return self.exists((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def get_greeting(self):
        """The "Good morning, <name>" line."""
        return self.text_of(self.GREETING)

    def is_card_displayed(self, card_title):
        return self.exists((By.XPATH, f"//*[normalize-space()='{card_title}']"))

    def is_recent_activity_card_displayed(self):
        return self.is_card_displayed("Recent Activity")
