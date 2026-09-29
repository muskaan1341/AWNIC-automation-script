"""Modules 10-12: Escalation, Complaints Register, Duplicate Detection."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case, Module
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR

# =====================================================================================
M10 = Module(
    code="M10",
    name="Escalation",
    plain_summary=(
        "When a deadline is missed the ticket automatically climbs the chain. Motor cases "
        "have four levels, non-motor cases have three, plus an overall working-day ceiling. "
        "A supervisor can also escalate early by hand."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="First escalation",
            title="A ticket that misses its first deadline escalates by itself",
            pre=(
                "A ticket has passed its first response deadline and is not resolved. Ask "
                "the team to run the deadline check if it runs on a schedule."
            ),
            steps=[
                "Let a ticket pass its first response deadline.",
                "Wait for the scheduled deadline check to run (ask the team how often).",
                "Open the ticket and read the escalation area.",
            ],
            expected=(
                "The ticket is now at escalation level one, the escalation is listed with "
                "the date and time, and the ticket card shows an escalation badge."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R18, R19, R37",
        ),
        Case(
            area="Notification",
            title="The right person is notified at each escalation level",
            pre="A ticket is about to escalate.",
            steps=[
                "Note who the configured contact is for level one in that department.",
                "Let the ticket escalate.",
                "Sign in as that contact and check their notifications and email.",
            ],
            expected=(
                "The configured level-one contact is notified in the app, and by email if "
                "that is configured, naming the ticket and how late it is."
            ),
            priority=CRITICAL, uat=True, role="System, then the contact", req="R18, R19",
        ),
        Case(
            area="Non-motor chain",
            title="A non-motor complaint climbs all three levels in order",
            pre="A non-motor complaint is left unattended past every deadline.",
            steps=[
                "Leave a non-motor complaint unattended.",
                "After each escalation window passes, check the ticket.",
                "Record the level, the time and who was notified each time.",
            ],
            expected=(
                "It moves through level one, then level two, then the final level, in order, "
                "with the right contact notified at each step. It never skips a level."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R19",
        ),
        Case(
            area="Motor chain",
            title="A motor complaint climbs all four levels in order",
            pre="A motor complaint is left unattended past every deadline.",
            steps=[
                "Leave a motor complaint unattended.",
                "Check it after each escalation window.",
                "Record the level, the time and who was notified each time.",
            ],
            expected=(
                "It moves through all four motor levels in order with the correct motor "
                "contact notified at each step."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R18",
        ),
        Case(
            area="Overall ceiling",
            title="A case still unresolved after the agreed working-day limit reaches the top",
            pre="A ticket has been open beyond the agreed overall working-day ceiling.",
            steps=[
                "Leave a ticket open past the overall ceiling (two or three working days, "
                "confirm which with the business).",
                "Check the ticket.",
            ],
            expected=(
                "The ticket has reached the final escalation level and the department head "
                "has been notified, regardless of which level it had reached before."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R25",
        ),
        Case(
            area="Manual escalation",
            title="A supervisor can escalate a ticket early by hand",
            pre="A ticket is still within its deadline.",
            steps=[
                "Open the ticket as a supervisor.",
                "Choose Escalate and give a reason.",
                "Confirm.",
            ],
            expected=(
                "The ticket moves to the next escalation level immediately, the contact is "
                "notified, and the history records who escalated it early and why."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R20",
        ),
        Case(
            area="Manual escalation",
            title="A supervisor can jump straight to the final level for a serious case",
            pre="A serious ticket needs immediate attention.",
            steps=[
                "Open the ticket and choose to escalate to the final level.",
                "Give a reason and confirm.",
            ],
            expected=(
                "The ticket goes straight to the final level, the department head is "
                "notified, and the jump plus reason are in the history."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR, req="R20",
        ),
        Case(
            area="De-escalation",
            title="A supervisor can send a ticket back down a level",
            pre="A ticket is escalated at level two.",
            steps=[
                "Open the ticket and choose to bring it back down a level.",
                "Give a reason and confirm.",
            ],
            expected=(
                "The level drops by one, the change and reason are in the history, and the "
                "escalation badge on the card updates."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR, req="R20",
        ),
        Case(
            area="Escalation history",
            title="The full escalation story is visible on the ticket",
            pre="A ticket has been escalated more than once.",
            steps=[
                "Open the ticket's escalation section.",
            ],
            expected=(
                "Every escalation is listed in order with the level, the date and time, who "
                "or what triggered it, the reason, and who was notified."
            ),
            priority=HIGH, uat=True, role=MANAGER, req="R20, R29",
        ),
        Case(
            area="Escalation contacts",
            title="The escalation contacts can be read and maintained on screen",
            pre="You are signed in as a head of department.",
            steps=[
                "Open the Teams and SLA screen.",
                "Read the escalation contacts for a department at each level.",
                "Change one contact and save.",
            ],
            expected=(
                "The contacts are visible per department and per level, can be changed by "
                "the permitted roles, and the change takes effect on the next escalation."
            ),
            priority=HIGH, uat=True, role=HOD, req="R18, R19",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="No double escalation",
            title="The same ticket does not escalate twice for the same missed deadline",
            kind=NEGATIVE,
            pre="A ticket has already escalated to level one.",
            steps=[
                "Ask the team to run the deadline check again immediately.",
                "Open the ticket and count the escalation entries.",
            ],
            expected=(
                "There is still only one level-one escalation and only one notification was "
                "sent. Repeated checks must not spam the contacts."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Resolved tickets",
            title="A resolved ticket does not escalate",
            kind=NEGATIVE,
            pre="A ticket was resolved before its deadline.",
            steps=[
                "Resolve a ticket.",
                "Let its original deadline pass.",
                "Ask the team to run the deadline check.",
                "Check the ticket and the contact's notifications.",
            ],
            expected=(
                "No escalation happens and nobody is notified. Finished work must not chase "
                "people."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Discarded tickets",
            title="A discarded ticket does not escalate",
            kind=NEGATIVE,
            pre="A ticket has been discarded.",
            steps=[
                "Discard a ticket that had a deadline.",
                "Let the original deadline pass and run the deadline check.",
                "Check the discarded ticket and the contacts' notifications.",
            ],
            expected="No escalation and no notifications. Junk never chases a department head.",
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Missing contact",
            title="A department with no escalation contact does not silently swallow the case",
            kind=NEGATIVE,
            pre="Ask the team for a department with no contact configured at some level.",
            steps=[
                "Let a ticket in that department escalate to the level with no contact.",
                "Check the ticket and any fallback notification.",
            ],
            expected=(
                "The escalation is still recorded on the ticket and somebody sensible - a "
                "fallback contact or an administrator - is told. The escalation is never "
                "just dropped."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Manual escalation",
            title="Escalating without a reason is refused",
            kind=NEGATIVE,
            pre="You are on a ticket as a supervisor.",
            steps=[
                "Start a manual escalation and leave the reason blank.",
                "Confirm.",
            ],
            expected="It is refused. A reason is always required for an early escalation.",
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Beyond the top",
            title="A ticket already at the final level cannot be escalated further",
            kind=NEGATIVE,
            pre="A ticket is at the final escalation level.",
            steps=[
                "Try to escalate it again by hand.",
            ],
            expected=(
                "The option is not offered or the action is refused with a message that it "
                "is already at the top."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Escalation and resolution together",
            title="Resolving a ticket at the same moment it escalates ends cleanly",
            kind=EDGE,
            pre="A ticket is about to escalate.",
            steps=[
                "Have an agent resolve the ticket at almost the same moment the deadline "
                "check runs.",
                "Read the ticket, its history and the contact's notifications.",
            ],
            expected=(
                "The ticket ends up either resolved or resolved-and-escalated-once, with a "
                "readable history. It never ends up in a stuck or contradictory state."
            ),
            priority=HIGH, role="System + " + AGENT,
        ),
        Case(
            area="Weekend escalation",
            title="Escalation timing respects working hours and weekends",
            kind=EDGE,
            pre="A ticket's escalation window would fall across a weekend.",
            steps=[
                "Let a ticket approach escalation on the last working day of the week.",
                "Note when it actually escalates.",
            ],
            expected=(
                "The escalation happens according to working hours, not raw clock hours. "
                "Confirm the agreed rule with the business - a department head must not be "
                "chased for a case that was never late in working time."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R25",
        ),
        Case(
            area="Reassignment",
            title="Reassigning an escalated ticket does not reset its level",
            kind=EDGE,
            pre="A ticket is escalated at level two.",
            steps=[
                "Reassign the ticket to a different agent.",
                "Check the escalation level.",
            ],
            expected=(
                "It stays at level two. Reassignment must never be a way to clear an "
                "escalation."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Department change",
            title="Moving an escalated ticket to another department behaves predictably",
            kind=EDGE,
            pre="An escalated ticket exists.",
            steps=[
                "Change the ticket's department.",
                "Check the escalation level and who is now the contact.",
            ],
            expected=(
                "The behaviour matches what the business agreed - either the level carries "
                "over with the new department's contacts, or it restarts. Record the answer "
                "and check it is consistent, not random."
            ),
            priority=HIGH, role=SUPERVISOR, ready=PARTLY,
        ),
        Case(
            area="Many at once",
            title="Many tickets breaching at the same time all escalate correctly",
            kind=EDGE,
            pre="Twenty tickets are about to pass their deadline together.",
            steps=[
                "Let twenty tickets breach at the same time.",
                "Run the deadline check.",
                "Count the escalations and the notifications.",
            ],
            expected=(
                "All twenty escalate, each with exactly one notification. None are missed "
                "and none are notified twice."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        Case(
            area="Scheduler failure",
            title="Escalations missed during an outage are caught up afterwards",
            kind=EDGE,
            pre="Ask the team to pause the scheduled deadline check.",
            steps=[
                "Pause the deadline check.",
                "Let several tickets breach.",
                "Resume the check.",
            ],
            expected=(
                "All the breached tickets escalate once the check resumes. Nothing is "
                "permanently missed because the scheduler was down."
            ),
            priority=CRITICAL, role="System (no user action)",
        ),
        Case(
            area="Duplicate schedulers",
            title="Escalation notifications are not sent twice",
            kind=EDGE,
            pre="A ticket has just escalated.",
            steps=[
                "Ask the contact to check their inbox and notification list carefully.",
                "Count how many notices arrived for that one escalation.",
            ],
            expected=(
                "Exactly one notification per escalation. Two copies suggests the check is "
                "running from two places, which the team must fix."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can escalate",
            title="An agent cannot escalate a ticket by hand",
            kind=ACCESS,
            pre="You are a Customer Care Agent on a ticket assigned to you.",
            steps=[
                "Look for an Escalate option.",
                "If you have the address of the action, try it directly.",
            ],
            expected="It is not offered and any direct attempt is refused.",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Who can de-escalate",
            title="Only senior roles can send a ticket back down",
            kind=ACCESS,
            pre="An escalated ticket exists.",
            steps=[
                "Sign in as each role and check who can bring the level down.",
                "Compare against the agreed role matrix.",
            ],
            expected=(
                "Only the roles named in the matrix can de-escalate. This matters because "
                "de-escalating hides a problem from a department head."
            ),
            priority=CRITICAL, uat=True, role="All roles",
        ),
        Case(
            area="Contacts",
            title="Only permitted roles can change escalation contacts",
            kind=ACCESS,
            pre="You have supervisor and head of department sign-ins.",
            steps=[
                "As a Customer Care Supervisor, try to edit the escalation contacts.",
                "As a head of department, try the same.",
            ],
            expected=(
                "Editing matches the agreed matrix, and any change is recorded with who made "
                "it."
            ),
            priority=HIGH, role=f"{SUPERVISOR}, then {HOD}",
        ),
        Case(
            area="Scheduled check",
            title="The deadline check cannot be triggered by an outsider",
            kind=ACCESS,
            pre="Ask the team for the address the scheduler calls.",
            steps=[
                "Call that address from a browser with no credentials.",
                "Call it again with a made-up key.",
            ],
            expected=(
                "Both are refused. Otherwise an outsider could trigger a flood of escalation "
                "notifications to AWNIC's management."
            ),
            priority=CRITICAL, role="Outsider with no access",
        ),
    ],
)

# =====================================================================================
M11 = Module(
    code="M11",
    name="Complaints Register",
    plain_summary=(
        "Complaints carry a much larger record than enquiries, plus investigation notes and "
        "resolution remarks that can only be added to - never edited or deleted."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Register record",
            title="A complaint has its own detailed register record",
            pre="A complaint exists.",
            steps=[
                "Open the complaint.",
                "Open the complaint register or details section.",
                "Read through all the fields.",
            ],
            expected=(
                "The full register is shown with all its fields grouped sensibly - customer "
                "details, policy details, the complaint itself, category, severity, dates "
                "and outcome."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R23",
        ),
        Case(
            area="Register record",
            title="A complaint handler can fill in and save the register fields",
            pre="A complaint exists with the register mostly empty.",
            steps=[
                "Open the register and fill in the customer, policy and complaint fields.",
                "Save.",
                "Reopen the complaint.",
            ],
            expected="Every value is saved and shown correctly when reopened.",
            priority=CRITICAL, uat=True, role=HANDLER, req="R23",
        ),
        Case(
            area="Complaint number",
            title="A complaint gets its own complaint number",
            pre="A new complaint has just been created.",
            steps=[
                "Open the complaint.",
                "Note the complaint reference number.",
                "Create a second complaint and compare.",
            ],
            expected=(
                "Each complaint gets a unique number in the agreed format, running in "
                "sequence."
            ),
            priority=HIGH, uat=True, role=HANDLER, req="R33",
        ),
        Case(
            area="Investigation notes",
            title="A handler can add an investigation note",
            pre="A complaint is open and assigned to you.",
            steps=[
                "Open the Investigation tab.",
                "Add a note describing what you found.",
                "Save.",
            ],
            expected=(
                "The note is added to the list with your name and the date and time. "
                "Previous notes stay exactly as they were."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R42",
        ),
        Case(
            area="Investigation notes",
            title="Several notes build up a readable investigation trail",
            pre="A complaint is under investigation.",
            steps=[
                "Add three notes on different days or at different times.",
                "Read the Investigation tab.",
            ],
            expected=(
                "All three notes are listed in order, each with its author and time, so "
                "anybody can follow what was done."
            ),
            priority=HIGH, uat=True, role=HANDLER, req="R42",
        ),
        Case(
            area="Resolution remarks",
            title="A handler can record how the complaint was resolved",
            pre="A complaint is ready to be closed out.",
            steps=[
                "Add a resolution remark describing the outcome and what was offered.",
                "Save and reopen.",
            ],
            expected=(
                "The remark is saved with the author and time and is shown with the "
                "complaint's outcome."
            ),
            priority=CRITICAL, uat=True, role=HANDLER, req="R42",
        ),
        Case(
            area="Categories",
            title="Complaint categories come from the approved list",
            pre="You are on the complaint register.",
            steps=[
                "Open the category list.",
                "Compare it with the approved category list from the business.",
                "Pick one, save, and reopen.",
            ],
            expected=(
                "The list matches the approved one exactly and the chosen value is saved "
                "correctly."
            ),
            priority=HIGH, uat=True, role=HANDLER, req="R23",
        ),
        Case(
            area="Historical complaints",
            title="Historical complaints imported from the old spreadsheet can be read",
            pre="Historical complaint records have been loaded into the test system.",
            steps=[
                "Search for a historical complaint.",
                "Open it and read its details.",
                "Try to edit it.",
            ],
            expected=(
                "The historical record opens and is readable. It is clearly marked as "
                "historical and is read-only."
            ),
            priority=HIGH, uat=True, role=MANAGER, ready=PARTLY,
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="Investigation notes",
            title="An investigation note cannot be edited after it is saved",
            kind=NEGATIVE,
            pre="An investigation note has been saved.",
            steps=[
                "Look for an edit control on the saved note.",
                "Sign in as a manager and look again.",
                "Sign in as an administrator and look again.",
            ],
            expected=(
                "Nobody can edit a saved note - not the author, not a manager, not an "
                "administrator. Notes are evidence. If a correction is needed, a new note is "
                "added."
            ),
            priority=CRITICAL, uat=True, role=f"{HANDLER}, {MANAGER}, {ADMIN}", req="R42",
        ),
        Case(
            area="Investigation notes",
            title="An investigation note cannot be deleted",
            kind=NEGATIVE,
            pre="An investigation note has been saved.",
            steps=[
                "Look for a delete control as the author, then as a manager, then as an "
                "administrator.",
            ],
            expected=(
                "There is no delete option for anybody. The note stays on the complaint "
                "permanently."
            ),
            priority=CRITICAL, uat=True, role=f"{HANDLER}, {MANAGER}, {ADMIN}", req="R42",
        ),
        Case(
            area="Investigation notes",
            title="An empty note cannot be saved",
            kind=NEGATIVE,
            pre="You are on the Investigation tab.",
            steps=[
                "Save a note with nothing in it.",
                "Try again with only spaces.",
            ],
            expected="Both are refused. No blank entry is added to the trail.",
            priority=MEDIUM, role=HANDLER,
        ),
        Case(
            area="Required fields",
            title="The register cannot be saved with required fields missing",
            kind=NEGATIVE,
            pre="You are on the complaint register.",
            steps=[
                "Clear the required fields such as category and severity.",
                "Save.",
            ],
            expected="Saving is refused and each missing field is marked.",
            priority=HIGH, role=HANDLER,
        ),
        Case(
            area="Dates",
            title="A complaint cannot be given a date in the future or before it was received",
            kind=NEGATIVE,
            pre="You are on the complaint register.",
            steps=[
                "Set a resolution date in the future and save.",
                "Set a resolution date before the complaint was received and save.",
            ],
            expected=(
                "Both are refused with a clear message. Dates that make no sense would "
                "corrupt the reporting figures."
            ),
            priority=HIGH, uat=True, role=HANDLER,
        ),
        Case(
            area="Type change",
            title="A complaint with register details cannot be turned into an enquiry",
            kind=NEGATIVE,
            pre="A complaint has register details and investigation notes saved.",
            steps=[
                "Try to change the ticket type to Enquiry.",
            ],
            expected=(
                "It is refused with a message explaining the complaint record would be "
                "orphaned. This protects the permanent complaint trail."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR,
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Long notes",
            title="A very long investigation note is saved in full",
            kind=EDGE,
            pre="You are on the Investigation tab.",
            steps=[
                "Paste a note of 5,000 characters.",
                "Save and reopen.",
            ],
            expected=(
                "The whole note is kept and is shown scrollable or expandable. It is not "
                "silently cut short."
            ),
            priority=MEDIUM, role=HANDLER,
        ),
        Case(
            area="Arabic notes",
            title="Investigation notes in Arabic save and display correctly",
            kind=EDGE,
            pre="You are on the Investigation tab.",
            steps=[
                "Add a note written in Arabic.",
                "Save and reopen.",
            ],
            expected="The Arabic text reads correctly right to left with no broken characters.",
            priority=HIGH, uat=True, role=HANDLER,
        ),
        Case(
            area="Two handlers",
            title="Two handlers adding notes at the same time both get saved",
            kind=EDGE,
            pre="Two handlers are signed in on the same complaint.",
            steps=[
                "Both add a note and save at the same moment.",
                "Refresh and read the trail.",
            ],
            expected="Both notes appear, in a sensible order, each with the right author.",
            priority=HIGH, role=f"Two {HANDLER}s",
        ),
        Case(
            area="Many fields",
            title="The full register form is usable on a normal screen",
            kind=EDGE,
            pre="You are on the complaint register with all its fields.",
            steps=[
                "Work through the whole form on a standard laptop screen.",
                "Tab from field to field with the keyboard only.",
                "Save from the keyboard.",
            ],
            expected=(
                "The form is grouped into readable sections, the tab order follows the "
                "visual order, and it can be completed without a mouse."
            ),
            priority=MEDIUM, role=HANDLER,
        ),
        Case(
            area="Partial save",
            title="Losing the connection while saving does not half-save the register",
            kind=EDGE,
            pre="You can disconnect the network on your test machine.",
            steps=[
                "Fill in several register fields.",
                "Disconnect the network and click Save.",
                "Reconnect and reopen the complaint.",
            ],
            expected=(
                "You are told the save failed. On reopening, either all your changes are "
                "there or none are - never a half-saved record."
            ),
            priority=HIGH, role=HANDLER,
        ),
        Case(
            area="Reopening",
            title="A resolved complaint that is reopened keeps its whole history",
            kind=EDGE,
            pre="A resolved complaint exists with notes and remarks.",
            steps=[
                "Reopen the complaint if your role allows it.",
                "Read the investigation and resolution trails.",
            ],
            expected=(
                "Everything previously recorded is still there and the reopening is added to "
                "the history. Nothing from the first round is lost."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can see complaints",
            title="A role without complaint rights cannot see the register",
            kind=ACCESS,
            pre="Sign in as a role that cannot view complaints.",
            steps=[
                "Check the Complaints menu is absent.",
                "Try the complaints list address directly.",
                "Try a complaint's investigation tab address directly.",
            ],
            expected="All refused, and the complaint shows as not found rather than forbidden.",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Own-assigned scope",
            title="A handler cannot read another handler's investigation notes",
            kind=ACCESS,
            pre="A complaint is assigned to a different handler.",
            steps=[
                "As a Complaint Handler, get that complaint's investigation tab address.",
                "Try to open it.",
            ],
            expected="Refused as not found. Investigation notes are sensitive.",
            priority=CRITICAL, uat=True, role=HANDLER,
        ),
        Case(
            area="Compliance access",
            title="A compliance officer can read complaints but cannot change them",
            kind=ACCESS,
            pre="You are signed in as a Compliance Officer.",
            steps=[
                "Open a complaint and its investigation and resolution trails.",
                "Look for any add, edit or delete control.",
                "Try a save action directly if you can reach one.",
            ],
            expected=(
                "Reading works for oversight. No change is possible from the screen or "
                "directly."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE,
        ),
        Case(
            area="Historical data",
            title="Historical complaint data respects the same visibility rules",
            kind=ACCESS,
            pre="Historical complaints are loaded and contain real customer details.",
            steps=[
                "Sign in as a role with limited ticket visibility.",
                "Search the historical complaints.",
            ],
            expected=(
                "Historical records follow the same visibility rules as live ones. An import "
                "must never become a back door to everybody's data."
            ),
            priority=CRITICAL, uat=True, role=HANDLER,
        ),
    ],
)

# =====================================================================================
M12 = Module(
    code="M12",
    name="Duplicate Detection",
    plain_summary=(
        "The system flags tickets that look like the same issue and shows them side by "
        "side. A person always decides - nothing is ever merged automatically."
    ),
    cases=[
        # --- POSITIVE ----------------------------------------------------------------
        Case(
            area="Detection",
            title="The same customer raising the same issue twice is flagged as a possible duplicate",
            pre="The duplicate check is running.",
            steps=[
                "Send an email about a specific claim from a customer mailbox.",
                "Wait for the ticket, then send a second, similarly worded email from the "
                "same customer.",
                "Open the second ticket.",
            ],
            expected=(
                "The second ticket carries a possible-duplicate flag pointing at the first, "
                "with a way to compare them."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R26",
        ),
        Case(
            area="Comparing",
            title="A supervisor can compare the two tickets side by side",
            pre="A ticket is flagged as a possible duplicate.",
            steps=[
                "Open the flagged ticket.",
                "Click to compare with the suggested duplicate.",
            ],
            expected=(
                "Both tickets are shown side by side with their reference numbers, "
                "customers, dates, descriptions and statuses, so the differences are obvious."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R26",
        ),
        Case(
            area="Confirming",
            title="A supervisor can confirm two tickets are the same case",
            pre="You are on the comparison screen.",
            steps=[
                "Review both tickets.",
                "Choose to confirm them as duplicates and give a reason.",
                "Confirm.",
            ],
            expected=(
                "The tickets are linked, one is marked as the duplicate, and the decision - "
                "who made it, when, and why - is recorded on both."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R26",
        ),
        Case(
            area="Rejecting",
            title="A supervisor can reject a duplicate suggestion",
            pre="A ticket is flagged as a possible duplicate but is actually different.",
            steps=[
                "Open the comparison and review both.",
                "Choose Not a duplicate and give a reason.",
                "Reopen the ticket.",
            ],
            expected=(
                "The flag is cleared, both tickets carry on separately, and the rejection is "
                "recorded with the reason."
            ),
            priority=CRITICAL, uat=True, role=SUPERVISOR, req="R26",
        ),
        Case(
            area="Decision record",
            title="Every duplicate decision is permanently recorded",
            pre="Duplicate decisions have been made on the test system.",
            steps=[
                "Open a ticket that had a duplicate decision.",
                "Read its history.",
            ],
            expected=(
                "The decision appears in the history with the person, the time, the outcome "
                "and the reason. It cannot be removed."
            ),
            priority=HIGH, uat=True, role=COMPLIANCE, req="R26, R29",
        ),
        Case(
            area="Multi-channel",
            title="The same customer contacting by two channels is spotted",
            pre="You can create tickets by email and by hand for the same customer.",
            steps=[
                "Create a ticket by email for a test customer.",
                "Create a second ticket by hand for the same customer about the same issue.",
                "Open the second ticket.",
            ],
            expected=(
                "The system flags the possible duplicate even though the two arrived by "
                "different routes. A customer using two channels is one case, not two."
            ),
            priority=CRITICAL, uat=True, role=AGENT, req="R26",
        ),
        # --- NEGATIVE ----------------------------------------------------------------
        Case(
            area="No silent merging",
            title="The system never merges two tickets on its own",
            kind=NEGATIVE,
            pre="A very obvious duplicate pair exists - identical text from the same sender.",
            steps=[
                "Create an obvious duplicate pair.",
                "Wait for the duplicate check to run.",
                "Check both tickets still exist independently.",
            ],
            expected=(
                "Both tickets still exist and both are still workable. Only the flag is "
                "added. An automatic merge would be a serious defect - the decision belongs "
                "to a person."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)", req="R26",
        ),
        Case(
            area="False positives",
            title="Two genuinely different tickets from one customer are not flagged",
            kind=NEGATIVE,
            pre="You have a customer mailbox.",
            steps=[
                "Send one email about a motor claim.",
                "Send another about a completely different travel policy question.",
                "Check both tickets.",
            ],
            expected=(
                "Neither is flagged as a duplicate. Over-flagging would train staff to "
                "ignore the warning."
            ),
            priority=HIGH, uat=True, role="System (no user action)",
        ),
        Case(
            area="Different customers",
            title="Similar wording from two different customers is not flagged",
            kind=NEGATIVE,
            pre="You have two different customer mailboxes.",
            steps=[
                "Send nearly identical text from two different customer addresses.",
                "Check both tickets.",
            ],
            expected=(
                "They are not flagged as duplicates of each other. Two customers with the "
                "same problem are two separate cases."
            ),
            priority=CRITICAL, uat=True, role="System (no user action)",
        ),
        Case(
            area="Reason required",
            title="A duplicate decision cannot be recorded without a reason",
            kind=NEGATIVE,
            pre="You are on the comparison screen.",
            steps=[
                "Choose confirm or reject and leave the reason blank.",
                "Submit.",
            ],
            expected="It is refused. A reason is always required for the record.",
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Already decided",
            title="A pair that has already been decided is not offered again",
            kind=NEGATIVE,
            pre="A duplicate pair has already been rejected.",
            steps=[
                "Wait for the duplicate check to run again.",
                "Open the ticket.",
            ],
            expected=(
                "The same pair is not flagged again. Repeatedly asking about a decision "
                "already made is noise."
            ),
            priority=HIGH, role="System (no user action)",
        ),
        # --- EDGE --------------------------------------------------------------------
        Case(
            area="Three-way",
            title="A customer sending the same thing three times is handled sensibly",
            kind=EDGE,
            pre="You have a customer mailbox.",
            steps=[
                "Send the same request three times over an hour.",
                "Open all three tickets.",
            ],
            expected=(
                "The duplicates are flagged in a way a supervisor can resolve in one pass, "
                "not a confusing web of pairs. All three can be linked to one real case."
            ),
            priority=HIGH, role=SUPERVISOR,
        ),
        Case(
            area="Closed tickets",
            title="A new ticket matching an old closed one is handled correctly",
            kind=EDGE,
            pre="A closed ticket exists from months ago.",
            steps=[
                "Send a new email about the same old issue.",
                "Open the new ticket.",
            ],
            expected=(
                "Either it is flagged as related to the closed one, or it is left alone with "
                "the customer's history still visible. It is never merged into a closed "
                "ticket where nobody would work it."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR,
        ),
        Case(
            area="Confirmed duplicate",
            title="A confirmed duplicate does not keep chasing its own deadline",
            kind=EDGE,
            pre="Two tickets have been confirmed as duplicates.",
            steps=[
                "Note what happened to the duplicate ticket's deadline.",
                "Let the original deadline pass.",
                "Check the breached list.",
            ],
            expected=(
                "The duplicate does not appear as a separate breach inflating the figures. "
                "Confirm the agreed behaviour with the business."
            ),
            priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
        ),
        Case(
            area="Two supervisors",
            title="Two supervisors deciding on the same pair at the same time",
            kind=EDGE,
            pre="Two supervisors are signed in on the same flagged pair.",
            steps=[
                "One confirms the duplicate, the other rejects it, at the same moment.",
                "Refresh and read the history.",
            ],
            expected=(
                "One decision wins and the other is refused with a message saying it was "
                "already decided. The history shows one clear outcome."
            ),
            priority=HIGH, role=f"Two {SUPERVISOR}s",
        ),
        Case(
            area="Volume",
            title="Duplicate checking does not slow down ticket creation",
            kind=EDGE,
            pre="The system has a large number of existing tickets.",
            steps=[
                "Create ten tickets in a row and time how long each takes to appear.",
            ],
            expected=(
                "Tickets appear promptly. The duplicate check happens without making staff "
                "wait."
            ),
            priority=MEDIUM, role=AGENT,
        ),
        # --- ACCESS ------------------------------------------------------------------
        Case(
            area="Who can decide",
            title="An agent cannot confirm or reject a duplicate",
            kind=ACCESS,
            pre="A flagged pair exists and you are a Customer Care Agent.",
            steps=[
                "Open the flagged ticket and look for the decision buttons.",
                "Try the decision action directly if you can get the address.",
            ],
            expected="The buttons are absent and any direct attempt is refused.",
            priority=CRITICAL, uat=True, role=AGENT,
        ),
        Case(
            area="Comparison scope",
            title="The comparison screen does not reveal a ticket you are not allowed to see",
            kind=ACCESS,
            pre=(
                "A flagged pair exists where one ticket is inside your scope and the other "
                "is not."
            ),
            steps=[
                "As a scoped role, open the comparison for that pair.",
            ],
            expected=(
                "The details of the ticket you may not see are not shown. The comparison "
                "screen must not become a way around the visibility rules - this is a "
                "classic leak point, so test it carefully."
            ),
            priority=CRITICAL, uat=True, role=POC,
        ),
        Case(
            area="Detection endpoint",
            title="The duplicate check entry point cannot be called by an outsider",
            kind=ACCESS,
            pre="Ask the team for the address the duplicate check uses.",
            steps=[
                "Call it from a browser with no credentials.",
                "Call it with a made-up key.",
            ],
            expected="Both are refused and no ticket data is returned.",
            priority=CRITICAL, role="Outsider with no access",
        ),
    ],
)
