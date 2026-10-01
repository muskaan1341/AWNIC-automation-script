"""
Regression tests for bugs already fixed (from the AWNIC Bug Tracking sheet).

FUNC_002 - a user must not be able to edit or deactivate their own account.
FUNC_050 - User Management search must return every match, not only the current page.
Other bugs on the sheet are not here because they are still open or need test data we can't create.
"""

import pytest
from selenium.common.exceptions import TimeoutException

from awnic_qa import users
from awnic_qa.base_test import BaseTest

pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


USER_MANAGEMENT = "/user-management"


class TestFixedBugRegression(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        request.cls.login_class(users.PLATFORM_ADMIN.email)

    def open_user_management(self):
        self.open(USER_MANAGEMENT)
        self.admin.wait_until_loaded()

    def search_and_wait(self, term):
        """Searches, waits until the list changes, and returns the listed emails."""
        # The search runs on the server after a short delay, so wait for the rows to change.
        before = self.admin.get_listed_emails()
        self.admin.search(term)
        try:
            self.wait.until(lambda d: self.admin.get_listed_emails() != before)
        except TimeoutException:
            raise AssertionError(
                f"Searching for {term!r} did not change the list ({len(before)} rows)."
            ) from None
        return self.admin.get_listed_emails()

    def menu_labels_for(self, email):
        """Opens one user's row menu and returns its items."""
        self.admin.search(email)
        self.wait.until(lambda d: self.admin.lists_user(email))
        self.admin.open_user_menu(email)
        self.wait.until(lambda d: self.admin.get_open_menu_labels() != [])
        return self.admin.get_open_menu_labels()

    # ---------- FUNC_002: you cannot edit or deactivate yourself ----------

    @pytest.mark.sanity
    def test_func_002_the_signed_in_user_is_not_offered_edit_on_their_own_row(self):
        """The admin's own row offers no Edit and no Deactivate/Reactivate."""
        self.open_user_management()
        labels = self.menu_labels_for(users.PLATFORM_ADMIN.email)

        assert "Edit" not in labels, (
            f"FUNC_002: Edit must not be offered on your own row. Menu: {labels}"
        )
        assert not any(label in labels for label in ("Deactivate", "Reactivate")), (
            f"FUNC_002: Deactivate/Reactivate must not be offered on your own row. Menu: {labels}"
        )

    def test_func_002_but_the_menu_itself_still_works_and_offers_view(self):
        """The admin's own row menu still opens and offers View (proves the test above is real)."""
        self.open_user_management()
        labels = self.menu_labels_for(users.PLATFORM_ADMIN.email)

        assert "View" in labels, f"The own-row menu should offer View. Menu: {labels}"

    def test_func_002_another_users_row_still_offers_edit_and_deactivate(self):
        """Another user's row still offers Edit and Deactivate/Reactivate."""
        self.open_user_management()
        other = users.CC_INITIATOR_ACCOUNT.email
        labels = self.menu_labels_for(other)

        assert "Edit" in labels, f"Edit should be offered for {other}. Menu: {labels}"
        assert any(label in labels for label in ("Deactivate", "Reactivate")), (
            f"Deactivate/Reactivate should be offered for {other}. Menu: {labels}"
        )

    # ---------- FUNC_050: search returns every match ----------

    def test_func_050_search_returns_every_matching_user_not_just_one(self):
        """A search term matching users on page 1 AND page 2 returns all of them."""
        self.open_user_management()
        first_page = self.admin.get_listed_emails()
        if not self.admin.has_next_page():
            pytest.skip("Every user fits on one page, so this bug cannot be shown here.")
        self.admin.go_to_next_page()
        second_page = self.admin.get_listed_emails()

        term = self._fragment_shared_across(first_page, second_page)
        if term is None:
            pytest.skip("No email fragment is shared by a page-1 and a page-2 user.")

        # The users from pages 1 and 2 whose email (before the @) contains the term.
        expected_set = set()
        for e in first_page + second_page:
            if term in e.split("@")[0].lower():
                expected_set.add(e.lower())
        expected = sorted(expected_set)

        # Search, then read every page of results.
        found = []
        for e in self.search_and_wait(term):
            found.append(e.lower())
        while self.admin.has_next_page():
            self.admin.go_to_next_page()
            for e in self.admin.get_listed_emails():
                found.append(e.lower())

        missing = []
        for e in expected:
            if e not in found:
                missing.append(e)
        assert not missing, (
            f"FUNC_050: {term!r} should return {expected}, but {missing} were missing. "
            f"Returned: {sorted(found)}"
        )

    def test_func_050_search_actually_narrows_the_list(self):
        """Every row returned by a search contains the term in its name or email."""
        self.open_user_management()
        emails = self.admin.get_listed_emails()
        if not emails:
            pytest.skip("No users are listed, so there is nothing to search.")

        term = emails[0].split("@")[0].lower()
        self.search_and_wait(term)

        unrelated = []
        for name, email in self.admin.get_listed_users():
            if term not in name.lower() and term not in email.lower():
                unrelated.append((name, email))
        assert not unrelated, (
            f"These rows do not contain {term!r} in name or email: {unrelated}"
        )

    @staticmethod
    def _fragment_shared_across(first, second):
        """Finds a piece of text (6 down to 3 letters) found in an email from each list."""
        first_locals = []
        for email in first:
            first_locals.append(email.split("@")[0].lower())
        second_locals = []
        for email in second:
            second_locals.append(email.split("@")[0].lower())

        for length in (6, 5, 4, 3):
            for name in first_locals:
                for start in range(len(name) - length + 1):
                    fragment = name[start:start + length]
                    for other in second_locals:
                        if fragment in other:
                            return fragment
        return None
