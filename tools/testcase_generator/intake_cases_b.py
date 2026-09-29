"""Part B - Email intake (the Microsoft Graph notification endpoint and everything it triggers).

Gate chain B1, thread resolution B2, sender routing B3, attachments and classification
B4, endpoint and subscription lifecycle B5, message-content edge cases B6.

Note for the tester: almost every failure in this flow is SILENT. The endpoint answers
Microsoft immediately, before any work starts, so a rejected notification produces no
error anywhere on screen. The evidence is a line in the application log and the absence
of a ticket. Every negative case below needs a log check, not a screen check.
"""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case

DEV = "QA with developer support (log access)"
AGENT = "Customer Care Agent"
POC = "Department Contact Person"

MAILBOX = (
    "The watched AWNIC mailbox is live and its subscription is active. You can send email "
    "to it from an outside address, and you can read the application log."
)

# ---------------------------------------------------------------------------------
# B1 - The gate chain: eight checks that each abort the whole notification
# ---------------------------------------------------------------------------------
B1_AREA = "B1 Notification gate chain"

B1 = [
    ("B1.1", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A notification for a subscription we do not know is dropped",
        pre=MAILBOX,
        steps=[
            "Send a notification to the intake address quoting a subscription id that is not "
            "registered.",
            "Check the log and the ticket list.",
        ],
        expected=(
            "The call is still answered normally - Microsoft must never be left waiting - but "
            "no ticket is created and the log records it as rejected for an unknown "
            "subscription."
        ),
        priority=CRITICAL, role=DEV, req="R03")),
    ("B1.2", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A notification with the wrong shared secret is dropped",
        pre=MAILBOX,
        steps=[
            "Send a notification quoting a real subscription id but the wrong client state.",
            "Repeat with the client state as an empty string.",
            "Repeat with the client state left out entirely.",
        ],
        expected=(
            "All three are rejected and logged. This is the only anti-forgery check this "
            "endpoint has, so a pass here that creates a ticket is a critical finding."
        ),
        priority=CRITICAL, role=DEV, req="R03")),
    ("B1.3", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A notification carrying no message id is dropped",
        pre=MAILBOX,
        steps=[
            "Send a well-formed, correctly signed notification whose resource data has no id.",
            "Repeat with the resource data omitted altogether.",
        ],
        expected="Both rejected and logged. No ticket, no fetch attempt.",
        priority=HIGH, role=DEV, req="R03")),
    ("B1.4", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A subscription pointing at a mailbox record that no longer exists",
        pre="A developer can delete the mailbox record a subscription refers to.",
        steps=[
            "Remove the mailbox record, then send a valid notification for that subscription.",
        ],
        expected="Rejected and logged. No ticket and no unhandled error.",
        priority=MEDIUM, role=DEV, req="R03")),
    ("B1.5", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A mailbox that no team owns",
        pre="A developer can change or clear the team that owns the mailbox address.",
        steps=[
            "Clear the owning team, then send a real email to the mailbox.",
        ],
        expected=(
            "No ticket is created and the log says no team matches the mailbox. The team is "
            "what the new ticket's routing is taken from, so it cannot proceed without one."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B1.5b", Case(
        area=B1_AREA, kind=EDGE,
        title="Two teams configured with the same mailbox address",
        pre="A developer can point two teams at one mailbox address.",
        steps=[
            "Configure two teams with the same address, then send an email to it.",
            "Read the log.",
        ],
        expected=(
            "No ticket. The log should say clearly that the configuration is ambiguous - "
            "check it is not swallowed as a generic unhandled failure, which would be very "
            "hard to diagnose in production."
        ),
        priority=MEDIUM, role=DEV, req="R03", ready=PARTLY,
        notes="Currently falls into the catch-all handler rather than a specific message.")),
    ("B1.6", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="The message cannot be fetched back from Microsoft",
        pre="The team can make the mail-fetch service fail or time out.",
        steps=[
            "With fetching broken, send a real email to the watched mailbox.",
            "Check the log and the ticket list.",
        ],
        expected=(
            "No ticket, an error in the log, and no retry. Confirm with the team whether a "
            "lost email in this window is acceptable - today the notification is simply gone."
        ),
        priority=CRITICAL, role=DEV, req="R03", ready=PARTLY,
        notes="No retry: a fetch failure loses that email permanently.")),
    ("B1.7", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="A fetched message with no unique message id",
        pre="A developer can make the fetch return a message without its internet message id.",
        steps=["Trigger the intake with such a message.", "Check the log."],
        expected=(
            "No ticket. That id is what stops the same email being ingested twice, so intake "
            "must not proceed without it."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B1.8", Case(
        area=B1_AREA, kind=NEGATIVE,
        title="The same email delivered twice makes one ticket",
        pre=MAILBOX,
        steps=[
            "Send an email to the mailbox and wait for its ticket.",
            "Have the same notification delivered a second time.",
            "Search the ticket list for the subject.",
        ],
        expected=(
            "Exactly one ticket, and the log records the second delivery as a duplicate. The "
            "customer must not receive two acknowledgment emails."
        ),
        priority=CRITICAL, uat=True, role=DEV, req="R03")),
    ("B1.9", Case(
        area=B1_AREA,
        title="A genuine new customer email creates a ticket ready for classification",
        pre=MAILBOX,
        steps=[
            "Send a normal customer email from an outside address to the watched mailbox.",
            "Wait, then open the newest ticket.",
        ],
        expected=(
            "A ticket exists showing Pending Classification, an unclassified priority, source "
            "Email, and the subject, sender and body from the email. The AI badge appears "
            "because classification was dispatched."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R03")),
]

# ---------------------------------------------------------------------------------
# B2 - Thread resolution: new ticket, reply, or skip
# ---------------------------------------------------------------------------------
B2_AREA = "B2 Thread resolution"
THREAD_PRE = "A ticket already exists for an email thread you can reply to."

B2 = [
    ("B2.1", Case(
        area=B2_AREA,
        title="A brand new email with no thread history creates a ticket",
        pre=MAILBOX,
        steps=["Send a fresh email - not a reply to anything - and wait."],
        expected="One new ticket, with the thread identifier recorded so later replies can find it.",
        priority=CRITICAL, uat=True, role=AGENT, req="R03")),
    ("B2.2", Case(
        area=B2_AREA,
        title="A reply on a known thread is recorded on the same ticket",
        pre=THREAD_PRE,
        steps=[
            "Reply to the original email from the customer's mailbox.",
            "Open the existing ticket and its Audit tab.",
            "Check the ticket list for a second ticket.",
        ],
        expected=(
            "No second ticket. The reply appears on the existing ticket's history, the "
            "customer message count goes up by one, and no second acknowledgment is sent."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R03")),
    ("B2.3", Case(
        area=B2_AREA, kind=EDGE,
        title="The same reply notification arriving twice is recorded once",
        pre=THREAD_PRE,
        steps=[
            "Send one reply and let it be recorded.",
            "Have the same notification delivered again.",
            "Open the ticket's Audit tab and count the entries.",
        ],
        expected=(
            "One reply entry, one increment of the message count, and one set of attachments - "
            "not two of anything."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B2.4", Case(
        area=B2_AREA, kind=EDGE,
        title="A reply whose thread id does not match still finds its ticket",
        pre="A ticket exists for an email you can reply to from an outside provider (e.g. Gmail).",
        steps=[
            "Reply from a mail provider that assigns its own thread identifier.",
            "Check whether a second ticket was created.",
            "Then send a further reply on the same chain.",
        ],
        expected=(
            "The first reply is matched to the existing ticket using the reply headers instead "
            "of the thread id, and the ticket adopts the new thread id so the second reply "
            "matches immediately. No duplicate ticket, no duplicate acknowledgment."
        ),
        priority=CRITICAL, uat=True, role=DEV, req="R03")),
    ("B2.5", Case(
        area=B2_AREA, kind=EDGE,
        title="An unrelated email that happens to carry an unknown thread id",
        pre=MAILBOX,
        steps=["Send an email carrying a thread id that matches no ticket and no reply headers."],
        expected="Treated as a brand new email - one new ticket.",
        priority=MEDIUM, role=DEV, req="R03")),
    ("B2.6", Case(
        area=B2_AREA, kind=EDGE,
        title="A reply with headers but no thread id",
        pre=THREAD_PRE,
        steps=["Send a reply that carries the reply headers but no thread identifier."],
        expected=(
            "Matched to the existing ticket by the headers, and recorded as a reply. There is "
            "no thread id to adopt, which is fine."
        ),
        priority=MEDIUM, role=DEV, req="R03")),
    ("B2.7", Case(
        area=B2_AREA, kind=EDGE,
        title="Two tickets sharing one thread id",
        pre="A developer can create two tickets carrying the same thread identifier.",
        steps=["Set that up, then send a reply on the thread and see where it lands."],
        expected=(
            "It lands on the most recently created of the two, every time - the choice must be "
            "predictable, not whichever the database returns first."
        ),
        priority=LOW, role=DEV, req="R03")),
    ("B2.8", Case(
        area=B2_AREA, kind=EDGE,
        title="A customer replies to a ticket that is already closed",
        pre="A ticket for an email thread has been resolved or closed.",
        steps=[
            "Reply to that thread from the customer's mailbox.",
            "Open the ticket.",
        ],
        expected=(
            "The reply is recorded on the closed ticket and the ticket does NOT reopen and "
            "does not become a new ticket. Confirm with the business that a customer coming "
            "back on a closed case should not reopen it - this is a deliberate deferral, not "
            "an oversight."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R03", ready=PARTLY,
        notes="Product decision outstanding: reopen on reply, or not.")),
    ("B2.9", Case(
        area=B2_AREA, kind=EDGE,
        title="A customer replies to a thread whose ticket was discarded as junk",
        pre="A ticket for an email thread has been discarded.",
        steps=["Reply to that thread and see where the reply lands."],
        expected=(
            "The reply is recorded on the discarded ticket, where nobody is looking. Raise "
            "whether a reply on junk should resurface the case."
        ),
        priority=MEDIUM, role=AGENT, req="R03", ready=PARTLY,
        notes="Same deferred decision as B2.8.")),
    ("B2.10", Case(
        area=B2_AREA, kind=EDGE,
        title="A long chain where the reply names several earlier messages",
        pre=THREAD_PRE,
        steps=["Build a chain of four or five replies and check each one after the other."],
        expected=(
            "Every message lands on the same single ticket. The count rises by one per "
            "customer message and no new ticket ever appears."
        ),
        priority=HIGH, role=AGENT, req="R03")),
    ("B2.11", Case(
        area=B2_AREA, kind=EDGE,
        title="A reply with malformed threading headers",
        pre=THREAD_PRE,
        steps=["Send a reply whose reply headers are present but malformed."],
        expected=(
            "Nothing usable is extracted, so it is treated as a new email and a new ticket is "
            "created. Confirm that is acceptable rather than an error."
        ),
        priority=LOW, role=DEV, req="R03")),
    ("B2.12", Case(
        area=B2_AREA, kind=EDGE,
        title="A reply's notification arriving before the original's",
        pre="The team can hold and release notifications out of order.",
        steps=[
            "Hold the original email's notification, release the reply's first, then release "
            "the original.",
            "Look at what was created.",
        ],
        expected=(
            "Today this produces two tickets. Record what actually happens and raise it - out "
            "of order delivery is possible in production."
        ),
        priority=MEDIUM, role=DEV, req="R03", ready=PARTLY,
        notes="Edge behaviour worth an explicit decision.")),
    ("B2.13", Case(
        area=B2_AREA, kind=EDGE,
        title="The same email processed by two workers at once",
        pre="The team can deliver one notification twice simultaneously.",
        steps=[
            "Deliver the identical notification twice at the same instant.",
            "Check the ticket list and the log.",
        ],
        expected=(
            "Exactly one ticket. The database refuses the second, and the log shows it failing "
            "cleanly - never a half-created ticket with no classification dispatched."
        ),
        priority=HIGH, role=DEV, req="R03")),
]

# ---------------------------------------------------------------------------------
# B3 - Who sent it: three handlers on a matched thread
# ---------------------------------------------------------------------------------
B3_AREA = "B3 Sender routing on a reply"

B3 = [
    ("B3.1", Case(
        area=B3_AREA,
        title="A reply sent from the watched mailbox counts as the agent answering",
        pre="A ticket exists for a thread, and you can send from the watched mailbox itself.",
        steps=[
            "Reply to the customer from the watched mailbox, in Outlook.",
            "Open the ticket, its Audit tab and its SLA panel.",
        ],
        expected=(
            "Recorded as an agent reply. The response clock stops. The customer message count "
            "does NOT go up - it counts customer messages only."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R37")),
    ("B3.2", Case(
        area=B3_AREA,
        title="A department contact replying from their own mailbox claims the ticket",
        pre="A ticket has a department set, and that department has configured contacts.",
        steps=[
            "Have one of the department's configured contacts reply to the thread from their "
            "own mailbox.",
            "Open the ticket.",
        ],
        expected=(
            "Recorded as a department contact reply, the response clock stops, and if nobody "
            "was assigned yet, that contact becomes the assigned point of contact. Any "
            "attachments on their reply are saved."
        ),
        priority=CRITICAL, uat=True, role=POC, req="R19, R37")),
    ("B3.3", Case(
        area=B3_AREA, kind=EDGE,
        title="A second department contact replying does not take the ticket over",
        pre="A department with two or more configured contacts, one of whom has already replied.",
        steps=[
            "Have a second contact from the same department reply to the thread.",
            "Open the ticket and read who it is assigned to.",
        ],
        expected=(
            "The reply is recorded and the clock stops again, but the assignment stays with "
            "the first contact who replied. First reply wins, not last."
        ),
        priority=HIGH, role=POC, req="R19")),
    ("B3.4", Case(
        area=B3_AREA, kind=EDGE,
        title="A department contact replying before the ticket has been classified",
        pre="A ticket is still Pending Classification, so it has no department yet.",
        steps=[
            "Have a department contact reply to that thread from their own mailbox.",
            "Open the ticket and read the history and the SLA panel.",
        ],
        expected=(
            "Today this is recorded as a CUSTOMER reply, because with no department there is "
            "no contact list to match against. The wrong clock is stopped and the customer "
            "message count goes up. Raise this."
        ),
        priority=HIGH, role=DEV, req="R37", ready=PARTLY,
        notes="Known gap - contact recognition depends on the department being known.")),
    ("B3.5", Case(
        area=B3_AREA, kind=EDGE,
        title="A deactivated department contact replying",
        pre="A department contact has been deactivated.",
        steps=["Have that person reply to a thread for their department's ticket."],
        expected=(
            "Recorded as a customer reply, because only active contacts are matched. Confirm "
            "that is the intent."
        ),
        priority=MEDIUM, role=DEV, req="R19")),
    ("B3.6", Case(
        area=B3_AREA,
        title="An ordinary customer reply",
        pre="A ticket exists for a thread.",
        steps=["Reply from the customer's own address.", "Open the ticket."],
        expected=(
            "Recorded as a customer reply, the customer response time is stamped, the message "
            "count goes up by one, and any attachments are saved and listed in the history."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R03")),
    ("B3.7", Case(
        area=B3_AREA, kind=EDGE,
        title="The mailbox address written in a different case",
        pre="A ticket exists for a thread.",
        steps=[
            "Have a reply arrive whose sender is the mailbox address in different casing.",
        ],
        expected="Still recognised as the agent replying, not as a customer.",
        priority=MEDIUM, role=DEV, req="R37")),
    ("B3.8", Case(
        area=B3_AREA, kind=EDGE,
        title="A sender with a display name but no address",
        pre="A ticket exists for a thread.",
        steps=["Have a reply arrive whose sender field has empty angle brackets."],
        expected=(
            "Handled as an ordinary customer reply. Nothing errors and no ticket is skipped."
        ),
        priority=LOW, role=DEV, req="R03")),
    ("B3.9", Case(
        area=B3_AREA, kind=ACCESS,
        title="A forged sender claiming to be the AWNIC mailbox",
        pre="A ticket exists for a thread.",
        steps=[
            "Send a reply on the thread with the sender header forged to look like the watched "
            "mailbox.",
            "Open the ticket and read the SLA panel.",
        ],
        expected=(
            "Record what happens: today direction is decided by the sender address alone, so a "
            "forged header would be recorded as the agent answering and would stop the SLA "
            "clock. Raise this with the team as a security finding."
        ),
        priority=HIGH, role=DEV, req="R37", ready=PARTLY,
        notes="Security: no sender authentication behind the direction decision.")),
    ("B3.10", Case(
        area=B3_AREA, kind=EDGE,
        title="A department contact whose stored address has stray spaces",
        pre="A developer can save a contact address with leading or trailing spaces.",
        steps=["Save the address with spaces, then have that person reply to the thread."],
        expected="Still recognised - the stored value is tidied before it is compared.",
        priority=LOW, role=DEV, req="R19")),
]

# ---------------------------------------------------------------------------------
# B4 - Attachments and classification dispatch
# ---------------------------------------------------------------------------------
B4_AREA = "B4 Attachments and classification"

B4 = [
    ("B4.1", Case(
        area=B4_AREA,
        title="An email with no attachments",
        pre=MAILBOX,
        steps=["Send a plain email with no attachments and open the resulting ticket."],
        expected="The ticket has an empty attachments panel and nothing was fetched.",
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B4.2", Case(
        area=B4_AREA,
        title="An email with several attachments",
        pre=MAILBOX,
        steps=[
            "Send an email with a PDF, an image and a spreadsheet attached.",
            "Open the ticket's attachments panel and download one.",
        ],
        expected=(
            "All three are listed with their names, types and sizes, and the download works. "
            "Only the reference is held in the database - the files themselves live in "
            "storage."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R03")),
    ("B4.3", Case(
        area=B4_AREA, kind=NEGATIVE,
        title="The ticket still arrives when attachment fetching fails",
        pre="The team can make attachment fetching fail.",
        steps=["With it broken, send an email with an attachment and wait."],
        expected=(
            "The ticket is created and sent for classification as normal. Only the attachment "
            "is missing, and the failure is logged. Losing a file must never lose the case."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B4.4", Case(
        area=B4_AREA, kind=EDGE,
        title="One attachment failing does not lose the others",
        pre="The team can make one file in a batch fail to record.",
        steps=["Send an email with three attachments, one of which will fail."],
        expected="The other two are still saved and listed.",
        priority=MEDIUM, role=DEV, req="R03")),
    ("B4.5", Case(
        area=B4_AREA, kind=EDGE,
        title="An email flagged as having attachments that turn out to be none",
        pre="The team can arrange this.",
        steps=["Trigger the case and open the ticket."],
        expected=(
            "No attachment rows, and on a reply no attachment entry is written to the history - "
            "an empty batch must not produce a '0 attachments received' entry."
        ),
        priority=LOW, role=DEV, req="R03")),
    ("B4.6", Case(
        area=B4_AREA, kind=EDGE,
        title="Two replies carrying a file with the same name",
        pre="A ticket exists for a thread.",
        steps=[
            "Reply with a file called report.pdf.",
            "Reply again with a different file, also called report.pdf.",
            "Open the attachments panel and download both.",
        ],
        expected=(
            "Both are listed and each downloads its own content. The second must not have "
            "overwritten the first in storage."
        ),
        priority=HIGH, role=AGENT, req="R03")),
    ("B4.7", Case(
        area=B4_AREA, kind=EDGE,
        title="One email carrying the same filename twice",
        pre=MAILBOX,
        steps=["Send one email with two different files that share a name."],
        expected="Both are saved under distinguishable names, and neither is lost.",
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B4.8", Case(
        area=B4_AREA,
        title="Files arriving on a reply show up in the ticket history",
        pre="A ticket exists for a thread.",
        steps=[
            "Reply with two attachments.",
            "Open the ticket's Audit tab.",
        ],
        expected=(
            "One entry saying two attachments were received, naming both files - the names "
            "must be visible on the tab, not hidden behind a count."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R29")),
    ("B4.9", Case(
        area=B4_AREA, kind=EDGE,
        title="An agent reply with a signature image is not stored as an attachment",
        pre="The watched mailbox's signature contains an image.",
        steps=[
            "Reply to a thread from the watched mailbox with the standard signature.",
            "Open the ticket's attachments panel.",
        ],
        expected=(
            "Nothing new is listed. Signature images are deliberately not kept, so the panel "
            "stays a list of real customer documents."
        ),
        priority=HIGH, role=AGENT, req="R03")),
    ("B4.10", Case(
        area=B4_AREA,
        title="A successfully dispatched ticket is marked as AI-handled straight away",
        pre=MAILBOX,
        steps=[
            "Send a normal email and open the ticket as soon as it appears, before "
            "classification finishes.",
        ],
        expected=(
            "The AI Generated badge is already there. The flag means the AI pipeline was "
            "started for this ticket, not that its answers have arrived."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B4.11", Case(
        area=B4_AREA, kind=NEGATIVE,
        title="The ticket survives when the classification pipeline refuses the job",
        pre="The team can make the AI platform reject the dispatch.",
        steps=[
            "With dispatch failing, send an email to the mailbox.",
            "Open the ticket.",
        ],
        expected=(
            "The ticket exists, holds the failure and its reason so someone can retry, and "
            "shows NO AI badge - nothing was actually processed."
        ),
        priority=CRITICAL, role=DEV, req="R03")),
    ("B4.12", Case(
        area=B4_AREA, kind=NEGATIVE,
        title="An unexpected error during dispatch behaves the same way",
        pre="The team can make the dispatch call raise an unexpected error.",
        steps=["Trigger it and check the ticket."],
        expected=(
            "Same as the previous case - the ticket is never undone by a dispatch problem."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B4.13", Case(
        area=B4_AREA,
        title="The dispatch carries the message id and the Email source",
        pre="You can inspect what was sent to the AI platform.",
        steps=[
            "Send an email and capture the dispatch payload.",
            "Then let classification complete and open the ticket.",
        ],
        expected=(
            "The payload carries the message id and the literal source Email. Without the "
            "message id no acknowledgment is ever sent to the customer; without the source, "
            "round-robin assignment finds no pool and the ticket is left unassigned."
        ),
        priority=CRITICAL, role=DEV, req="R03, R40")),
    ("B4.14", Case(
        area=B4_AREA,
        title="A reply that says the issue is resolved is flagged, never auto-resolved",
        pre="A ticket exists for a thread.",
        steps=[
            "Reply saying clearly that the issue is now resolved.",
            "Open the ticket, its Audit tab and the assignee's notifications.",
        ],
        expected=(
            "The ticket is flagged for a human to confirm, an entry appears in the history, "
            "and the assignee is notified. The status must still be whatever it was - only a "
            "person may resolve a ticket."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R42")),
    ("B4.15", Case(
        area=B4_AREA, kind=NEGATIVE,
        title="The reply is still recorded when the resolution check is unavailable",
        pre="The resolution-check service is unconfigured or failing.",
        steps=["Send a reply on a thread and open the ticket."],
        expected="The reply is recorded normally. The check failing never loses the reply.",
        priority=HIGH, role=DEV, req="R03")),
    ("B4.16", Case(
        area=B4_AREA, kind=EDGE,
        title="A reply with an empty body",
        pre="A ticket exists for a thread.",
        steps=["Reply with an attachment and no text at all."],
        expected=(
            "The reply is recorded and the attachment saved. The resolution check is skipped, "
            "since there is no text to read."
        ),
        priority=LOW, role=DEV, req="R03")),
]

# ---------------------------------------------------------------------------------
# B5 - The endpoint itself, the subscription lifecycle, and abuse
# ---------------------------------------------------------------------------------
B5_AREA = "B5 Endpoint and subscription lifecycle"

B5 = [
    ("B5.1", Case(
        area=B5_AREA,
        title="The one-time handshake Microsoft performs when a subscription is created",
        pre="You can call the intake address directly.",
        steps=["Call it with a validation token on the query string and no body."],
        expected=(
            "The token is echoed back as plain text with a success response. Anything else and "
            "Microsoft will refuse to create the subscription."
        ),
        priority=CRITICAL, role=DEV, req="R03")),
    ("B5.2", Case(
        area=B5_AREA, kind=EDGE,
        title="A handshake token containing special characters",
        pre="You can call the intake address directly.",
        steps=["Call it with a token containing encoded characters and spaces."],
        expected="The token comes back decoded and identical to what was sent.",
        priority=MEDIUM, role=DEV, req="R03")),
    ("B5.3", Case(
        area=B5_AREA, kind=EDGE,
        title="A handshake call that also carries a body",
        pre="You can call the intake address directly.",
        steps=["Call it with both a validation token and a notification body."],
        expected="The token is echoed and the body is ignored - no ticket is created.",
        priority=LOW, role=DEV, req="R03")),
    ("B5.4", Case(
        area=B5_AREA, kind=NEGATIVE,
        title="A body that is not valid JSON",
        pre="You can call the intake address directly.",
        steps=["Send plain text as the body.", "Send a truncated JSON document."],
        expected="Both refused with a bad-request response and a log line. No background work starts.",
        priority=MEDIUM, role=DEV, req="R03")),
    ("B5.5", Case(
        area=B5_AREA, kind=EDGE,
        title="A notification batch containing nothing",
        pre="You can call the intake address directly.",
        steps=["Send a well-formed body with an empty list of notifications."],
        expected="Accepted, reporting zero accepted. No error.",
        priority=LOW, role=DEV, req="R03")),
    ("B5.6", Case(
        area=B5_AREA, kind=EDGE,
        title="A batch of many notifications, one of them bad",
        pre="You can call the intake address directly.",
        steps=[
            "Send a batch of fifty notifications where one has a wrong client state.",
            "Check the tickets created and the log.",
        ],
        expected=(
            "The forty-nine good ones are processed and the bad one is rejected on its own. "
            "One bad entry must not abandon the batch."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B5.7", Case(
        area=B5_AREA, kind=EDGE,
        title="Unknown extra fields in the notification",
        pre="You can call the intake address directly.",
        steps=["Send a valid notification with several extra unexpected fields."],
        expected=(
            "Processed normally and the extra fields ignored. Only the subscription, the "
            "secret and the message id are ever read - everything else in the notification is "
            "untrusted and the real message is fetched separately."
        ),
        priority=MEDIUM, role=DEV, req="R03")),
    ("B5.8", Case(
        area=B5_AREA, kind=ACCESS,
        title="The intake address accepts anonymous calls by design",
        pre="You can call the intake address from outside.",
        steps=[
            "Call it with no credentials at all and a made-up subscription id.",
            "Read the log.",
        ],
        expected=(
            "The call is accepted at the door and then rejected inside. Microsoft cannot sign "
            "or add headers to its own calls, so the shared secret inside each notification is "
            "the only protection there is. Confirm that is understood and accepted by the team."
        ),
        priority=CRITICAL, role=DEV, req="R03", ready=PARTLY,
        notes="By design, documented. Worth an explicit sign-off.")),
    ("B5.9", Case(
        area=B5_AREA, kind=ACCESS,
        title="Replaying a captured genuine notification",
        pre="You can capture and resend a real notification.",
        steps=["Capture a genuine notification, then send it again an hour later."],
        expected=(
            "No second ticket and no second acknowledgment to the customer. A replay is "
            "stopped by the duplicate checks, not by the secret - which does not expire."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B5.10", Case(
        area=B5_AREA, kind=EDGE,
        title="A flood of notifications",
        pre="You can call the intake address repeatedly.",
        steps=["Send several hundred notifications in quick succession and watch the service."],
        expected=(
            "Each is queued for background processing. Record whether the rate limit refuses "
            "some of them and whether that would cause Microsoft to mark the subscription "
            "unreliable."
        ),
        priority=MEDIUM, role=DEV, req="R03", ready=PARTLY,
        notes="Interaction between the blanket rate limit and Graph's retry behaviour is untested.")),
    ("B5.11", Case(
        area=B5_AREA, kind=ACCESS,
        title="The maintenance endpoints refuse callers without the service token",
        pre="You can call the intake maintenance endpoints directly.",
        steps=[
            "Call renew-subscriptions with no service token.",
            "Repeat for ensure-subscription and subscription-status.",
            "Repeat all three with a wrong token.",
        ],
        expected="All six are refused. These are for the scheduler only, never for a browser.",
        priority=CRITICAL, role=DEV, req="R03")),
    ("B5.12", Case(
        area=B5_AREA, kind=ACCESS,
        title="A server with no service token configured refuses rather than allows",
        pre="A developer can unset the service token.",
        steps=["Unset it and call the maintenance endpoints."],
        expected=(
            "Refused as not configured. A missing secret must never mean 'no check needed'."
        ),
        priority=CRITICAL, role=DEV, req="R03")),
    ("B5.13", Case(
        area=B5_AREA, kind=EDGE,
        title="A renewal run where every subscription fails",
        pre="The team can make renewals fail.",
        steps=["Trigger the renewal endpoint with all renewals failing.", "Read the response."],
        expected=(
            "The response says partial, not success. A scheduler that only checks for success "
            "must not be told everything is fine when nothing renewed."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B5.14", Case(
        area=B5_AREA, kind=EDGE,
        title="A subscription Microsoft has already deleted is recreated",
        pre="A subscription has lapsed beyond renewal.",
        steps=[
            "Trigger renewal and watch the log.",
            "Then send a notification quoting the OLD subscription and secret.",
            "Then send a real email to the mailbox.",
        ],
        expected=(
            "A fresh subscription is created with a new secret. The old subscription and its "
            "old secret are no longer accepted, and real email starts flowing again."
        ),
        priority=CRITICAL, uat=True, role=DEV, req="R03")),
    ("B5.15", Case(
        area=B5_AREA, kind=EDGE,
        title="A subscription record with no stored callback address",
        pre="A developer can clear the stored callback address on a subscription.",
        steps=["Clear it, then trigger a renewal for a lapsed subscription."],
        expected=(
            "Skipped with a clear log line explaining it cannot heal itself without that "
            "address - not a crash and not a silent success."
        ),
        priority=MEDIUM, role=DEV, req="R03")),
    ("B5.16", Case(
        area=B5_AREA, kind=EDGE,
        title="Asking to ensure a subscription when one already exists",
        pre=MAILBOX,
        steps=["Call the ensure endpoint twice in a row and read both responses."],
        expected=(
            "Nothing is created the second time and Microsoft is not called at all. This runs "
            "on every scheduler tick, so it has to be cheap when there is nothing to do."
        ),
        priority=MEDIUM, role=DEV, req="R03")),
]

# ---------------------------------------------------------------------------------
# B6 - Message content edge cases
# ---------------------------------------------------------------------------------
B6_AREA = "B6 Message content"

B6 = [
    ("B6.1", Case(
        area=B6_AREA, kind=EDGE,
        title="The external-sender warning banner is stripped from the ticket text",
        pre=MAILBOX,
        steps=[
            "Send an email from an outside address, so the mail system prepends its external "
            "sender warning.",
            "Open the ticket and read the message body it stored.",
        ],
        expected=(
            "The warning is gone and the customer's own first line is the first line of the "
            "ticket. It must not appear in the body, in the AI summary, or in the reply."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R03")),
    ("B6.2", Case(
        area=B6_AREA, kind=EDGE,
        title="The banner appearing again inside the customer's own text",
        pre=MAILBOX,
        steps=[
            "Send an email where the same warning wording also appears further down, quoted "
            "inside the customer's message.",
        ],
        expected=(
            "Only the one at the very top is removed. The quoted copy lower down is part of "
            "what the customer wrote and must survive."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B6.3", Case(
        area=B6_AREA, kind=EDGE,
        title="An email with no subject line",
        pre=MAILBOX,
        steps=["Send an email with an empty subject and open the ticket."],
        expected=(
            "The ticket is created. The subject shows as empty rather than as the word None, "
            "and the completeness banner flags it as missing."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B6.4", Case(
        area=B6_AREA, kind=EDGE,
        title="An email with an empty body",
        pre=MAILBOX,
        steps=[
            "Send an email with a subject but no body text and no attachment.",
            "Open the ticket once classification has run.",
        ],
        expected=(
            "The ticket is created. Record what classification does with nothing to read - "
            "whether it discards it, leaves it unclassified, or guesses."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B6.5", Case(
        area=B6_AREA, kind=EDGE,
        title="An unreadable received date",
        pre="A developer can make the fetch return a malformed date.",
        steps=["Trigger it and open the ticket."],
        expected=(
            "The ticket is created with no email date shown, and its SLA deadline is still "
            "calculated - the deadline is measured from when we received it, not from the "
            "header."
        ),
        priority=LOW, role=DEV, req="R16")),
    ("B6.6", Case(
        area=B6_AREA, kind=EDGE,
        title="Sender addresses in unusual shapes",
        pre=MAILBOX,
        steps=[
            "Send from an address with no display name.",
            "Send from one whose display name contains a comma and an angle bracket.",
        ],
        expected=(
            "In both, the ticket shows the correct sender address and any reply goes to the "
            "right place."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B6.7", Case(
        area=B6_AREA, kind=EDGE,
        title="Arabic and mixed-language email",
        pre=MAILBOX,
        steps=[
            "Send an email written entirely in Arabic.",
            "Send another mixing Arabic and English.",
            "Open both tickets and read the acknowledgment the customer received.",
        ],
        expected=(
            "The text is stored and displayed intact in the correct reading direction, and the "
            "acknowledgment goes out in the right language."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R03")),
    ("B6.8", Case(
        area=B6_AREA, kind=EDGE,
        title="A rich HTML email with inline images, and a very long one",
        pre=MAILBOX,
        steps=[
            "Send a formatted HTML email with inline images and a signature block.",
            "Send a separate email with a very long body.",
            "Open both tickets.",
        ],
        expected=(
            "The readable text reaches the ticket and the classifier. Record whether inline "
            "images become attachments and whether long text is cut short anywhere."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
    ("B6.9", Case(
        area=B6_AREA, kind=EDGE,
        title="Automatic replies, bounces and newsletters",
        pre=MAILBOX,
        steps=[
            "Send an out-of-office automatic reply to the mailbox.",
            "Cause a delivery-failure notice to arrive.",
            "Send a marketing newsletter from a no-reply address.",
        ],
        expected=(
            "All three create tickets today. Check whether the junk gate catches them, and "
            "agree with the business what should happen - a bounce becoming a customer case "
            "is noise the team has to clear by hand."
        ),
        priority=HIGH, role=AGENT, req="R03", ready=PARTLY,
        notes="Product decision: should auto-generated mail be filtered before a ticket exists?")),
    ("B6.10", Case(
        area=B6_AREA, kind=EDGE,
        title="An agent forwarding an old customer email into the mailbox",
        pre=MAILBOX,
        steps=["Forward a customer's earlier email into the watched mailbox and open the ticket."],
        expected=(
            "A ticket is created, but the sender on it is the forwarding agent, not the "
            "customer. Check whether the acknowledgment would go to the wrong person."
        ),
        priority=HIGH, role=AGENT, req="R03")),
    ("B6.11", Case(
        area=B6_AREA, kind=EDGE,
        title="One customer emailing two watched mailboxes at once",
        pre="Two mailboxes are watched, each owned by a different team.",
        steps=[
            "Send one email addressed to both watched mailboxes.",
            "Check what was created.",
        ],
        expected=(
            "Two tickets, one per team, since each arrives as its own notification with its "
            "own message id. Decide whether duplicate detection should link them."
        ),
        priority=HIGH, role=AGENT, req="R03, R26", ready=PARTLY,
        notes="Cross-mailbox duplicates are not detected today.")),
    ("B6.12", Case(
        area=B6_AREA, kind=EDGE,
        title="A customer replying while classification is still running",
        pre=MAILBOX,
        steps=[
            "Send an email and, within a few seconds, reply to it before the ticket finishes "
            "being classified.",
            "Check the ticket list.",
        ],
        expected=(
            "One ticket, with the reply recorded on it. The reply must not race classification "
            "into creating a second ticket."
        ),
        priority=HIGH, role=DEV, req="R03")),
    ("B6.13", Case(
        area=B6_AREA, kind=EDGE,
        title="An email ticket assigned an initiator still shows as unassigned",
        pre=MAILBOX,
        steps=[
            "Send an email, wait for classification and automatic assignment to finish.",
            "Open the ticket and read the status pill and the assignee.",
            "Compare with a hand-typed ticket that has an initiator.",
        ],
        expected=(
            "Today the email ticket names an initiator but the status still reads New - "
            "Unassigned, while the hand-typed one reads New - Assigned. Record the mismatch - "
            "the automatic assignment does not update the status."
        ),
        priority=HIGH, role=AGENT, req="R40", ready=PARTLY,
        notes="Known gap, confirmed on the shared environment. Sits on the AI platform side.")),
    ("B6.14", Case(
        area=B6_AREA, kind=EDGE,
        title="A long-running thread with many replies",
        pre="A ticket exists for a thread.",
        steps=[
            "Exchange around fifty messages on the thread, some with attachments.",
            "Open the ticket, its Audit tab and its attachments panel.",
        ],
        expected=(
            "The message count is right, every reply is in the history in order, every "
            "attachment is listed, and the page still loads in a reasonable time."
        ),
        priority=MEDIUM, role=AGENT, req="R03")),
]

ALL_B = B1 + B2 + B3 + B4 + B5 + B6
