"""Modules 1-3: Login and Access, Users/Roles/Permissions, Email Intake."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, NOT_BUILT, PARTLY
from common import Case, Module

ADMIN = "System Administrator"
HOD = "Head of Department"
MANAGER = "Manager"
SUPERVISOR = "Customer Care Supervisor"
AGENT = "Customer Care Agent"
HANDLER = "Complaint Handler"
POC = "Department Contact Person"
COMPLIANCE = "Compliance Officer"
ANY = "Any signed-in staff member"

# =====================================================================================
M01 = Module(
    code="M01",
    name="Login and Access",
    plain_summary=(
        "Staff sign in with their existing AWNIC company account. There is no separate "
        "username and password for this platform. Covers signing in, staying signed in, "
        "signing out, and being blocked when not signed in."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Signing in",
            title="A staff member can sign in with their AWNIC company account",
            pre="You have a valid AWNIC account. You are not currently signed in.",
            steps=[
                "Open the platform address in a fresh browser window.",
                "You are shown the sign-in screen. Click the AWNIC sign-in button.",
                "Enter your normal AWNIC work credentials on the AWNIC sign-in page.",
                "Wait for the platform to load.",
            ],
            expected=(
                "You are signed in and taken to your home dashboard. You are never asked to "
                "create or type a separate password for this platform. Your name appears in "
                "the top corner of the screen."
            ),
            priority=CRITICAL, uat=True, role=ANY, req="R38",
        ),
        Case(
            area="Landing page",
            title="After signing in you land on the screen that suits your job",
            pre="You have accounts for at least two different roles available.",
            steps=[
                "Sign in as a Customer Care Agent and note which screen opens first.",
                "Sign out completely.",
                "Sign in as a System Administrator and note which screen opens first.",
            ],
            expected=(
                "The Customer Care Agent lands on the ticket dashboard. The System "
                "Administrator lands on the Admin screen. Neither one sees an empty page or "
                "an error."
            ),
            priority=HIGH, uat=True, role="Agent, then Administrator", req="R39",
        ),
        Case(
            area="Staying signed in",
            title="You stay signed in while you keep working",
            pre="You are signed in.",
            steps=[
                "Sign in and open a ticket.",
                "Keep using the system normally for about 20 minutes - open tickets, run a "
                "search, open a report.",
                "Refresh the browser page.",
            ],
            expected=(
                "You are still signed in throughout. You are never thrown back to the "
                "sign-in screen in the middle of your work."
            ),
            priority=HIGH, uat=True, role=ANY,
        ),
        Case(
            area="Staying signed in",
            title="The session renews itself quietly in the background",
            pre="You are signed in and have been idle for a while.",
            steps=[
                "Sign in.",
                "Leave the browser tab open and untouched for longer than the short session "
                "window (ask the team for the exact number, roughly 15-30 minutes).",
                "Come back and click on any menu item.",
            ],
            expected=(
                "The page loads normally. You are not asked to sign in again and you do not "
                "lose the screen you were on."
            ),
            priority=HIGH, role=ANY,
        ),
        Case(
            area="Signing out",
            title="Signing out ends the session properly",
            pre="You are signed in.",
            steps=[
                "Click your name in the top corner and choose Sign out.",
                "Confirm you are returned to the sign-in screen.",
                "Press the browser Back button.",
            ],
            expected=(
                "You end up back on the sign-in screen, not on the page you were viewing. "
                "No ticket information is still visible on screen."
            ),
            priority=CRITICAL, uat=True, role=ANY,
        ),
        Case(
            area="Returning to your page",
            title="You are returned to the page you originally asked for",
            pre="You are signed out. You have a direct link to a ticket list page.",
            steps=[
                "Paste a direct link to the complaints list into the address bar.",
                "You are shown the sign-in screen. Sign in normally.",
            ],
            expected=(
                "After signing in you land on the complaints list you originally asked for, "
                "not on the generic dashboard."
            ),
            priority=HIGH, uat=True, role=ANY,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Route protection",
            title="Someone who is not signed in cannot open any screen",
            kind=NEGATIVE,
            pre="No one is signed in. Clear the browser cookies first.",
            steps=[
                "Clear all cookies for the site.",
                "Try to open the ticket list, the reports screen, and the user management "
                "screen one at a time by typing each address directly.",
            ],
            expected=(
                "Every single one sends you to the sign-in screen. No ticket data, no names "
                "and no numbers appear for even a moment before the redirect."
            ),
            priority=CRITICAL, uat=True, role="Not signed in",
        ),
        Case(
            area="Signing in",
            title="Wrong AWNIC credentials are rejected",
            kind=NEGATIVE,
            pre="You are on the AWNIC sign-in page.",
            steps=[
                "Start the sign-in.",
                "Enter a valid username with a deliberately wrong password.",
                "Submit.",
            ],
            expected=(
                "AWNIC's sign-in page refuses you with its own message. You are not let into "
                "the platform. The message does not reveal whether the username exists."
            ),
            data="Valid username + wrong password",
            priority=CRITICAL, role="Not signed in",
        ),
        Case(
            area="Signing in",
            title="A person who has no account on this platform cannot get in",
            kind=NEGATIVE,
            pre="You have an AWNIC company account that has never been added to this platform.",
            steps=[
                "Sign in with that AWNIC account.",
            ],
            expected=(
                "Sign-in stops with a clear message that you do not have access to this "
                "system and should contact the administrator. You do not land on a blank or "
                "broken screen."
            ),
            priority=CRITICAL, uat=True, role="Company staff with no platform account",
        ),
        Case(
            area="Signing out",
            title="An old link does not work after signing out",
            kind=NEGATIVE,
            pre="You have been signed in and have copied a ticket link.",
            steps=[
                "Copy the address of a ticket you can see.",
                "Sign out.",
                "Paste the address into the same browser and press Enter.",
            ],
            expected="You are sent to the sign-in screen. The ticket does not open.",
            priority=CRITICAL, role=ANY,
        ),
        Case(
            area="Deactivated user",
            title="A deactivated staff member is locked out",
            kind=NEGATIVE,
            pre="An administrator has just deactivated a test user's account.",
            steps=[
                "Have the administrator deactivate the test user.",
                "As the test user, try to sign in.",
                "If the test user was already signed in, have them refresh their page.",
            ],
            expected=(
                "Sign-in is refused. An already-open session stops working on the next click "
                "and returns to the sign-in screen. The person cannot read or change anything."
            ),
            priority=CRITICAL, uat=True, role="Deactivated staff member", req="R39",
        ),
        Case(
            area="Test sign-in",
            title="The shortcut test sign-in is switched off in the live system",
            kind=NEGATIVE,
            pre="You have the address of the live (production) system.",
            steps=[
                "Open the live system's sign-in screen.",
                "Look for any 'developer' or 'test' sign-in option or box.",
                "If the team gives you the test sign-in address, try it directly.",
            ],
            expected=(
                "There is no test sign-in option visible, and calling it directly is refused. "
                "Only the real AWNIC sign-in works on the live system."
            ),
            priority=CRITICAL, role="Not signed in",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Two browsers",
            title="Signing in on a second device does not break the first",
            kind=EDGE,
            pre="You have two browsers or two devices available.",
            steps=[
                "Sign in on browser A and open a ticket.",
                "Sign in as the same person on browser B.",
                "Go back to browser A and click something.",
            ],
            expected=(
                "Both sessions keep working, or browser A is cleanly signed out with a "
                "message. What must NOT happen is browser A showing a broken page or a "
                "half-loaded screen."
            ),
            priority=MEDIUM, role=ANY,
        ),
        Case(
            area="Session expiry",
            title="A very old session is refused, not silently accepted",
            kind=EDGE,
            pre="You have been signed in for longer than the full session lifetime.",
            steps=[
                "Sign in and then leave the tab open overnight (or ask the team to shorten "
                "the session lifetime on the test system).",
                "Come back and click any menu item.",
            ],
            expected=(
                "You are taken to the sign-in screen with a message that your session has "
                "expired. You are not left staring at a spinner or an error code."
            ),
            priority=HIGH, role=ANY,
        ),
        Case(
            area="Network interruption",
            title="Losing the network during sign-in shows a helpful message",
            kind=EDGE,
            pre="You can disconnect the network on your test machine.",
            steps=[
                "Start the sign-in process.",
                "Disconnect the network before it finishes.",
                "Reconnect and try again.",
            ],
            expected=(
                "A readable message appears telling you sign-in could not be completed and "
                "to try again. No raw technical error text is shown. Retrying works."
            ),
            priority=MEDIUM, role=ANY,
        ),
        Case(
            area="Repeated attempts",
            title="Hammering the sign-in button is throttled",
            kind=EDGE,
            pre="You are on the sign-in screen.",
            steps=[
                "Attempt to sign in more than ten times in under a minute.",
            ],
            expected=(
                "After roughly ten attempts the system asks you to wait before trying again. "
                "It does not crash, and a genuine user is able to sign in a minute later."
            ),
            priority=MEDIUM, role="Not signed in",
        ),
        Case(
            area="Browser behaviour",
            title="Back and forward buttons behave sensibly after signing in",
            kind=EDGE,
            pre="You have just signed in.",
            steps=[
                "Sign in.",
                "Press Back repeatedly to try to reach the sign-in screen.",
                "Press Forward again.",
            ],
            expected=(
                "You either stay in the application or land on the sign-in screen already "
                "signed in and are bounced forward. You never see a stale page with old data."
            ),
            priority=LOW, role=ANY,
        ),
        Case(
            area="Multiple tabs",
            title="Signing out in one tab signs you out in the others",
            kind=EDGE,
            pre="You are signed in with the platform open in three tabs.",
            steps=[
                "Open three tabs on different screens.",
                "Sign out in tab one.",
                "Click something in tab two and then tab three.",
            ],
            expected="Tabs two and three also return to the sign-in screen on the next action.",
            priority=MEDIUM, role=ANY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Menu shape by role",
            title="Each role sees only the menu items their job needs",
            kind=ACCESS,
            pre="You have a sign-in for each of the eight roles.",
            steps=[
                "Sign in as each role in turn: Administrator, Head of Department, Manager, "
                "Customer Care Supervisor, Customer Care Agent, Complaint Handler, "
                "Department Contact Person, Compliance Officer.",
                "For each one, write down every menu item you can see.",
                "Compare your list against the agreed role matrix.",
            ],
            expected=(
                "Each role's menu matches the agreed matrix exactly. No role sees a menu item "
                "it should not have, and no role is missing an item it needs to do its job."
            ),
            priority=CRITICAL, uat=True, role="All eight roles", req="R39",
        ),
        Case(
            area="Hidden is not the same as blocked",
            title="A screen hidden from the menu is also blocked if typed in directly",
            kind=ACCESS,
            pre="Sign in as a role that does NOT have User Management in its menu.",
            steps=[
                "Confirm User Management is missing from your menu.",
                "Type the User Management address directly into the browser.",
                "Do the same for Role Management and the Reports screen.",
            ],
            expected=(
                "Each one is refused with a clear 'you do not have access' message or sends "
                "you back to your own home screen. None of them opens, not even briefly."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="No role assigned",
            title="A user with no role assigned can sign in but can do nothing",
            kind=ACCESS,
            pre="An administrator has created a user and given them no roles at all.",
            steps=[
                "Sign in as that user.",
                "Look at the menu.",
                "Try to open the ticket list directly by typing the address.",
            ],
            expected=(
                "The user sees an almost empty screen with a message explaining they have no "
                "access yet and should contact their administrator. They cannot see a single "
                "ticket. The system does not crash or show a blank white page."
            ),
            priority=CRITICAL, role="User with no roles",
        ),
        Case(
            area="Role change takes effect",
            title="Removing a role removes the access straight away",
            kind=ACCESS,
            pre="A test user currently holds the Manager role and is signed in.",
            steps=[
                "As the test user, confirm you can see the Reports screen.",
                "As an administrator, remove the Manager role from that user.",
                "As the test user, refresh and try to open Reports again.",
            ],
            expected=(
                "Reports disappears from the menu and typing the address is refused. The "
                "change does not wait for the user to sign out and back in again."
            ),
            priority=HIGH, uat=True, role=f"{ADMIN} + test user", req="R39",
        ),
        Case(
            area="Two roles at once",
            title="A person with two roles gets everything both roles allow",
            kind=ACCESS,
            pre="A test user has been given both Complaint Handler and Manager.",
            steps=[
                "Sign in as that user.",
                "Check the menu contains the items from both roles.",
                "Open one screen that only Complaint Handler allows and one that only "
                "Manager allows.",
            ],
            expected=(
                "Both screens open. Access is the two roles added together, never the "
                "smaller of the two."
            ),
            priority=HIGH, role="User with two roles",
        ),
    ],
)

# =====================================================================================
M02 = Module(
    code="M02",
    name="Users, Roles and Permissions",
    short="Users and Roles",
    plain_summary=(
        "Administrators add staff, switch them on and off, and give them a job role. The "
        "role decides which screens and buttons that person gets. Eight roles exist today."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Adding a user",
            title="An administrator can add a new staff member",
            pre="You are signed in as an administrator and are on the User Management screen.",
            steps=[
                "Click Add User.",
                "Fill in the full name, work email, department and job title.",
                "Pick one role from the role list.",
                "Save.",
            ],
            expected=(
                "The user is created and appears at the top of the user list straight away, "
                "showing their name, email, department and role. A confirmation message is "
                "shown."
            ),
            data="Name: Test Agent One / Email: test.agent1@awnic.ae / Dept: Motor Claims",
            priority=CRITICAL, uat=True, role=ADMIN, req="R39",
        ),
        Case(
            area="Editing a user",
            title="An administrator can change a staff member's details",
            pre="At least one test user exists.",
            steps=[
                "Open a test user from the list.",
                "Change their job title and their department.",
                "Save and reopen the record.",
            ],
            expected="Both changes are saved and shown correctly when the record is reopened.",
            priority=HIGH, uat=True, role=ADMIN, req="R39",
        ),
        Case(
            area="Assigning roles",
            title="An administrator can give a staff member a role",
            pre="A test user exists with no role.",
            steps=[
                "Open the test user.",
                "Assign the Customer Care Agent role.",
                "Save.",
                "Sign in as that user in a separate browser.",
            ],
            expected=(
                "The role shows on the user record, and the user immediately gets the "
                "Customer Care Agent menu when they sign in."
            ),
            priority=CRITICAL, uat=True, role=ADMIN, req="R39",
        ),
        Case(
            area="Assigning roles",
            title="An administrator can give one person more than one role",
            pre="A test user exists with one role.",
            steps=[
                "Open the test user and add a second role.",
                "Save and reopen.",
            ],
            expected="Both roles are listed on the record and both are saved.",
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Deactivating",
            title="An administrator can switch a leaver off without deleting them",
            pre="A test user exists and is active.",
            steps=[
                "Open the test user and switch them to inactive.",
                "Save.",
                "Look for that person in the user list.",
                "Open a ticket they used to work on and check the history.",
            ],
            expected=(
                "The person shows as Inactive but is still in the list and still named in "
                "the history of their old tickets. Nothing about their past work disappears."
            ),
            priority=CRITICAL, uat=True, role=ADMIN, req="R39",
        ),
        Case(
            area="Reactivating",
            title="An administrator can switch a returning staff member back on",
            pre="A test user is currently inactive.",
            steps=[
                "Open the inactive user and switch them back to active.",
                "Save.",
                "Have that person sign in.",
            ],
            expected="They can sign in again and their previous roles still apply.",
            priority=MEDIUM, role=ADMIN,
        ),
        Case(
            area="Finding a user",
            title="Search and filters find the right people",
            pre="There are at least 20 users in the system.",
            steps=[
                "Type part of a person's name into the search box.",
                "Clear it and search by part of their email.",
                "Clear it and filter by department, then by role, then by active/inactive.",
            ],
            expected=(
                "Each search and filter returns only matching people. Combining two filters "
                "narrows the list further rather than ignoring one of them."
            ),
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Role matrix",
            title="The role screen shows what each role is allowed to do",
            pre="You are on the Role Management screen.",
            steps=[
                "Open Role Management.",
                "Select each of the eight roles in turn.",
                "Read the list of things each role can do.",
            ],
            expected=(
                "All eight roles are listed - Administrator, Head of Department, Manager, "
                "Customer Care Supervisor, Customer Care Agent, Complaint Handler, "
                "Department Contact Person, Compliance Officer - each with a readable list "
                "of what it allows."
            ),
            priority=HIGH, uat=True, role=ADMIN, req="R39",
        ),
        Case(
            area="Activity log",
            title="Every change to a user is recorded with who did it and when",
            pre="You have just added and then edited a test user.",
            steps=[
                "Add a user, then change their department, then remove a role.",
                "Open the activity log on the Admin screen.",
            ],
            expected=(
                "All three actions appear in the log with the date, the time, the person who "
                "made the change, and what changed from and to."
            ),
            priority=HIGH, uat=True, role=ADMIN, req="R29",
        ),
        Case(
            area="Head of Department",
            title="A head of department can manage people inside their own department",
            pre="You are signed in as a Head of Department for Motor Claims.",
            steps=[
                "Open User Management.",
                "Create a new user inside Motor Claims.",
                "Edit an existing Motor Claims user.",
            ],
            expected="Both actions succeed and the new person appears under Motor Claims.",
            priority=HIGH, uat=True, role=HOD, req="R39",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Adding a user",
            title="You cannot save a user with the required fields left blank",
            kind=NEGATIVE,
            pre="You are on the Add User form.",
            steps=[
                "Leave the name and email blank.",
                "Click Save.",
            ],
            expected=(
                "The form does not save. Each missing field is marked in red with a message "
                "telling you what to fill in. Nothing is created."
            ),
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Adding a user",
            title="A badly formed email address is rejected",
            kind=NEGATIVE,
            pre="You are on the Add User form.",
            steps=[
                "Enter 'not-an-email' in the email box.",
                "Try to save.",
                "Try again with 'someone@' and then with 'someone@@awnic.ae'.",
            ],
            expected=(
                "Every one is refused with a message saying a valid email address is needed. "
                "The user is not created."
            ),
            data="not-an-email / someone@ / someone@@awnic.ae",
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Adding a user",
            title="The same email cannot be used twice",
            kind=NEGATIVE,
            pre="A user already exists with a known email address.",
            steps=[
                "Add a new user using that same email address.",
                "Save.",
                "Try again with the same address in capital letters.",
            ],
            expected=(
                "Both attempts are refused with a message that this email is already in use. "
                "Capital letters do not create a duplicate."
            ),
            priority=CRITICAL, role=ADMIN,
        ),
        Case(
            area="Self-management",
            title="An administrator cannot remove their own administrator role",
            kind=NEGATIVE,
            pre="You are signed in as an administrator.",
            steps=[
                "Open your own user record.",
                "Try to remove your administrator role, or deactivate yourself.",
            ],
            expected=(
                "The action is refused with a clear message. This exists so the system can "
                "never be left with nobody able to administer it."
            ),
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Last administrator",
            title="The last remaining administrator cannot be removed",
            kind=NEGATIVE,
            pre="Reduce the test system to exactly one administrator.",
            steps=[
                "Have a second administrator remove the administrator role from the only "
                "remaining administrator.",
            ],
            expected=(
                "The action is refused with a message explaining at least one administrator "
                "must always exist."
            ),
            priority=HIGH, role=ADMIN,
        ),
        Case(
            area="Deactivated user",
            title="A deactivated person cannot be given new work",
            kind=NEGATIVE,
            pre="A test user is deactivated.",
            steps=[
                "Open any ticket and try to assign it to the deactivated person.",
            ],
            expected=(
                "The deactivated person does not appear in the assignment list at all, or is "
                "shown greyed out and cannot be chosen."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Editing",
            title="Changing a user's email to one already in use is refused",
            kind=NEGATIVE,
            pre="Two users exist with different emails.",
            steps=[
                "Open user A and change their email to user B's email.",
                "Save.",
            ],
            expected="Refused with a clear duplicate message. User A keeps their original email.",
            priority=MEDIUM, role=ADMIN,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Long values",
            title="Very long names and titles are handled sensibly",
            kind=EDGE,
            pre="You are on the Add User form.",
            steps=[
                "Paste a 300-character name into the name box.",
                "Save, then look at that person in the user list and on a ticket they own.",
            ],
            expected=(
                "Either the form politely caps the length with a message, or the long name "
                "is saved and shown trimmed with dots in lists rather than breaking the "
                "layout. Columns do not overflow across the screen."
            ),
            priority=LOW, role=ADMIN,
        ),
        Case(
            area="Special characters",
            title="Names with apostrophes, hyphens and Arabic letters are accepted",
            kind=EDGE,
            pre="You are on the Add User form.",
            steps=[
                "Create a user named O'Brien-Al Marzooqi.",
                "Create a second user with an Arabic name.",
                "Search for both by name.",
            ],
            expected=(
                "Both save correctly, display correctly in the list, and can be found by "
                "searching. The Arabic name reads right to left properly."
            ),
            data="O'Brien-Al Marzooqi / an Arabic full name",
            priority=MEDIUM, role=ADMIN,
        ),
        Case(
            area="Two people editing",
            title="Two administrators editing the same user at the same time",
            kind=EDGE,
            pre="Two administrators are signed in on different machines.",
            steps=[
                "Both open the same user record.",
                "Administrator A changes the department and saves.",
                "Administrator B changes the job title and saves a moment later.",
            ],
            expected=(
                "Neither save silently wipes the other, or the second person is warned that "
                "the record changed. Reopening the record shows a sensible, explainable result."
            ),
            priority=MEDIUM, role=f"Two {ADMIN}s",
        ),
        Case(
            area="Empty list",
            title="Filtering down to no results shows a helpful empty message",
            kind=EDGE,
            pre="You are on the User Management screen.",
            steps=[
                "Search for a name that definitely does not exist.",
            ],
            expected=(
                "A friendly 'no users found' message appears with a way to clear the search. "
                "The table does not just go blank with no explanation."
            ),
            priority=LOW, role=ADMIN,
        ),
        Case(
            area="Large list",
            title="Paging works when there are many users",
            kind=EDGE,
            pre="The system has more users than fit on one page.",
            steps=[
                "Go to page two, then page three, then back to page one.",
                "Apply a filter and check the paging updates.",
            ],
            expected=(
                "Each page shows different people, no one is shown twice, and the filter "
                "resets the paging back to page one rather than leaving you on an empty page."
            ),
            priority=MEDIUM, role=ADMIN,
        ),
        Case(
            area="Role removal mid-work",
            title="Losing a permission while the screen is already open",
            kind=EDGE,
            pre="A test user is signed in with the Reports screen open.",
            steps=[
                "As the test user, open Reports and leave it open.",
                "As an administrator, remove the reports permission from that role.",
                "As the test user, click Refresh or change a filter on the report.",
            ],
            expected=(
                "The next action is refused and the user is told they no longer have access. "
                "They do not get fresh data they are no longer allowed to see."
            ),
            priority=HIGH, role=f"{ADMIN} + test user",
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can manage users",
            title="A Customer Care Agent cannot reach User Management at all",
            kind=ACCESS,
            pre="You are signed in as a Customer Care Agent.",
            steps=[
                "Check the menu for User Management - it should not be there.",
                "Type the User Management address directly.",
                "Type the Role Management address directly.",
            ],
            expected="Both are refused. No list of staff is ever shown.",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Department boundary",
            title="A head of department cannot create a user in another department",
            kind=ACCESS,
            pre="You are a Head of Department for Motor Claims.",
            steps=[
                "Open Add User.",
                "Try to set the department to Finance (a department you do not head).",
                "Save.",
            ],
            expected=(
                "Either Finance is not offered in the department list, or saving is refused "
                "with a message that you can only manage your own department."
            ),
            priority=CRITICAL, uat=True, role=HOD, req="R39",
        ),
        Case(
            area="Department boundary",
            title="A head of department cannot edit somebody from another department",
            kind=ACCESS,
            pre="You are a Head of Department for Motor Claims. A Finance user exists.",
            steps=[
                "Search for the Finance user in User Management.",
                "If they appear, try to open and edit them.",
                "Try opening their record by its direct address.",
            ],
            expected=(
                "The Finance user is either not listed at all, or opening and saving is "
                "refused. A head of department can never change somebody outside their own "
                "department."
            ),
            priority=CRITICAL, role=HOD,
        ),
        Case(
            area="Role escalation",
            title="Nobody can give somebody a role higher than their own",
            kind=ACCESS,
            pre="You are signed in as a Manager (not an administrator).",
            steps=[
                "Open a user you are allowed to edit.",
                "Try to give them the Administrator role.",
            ],
            expected=(
                "The Administrator role is not offered, or saving is refused. A manager can "
                "never create an administrator."
            ),
            priority=CRITICAL, uat=True, role=MANAGER,
        ),
        Case(
            area="Compliance officer",
            title="A compliance officer can read but cannot change users",
            kind=ACCESS,
            pre="You are signed in as a Compliance Officer.",
            steps=[
                "Open whichever user or audit screens your role allows.",
                "Look for Add, Edit and Delete buttons.",
                "Try to save a change if any form is reachable.",
            ],
            expected=(
                "You can read what your role permits, but no create, edit or delete action "
                "is available, and any direct attempt is refused."
            ),
            priority=HIGH, role=COMPLIANCE,
        ),
        Case(
            area="Activity log access",
            title="Only the right roles can read the user activity log",
            kind=ACCESS,
            pre="You have sign-ins for an agent and for an administrator.",
            steps=[
                "As a Customer Care Agent, try to open the activity log address.",
                "As an administrator, open the same address.",
            ],
            expected=(
                "The agent is refused. The administrator sees the full log. The log itself "
                "cannot be edited or deleted by either of them."
            ),
            priority=HIGH, role=f"{AGENT}, then {ADMIN}",
        ),
    ],
)

# =====================================================================================
M03 = Module(
    code="M03",
    name="Email Intake",
    plain_summary=(
        "Customer emails arriving at the AWNIC mailboxes turn into tickets automatically. "
        "Replies join the existing ticket instead of creating a new one, and attachments "
        "are saved with the ticket."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Email becomes a ticket",
            title="An email to the customer care mailbox creates a ticket by itself",
            pre="The email connection is switched on and working.",
            steps=[
                "From an outside email account, send an email to the customer care mailbox "
                "with a clear subject and a few lines of text.",
                "Wait for the system to pick it up (allow a few minutes).",
                "Open the ticket list and sort by newest.",
            ],
            expected=(
                "A new ticket appears without anybody typing it in. The subject becomes the "
                "ticket title, the message body is on the ticket, and the sender's email "
                "address is recorded as the customer."
            ),
            data="From: an external test mailbox / Subject: Motor policy renewal question",
            priority=CRITICAL, uat=True, role="System (no user action)", req="R03",
        ),
        Case(
            area="Reply joins the ticket",
            title="A customer's reply lands on the same ticket, not a new one",
            pre="A ticket already exists that came from an email.",
            steps=[
                "Reply to the original email thread from the customer's mailbox.",
                "Wait for the system to pick it up.",
                "Open the original ticket.",
            ],
            expected=(
                "The reply is added to the same ticket as a new message in the conversation. "
                "No second ticket is created and the ticket count does not go up."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R03",
        ),
        Case(
            area="Attachments",
            title="Files attached to a customer email are saved with the ticket",
            pre="The email connection is working.",
            steps=[
                "Send an email with a PDF and a photo attached.",
                "Wait for the ticket to appear.",
                "Open the ticket and look at the attachments area.",
                "Download each file.",
            ],
            expected=(
                "Both files are listed with their real names, types and sizes. Downloading "
                "gives back the same files that were sent, and they open correctly."
            ),
            data="One PDF and one JPG",
            priority=CRITICAL, uat=True, role=AGENT, req="R03",
        ),
        Case(
            area="Multiple mailboxes",
            title="Emails to each monitored mailbox all create tickets",
            pre="You have the list of monitored mailboxes from the team.",
            steps=[
                "Send one test email to each monitored mailbox in turn, including the "
                "SANADAK mailbox.",
                "Wait, then check the ticket list.",
            ],
            expected=(
                "Every mailbox produces a ticket, and each ticket records which mailbox it "
                "arrived at so you can tell them apart."
            ),
            priority=HIGH, uat=True, role="System (no user action)", req="R03, R05",
        ),
        Case(
            area="Customer details",
            title="The sender's name and email are captured on the ticket",
            pre="A test email has just created a ticket.",
            steps=[
                "Open the new ticket.",
                "Check the customer name, email address and the date and time received.",
            ],
            expected=(
                "The sender's display name and email address are shown correctly, and the "
                "received time matches when the email was actually sent."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Arabic email",
            title="An email written in Arabic creates a readable ticket",
            pre="The email connection is working.",
            steps=[
                "Send an email with an Arabic subject and Arabic body.",
                "Open the resulting ticket.",
            ],
            expected=(
                "The Arabic text is shown correctly on the ticket, reading right to left, "
                "with no question marks or boxes replacing the letters."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Connection self-healing",
            title="The mailbox connection renews itself before it expires",
            pre="Ask the team when the current mailbox connection expires.",
            steps=[
                "Note the expiry date of the mailbox connection.",
                "Wait until after the point where it should have renewed.",
                "Send a test email and confirm it still becomes a ticket.",
            ],
            expected=(
                "Email keeps flowing without anybody doing anything manually. The connection "
                "renews itself before it runs out."
            ),
            priority=CRITICAL, role="System (no user action)", req="R03",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Duplicate delivery",
            title="The same email arriving twice does not create two tickets",
            kind=NEGATIVE,
            pre="You can resend an identical email, or ask the team to replay one.",
            steps=[
                "Send an email and let it create a ticket.",
                "Have the same email delivered a second time (ask the team to replay it).",
                "Check the ticket list.",
            ],
            expected="Only one ticket exists. The second delivery is quietly ignored.",
            priority=CRITICAL, uat=True, role="System (no user action)", req="R03, R26",
        ),
        Case(
            area="Empty email",
            title="An email with no subject and no body still creates a usable ticket",
            kind=NEGATIVE,
            pre="The email connection is working.",
            steps=[
                "Send an email with a blank subject and a blank body.",
                "Check the ticket list.",
            ],
            expected=(
                "A ticket is still created so nothing is lost, showing something sensible "
                "like 'No subject' rather than an empty row or an error."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        Case(
            area="Automatic replies",
            title="Out-of-office and bounce messages do not clutter the ticket list",
            kind=NEGATIVE,
            pre="You can trigger an out-of-office reply to the mailbox.",
            steps=[
                "Send an out-of-office automatic reply to the monitored mailbox.",
                "Send a delivery-failure bounce message to the same mailbox.",
                "Check what appears in the ticket list.",
            ],
            expected=(
                "These are either not turned into tickets, or they are created and easy to "
                "discard in bulk. Agree the expected behaviour with the team before running "
                "this and record the answer."
            ),
            priority=HIGH, role="System (no user action)", ready=PARTLY,
            notes="Confirm the agreed behaviour with the team - this drives whether it is a bug.",
        ),
        Case(
            area="Attachments",
            title="An oversized attachment is handled without losing the email",
            kind=NEGATIVE,
            pre="Ask the team for the attachment size limit.",
            steps=[
                "Send an email with an attachment larger than the stated limit.",
                "Check whether a ticket is created.",
            ],
            expected=(
                "The ticket is still created with the email text. The oversized file is "
                "either stored or clearly marked as too large. The whole email is never "
                "silently dropped."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        Case(
            area="Attachments",
            title="A dangerous file type is not offered as a normal download",
            kind=NEGATIVE,
            pre="The email connection is working.",
            steps=[
                "Send an email with an executable file attached (for example a .exe or .bat).",
                "Open the resulting ticket and look at the attachment.",
            ],
            expected=(
                "The file is either rejected or clearly flagged, and it never runs when a "
                "user clicks it. Downloading it is a plain file download, nothing more."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Unknown sender",
            title="An email from an address with no matching customer still creates a ticket",
            kind=NEGATIVE,
            pre="You have an email address not linked to any AWNIC customer.",
            steps=[
                "Send an email from that unknown address.",
                "Open the resulting ticket.",
            ],
            expected=(
                "A ticket is created and the customer section says no matching customer was "
                "found rather than showing blanks or an error. An agent can still work it."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R21",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Long email",
            title="A very long email is stored in full and displayed readably",
            kind=EDGE,
            pre="The email connection is working.",
            steps=[
                "Send an email with several thousand words in the body.",
                "Open the ticket and read the message.",
            ],
            expected=(
                "The whole message is kept. The screen shows it in a scrollable area or with "
                "a 'show more' control. The page layout does not break."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Forwarded chains",
            title="A long forwarded email chain becomes one ticket, not many",
            kind=EDGE,
            pre="You have an email chain with five or more replies inside it.",
            steps=[
                "Forward the whole chain to the monitored mailbox.",
                "Check the ticket list.",
            ],
            expected=(
                "One ticket is created. The quoted history is kept but does not create extra "
                "tickets or extra customers."
            ),
            priority=MEDIUM, role="System (no user action)",
        ),
        Case(
            area="Threading",
            title="A reply with a changed subject line still joins the right ticket",
            kind=EDGE,
            pre="A ticket exists that came from an email.",
            steps=[
                "Reply to the original email but edit the subject line before sending.",
                "Check whether it joins the original ticket.",
            ],
            expected=(
                "The reply joins the original ticket because the conversation is matched on "
                "the email thread, not just the subject text."
            ),
            priority=HIGH, role="System (no user action)", req="R03",
        ),
        Case(
            area="Threading",
            title="A brand new email with the same subject does NOT join an old ticket",
            kind=EDGE,
            pre="A closed ticket exists with a known subject line.",
            steps=[
                "Compose a completely new email (not a reply) using exactly the same subject.",
                "Send it and check the ticket list.",
            ],
            expected=(
                "A new separate ticket is created. An unrelated new request must never be "
                "buried inside somebody's old closed ticket."
            ),
            priority=HIGH, uat=True, role="System (no user action)",
        ),
        Case(
            area="Burst of email",
            title="Many emails arriving at once are all turned into tickets",
            kind=EDGE,
            pre="You can send a batch of emails.",
            steps=[
                "Send 25 emails to the mailbox within one minute.",
                "Wait, then count the tickets created.",
            ],
            expected=(
                "All 25 become tickets. None are lost, none are duplicated, and the system "
                "stays responsive while it catches up."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        Case(
            area="Reply after closing",
            title="A customer replying to a closed ticket is noticed",
            kind=EDGE,
            pre="A ticket has been resolved and closed.",
            steps=[
                "Reply to the original email thread of the closed ticket.",
                "Check the closed ticket and the ticket list.",
            ],
            expected=(
                "The reply is attached to the closed ticket and somebody is alerted, or a "
                "linked follow-up ticket is created. The customer's reply is never lost. "
                "Confirm the agreed behaviour with the team."
            ),
            priority=HIGH, uat=True, role=AGENT, ready=PARTLY,
        ),
        Case(
            area="Connection outage",
            title="Email that arrives while the connection is down is not lost",
            kind=EDGE,
            pre="The team can pause and resume the mailbox connection on the test system.",
            steps=[
                "Ask the team to pause the mailbox connection.",
                "Send three emails.",
                "Ask the team to resume the connection.",
                "Wait and count the tickets.",
            ],
            expected=(
                "All three emails are picked up once the connection is back and become "
                "tickets. Nothing needs to be re-sent by the customer."
            ),
            priority=CRITICAL, role="System (no user action)", req="R03",
        ),
        Case(
            area="Same customer, many emails",
            title="Two different questions from one customer create two tickets",
            kind=EDGE,
            pre="You have one customer test mailbox.",
            steps=[
                "Send one email about a motor claim.",
                "Send a separate new email about a travel policy.",
                "Check the ticket list.",
            ],
            expected=(
                "Two separate tickets are created, both linked to the same customer. They "
                "are not merged just because the sender is the same."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Attachment access",
            title="Only people who can see the ticket can download its attachments",
            kind=ACCESS,
            pre="A ticket with an attachment exists in a department you do not belong to.",
            steps=[
                "As a Complaint Handler who is not assigned that ticket, get the attachment "
                "download address from a colleague who can see it.",
                "Paste it into your own browser.",
            ],
            expected=(
                "The download is refused. You are told the item does not exist rather than "
                "being told it exists but is forbidden."
            ),
            priority=CRITICAL, uat=True, role=HANDLER,
        ),
        Case(
            area="Attachment integrity",
            title="Nobody can add, change or delete an attachment through the screen",
            kind=ACCESS,
            pre="A ticket with an attachment is open.",
            steps=[
                "Look for an upload, replace or delete control in the attachments area.",
                "As an administrator, do the same.",
            ],
            expected=(
                "There is no way to add, replace or delete an attachment from the screen for "
                "any role. Attachments are evidence and are read-only by design."
            ),
            priority=HIGH, role="All roles including " + ADMIN,
        ),
        Case(
            area="Mailbox settings",
            title="Only an administrator can see or change the mailbox settings",
            kind=ACCESS,
            pre="You have agent and administrator sign-ins.",
            steps=[
                "As a Customer Care Agent, look for any mailbox or email connection settings.",
                "As an administrator, open the same settings.",
            ],
            expected=(
                "The agent cannot see or reach them. The administrator can. No mailbox "
                "password or key is ever displayed on screen to anybody."
            ),
            priority=HIGH, role=f"{AGENT}, then {ADMIN}",
        ),
        Case(
            area="Intake endpoint",
            title="The email intake entry point cannot be triggered by an outsider",
            kind=ACCESS,
            pre="Ask the team for the address the mail service calls.",
            steps=[
                "Call that address from a normal browser with no credentials.",
                "Call it again with an obviously made-up key.",
            ],
            expected=(
                "Both attempts are refused. No fake ticket is created. This is important - "
                "otherwise anyone could inject tickets into AWNIC's queue."
            ),
            priority=CRITICAL, role="Outsider with no access",
        ),
        Case(
            area="Not built yet",
            title="Social media messages do not create tickets yet",
            kind=ACCESS,
            pre="None.",
            steps=[
                "Confirm with the team that social media intake is not in this release.",
                "Check that no social media option appears in the channel list.",
            ],
            expected=(
                "Social media intake is correctly absent. Do NOT raise a bug - this is "
                "listed only so it is not quietly forgotten at sign-off."
            ),
            priority=LOW, role=ANY, req="R06", ready=NOT_BUILT,
        ),
    ],
)
