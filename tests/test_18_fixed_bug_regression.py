"""
REGRESSION COVER FOR BUGS THE TEAM HAS ALREADY FIXED
(AWNIC - Bug Tracking sheet (Functional issue).csv)

WHY ONLY SOME OF THE 55 BUGS ARE IN HERE
A regression test is only worth writing once the fix exists. Writing one for a bug that is
still open produces a permanently red test that everybody learns to ignore, which is worse
than no test at all - so each bug below was CHECKED IN THE APPLICATION CODE first, and only
the ones whose fix is actually present were automated. The bugs left out, and why, are
listed at the bottom of this docstring so the gap is visible rather than silent.

AUTOMATED HERE - fix confirmed in the code:

  FUNC_002  A logged-in user must not be able to edit or deactivate their own profile.
            Fix seen in UserManagementClient.tsx: `const isSelf = (u) => u.email ===
            currentUserEmail`, with both the Edit and the Deactivate/Reactivate menu items
            wrapped in `{!isSelf(u) && ...}`. "View" is deliberately left unconditional.

  FUNC_050  Admin user search returned only one row when several matched, because filtering
            happened client-side on the current page. Fix seen in the same file: search,
            role, team_id and status are now sent to the server as query parameters.

NOT AUTOMATED, and these are deliberate omissions:

  FUNC_011 / FUNC_045  Ticket search. STILL BROKEN - not a judgement from the sheet, but
            measured: all five search tests in test_04_ticket_list.py fail against the
            deployed site today, and they fail identically with this suite's own changes
            reverted, so it is the product and not the harness. Those five tests ARE the
            automation for this bug; they are correctly red and must stay red until it is
            fixed. Nothing to add here.

  FUNC_010, FUNC_017, FUNC_034  Marked Reopen on the sheet, with the reporter's own note
            saying the problem persists ("The actions buttons are still enable"). No fix to
            regress against yet.

  FUNC_008, FUNC_009, FUNC_015, FUNC_023, FUNC_027, FUNC_041, FUNC_043, FUNC_044,
  FUNC_046-049, FUNC_051-054  Blank status on the sheet - not claimed fixed by anyone.

  FUNC_026 (attachment preview), FUNC_039 (duplicate action lock)  Fix CONFIRMED in the code
            (AttachmentPreviewModal.tsx exists; ticket-permissions.ts freezes a ticket held
            pending duplicate review "for everyone - the supervisory override included").
            Not automated only because each needs a specific fixture - a ticket carrying an
            attachment, and a ticket actively held as a duplicate - which cannot be created
            on this environment while writeTestsEnabled is false. Worth adding the moment
            that data exists; the fixes themselves look right.
"""

from __future__ import annotations

import pytest
from selenium.common.exceptions import TimeoutException

from awnic_qa import users
from awnic_qa.base_test import BaseTest

#: Priority from QA/qa-priority-test-matrix.md:
#:   Regression cover for already-fixed bugs — protects P0/P1 behaviour
pytestmark = [pytest.mark.p1, pytest.mark.phase1, pytest.mark.regression]


USER_MANAGEMENT = "/user-management"


