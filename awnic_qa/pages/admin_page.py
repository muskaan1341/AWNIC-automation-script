"""
The people-and-permissions screens:

  /user-management     the full user list (platform administrator)
  /role-management     the read-only role matrix
  /access-management   the same two screens as tabs, for a Head of Department
                       (limited to their own department)
  /admin/activity      the activity log
"""

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class AdminPage(BasePage):
    # How many times to re-read the table if it redraws while we read it.
    STALE_READ_ATTEMPTS = 3

    # The four tiles above the user list.
    USER_KPIS = ["Total Users", "Active Users", "Pending Invitation", "Deactivated Users"]

    # The columns of the user table.
    USER_COLUMNS = ["Name", "Email", "Role", "Team", "Status"]

    HEADING = (By.TAG_NAME, "h1")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    COLUMN_HEADERS = (By.CSS_SELECTOR, "table thead th")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder^='Search by name']")
    ADD_USER_BUTTON = (By.XPATH, "//button[normalize-space()='Add User']")
    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")
    MENU_ITEMS = (By.CSS_SELECTOR, "[role='menu'] [role='menuitem']")
    NEXT_PAGE = (By.CSS_SELECTOR, "button[aria-label='Next page']")

    # The Add User form fields.
    NAME_FIELD = (By.ID, "add-user-name")
    EMAIL_FIELD = (By.ID, "add-user-email")
    ROLE_FIELD = (By.ID, "add-user-role")
    TEAM_FIELD = (By.ID, "add-user-team")

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self):
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text):
        self.type_into(self.SEARCH_INPUT, text)

    def tab_labels(self):
        """The tabs on Access Management, left to right."""
        labels = []
        for text in self.texts_of((By.CSS_SELECTOR, "[role='tab']")):
            if text:
                labels.append(text)
        return labels

    def open_tab(self, label):
        """Switches tab on Access Management ("Users Management" / "Roles Management")."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def open_add_user_form(self):
        self.click(self.ADD_USER_BUTTON)
        self.wait_visible(self.MODAL)

    def fill_new_user(self, name, email):
        self.type_into(self.NAME_FIELD, name)
        self.type_into(self.EMAIL_FIELD, email)

    def choose_role(self, role_label):
        self.select_native(self.ROLE_FIELD, role_label)

    def submit_new_user(self):
        self.click_button("Create User")

    def cancel_modal(self):
        self.click_button("Cancel")
        self.wait_gone(self.MODAL)

    def open_user_menu(self, email):
        """Opens one user's row menu (Edit / Deactivate)."""
        self.click((By.CSS_SELECTOR, f"button[aria-label='Actions for {email}']"))

    def filter_by_role(self, role_label):
        self.select_native((By.XPATH, "(//select)[1]"), role_label)

    def get_open_menu_labels(self):
        """Every item in the currently open row menu."""
        labels = []
        for text in self.texts_of(self.MENU_ITEMS):
            if text:
                labels.append(text)
        return labels

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self):
        return self.wait_visible(self.HEADING).text

    def get_row_count(self):
        return self.count(self.TABLE_ROWS)

    def get_column_headers(self):
        headers = []
        for header in self.texts_of(self.COLUMN_HEADERS):
            if header:
                headers.append(header)
        return headers

    def is_kpi_displayed(self, label):
        return self.exists((By.XPATH, f"//div[normalize-space()='{label}']"))

    def has_add_user_button(self):
        return self.exists(self.ADD_USER_BUTTON)

    def is_modal_open(self):
        return self.exists(self.MODAL)

    def get_modal_title(self):
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def is_create_user_enabled(self):
        """True when "Create User" is enabled (it is disabled until the form is valid)."""
        return self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Create User']"
        ).is_enabled()

    def get_assignable_roles(self):
        """The roles in the Role dropdown (a custom dropdown, not a native <select>)."""
        return self.read_dropdown_options(self.ROLE_FIELD)

    def new_user_email_fails_the_browsers_email_check(self):
        """
        True when the browser says the Work Email value is not a valid email.
        Checked without pressing Create User, so no real account is created.
        """
        return bool(
            self.driver.execute_script(
                "return arguments[0].validity.typeMismatch;",
                self.driver.find_element(*self.EMAIL_FIELD),
            )
        )

    def has_team_field(self):
        return self.exists(self.TEAM_FIELD)

    def get_listed_emails(self):
        """The email addresses in the table. Re-reads the rows if the table redraws mid-read."""
        for _ in range(self.STALE_READ_ATTEMPTS):
            try:
                emails = []
                for row in self.driver.find_elements(*self.TABLE_ROWS):
                    for cell in row.text.split("\n"):
                        if "@" in cell:
                            emails.append(cell.strip())
                            break
                return emails
            except StaleElementReferenceException:
                continue
        return []

    def get_listed_users(self):
        """(name, email) for every listed user, read from the Name and Email columns."""
        headers = self.texts_of(self.COLUMN_HEADERS)
        name_at = headers.index("Name")
        email_at = headers.index("Email")
        listed = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > max(name_at, email_at):
                listed.append((cells[name_at].text.strip(), cells[email_at].text.strip()))
        return listed

    def has_next_page(self):
        """True when the table has another page after this one."""
        buttons = self.driver.find_elements(*self.NEXT_PAGE)
        return bool(buttons) and buttons[0].is_enabled()

    def go_to_next_page(self):
        """Goes to the next page and waits until the rows change."""
        before = self.get_listed_emails()
        self.click(self.NEXT_PAGE)
        self.wait.until(lambda d: self.get_listed_emails() != before)

    # ---- /role-management: the "Ticket Export Access" matrix ----

    _EXPORT_ACCESS_CARD = (
        "//h3[normalize-space()='Ticket Export Access']/ancestor::div[contains(@class,'rounded-lg')][1]"
    )
    # Shown under the matrix to anyone who is not allowed to edit it.
    EXPORT_VIEW_ONLY_NOTE = (
        By.XPATH,
        "//p[contains(normalize-space(.),'View-only — editing requires an administrator.')]",
    )

    def export_access_checkboxes(self):
        """The matrix checkboxes, once the card is on screen."""
        self.wait_visible((By.XPATH, "//h3[normalize-space()='Ticket Export Access']"))
        return self.driver.find_elements(
            By.XPATH, self._EXPORT_ACCESS_CARD + "//input[@type='checkbox']"
        )

    def export_access_is_view_only(self):
        return self.exists(self.EXPORT_VIEW_ONLY_NOTE)

    def lists_user(self, email):
        """True when this user appears anywhere in the list."""
        return self.exists((By.XPATH, f"//td[contains(normalize-space(.),'{email}')]"))

    # ---- the role matrix (read-only) ----

    def shows_view_only_notice(self):
        return self.exists(self.innermost_containing("View-only access"))

    def get_role_matrix_columns(self):
        """The matrix column headings (the role names)."""
        return self.get_column_headers()

    def matrix_has_row(self, module_name):
        return self.exists((By.XPATH, f"//td[normalize-space()='{module_name}']"))

    # ---- the activity log ----

    def has_activity_rows(self):
        return self.get_row_count() > 0

    # The read-only drawer a click on an Activity Log row opens.
    DRAWER = (By.CSS_SELECTOR, "div[role='dialog']")
    DRAWER_TITLE = "Activity detail"
    DRAWER_CLOSE = (By.CSS_SELECTOR, "div[role='dialog'] button[aria-label='Close']")
    # The small uppercase labels in the drawer (Action, When, User, ...).
    DRAWER_LABELS = (By.XPATH, "//div[@role='dialog']//div[contains(@class,'uppercase')]")

    def activity_cell(self, row_number, column):
        """The full text (textContent) of one Activity Log cell. Row 1 is the top row."""
        headers = self.texts_of(self.COLUMN_HEADERS)
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_number - 1]
        cell = row.find_elements(By.TAG_NAME, "td")[headers.index(column)]
        return (cell.get_attribute("textContent") or "").strip()

    def open_activity_row(self, row_number):
        """Clicks an Activity Log row and waits for the detail drawer."""
        row = self.driver.find_elements(*self.TABLE_ROWS)[row_number - 1]
        self.scroll_to_middle(row)
        row.click()
        self.wait_visible(self.DRAWER)

    def drawer_title(self):
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def drawer_labels(self):
        """The field labels in the drawer, top to bottom."""
        labels = []
        for element in self.driver.find_elements(*self.DRAWER_LABELS):
            labels.append((element.get_attribute("textContent") or "").strip())
        return labels

    def drawer_text(self):
        return (self.driver.find_element(*self.DRAWER).get_attribute("textContent") or "").strip()

    def drawer_has_button(self, text):
        return self.exists((By.XPATH, f"//div[@role='dialog']//button[normalize-space()='{text}']"))

    def close_drawer(self):
        self.click(self.DRAWER_CLOSE)
        self.wait_gone(self.DRAWER)

    # ---- /admin/settings: System Settings > Ticket Numbering (read only here) ----

    SETTINGS_HEADING = "System Settings"
    # The app's error screen, shown when a page fails to load.
    ERROR_SCREEN = (By.XPATH, "//*[normalize-space(text())='Something went wrong']")
    NUMBERING_ROWS = (
        By.XPATH, "//h2[normalize-space()='Ticket Numbering']/following-sibling::div[1]/div"
    )

    def shows_error_screen(self):
        return self.exists(self.ERROR_SCREEN)

    def wait_for_settings(self):
        """Waits for the Ticket Numbering rows, or for the error screen."""
        self.wait.until(lambda d: self.exists(self.NUMBERING_ROWS) or self.shows_error_screen())

    def numbering_rows(self):
        """
        One dict per numbering series, read from the screen (the Edit button is never pressed):
        {"type": "Complaint", "prefix": "COM", "year": "2026", "starts": "1", "current": "12",
         "next": "COM-2026-0013"}
        """
        rows = []
        for row in self.driver.find_elements(*self.NUMBERING_ROWS):
            line = row.find_element(By.XPATH, "./div")
            parts = line.find_elements(By.XPATH, "./*")
            next_text = line.find_element(By.XPATH, ".//span[span[normalize-space(.)='Next']]")
            rows.append({
                "type": parts[0].text.strip(),
                "prefix": parts[1].text.strip(),
                "year": self._fact(line, "Year"),
                "starts": self._fact(line, "Starts at"),
                "current": self._fact(line, "Current"),
                "next": (next_text.get_attribute("textContent") or "").replace("Next", "", 1).strip(),
            })
        return rows

    @staticmethod
    def _fact(line, name):
        """The number next to a small label such as "Year" or "Current"."""
        value = line.find_element(By.XPATH, f".//span[span[normalize-space(.)='{name}']]/span[2]")
        return value.text.strip()

    # ---- the user list: status ----

    STATUS_FILTER = (By.CSS_SELECTOR, "button[aria-label='Filter by status']")

    def kpi_number(self, label):
        """The number on one of the four tiles above the user list, e.g. kpi_number("Deactivated Users")."""
        tile = self.wait_visible((By.CSS_SELECTOR, f"[data-testid='user-stat-{label}']"))
        digits = ""
        for character in tile.text.replace(label, ""):
            if character.isdigit():
                digits += character
        return int(digits)

    def filter_by_status(self, status_label):
        """Picks a value in the "Filter by status" dropdown (a filter only - nothing is changed)."""
        self.choose_option(self.STATUS_FILTER, status_label)

    def listed_statuses(self):
        """The Status column of every listed user."""
        headers = self.texts_of(self.COLUMN_HEADERS)
        status_at = headers.index("Status")
        statuses = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > status_at:
                statuses.append(cells[status_at].text.strip())
        return statuses
