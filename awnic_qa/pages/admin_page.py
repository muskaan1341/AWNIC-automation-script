"""
The people-and-permissions screens. Three of them share this page object because they are
built from the same two components:

  /user-management     the full user list  (platform administrator, organisation-wide)
  /role-management     the read-only role matrix - what each role is allowed to do
  /access-management   the SAME two screens as tabs, for a Head of Department, who can only
                       manage people inside their OWN department
  /admin/activity      the activity log - every user change, with who did it and when

That last point is the important one for testing: the head of department reaches the same
user list through a different door, and the department limit is enforced by the server, not
by the screen. Hiding a button is never protection on its own.
"""

from __future__ import annotations

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from awnic_qa.pages.base_page import BasePage


class AdminPage(BasePage):
    #: How many times a row read may be retried when the table redraws mid-read.
    STALE_READ_ATTEMPTS = 3

    #: The four tiles above the user list.
    USER_KPIS = ["Total Users", "Active Users", "Pending Invitation", "Deactivated Users"]

    #: The columns of the user table.
    USER_COLUMNS = ["Name", "Email", "Role", "Team", "Status"]

    HEADING = (By.TAG_NAME, "h1")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    COLUMN_HEADERS = (By.CSS_SELECTOR, "table thead th")
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[placeholder^='Search by name']")
    ADD_USER_BUTTON = (By.XPATH, "//button[normalize-space()='Add User']")
    MODAL = (By.CSS_SELECTOR, "div[role='dialog']")
    MENU_ITEMS = (By.CSS_SELECTOR, "[role='menu'] [role='menuitem']")
    NEXT_PAGE = (By.CSS_SELECTOR, "button[aria-label='Next page']")

    # The Add User form gives every field a real id - the best kind of locator.
    NAME_FIELD = (By.ID, "add-user-name")
    EMAIL_FIELD = (By.ID, "add-user-email")
    ROLE_FIELD = (By.ID, "add-user-role")
    TEAM_FIELD = (By.ID, "add-user-team")

    # ==================================================================
    # Actions
    # ==================================================================

    def wait_until_loaded(self) -> None:
        self.wait_visible(self.HEADING)
        self.wait.until(lambda d: self.exists((By.TAG_NAME, "table")))

    def search(self, text: str) -> None:
        self.type_into(self.SEARCH_INPUT, text)

    def tab_labels(self) -> list[str]:
        """The tabs Access Management offers, left to right."""
        return [text for text in self.texts_of((By.CSS_SELECTOR, "[role='tab']")) if text]

    def open_tab(self, label: str) -> None:
        """Switches tab on Access Management ("Users Management" / "Roles Management")."""
        self.click((By.XPATH, f"//*[@role='tab'][normalize-space()='{label}']"))

    def open_add_user_form(self) -> None:
        self.click(self.ADD_USER_BUTTON)
        self.wait_visible(self.MODAL)

    def fill_new_user(self, name: str, email: str) -> None:
        self.type_into(self.NAME_FIELD, name)
        self.type_into(self.EMAIL_FIELD, email)

    def choose_role(self, role_label: str) -> None:
        self.select_native(self.ROLE_FIELD, role_label)

    def submit_new_user(self) -> None:
        self.click_button("Create User")

    def cancel_modal(self) -> None:
        self.click_button("Cancel")
        self.wait_gone(self.MODAL)

    def open_user_menu(self, email: str) -> None:
        """Opens one user's row menu, where Edit / Deactivate live."""
        self.click((By.CSS_SELECTOR, f"button[aria-label='Actions for {email}']"))

    def filter_by_role(self, role_label: str) -> None:
        self.select_native((By.XPATH, "(//select)[1]"), role_label)

    def get_open_menu_labels(self) -> list[str]:
        """
        Everything the currently-open row menu offers.

        The menu is built from the shared Menu component, which is ARIA-correct - the panel
        is role="menu" and each entry role="menuitem" - so this needs no class names and
        survives restyling.
        """
        return [text for text in self.texts_of(self.MENU_ITEMS) if text]

    # ==================================================================
    # Checks
    # ==================================================================

    def get_heading(self) -> str:
        return self.wait_visible(self.HEADING).text

    def get_row_count(self) -> int:
        return self.count(self.TABLE_ROWS)

    def get_column_headers(self) -> list[str]:
        return [header for header in self.texts_of(self.COLUMN_HEADERS) if header]

    def is_kpi_displayed(self, label: str) -> bool:
        return self.exists((By.XPATH, f"//div[normalize-space()='{label}']"))

    def has_add_user_button(self) -> bool:
        return self.exists(self.ADD_USER_BUTTON)

    def is_modal_open(self) -> bool:
        return self.exists(self.MODAL)

    def get_modal_title(self) -> str:
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] h2"))

    def is_create_user_enabled(self) -> bool:
        """True when "Create User" is usable. It is disabled until the form is valid."""
        return self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Create User']"
        ).is_enabled()

    def get_assignable_roles(self) -> list[str]:
        """
        The roles this signed-in administrator is allowed to hand out.

        The Role field is a CustomSelect (AddUserModal.tsx), a <button> with a portaled option
        list - NOT a native <select>. Reading it with Selenium's Select class, as this used to,
        raises on the button, so the dropdown's options are read the CustomSelect way.
        """
        return self.read_dropdown_options(self.ROLE_FIELD)

    def new_user_email_fails_the_browsers_email_check(self) -> bool:
        """
        True when the browser itself judges the Work Email box's value not to be an email.

        The box is <input type="email" required>, and that check is the ONLY thing standing
        between a malformed address and the create request - there is no app-level email
        rule on this form. Asking the input's own validity (typeMismatch) proves the guard
        without pressing Create User, which on a working form would create a real account.
        """
        return bool(
            self.driver.execute_script(
                "return arguments[0].validity.typeMismatch;",
                self.driver.find_element(*self.EMAIL_FIELD),
            )
        )

    def has_team_field(self) -> bool:
        return self.exists(self.TEAM_FIELD)

    def get_listed_emails(self) -> list[str]:
        """
        The email addresses currently listed, so a scope test can prove what is visible.

        RE-FINDS THE ROWS IF THE TABLE REDRAWS UNDER IT. Selenium locates the rows, then reads
        each one in a separate round trip; paging or a search landing in between replaces
        those rows and the read raises StaleElementReferenceException - which is what ended
        the FUNC_050 paging loop. Re-finding is the fix; the rows are simply read again from
        the table as it now stands.
        """
        for _ in range(self.STALE_READ_ATTEMPTS):
            try:
                emails: list[str] = []
                for row in self.driver.find_elements(*self.TABLE_ROWS):
                    for cell in row.text.split("\n"):
                        if "@" in cell:
                            emails.append(cell.strip())
                            break
                return emails
            except StaleElementReferenceException:
                continue
        return []

    def get_listed_users(self) -> list[tuple[str, str]]:
        """
        (name, email) for every listed user, read from the Name and Email COLUMNS.

        The server's user search matches the display name OR the email
        (app/users/repository.py), so a test judging search results needs both - reading
        the email alone would call a legitimate name match "unrelated".
        """
        headers = self.texts_of(self.COLUMN_HEADERS)
        name_at, email_at = headers.index("Name"), headers.index("Email")
        listed: list[tuple[str, str]] = []
        for row in self.driver.find_elements(*self.TABLE_ROWS):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > max(name_at, email_at):
                listed.append((cells[name_at].text.strip(), cells[email_at].text.strip()))
        return listed

    def has_next_page(self) -> bool:
        """True when the user table's pager has a page after this one."""
        buttons = self.driver.find_elements(*self.NEXT_PAGE)
        return bool(buttons) and buttons[0].is_enabled()

    def go_to_next_page(self) -> None:
        """Moves the user table on one page and waits for the rows to actually change."""
        before = self.get_listed_emails()
        self.click(self.NEXT_PAGE)
        self.wait.until(lambda d: self.get_listed_emails() != before)

    # ---- /role-management: the "Ticket Export Access" matrix (RoleExportAccessMatrix.tsx) ----

    _EXPORT_ACCESS_CARD = (
        "//h3[normalize-space()='Ticket Export Access']/ancestor::div[contains(@class,'rounded-lg')][1]"
    )
    #: role-management/page.tsx appends this to the matrix description for anyone without
    #: MANAGE_USERS_ORG_WIDE. It is a second text node in the <p>, hence contains().
    EXPORT_VIEW_ONLY_NOTE = (
        By.XPATH,
        "//p[contains(normalize-space(.),'View-only — editing requires an administrator.')]",
    )

    def export_access_checkboxes(self) -> list:
        """The matrix's checkboxes (one per role x export tier), once the card has rendered."""
        self.wait_visible((By.XPATH, "//h3[normalize-space()='Ticket Export Access']"))
        return self.driver.find_elements(
            By.XPATH, self._EXPORT_ACCESS_CARD + "//input[@type='checkbox']"
        )

    def export_access_is_view_only(self) -> bool:
        return self.exists(self.EXPORT_VIEW_ONLY_NOTE)

    def lists_user(self, email: str) -> bool:
        """True when a named user appears anywhere in the list."""
        return self.exists((By.XPATH, f"//td[contains(normalize-space(.),'{email}')]"))

    # ---- the role matrix (read-only) ----

    def shows_view_only_notice(self) -> bool:
        """The role matrix's own "you can look but not change" notice."""
        return self.exists(self.innermost_containing("View-only access"))

    def get_role_matrix_columns(self) -> list[str]:
        """The matrix column headings, which are the role names."""
        return self.get_column_headers()

    def matrix_has_row(self, module_name: str) -> bool:
        return self.exists((By.XPATH, f"//td[normalize-space()='{module_name}']"))

    # ---- the activity log ----

    def has_activity_rows(self) -> bool:
        return self.get_row_count() > 0
