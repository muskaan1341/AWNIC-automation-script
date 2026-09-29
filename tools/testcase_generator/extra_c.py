"""Additional depth for modules 11-15. Imported for its side effects."""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case
from m01_m03 import ADMIN, AGENT, ANY, COMPLIANCE, HANDLER, HOD, MANAGER, POC, SUPERVISOR
from m10_m12 import M11, M12
from m13_m15 import M13, M14, M15

# --- M11 Complaints Register ----------------------------------------------------------
M11.cases += [
    Case(
        area="Register fields",
        title="Every field in the register is checked against the agreed field list",
        pre="You have the agreed complaint register field list from the business.",
        steps=[
            "Open the complaint register.",
            "Tick off each field on your list against what is on screen.",
            "Note anything missing and anything extra.",
        ],
        expected=(
            "All the agreed fields are present, correctly labelled and in a sensible order. "
            "Report anything missing to the business rather than guessing."
        ),
        priority=CRITICAL, uat=True, role=HANDLER, req="R23",
    ),
    Case(
        area="Register fields",
        title="Dropdown fields offer the agreed values",
        pre="You have the agreed value lists.",
        steps=[
            "Open each dropdown in the register - category, severity, source, outcome.",
            "Compare each list with the agreed values.",
        ],
        expected=(
            "Every list matches, with no test values left in and nothing missing. Reports "
            "group by these values, so a wrong list corrupts the reporting."
        ),
        priority=CRITICAL, uat=True, role=HANDLER, req="R23",
    ),
    Case(
        area="Saving progress",
        title="A part-filled register can be saved and finished later",
        pre="You are on the complaint register.",
        steps=[
            "Fill in half the fields and save.",
            "Sign out and back in.",
            "Reopen the complaint.",
        ],
        expected=(
            "The half-filled register is preserved. An investigation takes days, so a handler "
            "must be able to save progress."
        ),
        priority=CRITICAL, uat=True, role=HANDLER,
    ),
    Case(
        area="Completeness",
        title="The complaint shows what is still missing before it can be closed",
        pre="A complaint has an incomplete register.",
        steps=["Open a complaint with missing register fields.", "Look for a completeness hint."],
        expected=(
            "The handler can see what still needs filling in. Confirm with the business "
            "which fields must be complete before a complaint can be resolved."
        ),
        priority=HIGH, uat=True, role=HANDLER, ready=PARTLY,
    ),
    Case(
        area="Timeline",
        title="The complaint shows a readable timeline of what happened when",
        pre="A complaint has been open for a while with several actions.",
        steps=["Open the complaint and read its timeline or history."],
        expected=(
            "Received, acknowledged, investigated, escalated and resolved dates are all "
            "visible in order. This is what a regulator would ask to see."
        ),
        priority=CRITICAL, uat=True, role=COMPLIANCE, req="R29, R42",
    ),
    Case(
        area="Outcome",
        title="The complaint outcome is recorded in the agreed terms",
        pre="You are closing out a complaint.",
        steps=[
            "Record the outcome - upheld, partly upheld, not upheld, or whatever the "
            "business uses.",
            "Save and reopen.",
        ],
        expected=(
            "The outcome is saved and appears in the management report grouping. Confirm the "
            "agreed outcome values with the business."
        ),
        priority=HIGH, uat=True, role=HANDLER, req="R23",
    ),
    Case(
        area="Compensation",
        title="Any compensation or goodwill recorded is captured correctly",
        pre="The register has a compensation or goodwill field.",
        steps=[
            "Enter an amount and save.",
            "Try entering a negative amount and letters.",
        ],
        expected=(
            "A valid amount saves and displays with the right currency. Negative amounts and "
            "letters are refused."
        ),
        priority=HIGH, role=HANDLER, ready=PARTLY,
    ),
    Case(
        area="Field validation",
        title="An Emirates ID or policy number of the wrong length is refused",
        kind=NEGATIVE,
        pre="You are on the complaint register.",
        steps=["Enter a too-short Emirates ID and save.", "Enter letters in a numeric field."],
        expected="Both are refused with a message explaining the expected format.",
        priority=HIGH, role=HANDLER,
    ),
    Case(
        area="Resolution order",
        title="A complaint cannot be marked resolved before it has been investigated",
        kind=NEGATIVE,
        pre="A complaint has no investigation notes.",
        steps=["Try to record a resolution on a complaint with no investigation recorded."],
        expected=(
            "Either it is refused, or a warning appears. Confirm with the business whether "
            "investigation notes are mandatory before resolution."
        ),
        priority=HIGH, uat=True, role=HANDLER, ready=PARTLY,
    ),
    Case(
        area="Note attribution",
        title="A note always shows the real author, even after a role change",
        kind=EDGE,
        pre="A handler has added notes and then changed department.",
        steps=[
            "Add a note as a handler.",
            "Have an administrator change that handler's department or role.",
            "Reopen the complaint and read the note.",
        ],
        expected=(
            "The note still shows who actually wrote it and when. Attribution must not "
            "change when the person's details change."
        ),
        priority=HIGH, uat=True, role=COMPLIANCE, req="R42",
    ),
    Case(
        area="Deactivated author",
        title="Notes written by somebody who has left are still readable and attributed",
        kind=EDGE,
        pre="A handler with existing notes has been deactivated.",
        steps=["Deactivate the handler.", "Open a complaint they wrote notes on."],
        expected=(
            "The notes are still there with their name on them. Deactivating a person must "
            "never remove their contribution to the record."
        ),
        priority=CRITICAL, uat=True, role=COMPLIANCE,
    ),
    Case(
        area="Data protection",
        title="Complaint records containing personal data are not exposed in bulk",
        kind=ACCESS,
        pre="You have a role with limited complaint visibility.",
        steps=[
            "Look for any export, print or bulk view of the complaints register.",
            "If one exists, run it and check what it contains.",
        ],
        expected=(
            "Any bulk output contains only the complaints that person can see, and masked "
            "fields stay masked in it. The register holds real customer personal data."
        ),
        priority=CRITICAL, uat=True, role=HANDLER, req="R22",
    ),
]

