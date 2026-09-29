"""Modules 7-9: Changing a Ticket's Type, Ticket Stages (Kanban), SLA Timers."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case, Module
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR

# =====================================================================================
M07 = Module(
    code="M07",
    name="Changing a Ticket Type",
    plain_summary=(
        "An enquiry can be turned into a complaint and back, junk can be discarded, and a "
        "discarded item can be restored. Strict business rules apply - the swap is only "
        "allowed early and only once in a ticket's life."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Enquiry to complaint",
            title="A brand new enquiry can be turned into a complaint",
            pre=(
                "An enquiry exists that has NOT yet been given a department and is still "
                "inside its first response deadline."
            ),
            steps=[
                "Open the enquiry.",
                "Choose the option to change its type to Complaint.",
                "Give a reason and confirm.",
                "Reopen the ticket.",
            ],
            expected=(
                "The ticket is now a complaint. It appears in the complaints list, has "
                "gained a complaint reference number, and the history records the change "
                "with your name, the time and the reason."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R29",
        ),
        Case(
            area="Complaint to enquiry",
            title="A brand new complaint can be turned into an enquiry",
            pre=(
                "A complaint exists with no department assigned, still inside its first "
                "response deadline, and with no complaint register details filled in."
            ),
            steps=[
                "Open the complaint.",
                "Change its type to Enquiry with a reason.",
                "Confirm and reopen the ticket.",
            ],
            expected=(
                "The ticket is now an enquiry, shows in the enquiries list, and the change "
                "is in the history."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Deadline is preserved",
            title="The response clock does not restart when the type changes",
            pre="An enquiry has been open for some hours and is still within its deadline.",
            steps=[
                "Write down the exact deadline date and time on the enquiry.",
                "Change the ticket type to Complaint.",
                "Look at the deadline again.",
            ],
            expected=(
                "The deadline is unchanged. Time already spent is not given back. This is "
                "deliberate - restarting the clock would let a swap hide a late response."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
        ),
        Case(
            area="Discarding",
            title="A supervisor can discard a junk ticket",
            pre="A ticket exists that is clearly junk - an advert or a newsletter.",
            steps=[
                "Open the ticket as a supervisor.",
                "Choose Discard and give a reason.",
                "Confirm.",
                "Look at the enquiries list and then the discarded list.",
            ],
            expected=(
                "The ticket disappears from the working list and appears on the discarded "
                "list with a JNK reference number. Its deadline is removed so it no longer "
                "counts against anybody."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Restoring",
            title="A discarded ticket can be brought back",
            pre="A ticket is on the discarded list.",
            steps=[
                "Open the discarded ticket.",
                "Choose Restore and pick Enquiry as its type.",
                "Confirm and note the current time.",
                "Open the restored ticket and look at its deadline.",
            ],
            expected=(
                "The ticket returns to the enquiries list and a fresh deadline is set "
                "counting from the moment you restored it - not from when it first arrived. "
                "A discarded ticket built up no deadline while it sat there."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Discard reasons",
            title="The reason for discarding is kept and shown",
            pre="You have just discarded a ticket with a reason.",
            steps=[
                "Open the discarded ticket.",
                "Read the reason shown on the page and in the history.",
            ],
            expected=(
                "The reason you typed is displayed and is also in the permanent history with "
                "your name and the time."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR, req="R29",
        ),
        Case(
            area="Customer notification",
            title="The customer is told when their case type changes",
            pre="A test ticket has a working customer email address.",
            steps=[
                "Change the ticket type from Enquiry to Complaint.",
                "Check the test customer mailbox.",
                "Check the ticket's notification history.",
            ],
            expected=(
                "The customer receives an email telling them their case is now being handled "
                "as a complaint, and the ticket records that the notification was sent."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Internal notification",
            title="The assigned staff member is told when the type changes",
            pre="A ticket is assigned to a test agent.",
            steps=[
                "As a supervisor, change the ticket type.",
                "Sign in as the assigned agent and open their notifications.",
            ],
            expected="The agent sees a notification that their ticket's type changed.",
            priority=HIGH, role=SUPERVISOR,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="One-time rule",
            title="The same ticket cannot be swapped between the two types twice",
            kind=NEGATIVE,
            pre="A ticket has ALREADY been changed once from Enquiry to Complaint.",
            steps=[
                "Open that ticket while it is still early enough to change.",
                "Try to change it back to Enquiry.",
            ],
            expected=(
                "The change is refused with a clear message that a case can only be switched "
                "between enquiry and complaint once. Reverting counts as the second swap and "
                "is refused too."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Time window",
            title="The type cannot be changed once a department has been assigned",
            kind=NEGATIVE,
            pre="An enquiry has already been routed to a department.",
            steps=[
                "Open the enquiry and confirm a department is set.",
                "Try to change its type to Complaint.",
            ],
            expected=(
                "The option is not offered, or the change is refused with a message "
                "explaining it is too late because the case has already been routed."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Time window",
            title="The type cannot be changed after the first response deadline has passed",
            kind=NEGATIVE,
            pre="A ticket exists whose first response deadline has already gone by.",
            steps=[
                "Open that ticket.",
                "Try to change its type.",
            ],
            expected="The change is refused with a message explaining the window has closed.",
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Complaint register",
            title="A complaint with register details cannot be turned back into an enquiry",
            kind=NEGATIVE,
            pre="A complaint has complaint register details or investigation notes saved.",
            steps=[
                "Open that complaint.",
                "Try to change its type to Enquiry or to discard it.",
            ],
            expected=(
                "Changing away from Complaint is refused with a message explaining the "
                "complaint record would be orphaned. The register details stay attached."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R23, R42",
        ),
        Case(
            area="Reason required",
            title="A type change cannot be made without a reason",
            kind=NEGATIVE,
            pre="A ticket is eligible for a type change.",
            steps=[
                "Start the type change.",
                "Leave the reason box empty and confirm.",
                "Try again with only spaces.",
            ],
            expected="Both are refused. A reason is always required for the audit trail.",
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Discarding",
            title="A closed or resolved ticket cannot be discarded",
            kind=NEGATIVE,
            pre="A resolved ticket exists.",
            steps=[
                "Open the resolved ticket.",
                "Try to discard it.",
            ],
            expected=(
                "Either the option is not shown or it is refused. Confirm the agreed "
                "behaviour with the team before logging a bug."
            ),
            priority=MEDIUM, role=SUPERVISOR, ready=PARTLY,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Discard and restore",
            title="Discarding and restoring does not use up the one-time swap allowance",
            kind=EDGE,
            pre="A brand new enquiry exists that has never been swapped.",
            steps=[
                "Discard the enquiry.",
                "Restore it back to an Enquiry.",
                "Now try to change it from Enquiry to Complaint.",
            ],
            expected=(
                "The change to Complaint is allowed. Discarding and restoring are a separate "
                "thing and must never consume the one-time enquiry/complaint swap."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Discard and restore",
            title="A ticket can be discarded and restored more than once",
            kind=EDGE,
            pre="A ticket exists.",
            steps=[
                "Discard it, restore it, discard it again, restore it again.",
                "Read the history.",
            ],
            expected=(
                "Every cycle is allowed and each step is recorded in the history. There is "
                "no limit on discarding, because junk must always be removable."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Restoring",
            title="A discarded ticket can be restored as the other type",
            kind=EDGE,
            pre="An enquiry has been discarded.",
            steps=[
                "Restore it and choose Complaint rather than Enquiry.",
                "Check the reference number and the deadline.",
            ],
            expected=(
                "It comes back as a complaint with a complaint reference number and a fresh "
                "complaint deadline counted from the restore moment."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Old reference numbers",
            title="A customer quoting the old reference number still reaches the right case",
            kind=EDGE,
            pre="A ticket has changed type and therefore has an old and a new reference.",
            steps=[
                "Note the old reference number from before the change.",
                "Search for the old reference number in the ticket list.",
            ],
            expected=(
                "The search finds the ticket under its current reference. A customer quoting "
                "the old number is never told their case does not exist."
            ),
            priority=HIGH, uat=True, role=AGENT, req="R33, R34",
        ),
        Case(
            area="Two people at once",
            title="Two supervisors changing the type at the same moment",
            kind=EDGE,
            pre="Two supervisors are signed in on different machines.",
            steps=[
                "Both open the same eligible ticket.",
                "Both start a type change and confirm at the same time.",
                "Reopen the ticket and read the history.",
            ],
            expected=(
                "Only one change goes through. The other is refused with a clear message. "
                "The history shows exactly one swap, not two."
            ),
            priority=HIGH, role=f"Two {SUPERVISOR}s",
        ),
        Case(
            area="History chain",
            title="Every type change stays in the history forever",
            kind=EDGE,
            pre="A ticket has been discarded, restored and swapped.",
            steps=[
                "Open the ticket's history.",
                "Count the type change entries.",
            ],
            expected=(
                "Every change is listed in order with the old type, the new type, who did it "
                "and when. Nothing can be removed from this list."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R29",
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can change type",
            title="An agent cannot change a ticket's type",
            kind=ACCESS,
            pre="You are a Customer Care Agent on an otherwise eligible ticket.",
            steps=[
                "Look for a change-type option on the ticket.",
                "If you have the address of the action, try to trigger it directly.",
            ],
            expected="The option is not shown and any direct attempt is refused.",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Who can discard",
            title="Discarding needs its own separate permission",
            kind=ACCESS,
            pre="You have sign-ins for several roles.",
            steps=[
                "Sign in as each role and check who sees the Discard option.",
                "Compare against the agreed role matrix.",
            ],
            expected=(
                "Only roles granted the discard permission see it. Being able to change a "
                "ticket type does not automatically allow discarding - it is a tighter "
                "permission because discarding removes the deadline."
            ),
            priority=CRITICAL, uat=True, role="All roles",
        ),
        Case(
            area="Who can restore",
            title="Only permitted roles can restore a discarded ticket",
            kind=ACCESS,
            pre="A discarded ticket exists.",
            steps=[
                "Sign in as a Customer Care Agent and open the discarded list.",
                "Look for a Restore option.",
                "Try the restore action directly if you can get the address.",
            ],
            expected="Restore is not available to the agent and any direct attempt is refused.",
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Discarded list access",
            title="Roles without discarded-view rights cannot see the discarded list at all",
            kind=ACCESS,
            pre="You are signed in as a Complaint Handler.",
            steps=[
                "Check whether Discarded appears in the menu.",
                "Type the discarded list address directly.",
                "Try to open a discarded ticket by its address.",
            ],
            expected="All three are refused. The discarded ticket shows as not found.",
            priority=CRITICAL, role=HANDLER,
        ),
    ],
)

# =====================================================================================
M08 = Module(
    code="M08",
    name="Ticket Stages and Kanban",
    plain_summary=(
        "Every ticket moves through a set stage list, shown as a drag-and-drop board with "
        "four columns: New, In Progress, Pending POC and Resolved. Only sensible moves are "
        "allowed, and marking a ticket resolved is always a human decision."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Board layout",
            title="The board shows the four columns with the right tickets in each",
            pre="Tickets exist at several different stages.",
            steps=[
                "Open the Kanban board.",
                "Read the four column headings and the count on each.",
                "Spot-check three cards against the stage shown on their detail pages.",
            ],
            expected=(
                "The four columns are New, In Progress, Pending POC and Resolved. Each "
                "card sits in the column matching its stage. Closed tickets and discarded "
                "items do not appear on the board at all."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R14",
        ),
        Case(
            area="Card content",
            title="Each card shows enough to work from without opening it",
            pre="The board has cards in it.",
            steps=[
                "Look at any card.",
            ],
            expected=(
                "The card shows the reference number, a short subject, the customer, the "
                "assigned person, the priority and the deadline state. An escalated ticket "
                "carries a visible escalation badge."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Moving a ticket",
            title="An agent can drag a ticket from New to In Progress",
            pre="A ticket is in the New column and you have permission to move it.",
            steps=[
                "Drag the card from New into In Progress.",
                "Wait for it to settle.",
                "Refresh the page.",
                "Open the ticket and check its stage and status.",
            ],
            expected=(
                "The card stays in In Progress after refreshing, the ticket's stage is "
                "updated, its status reads In Progress, and the move is in the history."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R14",
        ),
        Case(
            area="Moving a ticket",
            title="A ticket can be moved through the whole normal path",
            pre="A fresh ticket is on the board.",
            steps=[
                "Move it from New to In Progress.",
                "Move it to Pending POC.",
                "Move it to Resolved.",
                "Read its history.",
            ],
            expected=(
                "Every move succeeds and each one is recorded in order in the history with "
                "the person and the time."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R14, R29",
        ),
        Case(
            area="Changing stage from the ticket",
            title="The stage can also be changed from the ticket page, not only by dragging",
            pre="A ticket is open on its detail page.",
            steps=[
                "Use the status or stage control on the ticket page to move it forward.",
                "Save, then check the board.",
            ],
            expected=(
                "The ticket moves on the board too. Both routes give the same result and "
                "follow the same rules."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Resolving",
            title="A person can mark a ticket resolved with resolution details",
            pre="A ticket is in progress and assigned to you.",
            steps=[
                "Open the ticket and choose Resolve.",
                "Enter the resolution details.",
                "Confirm.",
            ],
            expected=(
                "The ticket status becomes Resolved, it moves to the Resolved column, the "
                "deadline stops counting, and the resolution text and the person's name are "
                "recorded."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R14",
        ),
        Case(
            area="Board filters",
            title="The board can be filtered without losing the column layout",
            pre="You are on the board.",
            steps=[
                "Filter by department.",
                "Filter by priority as well.",
                "Clear the filters.",
            ],
            expected=(
                "The four columns stay in place and only matching cards are shown. The "
                "counts on each column update to match."
            ),
            priority=HIGH, role=AGENT,
        ),
        Case(
            area="Escalation badge",
            title="An escalated ticket is visibly marked on the board",
            pre="A ticket has been escalated.",
            steps=[
                "Find the escalated ticket on the board.",
            ],
            expected=(
                "The card carries an escalation badge showing its level, and it sits in the "
                "Pending POC column. Escalation is a badge on the card, never a column of "
                "its own."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Illegal moves",
            title="A ticket cannot be dragged backwards from Resolved to New",
            kind=NEGATIVE,
            pre="A resolved ticket is on the board.",
            steps=[
                "Try to drag the resolved card back into the New column.",
            ],
            expected=(
                "The card springs back to Resolved and a message explains the move is not "
                "allowed. The ticket's stage does not change - confirm by refreshing."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R14",
        ),
        Case(
            area="Illegal moves",
            title="A ticket cannot skip straight from New to Resolved",
            kind=NEGATIVE,
            pre="A ticket is in the New column.",
            steps=[
                "Try to drag it directly into Resolved.",
            ],
            expected=(
                "The move is refused with a message. Work cannot appear finished without "
                "passing through the stages in between."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Closed tickets",
            title="A closed ticket cannot be moved at all",
            kind=NEGATIVE,
            pre="A closed ticket exists.",
            steps=[
                "Confirm the closed ticket is not on the board.",
                "Open it and try to change its stage from the ticket page.",
            ],
            expected="Closed is the end of the line. No stage change is possible.",
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Resolving",
            title="A ticket cannot be resolved without resolution details",
            kind=NEGATIVE,
            pre="A ticket is in progress.",
            steps=[
                "Choose Resolve and leave the resolution text empty.",
                "Confirm.",
            ],
            expected=(
                "It is refused with a message. Resolution details are needed so the customer "
                "and the audit trail both have an answer."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Automatic resolution",
            title="The system never marks a ticket resolved by itself",
            kind=NEGATIVE,
            pre="A ticket exists where the customer replied saying the issue is fixed.",
            steps=[
                "Send a reply from the customer mailbox saying 'this is now resolved, thank "
                "you'.",
                "Wait for the system to process it.",
                "Check the ticket's status.",
            ],
            expected=(
                "The ticket is FLAGGED for attention and the assigned person is notified, "
                "but the status stays as it was. Only a person can mark something resolved. "
                "An automatic status change here is a serious defect."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Drag behaviour",
            title="Dropping a card outside any column cancels the move",
            kind=EDGE,
            pre="You are on the board.",
            steps=[
                "Start dragging a card and drop it on empty space outside the columns.",
                "Refresh the page.",
            ],
            expected="The card returns to its original column and nothing is changed.",
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Drag behaviour",
            title="Pressing Escape mid-drag cancels the move",
            kind=EDGE,
            pre="You are on the board.",
            steps=[
                "Start dragging a card and press the Escape key before releasing.",
                "Refresh.",
            ],
            expected="The move is cancelled and the card stays where it was.",
            priority=LOW, role=AGENT,
        ),
        Case(
            area="Two people at once",
            title="Two people moving the same card at the same time",
            kind=EDGE,
            pre="Two agents are signed in on different machines with the board open.",
            steps=[
                "Both drag the same card to two different columns at the same moment.",
                "Both refresh.",
            ],
            expected=(
                "Both end up seeing the same final column. The history shows a clear order "
                "of events. No ticket is left in two places or in no column."
            ),
            priority=HIGH, role=f"Two {AGENT}s",
        ),
        Case(
            area="Board size",
            title="A column with a very large number of cards stays usable",
            kind=EDGE,
            pre="One column has 200 or more tickets.",
            steps=[
                "Open the board and scroll down the busy column.",
                "Drag a card from the bottom of that column into another column.",
            ],
            expected=(
                "Scrolling is smooth, the column either pages or scrolls cleanly, and "
                "dragging still works from anywhere in the column."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        Case(
            area="Empty board",
            title="An empty column shows a message rather than looking broken",
            kind=EDGE,
            pre="Filter the board so one column has nothing in it.",
            steps=[
                "Apply a filter that empties one column.",
            ],
            expected="The empty column shows a short 'nothing here' message and keeps its heading.",
            priority=LOW, role=AGENT,
        ),
        Case(
            area="Escalated stages",
            title="The three escalation stages all sit in the Pending POC column",
            kind=EDGE,
            pre="Tickets exist at first, second and final escalation levels.",
            steps=[
                "Find each of the three on the board.",
            ],
            expected=(
                "All three appear in Pending POC, each with a badge showing its own level. "
                "They are not spread across different columns."
            ),
            priority=MEDIUM, role=SUPERVISOR,
        ),
        Case(
            area="Touch devices",
            title="Dragging works on a tablet",
            kind=EDGE,
            pre="You have a tablet or a touch-capable laptop.",
            steps=[
                "Open the board on the tablet.",
                "Press and hold a card, then drag it to another column.",
            ],
            expected=(
                "The drag works by touch, or a clear alternative such as a move menu is "
                "offered. The board is not unusable on touch."
            ),
            priority=MEDIUM, role=AGENT, ready=PARTLY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can move",
            title="A role without move rights cannot drag cards",
            kind=ACCESS,
            pre="Sign in as a role that can view tickets but not move them.",
            steps=[
                "Open the board.",
                "Try to drag a card.",
            ],
            expected=(
                "The card does not move, or the move is refused with a message. Refreshing "
                "confirms nothing changed."
            ),
            priority=CRITICAL, uat=True, role=COMPLIANCE,
        ),
        Case(
            area="Board scope",
            title="The board only shows tickets the person is allowed to see",
            kind=ACCESS,
            pre="Tickets exist in several departments.",
            steps=[
                "Sign in as a Department Contact Person and count the cards.",
                "Sign in as a Manager and count them again.",
            ],
            expected=(
                "The department contact person sees only their own department's tickets. The "
                "manager sees everything. The board follows the same visibility rules as the "
                "lists."
            ),
            priority=CRITICAL, uat=True, role=f"{POC}, then {MANAGER}",
        ),
        Case(
            area="Who can resolve",
            title="Only permitted roles can mark a ticket resolved",
            kind=ACCESS,
            pre="You have several role sign-ins.",
            steps=[
                "Sign in as each role and check who sees the Resolve action.",
                "For a role that should not, try the resolve action directly.",
            ],
            expected="It matches the agreed role matrix and direct attempts are refused.",
            priority=CRITICAL, uat=True, role="All roles",
        ),
        Case(
            area="Cross-scope move",
            title="Nobody can move a ticket they are not allowed to see",
            kind=ACCESS,
            pre="You have the reference of a ticket outside your scope.",
            steps=[
                "As a Complaint Handler, get the address of the stage-change action for a "
                "ticket assigned to somebody else.",
                "Try to trigger it.",
            ],
            expected="It is refused as not found. The other person's ticket does not move.",
            priority=CRITICAL, role=HANDLER,
        ),
    ],
)

# =====================================================================================
M09 = Module(
    code="M09",
    name="SLA Timers",
    plain_summary=(
        "Every ticket gets a response deadline based on its type and department, counted in "
        "working hours only. The screen shows Within SLA, At Risk or Breached so staff can "
        "see what needs attention."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Deadline is set",
            title="A new ticket automatically gets a response deadline",
            pre="The deadline rules are configured for the test department.",
            steps=[
                "Create or receive a new ticket.",
                "Open it and look at the deadline area.",
            ],
            expected=(
                "A deadline date and time is shown, along with how long is left. The staff "
                "member does not have to work it out or type it in."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R16",
        ),
        Case(
            area="Deadline rules",
            title="Different types and departments get their correct deadlines",
            pre="You have the agreed deadline table from the business.",
            steps=[
                "Create one ticket for each combination in the agreed table - a motor "
                "complaint, a non-motor complaint and a general enquiry.",
                "Compare each deadline against the agreed table.",
            ],
            expected=(
                "Every deadline matches the agreed table exactly. This is the core of the "
                "SLA promise, so any mismatch is critical."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16, R37",
        ),
        Case(
            area="Working hours",
            title="Only working hours count towards the deadline",
            pre="You know AWNIC's agreed working hours.",
            steps=[
                "Ask the team to create a ticket timed one hour before the end of the "
                "working day with a four-hour deadline.",
                "Work out where the deadline should fall.",
                "Compare with what the system shows.",
            ],
            expected=(
                "The deadline continues into the next working morning rather than expiring "
                "overnight. Evening and night hours do not count."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
        ),
        Case(
            area="Weekends",
            title="Weekends and public holidays do not count towards the deadline",
            pre="You know the agreed weekend days and the holiday calendar.",
            steps=[
                "Ask the team to create a ticket late on the last working day of the week.",
                "Check where the deadline lands.",
                "Repeat with a ticket created just before a configured public holiday.",
            ],
            expected=(
                "Both deadlines skip over the non-working days and land in the next working "
                "period."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
        ),
        Case(
            area="Deadline display",
            title="A ticket well inside its deadline shows as Within SLA",
            pre="A ticket has plenty of time left.",
            steps=[
                "Open the ticket and read the deadline badge.",
                "Look at the same ticket in the list.",
            ],
            expected=(
                "It reads Within SLA or On Track in green, on both the ticket and the list, "
                "with the time remaining shown."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Deadline display",
            title="A ticket close to its deadline shows as At Risk",
            pre="A ticket is inside the warning window before its deadline.",
            steps=[
                "Open a ticket whose deadline is close.",
                "Read the badge.",
            ],
            expected=(
                "It reads SLA at Risk or At Risk in amber, so staff can see what to do next "
                "before it becomes late."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R17",
        ),
        Case(
            area="Deadline display",
            title="A late ticket shows clearly as Breached, with how late it is",
            pre="A ticket's deadline has passed and it is not resolved.",
            steps=[
                "Open the late ticket.",
                "Read the badge on the ticket, in the list, and on the board card.",
            ],
            expected=(
                "All three show it as Breached in red, and the ticket page shows how long "
                "overdue it is."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R17",
        ),
        Case(
            area="Clock stops",
            title="Resolving a ticket stops the deadline clock",
            pre="A ticket is in progress and within its deadline.",
            steps=[
                "Resolve the ticket.",
                "Wait until after the original deadline time has passed.",
                "Look at the ticket again.",
            ],
            expected=(
                "The ticket shows as Completed and never turns red. Work that was finished "
                "on time must not later be counted as late."
            ),
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Breach list",
            title="A supervisor can see all breached tickets in one place",
            pre="Several tickets have passed their deadline.",
            steps=[
                "Open the dashboard or the SLA screen as a supervisor.",
                "Find the breached tickets view and open it.",
            ],
            expected=(
                "Every breached ticket is listed with how late it is, who owns it and which "
                "department it is in, so a supervisor can act."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R17",
        ),
        Case(
            area="SLA rules screen",
            title="The configured deadline rules can be read on screen",
            pre="You are signed in as a manager or head of department.",
            steps=[
                "Open the Teams and SLA screen.",
                "Read the rules for a few departments.",
            ],
            expected=(
                "The deadline rules are shown clearly - the type, department, deadline and "
                "escalation path - so the business can check them without asking IT."
            ),
            priority=HIGH, uat=True, role=MANAGER, req="R16",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Discarded tickets",
            title="A discarded ticket does not carry a deadline",
            kind=NEGATIVE,
            pre="A ticket with a live deadline exists.",
            steps=[
                "Note the ticket's deadline.",
                "Discard the ticket.",
                "Open it from the discarded list and look for a deadline.",
                "Check the breached tickets view.",
            ],
            expected=(
                "The deadline is gone and the discarded item never appears as breached. Junk "
                "must not count against the team's SLA figures."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Missing rules",
            title="A ticket in a department with no rule is handled safely",
            kind=NEGATIVE,
            pre="Ask the team for a department that has no deadline rule set.",
            steps=[
                "Create a ticket in that department.",
                "Open it and look at the deadline.",
            ],
            expected=(
                "Either a sensible default deadline is applied, or the ticket clearly shows "
                "that no deadline is set and is flagged for a supervisor. The page does not "
                "show an error or a blank where a date should be."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Manual editing",
            title="Staff cannot simply type in a different deadline",
            kind=NEGATIVE,
            pre="You are on a ticket with a deadline.",
            steps=[
                "Look for a way to type or pick a different deadline date.",
                "Sign in as a supervisor and look again.",
            ],
            expected=(
                "The deadline is calculated by the system, not typed by hand. If any role "
                "can change it, confirm with the business that this is intended and check it "
                "is recorded in the history."
            ),
            priority=HIGH, uat=True, role=f"{AGENT}, then {SUPERVISOR}",
        ),
        Case(
            area="Reassignment",
            title="Reassigning a ticket does not give it a fresh deadline",
            kind=NEGATIVE,
            pre="A ticket has been open for several hours.",
            steps=[
                "Note the exact deadline.",
                "Reassign the ticket to a different agent.",
                "Check the deadline again.",
            ],
            expected=(
                "The deadline is unchanged. Otherwise passing a ticket around would hide "
                "lateness."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Restore",
            title="A restored ticket's deadline starts from the restore moment",
            kind=EDGE,
            pre="A ticket was discarded several days ago.",
            steps=[
                "Note the current date and time.",
                "Restore the discarded ticket.",
                "Look at the new deadline.",
            ],
            expected=(
                "The deadline is counted from the moment of restoring, not from when the "
                "ticket first arrived. It does not appear instantly breached."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Exact boundary",
            title="A ticket exactly at its deadline is treated consistently",
            kind=EDGE,
            pre="Ask the team to set a ticket's deadline to the current minute.",
            steps=[
                "Watch a ticket as its deadline passes.",
                "Refresh at the exact minute and again a minute later.",
            ],
            expected=(
                "It changes from At Risk to Breached at the deadline and stays that way. It "
                "does not flicker between the two states."
            ),
            priority=MEDIUM, role=SUPERVISOR,
        ),
        Case(
            area="Start of day",
            title="A ticket arriving outside working hours starts counting the next morning",
            kind=EDGE,
            pre="You can send an email outside working hours.",
            steps=[
                "Send an email at 11pm.",
                "Next morning, open the ticket and check the deadline.",
            ],
            expected=(
                "The deadline is measured from the start of the next working day, so the "
                "team is not already late before they could possibly have seen it."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
        ),
        Case(
            area="Long deadlines",
            title="A multi-day deadline lands on the right working day",
            kind=EDGE,
            pre="A rule exists with a deadline of two or three working days.",
            steps=[
                "Create a ticket under that rule mid-week.",
                "Create another one on the last working day of the week.",
                "Work out both deadlines by hand and compare.",
            ],
            expected=(
                "Both land on the correct working day with the weekend skipped. This is the "
                "outer ceiling the business signed off, so check it carefully."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R25",
        ),
        Case(
            area="Time zone",
            title="Deadlines are shown in UAE local time everywhere",
            kind=EDGE,
            pre="You can change your computer's time zone.",
            steps=[
                "Note a ticket's deadline.",
                "Change your computer's time zone to a different country.",
                "Refresh and read the deadline again.",
            ],
            expected=(
                "The deadline reads the same in UAE local time regardless of the viewer's "
                "machine, or the time zone is clearly labelled. Two staff must never see two "
                "different deadlines for the same ticket."
            ),
            priority=HIGH, uat=True, role=AGENT,
        ),
        Case(
            area="Rule change",
            title="Changing a deadline rule does not silently move existing deadlines",
            kind=EDGE,
            pre="You can change a deadline rule on the test system.",
            steps=[
                "Note the deadline on an existing open ticket.",
                "Change the rule for that department to a shorter time.",
                "Check the existing ticket and then create a new one.",
            ],
            expected=(
                "The new ticket uses the new rule. Confirm with the business what should "
                "happen to existing tickets and record the answer - an existing ticket "
                "silently becoming breached is a serious issue."
            ),
            priority=CRITICAL, uat=True, role=HOD, ready=PARTLY,
        ),
        Case(
            area="Clock display",
            title="The countdown updates without needing a full page reload",
            kind=EDGE,
            pre="A ticket is close to its deadline.",
            steps=[
                "Open the ticket and watch the time-remaining figure for a few minutes.",
            ],
            expected=(
                "The remaining time counts down or refreshes sensibly, and is correct after "
                "a manual refresh. A stale figure that never moves is misleading."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="SLA rules",
            title="Only permitted roles can change the deadline rules",
            kind=ACCESS,
            pre="You have agent and head of department sign-ins.",
            steps=[
                "As a Customer Care Agent, open the Teams and SLA screen if it is reachable.",
                "Look for edit controls on the rules.",
                "As a head of department, look again.",
            ],
            expected=(
                "The agent can at most read, never change. Only the permitted roles can edit "
                "the rules, and every change is recorded."
            ),
            priority=CRITICAL, uat=True, role=f"{AGENT}, then {HOD}",
        ),
        Case(
            area="Breach view scope",
            title="The breached list only shows tickets the person may see",
            kind=ACCESS,
            pre="Breached tickets exist in several departments.",
            steps=[
                "Sign in as a Department Contact Person and open the breached view.",
                "Check every row belongs to your own department.",
                "Sign in as a Manager and check the same view.",
            ],
            expected=(
                "The department contact person sees only their own department. The manager "
                "sees everything. A breach list must not become a way around visibility rules."
            ),
            priority=CRITICAL, uat=True, role=f"{POC}, then {MANAGER}",
        ),
        Case(
            area="Ticket SLA tab",
            title="The SLA tab of a ticket outside your scope cannot be opened",
            kind=ACCESS,
            pre="You have the address of the SLA tab of a ticket you cannot see.",
            steps=[
                "Paste that address into your browser.",
            ],
            expected="It is refused as not found, exactly like the main ticket page.",
            priority=CRITICAL, role=HANDLER,
        ),
    ],
)
