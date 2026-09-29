"""Modules 4-6: Manual Ticket Creation, Ticket List & Details, AI Classification & Assignment."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, NOT_BUILT, PARTLY
from common import Case, Module
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR

# =====================================================================================
M04 = Module(
    code="M04",
    name="Manual Ticket Creation",
    plain_summary=(
        "Staff log walk-in and phone cases by hand using a form. These tickets are typed "
        "by a person, so they must never show any AI-generated content. Website forms "
        "that arrive on their own are module M16, not this one."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Creating an enquiry",
            title="An agent can log a phone enquiry by hand",
            pre="You are signed in as a Customer Care Agent.",
            steps=[
                "Open Enquiries and click New Enquiry.",
                "Fill in the customer name, contact number, email and the description of "
                "what they asked.",
                "Choose the channel (for example Phone) and the enquiry type.",
                "Click Save.",
            ],
            expected=(
                "The enquiry is created and opens on its own detail page. It has a reference "
                "number that starts with INQ, the current year, and a four digit number - for "
                "example INQ-2026-0001."
            ),
            data="Channel: Phone / Customer: Test Customer / Description: Renewal price query",
            priority=CRITICAL, uat=True, role=AGENT, req="R07",
        ),
        Case(
            area="Creating a complaint",
            title="An agent can log a walk-in complaint by hand",
            pre="You are signed in as a Customer Care Agent.",
            steps=[
                "Open Complaints and click New Complaint.",
                "Fill in the customer details and the complaint description.",
                "Choose the channel Walk-in and pick a complaint category and severity.",
                "Save.",
            ],
            expected=(
                "The complaint is created with a reference number starting COM - for example "
                "COM-2026-0001 - and a response deadline is set automatically."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R07, R27",
        ),
        Case(
            area="No AI content",
            title="A hand-typed ticket shows no AI labels or AI sections",
            pre="You have just created a ticket by hand.",
            steps=[
                "Open the ticket you just typed in.",
                "Look for an 'AI Generated' badge anywhere on the page.",
                "Look for the Enquiry Summary section.",
                "Look for the Recommended Action Plan tab.",
            ],
            expected=(
                "None of these appear. A hand-typed ticket must never display AI-written "
                "content, because a person entered the details, not the system."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Customer lookup while creating",
            title="An agent can find an existing customer while filling in the form",
            pre="You know a valid test policy number.",
            steps=[
                "Start a new enquiry.",
                "Use the customer search and enter the policy number.",
                "Pick the customer from the results.",
            ],
            expected=(
                "The customer's known details fill in automatically so the agent does not "
                "retype them. Sensitive numbers are shown partly hidden."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R21",
        ),
        Case(
            area="Channels",
            title="All the manual channels can be chosen",
            pre="You are on the new ticket form.",
            steps=[
                "Open the channel list.",
                "Create one ticket for each of Phone, Walk-in, Website and Website Callback.",
            ],
            expected=(
                "Every channel is available and is saved correctly on the ticket, so reports "
                "can later split cases by how they arrived. Note the Website channels here "
                "are for an agent logging a website case by hand - a form the customer "
                "submits themselves arrives automatically and is covered in M16."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R05",
        ),
        Case(
            area="Saving",
            title="A newly created ticket appears in the list straight away",
            pre="You have just saved a new enquiry.",
            steps=[
                "Save a new enquiry and note its reference number.",
                "Go to the enquiries list.",
                "Search for the reference number.",
            ],
            expected="The ticket is in the list immediately, with the right status and deadline.",
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Audit",
            title="Creating a ticket by hand is recorded in the history",
            pre="You have just created a ticket.",
            steps=[
                "Open the new ticket and go to its history or audit tab.",
            ],
            expected=(
                "There is an entry saying the ticket was created, by whom, and at what date "
                "and time."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R29",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Required fields",
            title="An empty form cannot be saved",
            kind=NEGATIVE,
            pre="You are on the new enquiry form.",
            steps=[
                "Without typing anything, click Save.",
            ],
            expected=(
                "Nothing is created. Every required field is marked with a message telling "
                "you what is missing. The page scrolls to the first problem."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Contact details",
            title="An invalid email address is refused",
            kind=NEGATIVE,
            pre="You are on the new ticket form.",
            steps=[
                "Enter 'abc' in the customer email box.",
                "Fill everything else in correctly and save.",
            ],
            expected="Saving is refused with a message asking for a valid email address.",
            data="abc",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Contact details",
            title="An invalid UAE phone number is refused",
            kind=NEGATIVE,
            pre="You are on the new ticket form.",
            steps=[
                "Enter '123' as the phone number and save.",
                "Try again with letters in the phone box.",
            ],
            expected=(
                "Both are refused with a message explaining the expected phone number format."
            ),
            data="123 / abcdefgh",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Cancel",
            title="Cancelling the form does not create a ticket",
            kind=NEGATIVE,
            pre="You are on the new ticket form with details typed in.",
            steps=[
                "Fill in the form completely.",
                "Click Cancel or navigate away.",
                "Confirm any 'are you sure' prompt.",
                "Check the ticket list.",
            ],
            expected=(
                "No ticket is created and no reference number is used up. If a confirmation "
                "prompt appears, choosing to stay keeps your typed details."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Double submit",
            title="Clicking Save twice does not create two tickets",
            kind=NEGATIVE,
            pre="You are on a completed new ticket form.",
            steps=[
                "Fill in the form.",
                "Click Save twice quickly.",
                "Check the ticket list.",
            ],
            expected=(
                "Only one ticket is created. The Save button becomes disabled or shows a "
                "spinner after the first click."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Bad category",
            title="A complaint cannot be saved without a category and severity",
            kind=NEGATIVE,
            pre="You are on the new complaint form.",
            steps=[
                "Fill in everything except the category and the severity.",
                "Save.",
            ],
            expected=(
                "Saving is refused. Category and severity are needed because they decide the "
                "deadline and the escalation path."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R16",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Long description",
            title="A very long description is saved in full",
            kind=EDGE,
            pre="You are on the new ticket form.",
            steps=[
                "Paste 5,000 characters into the description box.",
                "Save, then reopen the ticket.",
            ],
            expected=(
                "Either the box politely caps the length while you type with a visible "
                "counter, or the full text is saved and shown scrollable. Text is never "
                "silently cut in half."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Arabic input",
            title="A ticket typed in Arabic saves and displays correctly",
            kind=EDGE,
            pre="You are on the new ticket form.",
            steps=[
                "Type the customer name and description in Arabic.",
                "Save and reopen the ticket.",
                "Find the ticket by searching the Arabic name.",
            ],
            expected=(
                "Arabic saves, displays right to left, and can be searched. No question "
                "marks or boxes appear instead of letters."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Special characters",
            title="Quotes, ampersands and emojis do not break the ticket",
            kind=EDGE,
            pre="You are on the new ticket form.",
            steps=[
                "Type a description containing quotes, an ampersand, angle brackets and an "
                "emoji.",
                "Save and reopen.",
            ],
            expected=(
                "The text is shown back exactly as typed. Nothing is executed, no part of "
                "the page disappears, and no code appears on screen."
            ),
            data="Customer said \"it's <urgent> & needs help\" 😀",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Reference numbers",
            title="Two agents creating tickets at the same moment get different numbers",
            kind=EDGE,
            pre="Two agents are signed in on different machines.",
            steps=[
                "Both agents fill in a new enquiry form.",
                "Both click Save at the same moment.",
                "Compare the two reference numbers.",
            ],
            expected=(
                "The two reference numbers are different and run in sequence. The same "
                "number is never given to two tickets."
            ),
            priority=CRITICAL, role=f"Two {AGENT}s", req="R33",
        ),
        Case(
            area="Reference numbers",
            title="The number sequence restarts correctly in a new year",
            kind=EDGE,
            pre="Ask the team to move the test system's clock to 1 January.",
            steps=[
                "Note the last reference number of the old year.",
                "Have the team roll the test date into the new year.",
                "Create a new enquiry.",
            ],
            expected=(
                "The new ticket uses the new year in its number and the counter starts again "
                "from 0001 - for example INQ-2027-0001."
            ),
            priority=HIGH, role=AGENT, req="R33", ready=PARTLY,
            notes="Needs the team to change the test system date - cannot be done from the screen.",
        ),
        Case(
            area="Session expiry",
            title="A form left open for a long time does not lose the typed work silently",
            kind=EDGE,
            pre="You are on the new ticket form.",
            steps=[
                "Fill in the form completely.",
                "Leave it untouched long enough for the session to expire.",
                "Click Save.",
            ],
            expected=(
                "You are told your session expired and asked to sign in again. Ideally your "
                "typed details are still there afterwards. At minimum you are warned before "
                "anything is lost - you never get a silent failure."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Attachments on manual tickets",
            title="Attaching a file while creating a ticket by hand",
            kind=EDGE,
            pre="You are on the new ticket form.",
            steps=[
                "Look for an attachment control on the manual creation form.",
                "If present, attach a PDF and save.",
            ],
            expected=(
                "Either attaching is available and the file is saved with the ticket, or "
                "there is no such control at all. Confirm which is expected with the team "
                "before logging a bug."
            ),
            priority=MEDIUM, role=AGENT, ready=PARTLY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can create",
            title="Only roles allowed to create tickets see the New button",
            kind=ACCESS,
            pre="You have several role sign-ins.",
            steps=[
                "Sign in as each role in turn and go to the enquiries and complaints lists.",
                "Note which roles see the New Enquiry and New Complaint buttons.",
                "For a role that does not, type the new-ticket address directly.",
            ],
            expected=(
                "The button matches the agreed role matrix, and typing the address directly "
                "is refused for roles that should not create tickets."
            ),
            priority=CRITICAL, uat=True, role="All roles",
        ),
        Case(
            area="Complaint creation",
            title="A role that can create enquiries but not complaints is blocked correctly",
            kind=ACCESS,
            pre="Identify a role with enquiry rights but not complaint rights from the matrix.",
            steps=[
                "Sign in as that role.",
                "Confirm New Enquiry works.",
                "Type the new complaint address directly.",
            ],
            expected="New Enquiry works, new complaint is refused with a clear message.",
            priority=HIGH, role="Role from the matrix",
        ),
        Case(
            area="Department field",
            title="A department contact person cannot create a ticket for another department",
            kind=ACCESS,
            pre="You are a Department Contact Person for Motor Claims.",
            steps=[
                "Start a new ticket.",
                "Try to set the department to one you do not belong to.",
            ],
            expected=(
                "Either only your own department is offered, or saving to another department "
                "is refused."
            ),
            priority=HIGH, role=POC,
        ),
        Case(
            area="Read-only role",
            title="A compliance officer cannot create tickets",
            kind=ACCESS,
            pre="You are signed in as a Compliance Officer.",
            steps=[
                "Look for New Enquiry and New Complaint buttons.",
                "Type the new ticket address directly.",
            ],
            expected="Neither button is present and the direct address is refused.",
            priority=HIGH, role=COMPLIANCE,
        ),
    ],
)

# =====================================================================================
M05 = Module(
    code="M05",
    name="Ticket List and Details",
    plain_summary=(
        "The main working area - lists of enquiries, complaints and discarded items with "
        "search, filters and paging, plus the full detail page of one ticket, editing, and "
        "internal notes."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Viewing lists",
            title="The enquiries and complaints lists open and show the right tickets",
            pre="There are tickets of both types in the system.",
            steps=[
                "Open the Enquiries list and read the ticket types shown.",
                "Open the Complaints list and read the ticket types shown.",
            ],
            expected=(
                "The Enquiries list shows only enquiries and the Complaints list shows only "
                "complaints. Each row shows the reference number, subject, customer, status, "
                "department and deadline."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Opening a ticket",
            title="Clicking a row opens the full ticket",
            pre="You are on the enquiries list.",
            steps=[
                "Click any ticket row.",
            ],
            expected=(
                "The detail page opens showing the customer, the full description, the "
                "status, the assigned person, the department, the deadline and the tabs for "
                "history and related information."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Search",
            title="Searching by reference number finds the exact ticket",
            pre="You know an existing reference number.",
            steps=[
                "Type the full reference number into the search box.",
                "Then try searching just the numeric part.",
            ],
            expected=(
                "The full reference number returns exactly that one ticket. The partial "
                "search returns it too, along with any other matches."
            ),
            data="For example INQ-2026-0001",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Search",
            title="Searching by customer name, email and subject works",
            pre="You know a ticket's customer name, email and subject.",
            steps=[
                "Search by part of the customer name.",
                "Search by the customer email address.",
                "Search by a word from the subject.",
            ],
            expected="Each search returns the ticket. Searching is not case sensitive.",
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Filters",
            title="Filters narrow the list correctly",
            pre="You are on a ticket list with plenty of tickets.",
            steps=[
                "Filter by status and check every row matches.",
                "Add a department filter on top and check again.",
                "Add a date range and check again.",
                "Clear all filters.",
            ],
            expected=(
                "Each filter narrows the list, and two filters together narrow it further. "
                "The chosen filters are shown as removable chips. Clearing brings the full "
                "list back."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Sorting",
            title="Columns can be sorted both ways",
            pre="You are on a ticket list.",
            steps=[
                "Sort by date created, newest first, then oldest first.",
                "Sort by deadline.",
                "Sort by status.",
            ],
            expected=(
                "The order changes correctly each time and the arrow indicator shows which "
                "way it is sorted."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Paging",
            title="Moving between pages works",
            pre="There are more tickets than fit on one page.",
            steps=[
                "Go to page two, then the last page, then back to page one.",
                "Change the page size if that option exists.",
            ],
            expected=(
                "Different tickets appear on each page, no ticket is shown twice, and the "
                "total count is correct."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Editing",
            title="An agent can edit a ticket's details",
            pre="You are on a ticket you are allowed to edit.",
            steps=[
                "Click Edit.",
                "Change the description and the customer phone number.",
                "Save and reopen the ticket.",
            ],
            expected=(
                "Both changes are saved, and the history tab records what changed, who "
                "changed it and when."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R29",
        ),
        Case(
            area="Internal notes",
            title="An agent can add an internal note that the customer never sees",
            pre="You are on a ticket.",
            steps=[
                "Add an internal note.",
                "Save.",
                "Reopen the ticket and check the notes area.",
            ],
            expected=(
                "The note is saved with your name and the time. It is clearly marked as "
                "internal and is never included in anything sent to the customer."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Discarded list",
            title="Discarded items are kept on their own separate list",
            pre="At least one ticket has been discarded.",
            steps=[
                "Open the Discarded list.",
                "Confirm the discarded ticket is there.",
                "Go back to the Enquiries list and confirm it is not there.",
            ],
            expected=(
                "Discarded items appear only on the discarded list with a JNK reference "
                "number, and never clutter the working lists."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Search",
            title="Searching for something that does not exist shows a helpful message",
            kind=NEGATIVE,
            pre="You are on a ticket list.",
            steps=[
                "Search for 'zzzznonexistent'.",
            ],
            expected=(
                "A friendly 'no tickets found' message appears with a button to clear the "
                "search. The table does not go blank with no explanation and no error appears."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Opening a ticket",
            title="Opening a ticket that does not exist is handled cleanly",
            kind=NEGATIVE,
            pre="You are signed in.",
            steps=[
                "Take a ticket address and change the identifier to a made-up one.",
                "Open it.",
            ],
            expected=(
                "A clear 'ticket not found' page appears with a way back to the list. No "
                "raw error message or blank screen."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Editing",
            title="Saving an edit with a required field cleared is refused",
            kind=NEGATIVE,
            pre="You are editing a ticket.",
            steps=[
                "Delete the contents of a required field such as the description.",
                "Save.",
            ],
            expected="Saving is refused with a message. The original value is not lost.",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Editing",
            title="A closed ticket cannot be edited",
            kind=NEGATIVE,
            pre="A closed ticket exists.",
            steps=[
                "Open the closed ticket.",
                "Look for the Edit button.",
                "Try the edit address directly.",
            ],
            expected=(
                "Editing is not offered and the direct address is refused with a message "
                "explaining the ticket is closed."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Internal notes",
            title="An empty internal note cannot be saved",
            kind=NEGATIVE,
            pre="You are on a ticket.",
            steps=[
                "Click to add a note and save without typing anything.",
                "Try again with only spaces.",
            ],
            expected="Both are refused. No blank note is added to the ticket.",
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Internal notes",
            title="An internal note cannot be edited or deleted after saving",
            kind=NEGATIVE,
            pre="You have added an internal note.",
            steps=[
                "Look for edit or delete controls on the saved note.",
                "Sign in as an administrator and look again.",
            ],
            expected=(
                "Notes are permanent for everybody. Confirm with the team whether this is "
                "the agreed behaviour before logging a bug."
            ),
            priority=MEDIUM, role=f"{AGENT}, then {ADMIN}", ready=PARTLY,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Large list",
            title="The list stays usable with thousands of tickets",
            kind=EDGE,
            pre="The test system has several thousand tickets.",
            steps=[
                "Open the full ticket list with no filters.",
                "Time how long the first page takes to appear.",
                "Sort and then filter and time each one.",
            ],
            expected=(
                "The list appears in a few seconds, sorting and filtering stay responsive, "
                "and the browser does not freeze."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Filters",
            title="Filters survive going into a ticket and coming back",
            kind=EDGE,
            pre="You are on a filtered ticket list.",
            steps=[
                "Apply two filters and go to page three.",
                "Open a ticket.",
                "Press Back.",
            ],
            expected=(
                "You return to the same filtered list on the same page. You do not have to "
                "set the filters up again."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Filters",
            title="A filter combination with no matches is handled properly",
            kind=EDGE,
            pre="You are on a ticket list.",
            steps=[
                "Combine filters that cannot both be true - for example a department with "
                "no complaints plus the complaint type.",
            ],
            expected=(
                "An empty-state message appears with the active filters still visible so you "
                "can see why nothing matched, and a way to clear them."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Two people editing",
            title="Two people editing the same ticket at the same time",
            kind=EDGE,
            pre="Two agents are signed in on different machines.",
            steps=[
                "Both open the same ticket and click Edit.",
                "Agent A changes the description and saves.",
                "Agent B changes the phone number and saves a moment later.",
                "Reopen the ticket and read the history.",
            ],
            expected=(
                "Neither change is silently lost, or the second person is warned the ticket "
                "changed. The history shows both edits with names and times."
            ),
            priority=HIGH, role=f"Two {AGENT}s",
        ),
        Case(
            area="Search",
            title="Searching with unusual characters does not break anything",
            kind=EDGE,
            pre="You are on a ticket list.",
            steps=[
                "Search for a single quote character.",
                "Search for a percent sign.",
                "Search for a very long string of 500 characters.",
            ],
            expected=(
                "Each search returns a normal result or an empty state. No error appears, "
                "no code is shown on screen, and the page keeps working."
            ),
            data="' / % / 500 characters of text",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Long content",
            title="A ticket with very long content displays without breaking the layout",
            kind=EDGE,
            pre="A ticket exists with a very long description and long customer name.",
            steps=[
                "Open the ticket on a normal laptop screen.",
                "Open it again on a narrow window or tablet width.",
            ],
            expected=(
                "Text wraps or scrolls inside its own area. Nothing spills across the page "
                "and no horizontal scrollbar appears on the whole page."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Refresh",
            title="A ticket updated by somebody else shows the new information on refresh",
            kind=EDGE,
            pre="Two people are signed in.",
            steps=[
                "Person A opens a ticket.",
                "Person B changes its status.",
                "Person A refreshes the page.",
            ],
            expected="Person A sees the new status. No stale information is shown after refresh.",
            priority=MEDIUM, role="Two staff members",
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Ticket type visibility",
            title="A complaint handler sees complaints but not enquiries",
            kind=ACCESS,
            pre="You are signed in as a Complaint Handler.",
            steps=[
                "Check whether the Enquiries menu item is present.",
                "Type the enquiries list address directly.",
                "Take an enquiry reference from a colleague and try to open it directly.",
            ],
            expected=(
                "Enquiries are not in the menu, the list is refused, and the individual "
                "enquiry shows as not found. This is a data-visibility rule, so treat any "
                "failure here as serious."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R39",
        ),
        Case(
            area="Own-assigned scope",
            title="A complaint handler only sees complaints assigned to them",
            kind=ACCESS,
            pre="Complaints exist that are assigned to somebody else.",
            steps=[
                "Sign in as a Complaint Handler.",
                "Count the complaints in your list.",
                "Ask a supervisor for the reference of a complaint assigned to a different "
                "handler and try to open it directly.",
            ],
            expected=(
                "Your list contains only complaints assigned to you. The other handler's "
                "complaint shows as not found - it does not say 'forbidden', because that "
                "would confirm it exists."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R39",
        ),
        Case(
            area="Own-department scope",
            title="A department contact person only sees their own department's tickets",
            kind=ACCESS,
            pre="Tickets exist in at least two departments.",
            steps=[
                "Sign in as a Department Contact Person for Motor Claims.",
                "Check every ticket in your list belongs to Motor Claims.",
                "Try to open a Finance department ticket directly by its address.",
            ],
            expected=(
                "Only Motor Claims tickets are listed. The Finance ticket shows as not found."
            ),
            priority=CRITICAL, uat=True, role=POC, req="R39",
        ),
        Case(
            area="Department scope",
            title="A ticket with no department set does not leak to department-scoped users",
            kind=ACCESS,
            pre="A ticket exists that has not yet been given a department.",
            steps=[
                "Sign in as a Department Contact Person.",
                "Search for that ticket in your list.",
                "Try to open it directly by its address.",
            ],
            expected=(
                "The ticket is not visible and cannot be opened. When the department is "
                "unknown, access is refused rather than allowed."
            ),
            priority=CRITICAL, role=POC,
        ),
        Case(
            area="Organisation-wide scope",
            title="A manager can see every ticket across all departments",
            kind=ACCESS,
            pre="Tickets exist in several departments.",
            steps=[
                "Sign in as a Manager.",
                "Open the ticket list with no filters.",
                "Filter by three different departments in turn.",
            ],
            expected="Tickets from every department are visible.",
            priority=HIGH, uat=True, role=MANAGER, req="R39",
        ),
        Case(
            area="Sub-pages",
            title="Every tab of a ticket is protected, not just the main page",
            kind=ACCESS,
            pre="You have the address of a ticket you are not allowed to see.",
            steps=[
                "Try each sub-page of that ticket in turn: history, deadline, investigation, "
                "action plan, customer records, compare duplicate, edit and attachments.",
            ],
            expected=(
                "Every single one is refused with 'not found'. It is not enough for the main "
                "page to be protected - a gap on any tab is a data leak."
            ),
            priority=CRITICAL, uat=True, role=HANDLER,
        ),
        Case(
            area="Editing rights",
            title="A role that can view but not edit sees no Edit button and cannot force it",
            kind=ACCESS,
            pre="Sign in as a role that has view-only rights on tickets.",
            steps=[
                "Open a ticket you can see.",
                "Confirm there is no Edit button, no status control and no note box.",
                "Type the edit address directly.",
            ],
            expected="No editing controls are shown and the direct address is refused.",
            priority=CRITICAL, uat=True, role=COMPLIANCE,
        ),
        Case(
            area="Export",
            title="Exported ticket data respects what the person is allowed to see",
            kind=ACCESS,
            pre="An export or download option exists on the ticket list.",
            steps=[
                "Sign in as a Department Contact Person and export the ticket list.",
                "Open the exported file and check every row.",
            ],
            expected=(
                "The export contains only the tickets that person can see on screen. Export "
                "must never be a way around the visibility rules."
            ),
            priority=CRITICAL, uat=True, role=POC, ready=PARTLY,
            notes="Only run if an export option exists on the list screen.",
        ),
    ],
)

# =====================================================================================
M06 = Module(
    code="M06",
    name="AI Classification and Assignment",
    short="AI Routing and Assignment",
    plain_summary=(
        "The system reads an incoming ticket, decides its type, category and department, "
        "then picks an agent to handle it. Assignment rotates fairly and respects how much "
        "work each person already has."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Classification",
            title="An emailed enquiry is classified as an enquiry automatically",
            pre="The email connection and the AI pipeline are both running.",
            steps=[
                "Send an email that is clearly a question - for example asking for a renewal "
                "quote.",
                "Wait for the ticket to appear and for processing to finish.",
                "Open the ticket.",
            ],
            expected=(
                "The ticket is marked as an Enquiry, with a category, sub-category and "
                "department filled in, and an AI Generated badge on the classification card."
            ),
            data="Subject: Please quote my motor renewal",
            priority=CRITICAL, uat=True, role="System (no user action)", req="R08, R09",
        ),
        Case(
            area="Classification",
            title="An emailed complaint is classified as a complaint automatically",
            pre="The email connection and the AI pipeline are both running.",
            steps=[
                "Send an email that clearly complains - for example about a delayed claim "
                "settlement and poor service.",
                "Wait, then open the resulting ticket.",
            ],
            expected=(
                "The ticket is marked as a Complaint with a complaint category and a "
                "severity, and it gets a COM reference number."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R08, R23",
        ),
        Case(
            area="Routing",
            title="A ticket is routed to the correct department",
            pre="You have example emails for three different business areas.",
            steps=[
                "Send one email about a motor claim, one about a travel policy and one about "
                "a payment or refund.",
                "Wait, then check the department on each resulting ticket.",
            ],
            expected=(
                "Each ticket lands in the right department. Compare against the agreed "
                "routing rules and record any mismatch as a classification accuracy issue."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R11",
        ),
        Case(
            area="Assignment",
            title="A ticket is automatically given to an available agent",
            pre="Several agents are active in the target department's pool.",
            steps=[
                "Let a new ticket be classified.",
                "Open it and look at the assigned person.",
                "Check the person's notification list.",
            ],
            expected=(
                "An active agent from the right pool is assigned automatically and that "
                "person is notified. The ticket does not sit unassigned."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R12",
        ),
        Case(
            area="Assignment",
            title="Work is shared out fairly, not all given to one person",
            pre="At least three active agents are in the same pool.",
            steps=[
                "Create or send six tickets that all route to the same department.",
                "List who each one was assigned to.",
            ],
            expected=(
                "The six tickets are spread across the available agents in rotation rather "
                "than all landing on the first person."
            ),
            priority=HIGH, uat=True, role="System (no user action)", req="R12",
        ),
        Case(
            area="Assignment",
            title="An agent who is already full is skipped",
            pre="Ask the team to set a low ticket limit for one test agent and fill them up.",
            steps=[
                "Fill one agent up to their limit.",
                "Send more tickets to the same department.",
                "Check who they were assigned to.",
            ],
            expected=(
                "The full agent gets nothing more. New tickets go to colleagues who still "
                "have capacity."
            ),
            priority=HIGH, uat=True, role="System (no user action)", req="R12, R44",
        ),
        Case(
            area="Priority",
            title="Urgent tickets are marked with a higher priority",
            pre="The AI pipeline is running.",
            steps=[
                "Send an email that reads as urgent - for example an accident with injury.",
                "Send a routine one for comparison.",
                "Compare the priority shown on both tickets.",
            ],
            expected="The urgent one gets a higher priority than the routine one.",
            priority=HIGH, uat=True, role="System (no user action)", req="R13",
        ),
        Case(
            area="AI badge",
            title="AI-processed tickets are clearly marked as AI generated",
            pre="A ticket created from email has finished processing.",
            steps=[
                "Open an email-created ticket.",
                "Look for the AI Generated badge on the classification, priority and routing "
                "cards.",
                "Open the Recommended Action Plan tab.",
                "Read the Enquiry Summary section.",
            ],
            expected=(
                "The badge is shown on the AI-written cards, and the summary and action plan "
                "are available. Staff can always tell what the system wrote and what a person "
                "wrote."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Manual override",
            title="A supervisor can correct the department the system chose",
            pre="A ticket has been routed to the wrong department.",
            steps=[
                "Open the ticket as a supervisor.",
                "Change the department to the correct one.",
                "Save and check the history.",
            ],
            expected=(
                "The department changes, the ticket moves into the new department's queue, "
                "and the history records who overrode it and when."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R11, R29",
        ),
        Case(
            area="Manual override",
            title="A supervisor can reassign a ticket to a different agent",
            pre="A ticket is assigned to agent A.",
            steps=[
                "Open the ticket as a supervisor.",
                "Reassign it to agent B with a reason.",
                "Check both agents' notifications and the ticket history.",
            ],
            expected=(
                "The ticket now belongs to agent B, agent B is notified, and the change is "
                "in the history with the reason."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R12",
        ),
        Case(
            area="AI decision log",
            title="Every AI decision is recorded so it can be reviewed later",
            pre="A ticket has been processed by the AI.",
            steps=[
                "Open the ticket's history or audit tab.",
                "Look for the AI classification entry.",
            ],
            expected=(
                "There is a record of what the system decided, when, and on what basis, so a "
                "wrong decision can be traced afterwards."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R29, R35",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Unclear content",
            title="An email the system cannot understand is still handled safely",
            kind=NEGATIVE,
            pre="The AI pipeline is running.",
            steps=[
                "Send an email containing only nonsense text or a single word.",
                "Wait, then open the resulting ticket.",
            ],
            expected=(
                "A ticket still exists. The category is left blank or marked as needing "
                "review, and it appears in a queue for a person to look at. It is never "
                "silently dropped."
            ),
            data="Subject: hi / Body: ?",
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="AI unavailable",
            title="If the AI service is down, tickets are still created",
            kind=NEGATIVE,
            pre="Ask the team to stop the AI service on the test system.",
            steps=[
                "Have the team stop the AI service.",
                "Send an email.",
                "Check the ticket list.",
                "Have the team restart the service.",
            ],
            expected=(
                "The ticket is created with the raw email content and no classification. "
                "Nothing is lost. Once the service is back the ticket can be classified or "
                "handled by a person."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R03",
        ),
        Case(
            area="No agents available",
            title="A ticket for a department with no active agents does not vanish",
            kind=NEGATIVE,
            pre="Ask the team to deactivate every agent in one test department.",
            steps=[
                "Deactivate all agents in the test department.",
                "Send a ticket that routes there.",
                "Look for the ticket.",
            ],
            expected=(
                "The ticket exists and sits unassigned in that department's queue, visible "
                "to a supervisor. It is never dropped or assigned to a deactivated person."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R12",
        ),
        Case(
            area="Manual tickets",
            title="A hand-typed ticket is not given a fake AI classification",
            kind=NEGATIVE,
            pre="You have created a ticket by hand.",
            steps=[
                "Open the hand-typed ticket.",
                "Check the classification cards for an AI Generated badge.",
                "Check whether an action plan tab exists.",
            ],
            expected=(
                "No AI badge and no action plan tab. The category shown is the one the agent "
                "typed, presented as human-entered."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Category values",
            title="The system only uses categories from the approved list",
            kind=NEGATIVE,
            pre="You have the approved category list from the team.",
            steps=[
                "Look at the categories on twenty recently classified tickets.",
                "Compare each one against the approved list.",
            ],
            expected=(
                "Every value matches the approved list exactly, including spelling and "
                "punctuation. No invented or near-miss categories appear."
            ),
            priority=HIGH, role=SUPERVISOR, req="R09",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Mixed content",
            title="An email that is both a question and a complaint is handled sensibly",
            kind=EDGE,
            pre="The AI pipeline is running.",
            steps=[
                "Send an email that asks a renewal question and also complains about waiting "
                "times.",
                "Open the resulting ticket.",
            ],
            expected=(
                "The ticket is classified one way with a sensible reason, and a person can "
                "correct it. Two conflicting tickets are not created."
            ),
            priority=HIGH, uat=True, role="System (no user action)",
        ),
        Case(
            area="Arabic content",
            title="An Arabic email is classified as well as an English one",
            kind=EDGE,
            pre="The AI pipeline is running.",
            steps=[
                "Send the same complaint text in Arabic and in English from two mailboxes.",
                "Compare the classification, department and priority on both tickets.",
            ],
            expected=(
                "Both are classified the same way. Arabic is not treated as unclassifiable."
            ),
            priority=HIGH, uat=True, role="System (no user action)",
        ),
        Case(
            area="Timing",
            title="A ticket can be opened and worked on before the AI finishes",
            kind=EDGE,
            pre="The AI pipeline takes a noticeable amount of time on the test system.",
            steps=[
                "Send an email and open the ticket the moment it appears.",
                "Try to read it and add an internal note before classification completes.",
                "Refresh once processing finishes.",
            ],
            expected=(
                "The ticket is readable and workable straight away, shows that processing is "
                "in progress, and updates when the classification arrives. Your note is not "
                "lost."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Assignment",
            title="An agent going inactive mid-flow does not strand their new tickets",
            kind=EDGE,
            pre="An agent is about to be deactivated.",
            steps=[
                "Assign a fresh ticket to a test agent.",
                "Deactivate that agent.",
                "Look at the ticket.",
            ],
            expected=(
                "The ticket is visible to the supervisor as needing reassignment rather than "
                "sitting silently with a person who can no longer sign in."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Assignment",
            title="Two tickets arriving at the same instant are not both given to one person",
            kind=EDGE,
            pre="Two agents are active in a pool.",
            steps=[
                "Send two emails to the same department at the same moment.",
                "Check who each ticket went to.",
            ],
            expected=(
                "The rotation still works and the two tickets are shared out. Both landing "
                "on the same agent when a colleague was free is a defect."
            ),
            priority=MEDIUM, role="System (no user action)",
        ),
        Case(
            area="Repeat classification",
            title="Re-running classification does not duplicate anything",
            kind=EDGE,
            pre="Ask the team whether classification can be re-triggered on the test system.",
            steps=[
                "Have the team re-run classification on an already-processed ticket.",
                "Check the ticket and its history.",
            ],
            expected=(
                "The ticket is updated, not duplicated. The history shows both runs, and the "
                "reference number, the deadline and the assignment do not double up."
            ),
            priority=HIGH, role="System (no user action)", ready=PARTLY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can override",
            title="An agent cannot change the department or reassign to somebody else",
            kind=ACCESS,
            pre="You are a Customer Care Agent on a ticket assigned to you.",
            steps=[
                "Look for a department change control and an assign-to-somebody-else control.",
                "If either is visible, try to use it.",
            ],
            expected=(
                "Neither is available, matching the agreed role matrix. Reassignment belongs "
                "to a supervisor."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Assignment pools",
            title="Only the right roles can change assignment pools and capacity limits",
            kind=ACCESS,
            pre="You have agent and administrator sign-ins.",
            steps=[
                "As a Customer Care Agent, look for assignment pool or capacity settings.",
                "As an administrator or head of department, open the same settings.",
            ],
            expected="The agent cannot reach them. The administrator can.",
            priority=HIGH, role=f"{AGENT}, then {HOD}",
        ),
        Case(
            area="AI decision log",
            title="The AI decision log cannot be edited or deleted by anybody",
            kind=ACCESS,
            pre="You are signed in as an administrator.",
            steps=[
                "Open the AI decision entries on a ticket's history.",
                "Look for any edit or delete control.",
            ],
            expected=(
                "There is no way to change or remove an AI decision record, for any role "
                "including administrators. This is a compliance requirement."
            ),
            priority=CRITICAL, uat=True, role=ADMIN, req="R29, R35",
        ),
        Case(
            area="Not built yet",
            title="Automatic knowledge-base answers are not in this release",
            kind=ACCESS,
            pre="None.",
            steps=[
                "Confirm with the team that automatic answering from a knowledge base is not "
                "in scope for this release.",
                "Check no auto-answer is sent to a customer for a general enquiry.",
            ],
            expected=(
                "No automatic answer is sent. Do NOT raise a bug - listed only so it is not "
                "forgotten at sign-off."
            ),
            priority=LOW, role=ANY, ready=NOT_BUILT,
        ),
    ],
)
