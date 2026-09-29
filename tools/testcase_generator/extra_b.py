"""Additional depth for modules 6-10. Imported for its side effects."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR
from m04_m06 import M06
from m07_m09 import M07, M08, M09
from m10_m12 import M10

# --- M06 AI Classification and Assignment --------------------------------------------
M06.cases += [
    Case(
        area="Summary",
        title="The enquiry summary is a fair short version of the customer's message",
        pre="An email ticket has finished processing.",
        steps=[
            "Read the customer's original email.",
            "Read the summary the system produced.",
            "Compare them.",
        ],
        expected=(
            "The summary reflects what the customer actually said. It does not invent facts, "
            "policy numbers or promises that are not in the original."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Action plan",
        title="The recommended action plan is sensible for the case",
        pre="An email ticket has finished processing.",
        steps=["Open the Recommended Action Plan tab.", "Read the suggested steps."],
        expected=(
            "The steps make sense for this type of case and are clearly labelled as a "
            "suggestion, not an instruction the agent must follow."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Accuracy sample",
        title="Classification accuracy is measured over a real sample",
        pre="You have at least 20 processed tickets and the agreed classification rules.",
        steps=[
            "Take 20 processed tickets.",
            "For each one, record whether the type, category and department are correct.",
            "Work out the percentage correct for each.",
        ],
        expected=(
            "Record the actual percentages and compare with whatever accuracy the business "
            "agreed to accept. A single wrong ticket is not a defect on its own - the "
            "overall rate is what matters."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R08, R09, R11",
    ),
    Case(
        area="Severity",
        title="Complaint severity is set sensibly",
        pre="You have complaint emails of clearly different seriousness.",
        steps=[
            "Send a minor complaint and a serious one.",
            "Compare the severity on both tickets.",
        ],
        expected=(
            "The serious one gets the higher severity, and the severity feeds into the "
            "deadline and escalation path."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, req="R13, R23",
    ),
    Case(
        area="Correcting the AI",
        title="Correcting a wrong classification is recorded as a human decision",
        pre="A ticket has been classified incorrectly.",
        steps=[
            "As a supervisor, correct the category.",
            "Open the history.",
        ],
        expected=(
            "The history shows both the system's original decision and your correction, so "
            "the accuracy of the system can be measured over time."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, req="R29, R35",
    ),
    Case(
        area="Assignment rules",
        title="An assignment pool can be read and maintained",
        pre="You are signed in as an administrator or head of department.",
        steps=[
            "Open the assignment settings.",
            "Read who is in a department's pool and what their limits are.",
            "Add a person to a pool and save.",
        ],
        expected=(
            "The pool membership and limits are visible and editable by permitted roles, and "
            "the new person starts receiving tickets."
        ),
        priority=HIGH, uat=True, role=HOD, req="R12, R44",
    ),
    Case(
        area="Priority tiers",
        title="A high priority ticket is assigned ahead of a routine one",
        pre="An agent has limited capacity and there is a queue.",
        steps=[
            "Create a routine ticket and an urgent ticket for the same department at almost "
            "the same time.",
            "Check which is assigned first.",
        ],
        expected=(
            "The urgent one is dealt with first. Confirm with the business exactly what "
            "priority should mean for assignment order."
        ),
        priority=HIGH, role="System (no user action)", req="R44", ready=PARTLY,
    ),
    Case(
        area="Wrong department",
        title="A ticket routed to a department that does not handle it can be moved on",
        pre="A ticket has landed in the wrong department.",
        steps=[
            "As the receiving department contact, look for a way to send it on.",
            "Move it to the correct department with a reason.",
        ],
        expected=(
            "There is a clear way to hand a ticket on, it reaches the right department's "
            "queue, and the reason is recorded. Confirm which roles should be able to do this."
        ),
        priority=CRITICAL, uat=True, role=POC, req="R11",
    ),
    Case(
        area="Long content",
        title="A very long email is still classified",
        kind=EDGE,
        pre="The AI pipeline is running.",
        steps=["Send an email with several thousand words.", "Check the resulting ticket."],
        expected=(
            "It is classified rather than failing silently. If the system can only read part "
            "of it, the classification should still be sensible and the full text is kept."
        ),
        priority=HIGH, role="System (no user action)",
    ),
    Case(
        area="Attachment-only email",
        title="An email with no text but an attached document is handled",
        kind=EDGE,
        pre="The AI pipeline is running.",
        steps=["Send an email with an empty body and one PDF attached.", "Open the ticket."],
        expected=(
            "A ticket exists with the attachment. Either it is classified from the "
            "attachment, or it is flagged for a person to look at. It is never dropped."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Confidence",
        title="A low-confidence classification is visible to the agent",
        kind=EDGE,
        pre="You have a deliberately ambiguous email.",
        steps=["Send an ambiguous email.", "Open the ticket and read the classification card."],
        expected=(
            "The agent can tell the system was unsure - through a flag, a low confidence "
            "indicator or a review queue. A confident-looking wrong answer is worse than a "
            "hesitant one."
        ),
        priority=HIGH, uat=True, role=AGENT, ready=PARTLY,
    ),
    Case(
        area="Personal data",
        title="Customer personal details are protected during AI processing",
        kind=ACCESS,
        pre="Ask the team how personal details are handled before processing.",
        steps=[
            "Send an email containing an Emirates ID and a bank account number.",
            "Ask the team to show what was actually sent for processing.",
            "Check the resulting ticket still shows the right customer.",
        ],
        expected=(
            "Sensitive values are masked before processing and restored afterwards, so the "
            "ticket is complete but the raw values were not exposed unnecessarily."
        ),
        priority=CRITICAL, uat=True, role="Development team + QA", req="R22",
    ),
    Case(
        area="Processing endpoint",
        title="Classification results cannot be written by an outsider",
        kind=ACCESS,
        pre="Ask the team for the address used to write classification results.",
        steps=[
            "Call it with no credentials.",
            "Call it with a made-up key and a payload that would change a ticket.",
        ],
        expected=(
            "Both are refused and no ticket changes. Otherwise anyone could reclassify or "
            "reassign AWNIC's tickets."
        ),
        priority=CRITICAL, role="Outsider with no access",
    ),
]

# --- M07 Changing a Ticket Type -------------------------------------------------------
M07.cases += [
    Case(
        area="Confirmation",
        title="A type change asks for confirmation before it happens",
        pre="A ticket is eligible for a type change.",
        steps=["Start the type change.", "Read the confirmation shown."],
        expected=(
            "The confirmation explains what will happen - the new type, the new reference "
            "number and that the customer will be told - before anything changes."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Reference numbers",
        title="A changed ticket gets the correct new reference prefix",
        pre="An enquiry is eligible to become a complaint.",
        steps=[
            "Note the INQ reference number.",
            "Change the type to Complaint.",
            "Read the new reference number.",
        ],
        expected=(
            "The ticket now carries a COM reference number, and the old INQ number is still "
            "recorded in the history so it can be traced."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R33, R34",
    ),
    Case(
        area="Discarding",
        title="A discarded ticket keeps everything that was on it",
        pre="A ticket has notes, attachments and history.",
        steps=["Discard it.", "Open it from the discarded list and read every tab."],
        expected=(
            "The description, notes, attachments and history are all still there. Discarding "
            "hides a ticket from the working queue - it does not delete anything."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Discard reasons",
        title="The discard reason list covers the real junk AWNIC receives",
        pre="You are discarding a ticket.",
        steps=[
            "Open the discard reason list.",
            "Compare with the kinds of junk that actually arrive - adverts, newsletters, "
            "wrong number, test messages.",
        ],
        expected=(
            "The list covers the real cases, with a free-text option for anything else. "
            "Report any missing reason to the business."
        ),
        priority=MEDIUM, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Bulk discard",
        title="Several junk tickets can be discarded together",
        pre="Several junk tickets are in the list.",
        steps=["Select several tickets.", "Look for a bulk discard option and use it."],
        expected=(
            "Either bulk discard works with one reason applied to all, or it does not exist. "
            "Confirm with the business whether it is needed - a marketing burst can produce "
            "dozens of junk tickets at once."
        ),
        priority=MEDIUM, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Notification wording",
        title="The customer notification about a type change is understandable",
        kind=NEGATIVE,
        pre="You have just changed a ticket's type.",
        steps=["Read the email the customer received."],
        expected=(
            "It uses plain customer-facing language, includes the new reference number, and "
            "contains no internal jargon, no internal notes and no placeholders."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Restore validation",
        title="Restoring requires choosing what to restore it as",
        kind=NEGATIVE,
        pre="A discarded ticket exists.",
        steps=["Start the restore and try to confirm without choosing a type."],
        expected="It is refused until you choose Enquiry or Complaint.",
        priority=MEDIUM, role=SUPERVISOR,
    ),
    Case(
        area="Escalated tickets",
        title="An escalated ticket cannot quietly be discarded to hide it",
        kind=NEGATIVE,
        pre="A ticket has been escalated.",
        steps=["Try to discard the escalated ticket.", "Read what happens and check the history."],
        expected=(
            "Either it is refused, or it is allowed but recorded very visibly with the "
            "reason and the escalation contact notified. Discarding must never be a quiet way "
            "to make a late ticket disappear. Confirm the agreed behaviour with the business."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Reporting impact",
        title="A discarded ticket disappears from the SLA figures but not from the audit",
        kind=EDGE,
        pre="You have report figures before and after discarding a ticket.",
        steps=[
            "Note the open count and breach count on the report.",
            "Discard a ticket that was included.",
            "Re-run the report, then check the audit trail.",
        ],
        expected=(
            "The report figures drop by one, but the ticket and its whole history are still "
            "in the audit trail. It leaves the performance numbers, not the record."
        ),
        priority=HIGH, uat=True, role=MANAGER,
    ),
    Case(
        area="Assignment",
        title="A restored ticket is assigned to somebody again",
        kind=EDGE,
        pre="A discarded ticket is about to be restored.",
        steps=["Restore the ticket.", "Look at the assigned person and department."],
        expected=(
            "It is either reassigned automatically or clearly visible in a queue. A restored "
            "ticket must not sit owned by nobody."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR,
    ),
]

# --- M08 Ticket Stages and Kanban -----------------------------------------------------
M08.cases += [
    Case(
        area="Column counts",
        title="The number on each column matches the cards in it",
        pre="The board has cards in every column.",
        steps=["Read the count on each column heading.", "Count the cards in each column."],
        expected="The numbers match, and they update after a card is moved.",
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Board and list agreement",
        title="The board and the ticket list tell the same story",
        pre="A ticket is in a known stage.",
        steps=[
            "Note which column a ticket sits in on the board.",
            "Find the same ticket in the list and read its status.",
        ],
        expected=(
            "The column and the status agree. Two screens disagreeing about the same ticket "
            "destroys trust in both."
        ),
        priority=CRITICAL, uat=True, role=AGENT,
    ),
    Case(
        area="Moving a ticket",
        title="Moving a ticket updates who is expected to act next",
        pre="A ticket is in progress.",
        steps=[
            "Move a ticket to Pending POC.",
            "Check the assigned person and any notification sent.",
        ],
        expected=(
            "The right person or department is now expected to act, and they are told. A "
            "stage change that nobody hears about achieves nothing."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R14",
    ),
    Case(
        area="Resolution details",
        title="The resolution recorded on a ticket is visible afterwards",
        pre="A ticket has been resolved with details.",
        steps=["Open the resolved ticket.", "Find the resolution text and who wrote it."],
        expected=(
            "The resolution, the person and the time are all shown, so anybody picking the "
            "ticket up later knows what was done."
        ),
        priority=CRITICAL, uat=True, role=AGENT,
    ),
    Case(
        area="Reopening",
        title="A resolved ticket can be reopened if the customer comes back",
        pre="A resolved ticket exists.",
        steps=[
            "As a supervisor, reopen the resolved ticket with a reason.",
            "Check its stage, its deadline and its history.",
        ],
        expected=(
            "It returns to an active stage with the reason recorded. Confirm with the "
            "business what should happen to the deadline when a ticket is reopened."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Stage list",
        title="The stage names on screen match the names the business agreed",
        pre="You have the agreed stage list from the business.",
        steps=[
            "Read every stage name available on a ticket.",
            "Compare with the agreed list.",
        ],
        expected=(
            "The names match. Note that the system currently offers nine stage names while "
            "the requirement describes eight - settle this with the team before recording it "
            "as a defect."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, req="R14", ready=PARTLY,
    ),
    Case(
        area="Skipping stages",
        title="A stage cannot be skipped by submitting a change directly",
        kind=NEGATIVE,
        pre="Ask the team how to submit a stage change directly.",
        steps=["Take a ticket in New and try to set its stage directly to Closed."],
        expected=(
            "It is refused on the server. The rules must not live only in the drag-and-drop "
            "behaviour on screen."
        ),
        priority=CRITICAL, role=AGENT,
    ),
    Case(
        area="Unassigned tickets",
        title="An unassigned ticket cannot be moved into In Progress",
        kind=NEGATIVE,
        pre="A ticket has nobody assigned.",
        steps=["Try to drag an unassigned ticket into In Progress."],
        expected=(
            "Either it is refused with a message asking you to assign it first, or it is "
            "allowed and assigns it to you. Confirm which the business wants - work in "
            "progress owned by nobody is a real problem."
        ),
        priority=HIGH, uat=True, role=AGENT, ready=PARTLY,
    ),
    Case(
        area="Board refresh",
        title="The board reflects changes made elsewhere",
        kind=EDGE,
        pre="Two people are signed in with the board open.",
        steps=[
            "Person A moves a card.",
            "Person B refreshes their board.",
        ],
        expected="Person B sees the card in its new column.",
        priority=MEDIUM, role="Two staff members",
    ),
    Case(
        area="Long card content",
        title="A card with a long subject or long customer name stays readable",
        kind=EDGE,
        pre="A ticket has a very long subject.",
        steps=["Find that ticket's card on the board."],
        expected=(
            "The text is trimmed with dots and the card keeps its normal size. One card does "
            "not stretch the whole column."
        ),
        priority=LOW, role=AGENT,
    ),
    Case(
        area="Filtered drag",
        title="Moving a card while a filter is applied still works",
        kind=EDGE,
        pre="A filter is applied to the board.",
        steps=[
            "Apply a filter.",
            "Drag a card to another column.",
            "Clear the filter and check where the ticket is.",
        ],
        expected=(
            "The move is saved. If the ticket no longer matches the filter it may disappear "
            "from view, which is correct - but it must be in the right place when the filter "
            "is cleared."
        ),
        priority=MEDIUM, role=AGENT,
    ),
]

# --- M09 SLA Timers -------------------------------------------------------------------
M09.cases += [
    Case(
        area="Deadline on the list",
        title="The deadline state is visible without opening each ticket",
        pre="The list holds tickets in all three deadline states.",
        steps=["Look down the ticket list."],
        expected=(
            "Each row shows its deadline state clearly, so a supervisor can scan the queue "
            "and see what needs attention without opening anything."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R17",
    ),
    Case(
        area="Sorting by urgency",
        title="The list can be sorted by how close the deadline is",
        pre="Tickets have different deadlines.",
        steps=["Sort by deadline, soonest first."],
        expected=(
            "The most urgent appear first. This is how an agent decides what to work on next."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Deadline explanation",
        title="A ticket explains how its deadline was worked out",
        pre="A ticket has a deadline.",
        steps=["Open the ticket's SLA tab.", "Read what is shown."],
        expected=(
            "The rule that applied, the start point, the allowed time and the resulting "
            "deadline are shown, so a supervisor can check the maths rather than trusting it."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, req="R16",
    ),
    Case(
        area="Escalation ladder",
        title="The ticket shows what has already happened and what comes next",
        pre="A ticket has escalated at least once.",
        steps=["Open the SLA tab and read the escalation ladder."],
        expected=(
            "It shows which levels have been passed, which is current, and what happens next "
            "if nothing is done."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Holidays",
        title="The holiday calendar can be read and maintained",
        pre="You are signed in as a permitted role.",
        steps=[
            "Open the working hours or holiday settings.",
            "Check this year's UAE public holidays are listed.",
        ],
        expected=(
            "The holiday list is visible and can be maintained by permitted roles. A missing "
            "holiday means every deadline that week is wrong."
        ),
        priority=CRITICAL, uat=True, role=HOD, req="R16",
    ),
    Case(
        area="Different SLA per type",
        title="An enquiry and a complaint raised at the same moment get different deadlines",
        pre="You know the agreed deadlines for both.",
        steps=[
            "Create one enquiry and one complaint at the same time in the same department.",
            "Compare the two deadlines.",
        ],
        expected=(
            "They differ according to the agreed rules, showing the deadline follows the "
            "case type rather than a single global setting."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
    ),
    Case(
        area="Breach counting",
        title="One ticket breaching counts once, not repeatedly",
        kind=NEGATIVE,
        pre="A ticket has been breached for several days.",
        steps=[
            "Note the breach count on the report.",
            "Wait a day with the ticket still breached.",
            "Re-run the report for the same period.",
        ],
        expected=(
            "The ticket is still counted once. A breach that accumulates daily would make "
            "the management figures meaningless."
        ),
        priority=CRITICAL, uat=True, role=MANAGER, req="R28",
    ),
    Case(
        area="Closed tickets",
        title="A ticket resolved after its deadline is recorded as breached, not hidden",
        kind=NEGATIVE,
        pre="A ticket passed its deadline before being resolved.",
        steps=[
            "Let a ticket breach, then resolve it.",
            "Open it and read the deadline information.",
            "Check the report for that period.",
        ],
        expected=(
            "The ticket shows as completed, but the fact it was answered late is still "
            "recorded and still counted in the report. Resolving must not erase a breach."
        ),
        priority=CRITICAL, uat=True, role=MANAGER,
    ),
    Case(
        area="Fast clocks",
        title="Any test-only fast deadline setting is switched off in the live system",
        kind=NEGATIVE,
        pre="Ask the team whether a shortened-deadline test setting exists.",
        steps=[
            "Confirm with the team that the fast-clock setting exists only for testing.",
            "On the live system, create a ticket and check its deadline against the agreed "
            "rule.",
        ],
        expected=(
            "Live deadlines follow the real agreed times. A test setting left on in "
            "production would breach everything within minutes."
        ),
        priority=CRITICAL, role="Development team + QA",
    ),
    Case(
        area="Ramadan hours",
        title="Reduced working hours are handled if the business uses them",
        kind=EDGE,
        pre="Ask the business whether working hours change during Ramadan.",
        steps=[
            "Confirm whether reduced hours apply.",
            "If they do, check whether the system can be configured for them.",
        ],
        expected=(
            "Either reduced hours can be configured, or the business confirms they are not "
            "needed. Record the answer - this is easy to miss until it happens."
        ),
        priority=HIGH, uat=True, role=HOD, ready=PARTLY,
    ),
    Case(
        area="Very short deadline",
        title="A deadline shorter than one working day behaves correctly",
        kind=EDGE,
        pre="A rule exists with a deadline of a few hours.",
        steps=[
            "Create a ticket under that rule early in the day.",
            "Create another one an hour before closing.",
        ],
        expected=(
            "The first expires the same day. The second continues into the next working "
            "morning rather than expiring overnight."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R16",
    ),
]

# --- M10 Escalation -------------------------------------------------------------------
M10.cases += [
    Case(
        area="Notification content",
        title="An escalation notification contains enough to act on",
        pre="An escalation has just happened.",
        steps=["Read the notification the contact received."],
        expected=(
            "It names the reference number, the customer, how late the case is, the current "
            "level and a link straight to the ticket. A vague 'a ticket needs attention' is "
            "not enough."
        ),
        priority=HIGH, uat=True, role=POC,
    ),
    Case(
        area="Escalation visibility",
        title="A supervisor can see everything currently escalated in one place",
        pre="Several tickets are escalated at different levels.",
        steps=[
            "Open the escalation or teams view as a supervisor.",
            "Read the list.",
        ],
        expected=(
            "Every escalated ticket is listed with its level, its department and how long it "
            "has been there."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R20",
    ),
    Case(
        area="Resolution clears it",
        title="Resolving an escalated ticket closes off the escalation properly",
        pre="A ticket is escalated at level two.",
        steps=[
            "Resolve the escalated ticket.",
            "Check the escalation view and the contact's notifications.",
        ],
        expected=(
            "The ticket leaves the active escalation list, the escalation history stays on "
            "the ticket, and no further chasing notifications are sent."
        ),
        priority=CRITICAL, uat=True, role=AGENT,
    ),
    Case(
        area="Motor contacts",
        title="Motor escalation uses the Motor contact list, not the general one",
        pre="You have both contact lists from the business.",
        steps=[
            "Let a motor ticket escalate.",
            "Check who was notified against the Motor contact list.",
        ],
        expected=(
            "The Motor contacts are used. Motor has its own four-level chain and its own "
            "people, and mixing them up would send cases to the wrong managers."
        ),
        priority=CRITICAL, uat=True, role="System (no user action)", req="R18",
    ),
    Case(
        area="Level display",
        title="The escalation level is shown consistently everywhere",
        pre="A ticket is escalated.",
        steps=[
            "Look at the escalation indicator on the board card, in the list and on the "
            "ticket page.",
        ],
        expected=(
            "All three agree on the level and use the same wording. Raw numbers or internal "
            "codes should not appear."
        ),
        priority=MEDIUM, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Manual then automatic",
        title="A manually escalated ticket still escalates automatically afterwards",
        kind=EDGE,
        pre="A ticket has been escalated by hand to level one.",
        steps=[
            "Escalate a ticket by hand.",
            "Leave it unattended past the next escalation window.",
            "Check its level.",
        ],
        expected=(
            "It continues up the chain automatically from where the manual escalation left "
            "it. A manual escalation must not stop the automatic chain."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="De-escalation then breach",
        title="A de-escalated ticket that is still late escalates again",
        kind=EDGE,
        pre="A ticket was escalated and then brought back down.",
        steps=[
            "Bring an escalated ticket down a level.",
            "Leave it unattended.",
            "Check whether it escalates again.",
        ],
        expected=(
            "It escalates again if it stays late. De-escalating must not permanently switch "
            "off the chain for that ticket."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Contact leaves",
        title="An escalation contact who has left the company does not black-hole the case",
        kind=EDGE,
        pre="An escalation contact is about to be deactivated.",
        steps=[
            "Deactivate the configured contact for a level.",
            "Let a ticket escalate to that level.",
            "Check who was notified.",
        ],
        expected=(
            "Somebody active is told - a fallback or the department head - and the gap is "
            "visible to an administrator. A deactivated contact must not silently swallow "
            "escalations."
        ),
        priority=CRITICAL, uat=True, role=ADMIN,
    ),
    Case(
        area="Escalation history",
        title="The escalation history cannot be edited or removed",
        kind=ACCESS,
        pre="A ticket has escalation history.",
        steps=[
            "Look for edit or delete controls on the escalation entries as a supervisor.",
            "Look again as an administrator.",
        ],
        expected=(
            "No role can change or remove an escalation record. It is evidence of how the "
            "case was handled."
        ),
        priority=CRITICAL, uat=True, role=f"{SUPERVISOR}, then {ADMIN}", req="R29",
    ),
    Case(
        area="Cross-department",
        title="An escalation contact only sees the tickets they are entitled to",
        kind=ACCESS,
        pre="A contact is notified about a ticket outside their normal scope.",
        steps=[
            "Let a ticket escalate to a contact.",
            "Sign in as that contact and open the ticket from the notification.",
        ],
        expected=(
            "They can open the ticket they were escalated to, because being the escalation "
            "contact is their reason to see it. They still cannot browse the rest of that "
            "department's tickets."
        ),
        priority=CRITICAL, uat=True, role=POC,
    ),
]
