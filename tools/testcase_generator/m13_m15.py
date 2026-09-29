"""Modules 13-15: Customer Information, Notifications & Templates, Dashboard/Reports/Audit."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, NOT_BUILT, PARTLY
from common import Case, Module
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR

# =====================================================================================
M13 = Module(
    code="M13",
    name="Customer Information",
    plain_summary=(
        "Staff look up a customer by policy number, Emirates ID or phone and see all their "
        "past cases in one place. Sensitive details are partly hidden, and every lookup is "
        "logged."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Lookup",
            title="An agent can look up a customer by policy number",
            pre="You have a valid test policy number.",
            steps=[
                "Open a ticket or the customer search.",
                "Enter the policy number and search.",
            ],
            expected=(
                "The customer's details come back - name, contact details and policy "
                "information - within a few seconds."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R21",
        ),
        Case(
            area="Lookup",
            title="A customer can be found by Emirates ID, phone and email too",
            pre="You have valid test search values for each type.",
            steps=[
                "Search by Emirates ID.",
                "Search by mobile number.",
                "Search by email address.",
            ],
            expected="Each search returns the right customer.",
            priority=HIGH, uat=True, role=AGENT, req="R21",
        ),
        Case(
            area="Masking",
            title="Sensitive numbers are shown partly hidden",
            pre="A customer lookup has returned results.",
            steps=[
                "Read the Emirates ID, policy number and any bank details on screen.",
            ],
            expected=(
                "Sensitive values are partly masked - for example showing only the last four "
                "digits. The full value is not printed on screen for everyone to read."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R22",
        ),
        Case(
            area="Customer history",
            title="All of a customer's previous cases are shown in one place",
            pre="A test customer has several past tickets.",
            steps=[
                "Open a ticket for that customer.",
                "Open the customer records or history section.",
            ],
            expected=(
                "Every previous enquiry and complaint for that customer is listed with its "
                "reference, date, type, subject and outcome, so the agent has the full "
                "picture without searching."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R22",
        ),
        Case(
            area="Customer history",
            title="Clicking a past case opens it",
            pre="You are on the customer history view.",
            steps=[
                "Click one of the past cases.",
            ],
            expected="That ticket opens, assuming you are allowed to see it.",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Lookup logging",
            title="Every customer lookup is recorded with who looked and why",
            pre="You have just performed a lookup.",
            steps=[
                "Perform a lookup on a test customer.",
                "As a compliance officer or administrator, open the audit view.",
                "Find the lookup entry.",
            ],
            expected=(
                "The entry records who searched, when, which ticket it related to, the "
                "stated reason, and a masked version of what was searched for. The full "
                "search value is never written into the log."
            ),
            priority=CRITICAL, uat=True, role=COMPLIANCE, req="R21, R29",
        ),
        Case(
            area="Filling the form",
            title="Looking up a customer fills the ticket form automatically",
            pre="You are creating a new ticket.",
            steps=[
                "Search for a customer and select them.",
            ],
            expected=(
                "The customer's name and contact details fill in automatically, saving the "
                "agent from retyping and from typing mistakes."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R21",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Not found",
            title="A search with no match gives a clear 'no data found' message",
            kind=NEGATIVE,
            pre="You have a policy number that does not exist.",
            steps=[
                "Search using the non-existent policy number.",
            ],
            expected=(
                "A plain 'no customer found' message appears. No error code, no blank panel, "
                "and the agent can carry on working the ticket without a customer record."
            ),
            data="A made-up policy number",
            priority=CRITICAL, uat=True, role=AGENT, req="R21",
        ),
        Case(
            area="Not found",
            title="A failed lookup is still recorded in the log",
            kind=NEGATIVE,
            pre="You have just searched for a customer who does not exist.",
            steps=[
                "Search for a non-existent customer.",
                "Check the audit view for the lookup entry.",
            ],
            expected=(
                "The attempt is logged even though nothing was found. Who searched for what "
                "matters for compliance whether or not there was a result."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R21",
        ),
        Case(
            area="Empty search",
            title="An empty search is refused",
            kind=NEGATIVE,
            pre="You are on the customer search.",
            steps=[
                "Click Search with the box empty.",
                "Try again with only spaces.",
            ],
            expected="You are asked to enter something. No blank request is sent.",
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Service unavailable",
            title="If the customer system is unreachable the agent is told plainly",
            kind=NEGATIVE,
            pre="Ask the team to block the connection to the customer system.",
            steps=[
                "Have the team block the connection.",
                "Perform a lookup.",
                "Have them restore it and try again.",
            ],
            expected=(
                "A readable message says customer information is temporarily unavailable and "
                "to try again. The ticket screen still works. No technical error text is "
                "shown. Retrying after the fix works."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Bad input",
            title="A badly formatted search value is refused politely",
            kind=NEGATIVE,
            pre="You are on the customer search.",
            steps=[
                "Search using letters where a policy number is expected.",
                "Search using a two-digit Emirates ID.",
            ],
            expected=(
                "You are told the format is wrong before the search is sent, or a clean 'no "
                "results' comes back. No error is shown."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Many results",
            title="A search returning many customers is usable",
            kind=EDGE,
            pre="You have a search value matching several customers.",
            steps=[
                "Search by a common surname or a shared phone number.",
            ],
            expected=(
                "The matches are listed with enough detail to tell them apart, and can be "
                "paged or narrowed. One is chosen deliberately, never picked automatically."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Long history",
            title="A customer with a very long history is displayed sensibly",
            kind=EDGE,
            pre="A test customer has 50 or more past cases.",
            steps=[
                "Open that customer's history.",
                "Scroll or page through it.",
            ],
            expected=(
                "The list pages or scrolls, is sorted newest first, and the page stays "
                "responsive."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Slow response",
            title="A slow customer lookup does not freeze the screen",
            kind=EDGE,
            pre="Ask the team to slow the connection to the customer system.",
            steps=[
                "Perform a lookup on a deliberately slow connection.",
                "Try to use the rest of the ticket screen while it loads.",
            ],
            expected=(
                "A loading indicator appears, the rest of the screen stays usable, and the "
                "request eventually finishes or times out with a clear message."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Cached data",
            title="Repeating the same lookup is fast and consistent",
            kind=EDGE,
            pre="You have already looked up a customer once.",
            steps=[
                "Look up the same customer again straight away.",
                "Compare the details with the first result.",
            ],
            expected=(
                "The second lookup returns the same details, faster. Both lookups are still "
                "recorded in the log."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="History across types",
            title="A customer's history includes both enquiries and complaints",
            kind=EDGE,
            pre="A test customer has both an enquiry and a complaint in their past.",
            steps=[
                "Open that customer's history.",
            ],
            expected=(
                "Both appear, each clearly marked as an enquiry or a complaint, so nothing "
                "about the relationship is hidden from the agent."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R22",
        ),
        Case(
            area="History and discarded",
            title="Discarded items do not clutter the customer's history",
            kind=EDGE,
            pre="A customer has a discarded ticket in their past.",
            steps=[
                "Open that customer's history.",
            ],
            expected=(
                "Discarded junk is either excluded or clearly marked. Confirm the agreed "
                "behaviour with the business."
            ),
            priority=MEDIUM, role=AGENT, ready=PARTLY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can look up",
            title="Only permitted roles can search for customer information",
            kind=ACCESS,
            pre="You have several role sign-ins.",
            steps=[
                "Sign in as each role and check who can reach the customer search.",
                "For a role that should not, try the customer records address directly.",
            ],
            expected=(
                "Access matches the agreed matrix and direct attempts are refused. This is "
                "personal data, so treat any gap as serious."
            ),
            priority=CRITICAL, uat=True, role="All roles", req="R21",
        ),
        Case(
            area="Customer records tab",
            title="The customer records tab of a ticket outside your scope cannot be opened",
            kind=ACCESS,
            pre="You have the address of that tab for a ticket you cannot see.",
            steps=[
                "Paste the address into your browser.",
            ],
            expected="It is refused as not found.",
            priority=CRITICAL, role=HANDLER,
        ),
        Case(
            area="History scope",
            title="The customer history only shows cases the person is allowed to see",
            kind=ACCESS,
            pre=(
                "A customer has tickets in two departments and you are scoped to one of them."
            ),
            steps=[
                "As a Department Contact Person, open that customer's history.",
                "Compare the list with what a manager sees for the same customer.",
            ],
            expected=(
                "You see only your own department's cases. Customer history must not become "
                "a way to read every department's tickets."
            ),
            priority=CRITICAL, uat=True, role=POC,
        ),
        Case(
            area="Direct access",
            title="Nobody can reach the external customer system directly from the browser",
            kind=ACCESS,
            pre="Ask the team for the address of the external customer system.",
            steps=[
                "Try to open that address directly from a browser.",
                "Check the browser network tools while doing a lookup to see whether the "
                "browser is calling it.",
            ],
            expected=(
                "The browser never talks to the external system directly - all lookups go "
                "through AWNIC's own platform. No key or credential is visible in the browser."
            ),
            priority=CRITICAL, role="Any staff member with browser tools",
        ),
        Case(
            area="Masking",
            title="Masked values are masked in the data too, not just on screen",
            kind=ACCESS,
            pre="You can open the browser's network tools.",
            steps=[
                "Perform a customer lookup with the network tools open.",
                "Inspect what the browser actually received.",
            ],
            expected=(
                "The sensitive values are already masked in what the browser receives. "
                "Masking only in the display would mean the full value is still one click "
                "away."
            ),
            priority=CRITICAL, uat=True, role="Any staff member with browser tools", req="R22",
        ),
    ],
)

# =====================================================================================
M14 = Module(
    code="M14",
    name="Notifications and Templates",
    plain_summary=(
        "Two separate things - alerts inside the app for staff, and emails sent out to "
        "customers - plus a library of ready-made English and Arabic replies for agents."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Assignment alert",
            title="An agent is notified when a ticket is assigned to them",
            pre="You are signed in as the receiving agent in one browser.",
            steps=[
                "Have a supervisor assign a ticket to you.",
                "Open your notifications.",
            ],
            expected=(
                "A notification appears naming the ticket, with a link that opens it. The "
                "unread count goes up."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R12",
        ),
        Case(
            area="Escalation alert",
            title="The escalation contact is notified when a ticket escalates",
            pre="A ticket is about to escalate to a contact you can sign in as.",
            steps=[
                "Let the ticket escalate.",
                "Sign in as the contact and open notifications.",
            ],
            expected=(
                "A notification names the ticket, the escalation level and how late it is."
            ),
            priority=CRITICAL, uat=True, role=POC, req="R18, R19",
        ),
        Case(
            area="Breach alert",
            title="A supervisor is alerted when a deadline is missed",
            pre="A ticket is about to pass its deadline.",
            steps=[
                "Let a ticket pass its deadline.",
                "Sign in as the supervisor and check notifications.",
            ],
            expected="A notification names the ticket and says the deadline was missed.",
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R17",
        ),
        Case(
            area="Customer acknowledgement",
            title="The customer gets an acknowledgement when their case is logged",
            pre="A test customer mailbox is set up.",
            steps=[
                "Send an email from the customer mailbox.",
                "Wait for the ticket to be created.",
                "Check the customer mailbox.",
            ],
            expected=(
                "An acknowledgement email arrives containing the reference number and what "
                "happens next, using AWNIC's approved wording."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R03",
        ),
        Case(
            area="Reading notifications",
            title="Opening a notification marks it as read and takes you to the ticket",
            pre="You have unread notifications.",
            steps=[
                "Open your notification list.",
                "Click one.",
                "Go back to the list.",
            ],
            expected=(
                "The right ticket opens, that notification is now marked read, and the "
                "unread count drops by one."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Mark all read",
            title="All notifications can be cleared at once",
            pre="You have several unread notifications.",
            steps=[
                "Use the mark-all-as-read option.",
                "Refresh the page.",
            ],
            expected="The unread count drops to zero and stays there after refreshing.",
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Reply library",
            title="An agent can find and use a ready-made reply",
            pre="You are on a ticket ready to reply.",
            steps=[
                "Open the reply template library.",
                "Search for a template by keyword.",
                "Insert it into the reply.",
            ],
            expected=(
                "The library opens, searching finds the right template, and inserting it "
                "fills the reply with the approved wording, which can then be edited."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Reply library",
            title="Templates are available in both English and Arabic",
            pre="You are in the template library.",
            steps=[
                "Find a template and switch to its Arabic version.",
                "Insert the Arabic version.",
            ],
            expected=(
                "Both languages exist for the scenario, and the Arabic text is inserted "
                "correctly reading right to left."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Customer templates",
            title="The system's outgoing customer emails use the approved wording",
            pre="You have the approved wording from the business.",
            steps=[
                "Trigger each type of automatic customer email - acknowledgement, "
                "reclassification, resolution.",
                "Compare each against the approved wording.",
            ],
            expected=(
                "Each email matches the approved text, with the ticket's real reference "
                "number and customer name filled in properly."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Separation",
            title="Internal notes are never included in an email to the customer",
            kind=NEGATIVE,
            pre="A ticket has internal notes on it.",
            steps=[
                "Add a clearly identifiable internal note.",
                "Trigger a customer email on that ticket.",
                "Read the email in the customer mailbox.",
            ],
            expected=(
                "The internal note does not appear anywhere in the customer's email. This is "
                "a confidentiality issue, so treat any leak as critical."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Placeholders",
            title="No unfilled placeholders reach the customer",
            kind=NEGATIVE,
            pre="Trigger each type of customer email.",
            steps=[
                "Read each outgoing email carefully.",
                "Look for anything in brackets or braces that was not replaced.",
            ],
            expected=(
                "Every placeholder is filled with real values. A customer must never receive "
                "an email containing something like {customer_name}."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Bad address",
            title="A customer email that cannot be delivered is recorded, not lost",
            kind=NEGATIVE,
            pre="A ticket has an invalid customer email address.",
            steps=[
                "Trigger a customer email on that ticket.",
                "Check the ticket for a record of the attempt.",
            ],
            expected=(
                "The failure is recorded on the ticket and somebody can see the customer was "
                "not reached. It does not silently look successful."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="No spam",
            title="One event produces one notification, not several",
            kind=NEGATIVE,
            pre="You are the assigned agent.",
            steps=[
                "Have a supervisor assign one ticket to you.",
                "Count the notifications you receive.",
            ],
            expected=(
                "Exactly one notification for one assignment. Duplicates train people to "
                "ignore notifications."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Wrong recipient",
            title="A notification never goes to somebody who cannot see the ticket",
            kind=NEGATIVE,
            pre="A ticket exists in a department a test user does not belong to.",
            steps=[
                "Cause an event on that ticket - assign it, escalate it, breach it.",
                "Sign in as the unrelated user and check their notifications.",
            ],
            expected=(
                "They receive nothing. A notification naming a ticket they cannot open is a "
                "small data leak in itself."
            ),
            priority=CRITICAL, uat=True, role="Unrelated staff member",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Many notifications",
            title="A long notification list stays usable",
            kind=EDGE,
            pre="A test user has 100 or more notifications.",
            steps=[
                "Open the notification list and scroll or page through it.",
            ],
            expected=(
                "The list pages or scrolls smoothly, newest first, and does not slow the "
                "rest of the application."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Deleted target",
            title="A notification for a discarded ticket behaves sensibly",
            kind=EDGE,
            pre="You have a notification for a ticket that has since been discarded.",
            steps=[
                "Click the notification.",
            ],
            expected=(
                "You either reach the discarded ticket if allowed, or see a clear message. "
                "You never get an error page."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Template edits",
            title="Editing a template does not change emails already sent",
            kind=EDGE,
            pre="A customer email has already been sent using a template.",
            steps=[
                "Note what the customer received.",
                "Have an administrator change that template.",
                "Look at the record of the already-sent email.",
            ],
            expected=(
                "The record still shows what was actually sent. History must reflect reality, "
                "not the current template."
            ),
            priority=HIGH, uat=True, role=ADMIN,
        ),
        Case(
            area="Long content",
            title="A very long ticket subject does not break the notification or the email",
            kind=EDGE,
            pre="A ticket has a 300-character subject.",
            steps=[
                "Cause a notification and a customer email for that ticket.",
                "Read both.",
            ],
            expected=(
                "The subject is trimmed sensibly in both. Neither the list layout nor the "
                "email formatting breaks."
            ),
            priority=LOW, role=AGENT,
        ),
        Case(
            area="Arabic emails",
            title="An Arabic customer email arrives readable",
            kind=EDGE,
            pre="A ticket exists with an Arabic-speaking test customer.",
            steps=[
                "Trigger an Arabic customer email.",
                "Open it in the customer mailbox.",
            ],
            expected=(
                "The Arabic text is correct, reads right to left, and shows no broken "
                "characters in any common mail client."
            ),
            priority=HIGH, uat=True, role="System (no user action)",
        ),
        Case(
            area="Mail outage",
            title="Notifications queued during a mail outage are sent afterwards",
            kind=EDGE,
            pre="Ask the team to pause outgoing mail on the test system.",
            steps=[
                "Pause outgoing mail.",
                "Cause three customer emails.",
                "Resume mail.",
            ],
            expected=(
                "All three are eventually delivered, or are clearly marked as failed on the "
                "tickets so somebody can act. They are not silently dropped."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Own notifications only",
            title="You can only see your own notifications",
            kind=ACCESS,
            pre="Two test users both have notifications.",
            steps=[
                "Sign in as user A and read the list.",
                "Sign in as user B and read the list.",
                "As user A, try to reach user B's notifications directly if you can get the "
                "address.",
            ],
            expected="Each person sees only their own, and any direct attempt is refused.",
            priority=CRITICAL, uat=True, role="Two staff members",
        ),
        Case(
            area="Template management",
            title="Only permitted roles can add or change templates",
            kind=ACCESS,
            pre="You have agent and administrator sign-ins.",
            steps=[
                "As a Customer Care Agent, look for template edit controls.",
                "As an administrator, look again.",
            ],
            expected=(
                "The agent can use templates but not change them. Only permitted roles can "
                "edit, and every change is recorded."
            ),
            priority=HIGH, uat=True, role=f"{AGENT}, then {ADMIN}",
        ),
        Case(
            area="Sending to customers",
            title="Only permitted roles can send an email to a customer",
            kind=ACCESS,
            pre="You have several role sign-ins.",
            steps=[
                "Sign in as each role and check who can send a customer reply.",
                "Compare against the agreed matrix.",
            ],
            expected=(
                "It matches the matrix. Sending to a customer is outward-facing, so it "
                "should not be available to view-only roles."
            ),
            priority=CRITICAL, uat=True, role="All roles",
        ),
    ],
)

# =====================================================================================
M15 = Module(
    code="M15",
    name="Dashboard, Reports and Audit",
    short="Reports and Audit",
    plain_summary=(
        "The home dashboard with counts and charts, the management report, and the complete "
        "permanent record of every action taken on every ticket."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Dashboard",
            title="The dashboard shows the key numbers correctly",
            pre="You know roughly how many open, breached and resolved tickets exist.",
            steps=[
                "Open the dashboard.",
                "Read each number tile.",
                "Cross-check two of them by filtering the ticket list the same way and "
                "comparing the count.",
            ],
            expected=(
                "The tiles show open, in progress, breached and resolved counts, and each "
                "matches what the ticket list gives for the same filter."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R28",
        ),
        Case(
            area="Dashboard",
            title="The charts match the underlying numbers",
            pre="You are on the dashboard.",
            steps=[
                "Read each chart - by department, by type, by status, over time.",
                "Add up one chart's values and compare with the matching tile.",
            ],
            expected="The chart totals agree with the tiles. Every chart has a readable legend.",
            priority=HIGH, uat=True, role=SUPERVISOR, req="R28",
        ),
        Case(
            area="Dashboard",
            title="Clicking a dashboard number opens the matching ticket list",
            pre="You are on the dashboard.",
            steps=[
                "Click the breached tile.",
                "Read the list that opens.",
            ],
            expected=(
                "The ticket list opens already filtered to breached tickets, and the number "
                "of rows matches the tile."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Reports",
            title="A manager can run the management report",
            pre="You are signed in as a manager.",
            steps=[
                "Open Reports.",
                "Choose a date range covering known data.",
                "Run the report.",
            ],
            expected=(
                "The report shows volumes, deadline performance, escalations and resolution "
                "times for the chosen period, calculated from live data."
            ),
            priority=CRITICAL, uat=True, role=MANAGER, req="R28",
        ),
        Case(
            area="Reports",
            title="Report filters change the figures correctly",
            pre="You are on the reports screen.",
            steps=[
                "Run the report for a wide date range and note the totals.",
                "Narrow the date range and run again.",
                "Add a department filter and run again.",
            ],
            expected=(
                "The figures drop sensibly each time, and the narrower results are a subset "
                "of the wider ones."
            ),
            priority=CRITICAL, uat=True, role=MANAGER, req="R28",
        ),
        Case(
            area="Reports",
            title="A report can be exported",
            pre="A report is on screen.",
            steps=[
                "Export or download the report.",
                "Open the file.",
                "Compare the figures with the screen.",
            ],
            expected=(
                "The file opens cleanly and the figures match the screen exactly, including "
                "the date range and filters used."
            ),
            priority=HIGH, uat=True, role=MANAGER, req="R28", ready=PARTLY,
            notes="Only run if an export option exists on the reports screen.",
        ),
        Case(
            area="Audit trail",
            title="Every action on a ticket is recorded in its history",
            pre="You will perform several actions on one ticket.",
            steps=[
                "On one ticket: edit a field, change the stage, reassign it, add a note and "
                "resolve it.",
                "Open the ticket's history tab.",
            ],
            expected=(
                "All five actions are listed in order, each with what changed, who did it "
                "and the exact date and time."
            ),
            priority=CRITICAL, uat=True, role=COMPLIANCE, req="R29",
        ),
        Case(
            area="Audit trail",
            title="The organisation-wide audit trail can be searched and filtered",
            pre="You are signed in as a compliance officer or administrator.",
            steps=[
                "Open the Audit Trail screen.",
                "Filter by date range, then by user, then by action type.",
                "Search for a specific ticket reference.",
            ],
            expected=(
                "Each filter narrows the list correctly and the ticket search returns that "
                "ticket's entries."
            ),
            priority=CRITICAL, uat=True, role=COMPLIANCE, req="R29",
        ),
        Case(
            area="Audit trail",
            title="AI decisions appear in the audit trail alongside human actions",
            pre="A ticket has been processed by the AI.",
            steps=[
                "Open that ticket's history.",
                "Find the AI entries and the human entries.",
            ],
            expected=(
                "Both are present and it is obvious which is which, so a reviewer can tell "
                "what the system decided and what a person decided."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R29, R35",
        ),
        Case(
            area="History screen",
            title="The history screen shows recent activity across tickets",
            pre="Several tickets have been worked on recently.",
            steps=[
                "Open the History screen.",
                "Read the recent activity.",
            ],
            expected=(
                "Recent activity is listed newest first with the ticket, the action, the "
                "person and the time."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Audit integrity",
            title="Nobody can edit an audit entry",
            kind=NEGATIVE,
            pre="You are signed in as an administrator.",
            steps=[
                "Open a ticket's history and look for an edit control on any entry.",
                "Open the organisation-wide audit trail and look again.",
            ],
            expected=(
                "There is no way to change an audit entry anywhere, for any role including "
                "administrators. This is a regulatory requirement - treat any editable entry "
                "as a critical defect."
            ),
            priority=CRITICAL, uat=True, role=ADMIN, req="R29",
        ),
        Case(
            area="Audit integrity",
            title="Nobody can delete an audit entry",
            kind=NEGATIVE,
            pre="You are signed in as an administrator.",
            steps=[
                "Look for a delete or clear option on any audit entry or on the whole trail.",
                "If you can reach a delete action directly, try it.",
            ],
            expected="No delete exists anywhere and any direct attempt is refused.",
            priority=CRITICAL, uat=True, role=ADMIN, req="R29",
        ),
        Case(
            area="Reports",
            title="A date range with no data shows an empty report, not an error",
            kind=NEGATIVE,
            pre="You are on the reports screen.",
            steps=[
                "Choose a date range far in the past with no tickets.",
                "Run the report.",
            ],
            expected=(
                "The report shows zeros and a clear 'no data for this period' message. No "
                "error and no misleading blank charts."
            ),
            priority=HIGH, role=MANAGER,
        ),
        Case(
            area="Reports",
            title="An invalid date range is refused",
            kind=NEGATIVE,
            pre="You are on the reports screen.",
            steps=[
                "Set the end date before the start date and run the report.",
                "Set a date far in the future and run it.",
            ],
            expected=(
                "Both are refused with a clear message. No nonsense figures are produced."
            ),
            priority=MEDIUM, role=MANAGER,
        ),
        Case(
            area="No invented figures",
            title="Reports never show made-up or cached-stale numbers",
            kind=NEGATIVE,
            pre="You can create a ticket while the report is open.",
            steps=[
                "Run a report and note a count.",
                "Create a new ticket that falls inside the report's filters.",
                "Re-run the report.",
            ],
            expected=(
                "The count goes up by one. Reports are built from live data, so a figure "
                "that never moves means something is wrong."
            ),
            priority=CRITICAL, uat=True, role=MANAGER, req="R28",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Large ranges",
            title="A report over a very large date range still completes",
            kind=EDGE,
            pre="The test system has a lot of history.",
            steps=[
                "Run the report across the widest available date range.",
                "Time how long it takes.",
            ],
            expected=(
                "It completes in a reasonable time with a loading indicator while it works. "
                "It does not time out or freeze the browser."
            ),
            priority=HIGH, role=MANAGER,
        ),
        Case(
            area="Time zone",
            title="Report date ranges use UAE working days consistently",
            kind=EDGE,
            pre="You know a ticket created very late in the evening.",
            steps=[
                "Run a report for exactly the day that ticket was created.",
                "Check whether it is counted in that day.",
            ],
            expected=(
                "The ticket falls in the correct UAE day. A ticket created at 11pm must not "
                "land in the following day's figures."
            ),
            priority=HIGH, uat=True, role=MANAGER,
        ),
        Case(
            area="Dashboard refresh",
            title="Dashboard numbers update after a change",
            kind=EDGE,
            pre="You are on the dashboard.",
            steps=[
                "Note the open ticket count.",
                "Resolve a ticket in another tab.",
                "Refresh the dashboard.",
            ],
            expected="The counts move to reflect the change.",
            priority=MEDIUM, role=SUPERVISOR,
        ),
        Case(
            area="Audit volume",
            title="A ticket with a very long history is still readable",
            kind=EDGE,
            pre="A ticket has 100 or more history entries.",
            steps=[
                "Open its history tab and scroll or page through.",
            ],
            expected=(
                "The list pages or scrolls smoothly in a sensible order and does not slow "
                "the page down."
            ),
            priority=MEDIUM, role=COMPLIANCE,
        ),
        Case(
            area="Charts",
            title="Charts stay readable with very few and very many categories",
            kind=EDGE,
            pre="You can filter the dashboard down and open it up.",
            steps=[
                "Filter so a chart has only one category.",
                "Remove the filters so it has as many as possible.",
            ],
            expected=(
                "Both are readable - labels do not overlap into an unreadable mess and the "
                "single-value case does not look broken."
            ),
            priority=LOW, role=SUPERVISOR,
        ),
        Case(
            area="Printing",
            title="A report prints or saves as PDF readably",
            kind=EDGE,
            pre="A report is on screen.",
            steps=[
                "Use the browser print preview.",
            ],
            expected=(
                "The report fits the page, charts and tables are not cut in half, and the "
                "date range and filters are visible on the printout."
            ),
            priority=LOW, role=MANAGER,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Report access",
            title="An agent cannot open the reports screen",
            kind=ACCESS,
            pre="You are a Customer Care Agent.",
            steps=[
                "Check Reports is not in your menu.",
                "Type the reports address directly.",
            ],
            expected="It is not in the menu and the direct address is refused.",
            priority=CRITICAL, uat=True, role=AGENT, req="R28",
        ),
        Case(
            area="Report scope",
            title="A report respects what the person is allowed to see",
            kind=ACCESS,
            pre="Tickets exist in several departments.",
            steps=[
                "Sign in as a head of department and run the report.",
                "Sign in as a manager and run the same report for the same period.",
                "Compare the figures.",
            ],
            expected=(
                "Confirm with the business whether the head of department should see only "
                "their own department or the whole organisation, and check the behaviour "
                "matches. Whatever the answer, it must be deliberate and consistent."
            ),
            priority=CRITICAL, uat=True, role=f"{HOD}, then {MANAGER}", ready=PARTLY,
        ),
        Case(
            area="Audit access",
            title="An agent cannot open the organisation-wide audit trail",
            kind=ACCESS,
            pre="You are a Customer Care Agent.",
            steps=[
                "Check Audit Trail is not in your menu.",
                "Type the audit trail address directly.",
            ],
            expected=(
                "Both are refused. The agent can still see the history of tickets they are "
                "allowed to work on."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Ticket history scope",
            title="The history tab of a ticket outside your scope cannot be opened",
            kind=ACCESS,
            pre="You have the address of that tab for a ticket you cannot see.",
            steps=[
                "Paste the address into your browser.",
            ],
            expected="It is refused as not found.",
            priority=CRITICAL, role=HANDLER,
        ),
        Case(
            area="Compliance access",
            title="A compliance officer can read the full audit trail",
            kind=ACCESS,
            pre="You are signed in as a Compliance Officer.",
            steps=[
                "Open the Audit Trail screen.",
                "Filter and search it.",
                "Look for any edit or delete control.",
            ],
            expected=(
                "Full read access for oversight, with no ability to change anything. This is "
                "exactly what the role is for."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R29",
        ),
        Case(
            area="Not built yet",
            title="Automatic scheduled report emails are not in this release",
            kind=ACCESS,
            pre="None.",
            steps=[
                "Confirm with the team whether scheduled report delivery is in scope.",
                "Check no scheduling option appears on the reports screen.",
            ],
            expected=(
                "Scheduling is correctly absent if it was not in scope. Do NOT raise a bug - "
                "listed only so it is not forgotten at sign-off."
            ),
            priority=LOW, role=MANAGER, ready=NOT_BUILT,
        ),
    ],
)