class TestFixedBugRegression(BaseTest):
    @pytest.fixture(scope="class", autouse=True)
    def sign_in(self, request, browser):
        # Administration is the admin account's only screen - it holds MANAGE_USERS_ORG_WIDE
        # and no ticket capability at all.
        request.cls.login_class(users.PLATFORM_ADMIN.email)

    def open_user_management(self) -> None:
        self.open(USER_MANAGEMENT)
        self.admin.wait_until_loaded()

    def search_and_wait(self, term: str) -> list[str]:
        """
        Types a search term and waits until the table has actually RESPONDED to it.

        WHY THIS IS NOT JUST search() FOLLOWED BY AN ASSERTION. The search box is debounced
        and then fetched from the SERVER (UserManagementClient.tsx: a setTimeout sets
        `debouncedSearch`, which an effect sends as a query parameter). So for a few hundred
        milliseconds after typing, the table still shows the UNFILTERED list - and asserting
        in that window reads the old rows and reports a product bug that does not exist.
        That is exactly what this helper was written to stop; the first version of the
        FUNC_050 tests failed that way and the failure was mine, not the application's.

        Waiting for the row set to CHANGE - rather than for a fixed delay - is what makes it
        both correct and quick.
        """
        before = self.admin.get_listed_emails()
        self.admin.search(term)
        try:
            self.wait.until(lambda d: self.admin.get_listed_emails() != before)
        except TimeoutException:
            raise AssertionError(
                f"Searching for {term!r} left the list completely unchanged "
                f"({len(before)} rows). Either the search did not run, or it returned "
                "exactly the same people it already showed."
            ) from None
        return self.admin.get_listed_emails()

    def menu_labels_for(self, email: str) -> list[str]:
        """Opens one row's action menu and reads what it offers."""
        self.admin.search(email)
        self.wait.until(lambda d: self.admin.lists_user(email))
        self.admin.open_user_menu(email)
        self.wait.until(lambda d: self.admin.get_open_menu_labels() != [])
        return self.admin.get_open_menu_labels()

    # ==================================================================
    # FUNC_002 - you cannot edit or deactivate yourself
    # ==================================================================

    @pytest.mark.sanity
    def test_func_002_the_signed_in_user_is_not_offered_edit_on_their_own_row(self):
        """
        The bug: a User Management user could open their own row and edit or switch off
        their own account - the classic way to lock the last administrator out of a system.
        """
        self.open_user_management()
        labels = self.menu_labels_for(users.PLATFORM_ADMIN.email)

        assert "Edit" not in labels, (
            "FUNC_002: the signed-in user must not be offered Edit on their own profile. "
            f"Their row menu offers: {labels}"
        )
        assert not any(label in labels for label in ("Deactivate", "Reactivate")), (
            "FUNC_002: the signed-in user must not be able to switch their own account off. "
            f"Their row menu offers: {labels}"
        )

    def test_func_002_but_the_menu_itself_still_works_and_offers_view(self):
        """
        THE CONTROL FOR THE TEST ABOVE, and the reason that one can be trusted.

        "Edit is not in the menu" is also true when the menu never opened, when the search
        found nobody, and when the row has no menu at all - so on its own it proves nothing.
        The fix left "View" deliberately unconditional, so seeing View on the very same menu
        is what distinguishes "correctly withheld" from "nothing rendered".
        """
        self.open_user_management()
        labels = self.menu_labels_for(users.PLATFORM_ADMIN.email)

        assert "View" in labels, (
            "The own-row menu should still open and offer View - without it, the assertion "
            f"that Edit is absent would be meaningless. Menu: {labels}"
        )

    def test_func_002_another_users_row_still_offers_edit_and_deactivate(self):
        """
        The other half of the control: the withholding must be specific to YOURSELF, not a
        menu that lost its items for everybody. A fix that hid Edit from every row would
        pass the first test and break the product.
        """
        self.open_user_management()
        other = users.CC_AGENT.email
        labels = self.menu_labels_for(other)

        assert "Edit" in labels, (
            f"An administrator must still be able to edit somebody else ({other}). "
            f"Menu: {labels}"
        )
        assert any(label in labels for label in ("Deactivate", "Reactivate")), (
            f"An administrator must still be able to switch {other} on or off. "
            f"Menu: {labels}"
        )

    # ==================================================================
    # FUNC_050 - search returns every match, not just one
    # ==================================================================

    def test_func_050_search_returns_every_matching_user_not_just_one(self):
        """
        The bug: searching returned a single row even when several users matched, because
        the filter ran over the current PAGE rather than the whole table.

        WHAT THIS REPLACED: it took a fragment shared by two users on PAGE ONE and checked the
        search returned more than one row. Both matches were already on the current page, so
        the exact bug described above - filtering only what is on screen - would have found
        them both and passed. It could not detect the regression it is named after.

        Now the fragment must be shared by a user on page one AND a user on page two. A
        current-page filter cannot return the page-two user, so the test fails if the bug
        returns. The fragment is still DERIVED FROM THE DATA, so it cannot silently decay into
        a one-match search when the seed data changes. Every page of results is read, since
        the answer can itself run past one page.
        """
        self.open_user_management()
        first_page = self.admin.get_listed_emails()
        if not self.admin.has_next_page():
            pytest.skip(
                "Every user fits on one page, so a search over the current page and a search "
                "over the whole table cannot be told apart here."
            )
        self.admin.go_to_next_page()
        second_page = self.admin.get_listed_emails()

        term = self._fragment_shared_across(first_page, second_page)
        if term is None:
            pytest.skip(
                "No email fragment is shared between a page-one and a page-two user, so this "
                "environment cannot demonstrate a search that reaches past the current page."
            )
        expected = sorted(
            {e.lower() for e in first_page + second_page if term in e.split("@")[0].lower()}
        )

        found = [e.lower() for e in self.search_and_wait(term)]
        while self.admin.has_next_page():
            self.admin.go_to_next_page()
            found += [e.lower() for e in self.admin.get_listed_emails()]

        missing = [e for e in expected if e not in found]
        assert not missing, (
            f"FUNC_050: {term!r} matches {expected} across pages one and two, but the search "
            f"did not return {missing}. Returned: {sorted(found)}"
        )

    def test_func_050_search_actually_narrows_the_list(self):
        """
        The companion to the test above. "Every match came back" would also be satisfied by a
        search that does nothing at all and returns the whole table, so this pins the other
        side: every row that comes back must genuinely match the term.

        "Match" is the SERVER'S rule - the display name OR the email contains the term
        (app/users/repository.py). Checking the email alone, as this used to, would call a
        legitimate name match "unrelated" and fail for a reason that is not a bug.
        """
        self.open_user_management()
        emails = self.admin.get_listed_emails()
        if not emails:
            pytest.skip("No users are listed, so there is nothing to search.")

        term = emails[0].split("@")[0].lower()
        self.search_and_wait(term)

        unrelated = [
            (name, email)
            for name, email in self.admin.get_listed_users()
            if term not in name.lower() and term not in email.lower()
        ]
        assert not unrelated, (
            f"Every row returned for {term!r} should contain it in its name or email. "
            f"These do not: {unrelated}"
        )

    @staticmethod
    def _fragment_shared_across(first: list[str], second: list[str]) -> str | None:
        """
        The longest local-part fragment (6 down to 3 characters) found in at least one
        address from EACH list - so a search for it must reach both pages to be complete.
        """
        first_locals = [email.split("@")[0].lower() for email in first]
        second_locals = [email.split("@")[0].lower() for email in second]
        for length in (6, 5, 4, 3):
            for name in first_locals:
                for start in range(len(name) - length + 1):
                    fragment = name[start : start + length]
                    if any(fragment in other for other in second_locals):
                        return fragment
        return None