# --- M12 Duplicate Detection ----------------------------------------------------------
M12.cases += [
    Case(
        area="Flag visibility",
        title="The possible-duplicate flag is obvious on the ticket and in the list",
        pre="A ticket is flagged as a possible duplicate.",
        steps=["Look at the ticket in the list and then open it."],
        expected=(
            "The flag is visible in both places with a way to compare, so an agent does not "
            "start work on a duplicate without noticing."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R26",
    ),
    Case(
        area="Linked view",
        title="After confirming, both tickets show the link to each other",
        pre="Two tickets have been confirmed as duplicates.",
        steps=["Open each of the two tickets in turn."],
        expected=(
            "Each one shows the link to the other, so whoever opens either ticket sees the "
            "full picture."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Customer communication",
        title="A confirmed duplicate does not send the customer two sets of updates",
        pre="Two tickets for one customer have been confirmed as duplicates.",
        steps=[
            "Confirm the duplicate.",
            "Cause an update that would notify the customer.",
            "Check the customer mailbox.",
        ],
        expected=(
            "The customer receives one coherent update, not two conflicting ones about what "
            "is really the same case."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Merge content",
        title="Confirming a duplicate does not lose any information",
        pre="Both tickets have notes and attachments.",
        steps=[
            "Note what is on each ticket.",
            "Confirm them as duplicates.",
            "Check both tickets again.",
        ],
        expected=(
            "Nothing is deleted. Notes and attachments on both are still reachable. A "
            "duplicate decision links records - it must never destroy one."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, req="R26",
    ),
    Case(
        area="Undo",
        title="A duplicate decision made in error can be corrected",
        kind=NEGATIVE,
        pre="Two tickets were confirmed as duplicates by mistake.",
        steps=["Look for a way to undo the decision.", "If one exists, use it and check both tickets."],
        expected=(
            "Either the decision can be reversed with the correction recorded, or it cannot "
            "and the business has accepted that. Confirm which - people make mistakes."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Detection timing",
        title="Duplicates are spotted quickly enough to be useful",
        kind=EDGE,
        pre="You can time how long detection takes.",
        steps=[
            "Create a duplicate pair and note the time.",
            "Watch how long until the flag appears.",
        ],
        expected=(
            "The flag appears before an agent would realistically start work on it. A "
            "duplicate spotted after both were answered has no value."
        ),
        priority=HIGH, role="System (no user action)",
    ),
    Case(
        area="Across types",
        title="An enquiry and a complaint about the same issue are related sensibly",
        kind=EDGE,
        pre="A customer raised an enquiry and then a complaint about the same issue.",
        steps=["Create both.", "Check whether they are linked or flagged."],
        expected=(
            "They are linked or at least visible together in the customer's history. Confirm "
            "with the business whether these should count as duplicates or as related cases."
        ),
        priority=HIGH, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
]

# --- M13 Customer Information ---------------------------------------------------------
M13.cases += [
    Case(
        area="Reason for lookup",
        title="The agent states why they are looking a customer up",
        pre="You are about to perform a lookup.",
        steps=["Start a lookup.", "Look at what the system asks for before searching."],
        expected=(
            "The purpose is captured - either typed by the agent or taken from the ticket "
            "context - and it appears in the log. This is what makes the log meaningful."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R21",
    ),
    Case(
        area="Policy details",
        title="The policy information returned is the information agents actually need",
        pre="You have the agreed field list for the customer lookup.",
        steps=[
            "Perform a lookup.",
            "Compare the fields shown against the agreed list.",
        ],
        expected=(
            "The needed fields are there and nothing sensitive that was meant to be dropped "
            "is being shown."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R21",
    ),
    Case(
        area="History filters",
        title="A customer's history can be filtered and sorted",
        pre="A customer has many past cases.",
        steps=["Filter their history by type and by date.", "Sort it by date."],
        expected="Each filter and sort works, so an agent can find the relevant past case fast.",
        priority=MEDIUM, role=AGENT,
    ),
    Case(
        area="Multiple policies",
        title="A customer with several policies shows all of them",
        pre="A test customer holds more than one policy.",
        steps=["Look that customer up.", "Read the policies listed."],
        expected=(
            "Every policy is shown with enough detail to tell them apart, so the agent picks "
            "the right one."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R21",
    ),
    Case(
        area="Unmasking",
        title="If a full value can ever be revealed, that action is logged too",
        pre="Ask the team whether a masked value can be revealed by a permitted role.",
        steps=[
            "Confirm whether an unmask or reveal action exists.",
            "If it does, use it and then check the audit log.",
        ],
        expected=(
            "Either no unmask exists at all, or using it is logged with who revealed what "
            "and when. An unlogged reveal defeats the whole masking design."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR, ready=PARTLY,
    ),
    Case(
        area="Stale cache",
        title="Customer details that changed at the source are refreshed",
        kind=EDGE,
        pre="Ask the team how long looked-up details are kept before refreshing.",
        steps=[
            "Look a customer up.",
            "Have their details changed at the source if possible.",
            "Look them up again after the refresh period.",
        ],
        expected=(
            "The updated details eventually appear. Confirm the refresh period with the "
            "team - permanently stale customer contact details would cause real problems."
        ),
        priority=HIGH, role=AGENT, ready=PARTLY,
    ),
    Case(
        area="Repeated lookups",
        title="Rapid repeated lookups are throttled rather than allowed to scrape data",
        kind=NEGATIVE,
        pre="You are on the customer search.",
        steps=["Perform many lookups in quick succession with different values."],
        expected=(
            "After a reasonable number you are asked to slow down. This limits how fast "
            "somebody could harvest customer data, and every attempt is still logged."
        ),
        priority=HIGH, role=AGENT,
    ),
    Case(
        area="Search value in the log",
        title="The full search value never appears in the log or in an error message",
        kind=ACCESS,
        pre="You have performed lookups.",
        steps=[
            "Look at several log entries.",
            "Cause a failed lookup and read the error message on screen.",
        ],
        expected=(
            "Only a masked form appears anywhere - for example the last four digits. A full "
            "Emirates ID or policy number in a log is itself a data exposure."
        ),
        priority=CRITICAL, uat=True, role=COMPLIANCE, req="R21, R22",
    ),
]

# --- M14 Notifications and Templates --------------------------------------------------
M14.cases += [
    Case(
        area="Notification list",
        title="Notifications say clearly what happened and to which ticket",
        pre="You have several notifications of different kinds.",
        steps=["Read each notification in your list."],
        expected=(
            "Each one names the event, the ticket reference and when it happened, in plain "
            "words. No internal codes."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Unread count",
        title="The unread count is accurate and visible from every screen",
        pre="You have unread notifications.",
        steps=["Move between several screens and watch the unread count."],
        expected="It shows the same accurate number everywhere and updates as you read them.",
        priority=MEDIUM, role=AGENT,
    ),
    Case(
        area="Template list",
        title="The reply library covers the scenarios agents actually face",
        pre="You have the agreed scenario list from the business.",
        steps=[
            "Open the template library and browse the full list.",
            "Compare with the agreed scenario list.",
        ],
        expected=(
            "The agreed scenarios are covered in both languages. Report any missing scenario "
            "to the business rather than treating it as a system defect."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Template editing before sending",
        title="An inserted template can be edited before it goes out",
        pre="You have inserted a template into a reply.",
        steps=["Insert a template.", "Edit the wording.", "Send and read what the customer got."],
        expected=(
            "The customer receives your edited version, not the original template. The "
            "template is a starting point, not a locked message."
        ),
        priority=HIGH, uat=True, role=AGENT,
    ),
    Case(
        area="Sent record",
        title="Everything sent to the customer is recorded on the ticket",
        pre="A reply has been sent to a customer.",
        steps=["Open the ticket and read the conversation."],
        expected=(
            "The outgoing message is shown with who sent it and when, so anybody picking the "
            "ticket up knows exactly what the customer has been told."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R29",
    ),
    Case(
        area="Reference number in emails",
        title="Every customer email carries the reference number",
        pre="You can trigger each type of customer email.",
        steps=["Trigger each type and read them all."],
        expected=(
            "Each one includes the correct reference number, so a customer replying keeps "
            "the conversation attached to the right case."
        ),
        priority=CRITICAL, uat=True, role="System (no user action)", req="R33",
    ),
    Case(
        area="Wrong ticket",
        title="A notification always links to the ticket it actually refers to",
        kind=NEGATIVE,
        pre="You have several notifications.",
        steps=["Open five notifications and check each lands on the ticket it named."],
        expected=(
            "Every link opens the correct ticket. A link to the wrong ticket would show "
            "somebody data about a case they were not told about."
        ),
        priority=CRITICAL, role=AGENT,
    ),
    Case(
        area="Reply-to address",
        title="A customer replying to a system email reaches the right mailbox",
        kind=EDGE,
        pre="A customer has received an automatic email.",
        steps=["Reply to the automatic email from the customer mailbox.", "Check the ticket."],
        expected=(
            "The reply reaches a monitored mailbox and joins the right ticket. An automatic "
            "email that cannot be replied to would strand customers."
        ),
        priority=CRITICAL, uat=True, role="System (no user action)", req="R03",
    ),
    Case(
        area="Email appearance",
        title="Customer emails look right in the mail clients customers use",
        kind=EDGE,
        pre="You can read the test mailbox in more than one client.",
        steps=["Open a customer email in a desktop client and on a phone."],
        expected=(
            "The AWNIC branding, the layout and the text all read correctly in both, "
            "including the Arabic version."
        ),
        priority=MEDIUM, role="System (no user action)",
    ),
    Case(
        area="Preferences",
        title="Any notification preferences that exist are respected",
        kind=EDGE,
        pre="Ask the team whether staff can choose which notifications they receive.",
        steps=[
            "Confirm whether preferences exist.",
            "If they do, switch one type off and cause that event.",
        ],
        expected=(
            "The switched-off type is not sent while the others still are. If preferences do "
            "not exist, record that as a gap for the business rather than a defect."
        ),
        priority=LOW, role=AGENT, ready=PARTLY,
    ),
]

# --- M15 Dashboard, Reports and Audit -------------------------------------------------
M15.cases += [
    Case(
        area="Dashboard by role",
        title="Each role's dashboard shows what that job needs",
        pre="You have several role sign-ins.",
        steps=[
            "Sign in as an agent, a supervisor and a manager in turn.",
            "Compare what each dashboard shows.",
        ],
        expected=(
            "The agent sees their own work, the supervisor sees the team's queue and "
            "breaches, the manager sees organisation-wide figures. Compare against what the "
            "business agreed."
        ),
        priority=CRITICAL, uat=True, role="All roles", req="R28",
    ),
    Case(
        area="Report content",
        title="The management report answers the questions the business asked for",
        pre="You have the agreed report requirements.",
        steps=[
            "Run the report.",
            "Check it covers volumes by type, by department and by channel, deadline "
            "performance, escalation counts and average resolution time.",
        ],
        expected=(
            "Every agreed measure is present. Report anything missing to the business as a "
            "gap rather than guessing what should be there."
        ),
        priority=CRITICAL, uat=True, role=MANAGER, req="R28",
    ),
    Case(
        area="Report accuracy",
        title="Report figures can be proved against the ticket list",
        pre="You can filter the ticket list the same way as the report.",
        steps=[
            "Pick one report figure - complaints in a department last month.",
            "Filter the ticket list identically and count.",
            "Compare.",
        ],
        expected=(
            "The two agree exactly. This is the single most important check in the module - "
            "management decisions are made on these numbers."
        ),
        priority=CRITICAL, uat=True, role=MANAGER, req="R28",
    ),
    Case(
        area="Averages",
        title="Average resolution time is calculated the way the business expects",
        pre="You know the resolution times of a few tickets.",
        steps=[
            "Pick a small period with a handful of resolved tickets.",
            "Work out the average by hand.",
            "Compare with the report.",
        ],
        expected=(
            "They match. Confirm with the business whether the average uses working hours or "
            "calendar hours, and whether unresolved tickets are excluded."
        ),
        priority=CRITICAL, uat=True, role=MANAGER, ready=PARTLY,
    ),
    Case(
        area="Audit detail",
        title="An audit entry contains enough to reconstruct what happened",
        pre="You have made a change to a ticket.",
        steps=["Open the audit entry for that change.", "Read every part of it."],
        expected=(
            "It names the person, the exact time, the ticket, what changed, and the old and "
            "new values. An entry saying only 'updated' is not enough for a regulator."
        ),
        priority=CRITICAL, uat=True, role=COMPLIANCE, req="R29",
    ),
    Case(
        area="Audit completeness",
        title="Every kind of action reaches the audit trail",
        pre="You can perform each kind of action on a test ticket.",
        steps=[
            "On one ticket perform: create, edit, reassign, stage change, type change, "
            "escalate, note, customer lookup, resolve, close.",
            "Open the audit trail and check each one appears.",
        ],
        expected=(
            "All ten appear. A gap here is a compliance gap - work through this list "
            "deliberately rather than spot-checking."
        ),
        priority=CRITICAL, uat=True, role=COMPLIANCE, req="R29",
    ),
    Case(
        area="Audit export",
        title="The audit trail can be produced for an external reviewer",
        pre="You are signed in as a compliance officer.",
        steps=[
            "Filter the audit trail to a period.",
            "Export or print it.",
        ],
        expected=(
            "A complete, readable record for that period can be produced. If no export "
            "exists, record it as a gap - regulators ask for this."
        ),
        priority=HIGH, uat=True, role=COMPLIANCE, ready=PARTLY,
    ),
    Case(
        area="Empty dashboard",
        title="A brand new user with no tickets sees a sensible dashboard",
        kind=NEGATIVE,
        pre="A newly created user has no tickets assigned.",
        steps=["Sign in as the new user and open the dashboard."],
        expected=(
            "Zeros and a friendly message, not blank panels or errors. First impressions "
            "matter for adoption."
        ),
        priority=MEDIUM, role=AGENT,
    ),
    Case(
        area="Figures during change",
        title="A report run while tickets are being worked on stays internally consistent",
        kind=EDGE,
        pre="Colleagues are working tickets on the test system.",
        steps=["Run the report while others are actively changing tickets.", "Check the totals."],
        expected=(
            "The parts of the report add up to its own totals. A report whose sections "
            "disagree with each other cannot be trusted."
        ),
        priority=HIGH, role=MANAGER,
    ),
    Case(
        area="Long period",
        title="A report spanning a year-end handles the change of year",
        kind=EDGE,
        pre="The test system has data either side of a year boundary if possible.",
        steps=["Run a report spanning the end of a year."],
        expected=(
            "Tickets from both years are included and grouped correctly. Reference numbers "
            "restart each year, so this is a real risk area."
        ),
        priority=HIGH, role=MANAGER, ready=PARTLY,
    ),
    Case(
        area="Audit performance",
        title="The audit trail stays usable as it grows",
        kind=EDGE,
        pre="The audit trail holds a large number of entries.",
        steps=["Open the audit trail with no filters.", "Then filter to a narrow period."],
        expected=(
            "It loads in a reasonable time and filtering is fast. The audit trail only ever "
            "grows, so it must not become unusable."
        ),
        priority=HIGH, role=COMPLIANCE,
    ),
    Case(
        area="Dashboard scope",
        title="A supervisor's dashboard counts match their own visible tickets",
        kind=ACCESS,
        pre="Tickets exist beyond the supervisor's scope if their role is scoped.",
        steps=[
            "Read the dashboard counts as the scoped role.",
            "Filter the ticket list the same way and count.",
        ],
        expected=(
            "They agree. A dashboard total that includes tickets the person cannot open "
            "leaks how much other work exists."
        ),
        priority=CRITICAL, uat=True, role=SUPERVISOR,
    ),
    Case(
        area="Audit content",
        title="The audit trail does not itself expose data the reader should not see",
        kind=ACCESS,
        pre="A role has limited ticket visibility but some audit access.",
        steps=[
            "Sign in as that role and open whatever audit view they can reach.",
            "Look for entries about tickets they cannot open.",
        ],
        expected=(
            "They see audit entries only for tickets within their scope, or the audit view "
            "is closed to them entirely. Confirm the intended behaviour with the business."
        ),
        priority=CRITICAL, uat=True, role=POC, ready=PARTLY,
    ),
]
