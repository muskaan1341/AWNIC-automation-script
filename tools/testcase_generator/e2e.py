"""End-to-end business journeys - complete cases followed from arrival to closure.

These cross several modules on purpose. They are what AWNIC business users should run
first at UAT, because they prove the system does the job rather than proving one
screen behaves.
"""

from common import CRITICAL, EDGE, HIGH, NEGATIVE, PARTLY
from common import Case, Module
from m01_m03 import AGENT, COMPLIANCE, HANDLER, MANAGER, POC, SUPERVISOR

E2E = Module(
    code="E2E",
    name="End-to-End Business Journeys",
    short="Business Journeys",
    plain_summary=(
        "Complete cases followed from the moment a customer makes contact to the moment the "
        "case is closed, crossing several modules. Run these first at UAT - they prove the "
        "system does the job, not just that one screen works."
    ),
    cases=[
        Case(
            area="Journey 1 - simple enquiry by email",
            title="An emailed enquiry is received, classified, answered and closed",
            pre="Email intake and the AI pipeline are both running. You have a test mailbox.",
            steps=[
                "From the customer test mailbox, send an enquiry about a motor policy "
                "renewal price.",
                "Wait for the ticket to appear, then confirm the customer received an "
                "acknowledgement with a reference number.",
                "Open the ticket and check the type, category, department and priority the "
                "system chose.",
                "Confirm an agent has been assigned and that they were notified.",
                "Sign in as that agent, move the ticket to In Progress and read the "
                "recommended action plan.",
                "Reply to the customer using a template from the reply library.",
                "Mark the ticket resolved with resolution details.",
                "Open the ticket history and read it from top to bottom.",
            ],
            expected=(
                "The whole journey completes without anybody re-typing the customer's "
                "details. The reference number stays the same throughout, the deadline is "
                "met, the customer receives an acknowledgement and an answer, and the "
                "history tells the complete story of who did what and when."
            ),
            priority=CRITICAL, uat=True, role="System, then " + AGENT, req="R03, R08, R12, R14",
        ),
        Case(
            area="Journey 2 - complaint with investigation",
            title="A complaint is received, investigated, resolved and recorded in full",
            pre="Email intake is running and a complaint handler sign-in is available.",
            steps=[
                "Send a clear complaint by email - a delayed claim settlement with poor "
                "service.",
                "Confirm it becomes a complaint with a COM reference number and a deadline.",
                "Confirm a complaint handler was assigned and notified.",
                "As the handler, fill in the complaint register fields.",
                "Add two investigation notes on separate occasions.",
                "Record a resolution remark with the outcome.",
                "Mark the complaint resolved.",
                "As a compliance officer, open the complaint and read the whole record.",
            ],
            expected=(
                "The complaint carries its full register, both investigation notes in order "
                "with their authors, the resolution remark and the outcome. Nothing that was "
                "written can be edited or deleted. A reviewer can reconstruct exactly how "
                "the complaint was handled."
            ),
            priority=CRITICAL, uat=True, role=f"System, {HANDLER}, {COMPLIANCE}",
            req="R23, R42, R29",
        ),
        Case(
            area="Journey 3 - missed deadline and escalation",
            title="A case that nobody answers climbs the escalation chain to the department head",
            pre=(
                "A test ticket can be left unattended. Ask the team how often the deadline "
                "check runs and what the escalation windows are."
            ),
            steps=[
                "Create a ticket and note its deadline.",
                "Deliberately leave it unattended past the first deadline.",
                "Confirm it escalates to level one and that the level-one contact is "
                "notified.",
                "Leave it unattended again and confirm it reaches level two.",
                "Continue until it reaches the final level and the department head is "
                "notified.",
                "As a supervisor, open the escalation view and confirm the ticket is listed "
                "at the right level.",
                "Assign it, resolve it, and confirm it leaves the escalation list.",
            ],
            expected=(
                "Each level fires at the right time, notifies the right person exactly once, "
                "and is recorded on the ticket. Resolving it stops the chasing. The full "
                "escalation story stays on the ticket permanently."
            ),
            priority=CRITICAL, uat=True, role=f"System, then {SUPERVISOR}",
            req="R18, R19, R25, R37",
        ),
        Case(
            area="Journey 4 - walk-in customer",
            title="A walk-in complaint is logged by hand and handled to closure",
            pre="A customer care agent sign-in is available and you have a test policy number.",
            steps=[
                "As an agent, start a new complaint.",
                "Look the customer up by policy number and let their details fill in.",
                "Complete the complaint details, category, severity and channel Walk-in.",
                "Save and note the reference number and the deadline.",
                "Confirm the ticket shows NO AI badges and no action plan tab.",
                "Confirm it has been assigned to somebody or is visible in a queue.",
                "Work the ticket through to resolved.",
            ],
            expected=(
                "The hand-typed complaint behaves exactly like an emailed one for deadlines, "
                "assignment, escalation and audit - but shows no AI-generated content "
                "anywhere, because a person entered the details."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R07, R21, R27",
        ),
        Case(
            area="Journey 4b - website form",
            title="A customer fills in the website form and the case is handled to closure",
            pre=(
                "Website intake is switched on. You can submit the real website form, or ask "
                "the team for a test submission with the shared secret."
            ),
            steps=[
                "As an ordinary website visitor, open the AWNIC complaint form - confirm you "
                "are never asked to sign in or create an account.",
                "Fill it in and submit it.",
                "Confirm a reference number comes back quickly rather than after a long wait.",
                "Find the ticket in the complaints list and check the details match what was "
                "typed.",
                "Confirm it was classified, routed and assigned, and that it DOES show the AI "
                "badge.",
                "As the assigned handler, work it through investigation to resolution.",
                "Read the full history.",
            ],
            expected=(
                "A case filed from the public website behaves identically to one that arrived "
                "by email - deadline, assignment, escalation and audit all apply - with no "
                "customer login anywhere, and the customer got their reference number "
                "immediately rather than waiting on the AI."
            ),
            priority=CRITICAL, uat=True,
            role="Website visitor, then " + HANDLER, req="R05, R23",
        ),
        Case(
            area="Journey 5 - enquiry becomes a complaint",
            title="A case that starts as a question turns out to be a complaint",
            pre="An enquiry has just arrived and has not been routed to a department yet.",
            steps=[
                "Let a new enquiry arrive and note its reference number and deadline.",
                "As a supervisor, change its type to Complaint with a reason.",
                "Confirm the new COM reference number and that the deadline did NOT restart.",
                "Confirm the customer was told and the assigned agent was notified.",
                "Search for the old INQ reference number and confirm it still finds the case.",
                "Try to change the type back to Enquiry.",
                "Complete the complaint register and resolve the case.",
            ],
            expected=(
                "The change works once, the clock is preserved, the customer is informed, "
                "the old number still resolves to the live case, and the attempt to change "
                "back is refused because the one-time swap has been used."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Journey 6 - junk in, junk out",
            title="Marketing email is discarded and does not pollute the figures",
            pre="You can send a marketing-style email to a monitored mailbox.",
            steps=[
                "Note the current open count and breach count on the dashboard.",
                "Send a marketing email to the mailbox.",
                "Confirm a ticket is created and note its deadline.",
                "As a supervisor, discard it with a reason.",
                "Confirm it moves to the discarded list with a JNK number and has no deadline.",
                "Wait past the original deadline and confirm it never appears as breached.",
                "Check the dashboard and report figures.",
                "Restore it and confirm a fresh deadline starts from the restore moment.",
            ],
            expected=(
                "Junk can be removed in one action, stops counting against the team "
                "immediately, and never appears as a breach - but the ticket and its full "
                "history remain in the audit trail and it can be brought back if the "
                "decision was wrong."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Journey 7 - the same customer twice",
            title="A customer who emails and then phones is treated as one case",
            pre="You have a customer test mailbox and an agent sign-in.",
            steps=[
                "Send an email about a specific claim from the customer mailbox.",
                "As an agent, log a phone call from the same customer about the same claim.",
                "Check for a duplicate warning or flag.",
                "Open the comparison and review both side by side.",
                "Confirm them as duplicates with a reason.",
                "Open the customer's history and confirm both are visible and linked.",
            ],
            expected=(
                "The system spots that one customer used two channels for one issue, a "
                "person decides rather than the system merging silently, both records "
                "survive the decision, and the customer is not chased twice about the same "
                "thing."
            ),
            priority=CRITICAL, uat=True, role=f"System, then {SUPERVISOR}", req="R26",
        ),
        Case(
            area="Journey 8 - handover between people",
            title="A case passes between three people and nothing is lost",
            pre="You have agent, supervisor and department contact sign-ins.",
            steps=[
                "Let a ticket be assigned to agent A.",
                "As agent A, add an internal note and move it to In Progress.",
                "As a supervisor, reassign it to agent B with a reason.",
                "As agent B, confirm you can see agent A's note and the full history.",
                "Move the ticket to Pending POC.",
                "As the department contact, confirm you can see it and add your response.",
                "Resolve it and read the full history.",
            ],
            expected=(
                "Each person picks the case up with everything the previous person recorded. "
                "The deadline never restarts. The history names every person and every "
                "handover, so nobody can lose accountability by passing a ticket on."
            ),
            priority=CRITICAL, uat=True, role=f"{AGENT}, {SUPERVISOR}, {POC}",
        ),
        Case(
            area="Journey 9 - customer comes back",
            title="A customer replies after their case was resolved",
            pre="A resolved ticket exists that came from email.",
            steps=[
                "Resolve a ticket and confirm the customer was told.",
                "From the customer mailbox, reply to the original email saying the problem "
                "is not fixed.",
                "Check what happens to the ticket and who is notified.",
                "Work the case to resolution again.",
                "Read the full history.",
            ],
            expected=(
                "The customer's reply is never lost. Either the case reopens or a linked "
                "follow-up is created, somebody is told, and the whole story stays connected "
                "so the customer does not have to explain themselves twice. Confirm the "
                "agreed behaviour with the business before running this."
            ),
            priority=CRITICAL, uat=True, role=f"System, then {AGENT}", ready=PARTLY,
        ),
        Case(
            area="Journey 10 - month-end reporting",
            title="A manager reports on a month's work and the numbers stand up",
            pre="The test system has a month of realistic activity.",
            steps=[
                "As a manager, run the report for a full month.",
                "Note the total cases, the breach count and the average resolution time.",
                "Pick one figure and prove it by filtering the ticket list the same way and "
                "counting.",
                "Filter the report to one department and confirm the figures drop sensibly.",
                "Export or print the report if that is available.",
                "As a compliance officer, spot-check three of the counted tickets in the "
                "audit trail.",
            ],
            expected=(
                "Every figure can be traced back to real tickets. Nothing is invented, "
                "nothing is stale, and the audit trail backs up what the report claims. This "
                "is what management decisions will be based on."
            ),
            priority=CRITICAL, uat=True, role=f"{MANAGER}, then {COMPLIANCE}", req="R28, R29",
        ),
        Case(
            area="Journey 11 - a day in the life of an agent",
            title="An agent works a full shift using only the screens their role gives them",
            pre="An agent sign-in with a realistic queue of tickets.",
            steps=[
                "Sign in as an agent and read the dashboard.",
                "Use the quick filter for your own tickets, sorted by deadline.",
                "Work the three most urgent in turn - read, look the customer up, add a note, "
                "reply and resolve.",
                "Log one phone enquiry by hand.",
                "Check your notifications during the shift.",
                "Sign out.",
            ],
            expected=(
                "Everything an agent needs is reachable from their own menu without asking "
                "for help, and nothing they should not have is visible. Note anything that "
                "took more clicks than it should - this journey is as much about usability "
                "as correctness."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Journey 12 - a day in the life of a supervisor",
            title="A supervisor runs the queue for a shift",
            pre="A supervisor sign-in with a queue containing breached and unassigned tickets.",
            steps=[
                "Sign in as a supervisor and read the dashboard.",
                "Open the breached view and act on the worst case - reassign it and escalate "
                "it early with a reason.",
                "Find an unassigned ticket and assign it.",
                "Correct one wrongly classified ticket's department.",
                "Review and decide one duplicate suggestion.",
                "Discard one piece of junk.",
                "Check the escalation view before signing out.",
            ],
            expected=(
                "A supervisor can see the whole picture and act on it without leaving the "
                "system or asking IT. Every one of those actions is recorded in the audit "
                "trail with their name and reason."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Journey 13 - the wrong person",
            title="Somebody tries to reach a case they have no business seeing",
            kind=NEGATIVE,
            pre=(
                "You have a complaint handler sign-in and the reference and address of a "
                "ticket assigned to a different handler."
            ),
            steps=[
                "As the complaint handler, search for that reference number.",
                "Try to open the ticket by its direct address.",
                "Try each of its tabs in turn - history, deadline, investigation, action "
                "plan, customer records, attachments.",
                "Try the enquiries list and the discarded list.",
                "Ask a colleague to send you a notification link to that ticket and click it.",
            ],
            expected=(
                "Every single route is refused, and the refusal says the item was not found "
                "rather than admitting it exists. Nothing about the customer, the case or "
                "even its existence leaks through any door. Treat any single gap here as a "
                "release blocker."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R39",
        ),
        Case(
            area="Journey 14 - busy morning",
            title="The system copes with a realistic morning peak",
            kind=EDGE,
            pre="You can send a batch of emails and have several testers signed in.",
            steps=[
                "Send 30 emails to the monitored mailboxes over ten minutes.",
                "At the same time, have three testers work tickets, run searches and open "
                "reports.",
                "Watch how long screens take to respond.",
                "Once it settles, count the tickets created and check none were lost or "
                "duplicated.",
            ],
            expected=(
                "All 30 become tickets exactly once, everybody's screens stay responsive, "
                "and no error appears. AWNIC handles around a thousand tickets a day, so a "
                "morning peak is normal, not an extreme test."
            ),
            priority=CRITICAL, uat=True, role="Several testers together",
        ),
        Case(
            area="Journey 15 - recovery",
            title="The system recovers cleanly after a restart",
            kind=EDGE,
            pre="Ask the team to restart the test system at an agreed time.",
            steps=[
                "Note the state of three tickets before the restart.",
                "Have a tester mid-way through filling a form when the restart happens.",
                "Have the team restart the system.",
                "Sign in again and check the three tickets.",
                "Send a test email and confirm it still becomes a ticket.",
                "Let a ticket breach and confirm escalation still runs.",
            ],
            expected=(
                "No ticket is corrupted or half-changed. Email intake, deadlines and "
                "escalation all resume by themselves without anybody re-running anything. "
                "The tester who was interrupted gets a clear message rather than a silent "
                "failure."
            ),
            priority=CRITICAL, uat=True, role="Development team + QA",
        ),
    ],
)
