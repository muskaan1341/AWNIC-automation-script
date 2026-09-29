"""Part A - Manual ticket creation (POST /tickets, the New Ticket form).

Permutation tables A1-A4, access negatives A5, edge cases A6. Every expected result
is taken from the code that enforces it, not from the specification.
"""

from common import ACCESS, CRITICAL, EDGE, HIGH, LOW, MEDIUM, NEGATIVE, PARTLY
from common import Case

AGENT = "Customer Care Agent"
SUPERVISOR = "Customer Care Supervisor"
MANAGER = "Manager"
ANY = "Any signed-in staff member"

SIGNED_IN = "You are signed in as a Customer Care Agent and are on the New Ticket screen."
API = "Use an API client (Postman / curl) with a valid signed-in session."

# ---------------------------------------------------------------------------------
# A1 - Source x customer attached: the required-field gate (full 5 x 2 enumeration)
# ---------------------------------------------------------------------------------
A1_AREA = "A1 Source x Customer attached"

A1 = [
    ("A1.1", Case(
        area=A1_AREA,
        title="Walk-in with a customer attached needs a reason for the visit",
        pre=SIGNED_IN,
        steps=[
            "Search for a customer and pick one from the results.",
            "Set Source to Walk-in. A 'Reason for Walk-in' box appears.",
            "Type a reason, then fill Department and Priority.",
            "Click Create ticket.",
        ],
        expected=(
            "The ticket is created. Open it and check the reason for the walk-in was saved "
            "against the ticket, and the Source reads Walk-in."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R43")),
    ("A1.2", Case(
        area=A1_AREA,
        title="Walk-in with no customer attached needs the reason AND both alternate contacts",
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search - click Create ticket to go straight to the form.",
            "Set Source to Walk-in and type a reason.",
            "Fill Department, Priority, Alternate Email and Alternate Mobile.",
            "Click Create ticket.",
        ],
        expected="The ticket is created and both alternate contact details are stored on it.",
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R36, R43")),
    ("A1.3", Case(
        area=A1_AREA,
        title="Walk-in with the reason left blank cannot be saved",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Attach a customer, set Source to Walk-in and leave the reason box empty.",
            "Fill every other required field.",
            "Try to click Create ticket.",
            "Then send the same request straight to the API, bypassing the form.",
        ],
        expected=(
            "On the form the Create button stays greyed out. The API refuses the request and "
            "says the reason is required when the source is Walk-in."
        ),
        priority=HIGH, role=AGENT, req="R43")),
    ("A1.4", Case(
        area=A1_AREA,
        title="A reason made only of spaces",
        kind=EDGE,
        pre=SIGNED_IN,
        steps=[
            "Set Source to Walk-in and type only spaces into the reason box.",
            "Fill every other required field and try to save.",
            "Send the same value (a single space) directly to the API.",
        ],
        expected=(
            "The form should refuse it. Note what the API does: it currently checks only that "
            "the field is non-empty, so a space may be accepted. Record which side behaves "
            "differently."
        ),
        priority=MEDIUM, role=AGENT, req="R43", ready=PARTLY,
        notes="Known: the server-side check tests presence, not meaningful content.")),
    ("A1.5", Case(
        area=A1_AREA,
        title="Phone ticket with a customer attached needs nothing extra",
        pre=SIGNED_IN,
        steps=[
            "Attach a customer and set Source to Phone.",
            "Fill Department and Priority only.",
            "Click Create ticket.",
        ],
        expected="The ticket is created. No reason-for-walk-in field is shown or required.",
        priority=CRITICAL, uat=True, role=AGENT, req="R07")),
    ("A1.6", Case(
        area=A1_AREA,
        title="Phone ticket with no customer attached needs both alternate contacts",
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search.",
            "Set Source to Phone, fill Department and Priority.",
            "Fill both Alternate Email and Alternate Mobile.",
            "Click Create ticket.",
        ],
        expected="The ticket is created and both contact details are saved.",
        priority=HIGH, uat=True, role=AGENT, req="R07, R36")),
    ("A1.7", Case(
        area=A1_AREA,
        title="No customer, alternate email only - refused",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search.",
            "Fill Source, Department, Priority and Alternate Email. Leave the mobile empty.",
            "Try to save, then repeat the request against the API.",
        ],
        expected=(
            "Create stays disabled on the form. The API refuses and names the missing "
            "alternate mobile number."
        ),
        priority=HIGH, role=AGENT, req="R36")),
    ("A1.8", Case(
        area=A1_AREA,
        title="No customer, alternate mobile only - refused",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search.",
            "Fill Source, Department, Priority and Alternate Mobile. Leave the email empty.",
            "Try to save, then repeat against the API.",
        ],
        expected="Create stays disabled. The API refuses and names the missing alternate email.",
        priority=HIGH, role=AGENT, req="R36")),
    ("A1.9", Case(
        area=A1_AREA,
        title="No customer and no alternate contacts at all - refused",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search.",
            "Fill only Source, Department and Priority.",
            "Try to save, then repeat against the API.",
        ],
        expected=(
            "Create stays disabled. The API refuses and names BOTH missing fields in one "
            "message, not one at a time."
        ),
        priority=HIGH, role=AGENT, req="R36")),
    ("A1.10", Case(
        area=A1_AREA,
        title="Source 'Email' on a hand-typed ticket is allowed and stays 'Email'",
        pre=SIGNED_IN,
        steps=[
            "Attach a customer, set Source to Email.",
            "Fill Department and Priority, then save.",
            "Open the ticket and read the Source Channel field.",
        ],
        expected=(
            "The ticket is created with Source = Email. It must NOT be treated as an "
            "automated email-intake ticket: no AI badge, no email thread, no classification "
            "shell."
        ),
        priority=MEDIUM, role=AGENT, req="R43")),
    ("A1.11", Case(
        area=A1_AREA,
        title="Website Callback with no customer attached",
        pre=SIGNED_IN,
        steps=[
            "Skip the customer search, set Source to Website Callback.",
            "Fill Department, Priority and both alternate contacts.",
            "Save.",
        ],
        expected="The ticket is created with Source = Website Callback.",
        priority=MEDIUM, role=AGENT, req="R43")),
    ("A1.12", Case(
        area=A1_AREA,
        title="Website Complaint with a customer attached",
        pre=SIGNED_IN,
        steps=[
            "Attach a customer, choose the Complaint form, set Source to Website Complaint.",
            "Fill Department, Product Line, Complaint Category and Priority.",
            "Save.",
        ],
        expected="The complaint is created with Source = Website Complaint.",
        priority=MEDIUM, role=AGENT, req="R43")),
    ("A1.13", Case(
        area=A1_AREA,
        title="A walk-in reason sent with a non-walk-in source is refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Build a valid create request with Source = Phone.",
            "Add a reason-for-walk-in value to the same request.",
            "Send it.",
        ],
        expected=(
            "Refused with a clear message that the reason was supplied but the source is not "
            "Walk-in. This is checked twice - at the request layer and again just before the "
            "row is written - so neither can be bypassed."
        ),
        priority=HIGH, role=AGENT, req="R43", data="source=Phone, reason_for_walkin='x'")),
    ("A1.14", Case(
        area=A1_AREA,
        title="Sources that exist in the system but are not valid for hand-typed tickets",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Send a create request with Source = Website.",
            "Repeat with Source = SANADAK.",
            "Repeat with Source = Social Media.",
        ],
        expected=(
            "All three are refused. These are real intake channels, but a person typing a "
            "ticket by hand may only pick Walk-in, Phone, Email, Website Callback or Website "
            "Complaint. The error should say so."
        ),
        priority=HIGH, role=AGENT, req="R43")),
    ("A1.15", Case(
        area=A1_AREA,
        title="Empty or unknown source",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Send a create request with Source omitted entirely.",
            "Repeat with Source = 'Carrier Pigeon'.",
        ],
        expected="Both refused. The source is never guessed or defaulted on a manual ticket.",
        priority=MEDIUM, role=AGENT, req="R43")),
    ("A1.16", Case(
        area=A1_AREA,
        title="An email address alone counts as 'customer attached'",
        kind=EDGE,
        pre=API,
        steps=[
            "Send a create request with no customer name, no policy and no claim number, "
            "but WITH a customer contact email.",
            "Leave both alternate contact fields empty.",
        ],
        expected=(
            "Accepted - any one customer field switches off the alternate-contacts rule. "
            "Confirm with the business that a lone email is enough to reach the customer."
        ),
        priority=MEDIUM, role=AGENT, req="R36", ready=PARTLY,
        notes="Behaviour as coded; worth a business confirmation.")),
]

# ---------------------------------------------------------------------------------
# A2 - Reference type x taxonomy path
# ---------------------------------------------------------------------------------
A2_AREA = "A2 Ticket type x Classification path"

A2 = [
    ("A2.1", Case(
        area=A2_AREA,
        title="A full, valid enquiry classification is accepted",
        pre=SIGNED_IN,
        steps=[
            "Open the New Enquiry form and attach a customer.",
            "Pick Type, then Department, then Enquiry, then Sub-Enquiry - taking each value "
            "from the dropdown the previous choice offered.",
            "Fill Source and Priority and save.",
        ],
        expected=(
            "The ticket is created with all four classification levels stored, and the "
            "completeness banner does not appear."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R23")),
    ("A2.2", Case(
        area=A2_AREA,
        title="A partly classified enquiry (type and department only) is accepted",
        pre=SIGNED_IN,
        steps=[
            "Pick a Type and its Department. Leave Enquiry and Sub-Enquiry unset.",
            "Fill Source and Priority and save.",
        ],
        expected=(
            "The ticket is created. The deeper levels stay empty and the ticket shows the "
            "'not identified' markers for them."
        ),
        priority=HIGH, role=AGENT, req="R23")),
    ("A2.3", Case(
        area=A2_AREA,
        title="One classification level on its own is not combination-checked",
        kind=EDGE,
        pre=API,
        steps=[
            "Send a create request carrying a department and nothing else from the "
            "classification tree.",
        ],
        expected=(
            "Accepted. A single value cannot contradict itself, so the combination check "
            "deliberately does not run below two levels. Membership of one value is the "
            "dropdown's job."
        ),
        priority=MEDIUM, role=AGENT, req="R23")),
    ("A2.4", Case(
        area=A2_AREA,
        title="A type and department that never occur together are refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Pick any Type from the taxonomy and a Department that belongs to a different "
            "Type.",
            "Send the create request.",
        ],
        expected=(
            "Refused with a per-field error saying the combination is not valid. The error "
            "is reported against the deepest level supplied - the one most likely wrong."
        ),
        priority=CRITICAL, role=AGENT, req="R23",
        data="e.g. type=Sales with department=Business Support")),
    ("A2.5", Case(
        area=A2_AREA,
        title="Skipping levels still has to land on one real branch",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Send a Type and a Sub-Enquiry that do not sit on the same branch, leaving the "
            "two levels between them empty.",
        ],
        expected=(
            "Refused. Gaps are allowed, but whatever IS supplied must all appear on a single "
            "real classification row."
        ),
        priority=HIGH, role=AGENT, req="R23")),
    ("A2.6", Case(
        area=A2_AREA,
        title="A value deeper than the taxonomy actually confirms is refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Find a department whose taxonomy rows stop at department level (nothing recorded "
            "below it).",
            "Send that department together with an enquiry value.",
        ],
        expected=(
            "Refused. A blank in the taxonomy means 'not confirmed at this level', never "
            "'any value allowed'."
        ),
        priority=HIGH, role=AGENT, req="R23")),
    ("A2.7", Case(
        area=A2_AREA,
        title="A valid value with a stray space is refused, not silently accepted",
        kind=EDGE,
        pre=API,
        steps=[
            "Take a valid department name and add a trailing space.",
            "Send it with a second valid level.",
        ],
        expected=(
            "Refused. The value is trimmed and then matched exactly, so a stray space fails "
            "the match rather than slipping through as 'not supplied'."
        ),
        priority=MEDIUM, role=AGENT, req="R23")),
    ("A2.8", Case(
        area=A2_AREA,
        title="A department made only of spaces is accepted and leaves the ticket with no SLA",
        kind=EDGE,
        pre=API,
        steps=[
            "Send a create request with the department set to a single space.",
            "Fill everything else validly and send.",
            "Open the created ticket and look at its SLA deadline.",
        ],
        expected=(
            "Currently accepted: the required-field check sees a non-empty string, while the "
            "classification check treats it as absent. The ticket is created with no SLA "
            "deadline and zero SLA days. Raise this - a ticket with no deadline is invisible "
            "to the breach scanners."
        ),
        priority=HIGH, role=AGENT, req="R16, R23", ready=PARTLY,
        notes="Bug watch. Confirmed by reading the validators; needs a fix decision.")),
    ("A2.9", Case(
        area=A2_AREA,
        title="A complaint with no complaint category cannot be saved",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Open the New Complaint form and fill Source, Department, Product Line and "
            "Priority.",
            "Leave Complaint Category empty and try to save.",
            "Repeat the request against the API.",
        ],
        expected=(
            "Create stays disabled on the form; the API refuses and says the category is "
            "required for a complaint."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R23, R42")),
    ("A2.10", Case(
        area=A2_AREA,
        title="A full six-level complaint classification is accepted",
        pre=SIGNED_IN,
        steps=[
            "On the Complaint form pick Department, Product Line, Sub-Product Line, Category, "
            "Type and Sub-Type, each from the dropdown the previous choice offered.",
            "Fill Source and Priority and save.",
        ],
        expected="The complaint is created with all six levels stored.",
        priority=CRITICAL, uat=True, role=AGENT, req="R23, R42")),
    ("A2.11", Case(
        area=A2_AREA,
        title="A sub-product line for a product line that has none is refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Pick a product line for which the form hides the Sub-Product Line field.",
            "Send a create request that supplies a sub-product line anyway.",
        ],
        expected=(
            "Refused. The form hiding the field is a convenience; the server must still say no."
        ),
        priority=HIGH, role=AGENT, req="R23")),
    ("A2.12", Case(
        area=A2_AREA,
        title="A valid category under the wrong department is refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Take a complaint category that exists and pair it with a department it never "
            "appears under.",
            "Send the create request.",
        ],
        expected="Refused with a per-field combination error.",
        priority=HIGH, role=AGENT, req="R23")),
    ("A2.13", Case(
        area=A2_AREA,
        title="A ticket with no department at all is refused, for both types",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Send an enquiry create request with no department.",
            "Send a complaint create request with no department.",
        ],
        expected=(
            "Both refused. The department is what the SLA times are looked up by, so even a "
            "complaint needs one."
        ),
        priority=CRITICAL, role=AGENT, req="R16, R23")),
    ("A2.14", Case(
        area=A2_AREA,
        title="A ticket cannot be created straight into Discarded",
        kind=NEGATIVE,
        pre=API,
        steps=["Send a create request asking for the Discarded ticket type."],
        expected=(
            "Refused. Junk only ever comes from the automated intake gate; a person cannot "
            "hand-create it."
        ),
        priority=HIGH, role=AGENT, req="R07")),
    ("A2.15", Case(
        area=A2_AREA,
        title="Ticket type is case-sensitive",
        kind=NEGATIVE,
        pre=API,
        steps=["Send 'inquiry' in lower case, then 'COMPLAINT' in upper case."],
        expected="Both refused - only the exact values Inquiry and Complaint are accepted.",
        priority=LOW, role=AGENT, req="R07")),
    ("A2.16", Case(
        area=A2_AREA,
        title="The team/inquiry-type field is not checked against anything",
        kind=EDGE,
        pre=API,
        steps=[
            "Send a create request with the inquiry type set to free text that matches no "
            "team or SLA rule.",
            "Open the created ticket and look at its SLA deadline.",
        ],
        expected=(
            "Accepted, and the SLA lookup then finds no rule, so the ticket has no deadline. "
            "Confirm whether this field should be constrained."
        ),
        priority=MEDIUM, role=AGENT, req="R16", ready=PARTLY,
        notes="Unvalidated free text feeding the SLA lookup key.")),
]

# ---------------------------------------------------------------------------------
# A3 - Channel x CC Initiator
# ---------------------------------------------------------------------------------
A3_AREA = "A3 Channel x CC Initiator"

A3 = [
    ("A3.1", Case(
        area=A3_AREA,
        title="No channel picked - the ticket is created unassigned",
        pre=SIGNED_IN,
        steps=[
            "Fill the form without touching the Assignment section.",
            "Save, then open the ticket.",
        ],
        expected=(
            "Status shows as New. Stored as 'New - Unassigned'. No CC Initiator on the "
            "ticket, no assignment notification, and anyone who can see the ticket can act "
            "on it."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R40")),
    ("A3.2", Case(
        area=A3_AREA,
        title="A channel picked but no initiator chosen still creates an unassigned ticket",
        pre=SIGNED_IN,
        steps=[
            "Pick a Channel. The CC Initiator dropdown appears.",
            "Leave the initiator unselected and save.",
        ],
        expected="The ticket is created as 'New - Unassigned'. The channel alone assigns nobody.",
        priority=HIGH, role=AGENT, req="R07, R40")),
    ("A3.3", Case(
        area=A3_AREA,
        title="Picking a channel and an initiator assigns the ticket",
        pre=SIGNED_IN,
        steps=[
            "Pick a Channel, then pick an active member from the CC Initiator dropdown.",
            "Save and open the ticket.",
            "Sign in as that initiator and open their notifications.",
        ],
        expected=(
            "Status shows as New (green), stored as 'New - Assigned'. The initiator's name "
            "and email are on the ticket. The initiator has an in-app notification saying the "
            "ticket was assigned to them. Only they, the department contact, or a supervisor "
            "can now change it."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R40")),
    ("A3.4", Case(
        area=A3_AREA,
        title="'Other' offers the general pool",
        pre=SIGNED_IN,
        steps=[
            "Open the Channel dropdown and check 'Other' is the last option.",
            "Pick 'Other' and open the CC Initiator dropdown.",
            "Pick a member and save.",
        ],
        expected=(
            "The initiator list shows the general pool's active members, not one channel's "
            "subset. The ticket is created as 'New - Assigned'."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R40")),
    ("A3.5", Case(
        area=A3_AREA,
        title="A member deactivated after the page loaded is still accepted",
        kind=EDGE,
        pre="You have the New Ticket form open. An administrator can deactivate a pool member.",
        steps=[
            "Open the form and pick a channel and an initiator, but do not save.",
            "Have an administrator deactivate that pool member.",
            "Now save the ticket.",
        ],
        expected=(
            "The ticket is created and assigned to the now-inactive person. The server does "
            "not re-check the pool. Raise this - the ticket is locked to somebody who is no "
            "longer working cases."
        ),
        priority=HIGH, role=AGENT, req="R40", ready=PARTLY,
        notes="Gap: no server-side validation of the initiator against the pool.")),
    ("A3.6", Case(
        area=A3_AREA,
        title="An initiator who is in no pool at all is accepted",
        kind=EDGE,
        pre=API,
        steps=[
            "Send a create request naming an initiator email that belongs to no round-robin "
            "pool - even an address with no account at all.",
            "Open the created ticket and try to edit it as an ordinary agent.",
        ],
        expected=(
            "Accepted. The ticket is then locked to a person who cannot sign in, so only "
            "supervisors can act on it, and the assignment notification is addressed to "
            "nobody. Raise this."
        ),
        priority=HIGH, role=AGENT, req="R40", ready=PARTLY,
        notes="Gap: same missing pool check as A3.5, reachable directly through the API.")),
    ("A3.7", Case(
        area=A3_AREA,
        title="An initiator name without an email, or an email without a name, is refused",
        kind=NEGATIVE,
        pre=API,
        steps=[
            "Send a create request with an initiator name but no email.",
            "Send another with an initiator email but no name.",
        ],
        expected=(
            "Both refused - an initiator needs a name to display and an email to notify and "
            "route on, so it is both or neither."
        ),
        priority=HIGH, role=AGENT, req="R40")),
    ("A3.8", Case(
        area=A3_AREA,
        title="A pool member with no recorded name still assigns cleanly",
        kind=EDGE,
        pre="A pool contains a member whose display name is blank.",
        steps=[
            "Pick that member as the CC Initiator on the form and save.",
            "Open the ticket and look at the assignment.",
        ],
        expected=(
            "The ticket saves. The form sends the email address in place of the missing name, "
            "so the both-or-neither rule is not tripped. The ticket shows the email as the "
            "assignee name."
        ),
        priority=MEDIUM, role=AGENT, req="R40")),
    ("A3.9", Case(
        area=A3_AREA,
        title="Different email casing must not lock the assignee out of their own ticket",
        kind=EDGE,
        pre=API,
        steps=[
            "Create a ticket assigning an initiator with their email typed in a different "
            "case to their login (e.g. capitalised).",
            "Sign in as that person and try to edit the ticket.",
        ],
        expected="They can edit it. Casing is ignored when the lock is checked.",
        priority=HIGH, role=AGENT, req="R40")),
    ("A3.10", Case(
        area=A3_AREA,
        title="Changing the channel clears the chosen initiator",
        pre=SIGNED_IN,
        steps=[
            "Pick a Channel and then an initiator.",
            "Change the Channel to a different one.",
            "Check the CC Initiator dropdown, then save without picking again.",
        ],
        expected=(
            "The initiator selection is cleared as soon as the channel changes, and the saved "
            "ticket carries no initiator from the previous channel."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R40")),
    ("A3.11", Case(
        area=A3_AREA,
        title="A person in two channels appears once in each, never twice in one",
        kind=EDGE,
        pre=SIGNED_IN,
        steps=[
            "Find a pool member who belongs to more than one channel.",
            "Open each of those channels in turn and read the initiator list.",
        ],
        expected="They appear exactly once in each channel's list, with no duplicate entries.",
        priority=LOW, role=AGENT, req="R40")),
    ("A3.12", Case(
        area=A3_AREA,
        title="Pools that are not initiator channels never appear in the Channel dropdown",
        kind=NEGATIVE,
        pre=SIGNED_IN,
        steps=[
            "Open the Channel dropdown and read every option.",
            "Compare against the full list of configured round-robin pools.",
        ],
        expected=(
            "Only the CC Ticket Initiator channels are listed, plus 'Other' at the bottom. "
            "Pools that exist for other purposes - the complaint-handler pool, for example - "
            "must not be offered as a channel."
        ),
        priority=HIGH, role=AGENT, req="R40")),
]

# ---------------------------------------------------------------------------------
# A4 - Duplicate detection at creation
# ---------------------------------------------------------------------------------
A4_AREA = "A4 Duplicate detection"
DUP_PRE = "You can create tickets and you know an existing open ticket's policy/claim number."

A4 = [
    ("A4.1", Case(
        area=A4_AREA,
        title="A ticket with no policy and no claim number is never duplicate-checked",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket without attaching a customer, so no policy or claim number is "
            "carried.",
            "Open the ticket and look for a duplicate banner.",
        ],
        expected="No duplicate banner and no duplicate record. The check does not run at all.",
        priority=MEDIUM, role=AGENT, req="R26")),
    ("A4.2", Case(
        area=A4_AREA,
        title="A matching policy number on an open ticket is flagged and held",
        pre=DUP_PRE,
        steps=[
            "Note the policy number on an existing OPEN ticket of a given type.",
            "Create a new ticket of the SAME type for a customer with that policy number.",
            "Do not assign a CC Initiator.",
            "Open the new ticket.",
        ],
        expected=(
            "A duplicate banner appears linking to the existing ticket, and the new ticket is "
            "held for a human to resolve the duplicate before it moves on."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R26")),
    ("A4.3", Case(
        area=A4_AREA,
        title="Assigning an initiator flags the duplicate but does not hold the ticket",
        pre=DUP_PRE,
        steps=[
            "Repeat A4.2, but this time pick a Channel and a CC Initiator before saving.",
            "Open the new ticket.",
        ],
        expected=(
            "The duplicate is still flagged and the banner still shows, but the ticket is NOT "
            "held - a person is already in the loop, so their decision is not overridden."
        ),
        priority=HIGH, role=AGENT, req="R26")),
    ("A4.4", Case(
        area=A4_AREA,
        title="A matching claim number is flagged the same way",
        pre=DUP_PRE,
        steps=[
            "Create a ticket for a customer whose claim number matches an existing open "
            "ticket of the same type, with a different policy number.",
        ],
        expected="Flagged, with the reason recorded as a claim-number match.",
        priority=HIGH, role=AGENT, req="R26")),
    ("A4.5", Case(
        area=A4_AREA,
        title="Both numbers matching records both reasons",
        pre=DUP_PRE,
        steps=["Create a ticket whose policy AND claim number both match an open ticket."],
        expected="Flagged once, with both match reasons recorded, not two separate records.",
        priority=MEDIUM, role=AGENT, req="R26")),
    ("A4.6", Case(
        area=A4_AREA,
        title="A closed or resolved ticket is not a duplicate",
        kind=EDGE,
        pre="You know the policy number of a ticket that is already Resolved or Closed.",
        steps=[
            "Create a new ticket of the same type carrying that policy number.",
            "Open it.",
        ],
        expected=(
            "No duplicate banner. Only tickets still being worked on count - a closed case "
            "coming back is a new case."
        ),
        priority=HIGH, role=AGENT, req="R26")),
    ("A4.7", Case(
        area=A4_AREA,
        title="An enquiry and a complaint on the same policy are not duplicates of each other",
        kind=EDGE,
        pre="You know the policy number of an open ENQUIRY.",
        steps=["Create a new COMPLAINT for that same policy number.", "Open it."],
        expected=(
            "No duplicate banner. An enquiry and a complaint are separate cases even on the "
            "same policy."
        ),
        priority=HIGH, role=AGENT, req="R26")),
    ("A4.8", Case(
        area=A4_AREA,
        title="A discarded ticket is not a duplicate",
        kind=EDGE,
        pre="You know the policy number of a ticket that was discarded as junk.",
        steps=["Create a new ticket for that policy number.", "Open it."],
        expected="No duplicate banner.",
        priority=MEDIUM, role=AGENT, req="R26")),
    ("A4.9", Case(
        area=A4_AREA,
        title="Three existing matches produce one duplicate record, not three",
        kind=EDGE,
        pre="Three open tickets of the same type share one policy number.",
        steps=["Create a fourth ticket for that policy number.", "Open it."],
        expected=(
            "One duplicate record against the first match found. Confirm with the business "
            "that showing only one is what they want when several exist."
        ),
        priority=MEDIUM, role=AGENT, req="R26", ready=PARTLY,
        notes="Behaviour as coded - first match only. Needs a business confirmation.")),
    ("A4.10", Case(
        area=A4_AREA,
        title="A policy number with surrounding spaces does not match",
        kind=EDGE,
        pre=API,
        steps=[
            "Create a ticket whose policy number is an existing open ticket's number with a "
            "leading and trailing space.",
        ],
        expected=(
            "No duplicate flagged - the comparison is exact. Decide whether it should trim "
            "before comparing."
        ),
        priority=MEDIUM, role=AGENT, req="R26", ready=PARTLY,
        notes="Duplicate matching does not normalise whitespace.")),
]

# ---------------------------------------------------------------------------------
# A5 - Access, permission and transport (all negative)
# ---------------------------------------------------------------------------------
A5_AREA = "A5 Access and transport"

A5 = [
    ("A5.1", Case(
        area=A5_AREA, kind=ACCESS,
        title="Creating a ticket without signing in is refused",
        pre="You are signed out.",
        steps=["Send a create request with no session.", "Open the New Ticket URL directly."],
        expected="The request is refused as unauthenticated and the page sends you to sign in.",
        priority=CRITICAL, uat=True, role="Nobody - signed out", req="R07")),
    ("A5.2", Case(
        area=A5_AREA, kind=ACCESS,
        title="The three roles that may create tickets can create them",
        pre="You have sign-ins for all three roles.",
        steps=[
            "Sign in as a Customer Care Agent and create a ticket.",
            "Repeat as a Customer Care Supervisor.",
            "Repeat as a Manager.",
        ],
        expected="All three succeed and the New Ticket button is visible for each.",
        priority=CRITICAL, uat=True, role="Agent, Supervisor, Manager", req="R07")),
    ("A5.3", Case(
        area=A5_AREA, kind=ACCESS,
        title="A Head of Department cannot create a ticket",
        pre="You are signed in as a Head of Department.",
        steps=[
            "Look for the New Ticket button on the ticket lists.",
            "Send a create request directly to the API.",
        ],
        expected=(
            "No New Ticket button, and the API refuses with a permission error - not a "
            "'not found' and not a silent success."
        ),
        priority=CRITICAL, uat=True, role="Head of Department", req="R07")),
    ("A5.4", Case(
        area=A5_AREA, kind=ACCESS,
        title="Department contact, complaint handler, compliance officer and administrator cannot create tickets",
        pre="You have a sign-in for each of these four roles.",
        steps=[
            "For each role in turn: sign in, check the New Ticket button is absent, then send "
            "a create request straight to the API.",
        ],
        expected="All four are refused by the API, and none of them sees the button.",
        priority=CRITICAL, uat=True, role="Four roles in turn", req="R07")),
    ("A5.5", Case(
        area=A5_AREA, kind=ACCESS,
        title="A signed-in user with no role at all is refused",
        pre="An account exists that has been given no role.",
        steps=["Sign in as that account and send a create request."],
        expected=(
            "Refused. Permissions fail closed - having no role means having nothing, never "
            "having everything."
        ),
        priority=CRITICAL, role="Account with no role", req="R07")),
    ("A5.6", Case(
        area=A5_AREA, kind=ACCESS,
        title="A create request without the browser-request header is refused",
        pre=API,
        steps=["Send a valid create request but omit the X-Requested-With header."],
        expected=(
            "Refused. This is the cross-site protection - a forged form post from another "
            "site cannot set that header."
        ),
        priority=CRITICAL, role=AGENT, req="-")),
    ("A5.7", Case(
        area=A5_AREA, kind=ACCESS,
        title="More than 120 requests a minute from one user are throttled",
        pre=API,
        steps=["Send 121 requests within one minute from a single signed-in user."],
        expected="The excess requests are refused with a rate-limit response, not a 500.",
        priority=MEDIUM, role=AGENT, req="-")),
    ("A5.8", Case(
        area=A5_AREA, kind=ACCESS,
        title="Two agents behind one office connection are not throttled as one",
        pre="Two different agents on the same office network or VPN.",
        steps=["Have each agent send 60 requests inside the same minute."],
        expected=(
            "All succeed. The limit counts each signed-in person separately, so a shared "
            "office address must not throttle everyone behind it."
        ),
        priority=HIGH, role="Two agents", req="-")),
    ("A5.9", Case(
        area=A5_AREA, kind=ACCESS,
        title="Fields the caller must not set are ignored, not honoured",
        pre=API,
        steps=[
            "Send a create request that also sets a reference number, a status, an SLA "
            "deadline and a department contact person.",
            "Read the created ticket back.",
        ],
        expected=(
            "The ticket is created, and every one of those values is the system's own - the "
            "reference number is freshly minted, the status is New, the deadline is "
            "calculated, and no contact person is assigned."
        ),
        priority=CRITICAL, role=AGENT, req="R33, R34")),
    ("A5.10", Case(
        area=A5_AREA, kind=ACCESS,
        title="A caller cannot mark a manual ticket as AI-generated",
        pre=API,
        steps=[
            "Send a create request that also tries to set the AI-processed flag to true.",
            "Open the created ticket.",
        ],
        expected=(
            "The flag stays false. No AI badge, no enquiry summary and no recommended action "
            "plan appear on a hand-typed ticket."
        ),
        priority=HIGH, role=AGENT, req="-")),
    ("A5.11", Case(
        area=A5_AREA, kind=ACCESS,
        title="Script and SQL fragments in free text are stored safely and displayed harmlessly",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket with a script tag in the Subject, an SQL fragment in the "
            "Description, and both in the Internal Note and Customer Name.",
            "Open the ticket detail page, the ticket list, the audit trail and any export.",
        ],
        expected=(
            "The text is shown exactly as typed, as text. Nothing executes, no dialog appears, "
            "and no query error is produced anywhere."
        ),
        priority=CRITICAL, uat=False, role=AGENT, req="-")),
    ("A5.12", Case(
        area=A5_AREA, kind=ACCESS,
        title="A malformed request body is refused cleanly",
        pre=API,
        steps=[
            "Send a body that is not valid JSON.",
            "Send a JSON array where an object is expected.",
            "Send an enormous payload.",
        ],
        expected="Each is refused with a clear validation response, never a server error.",
        priority=MEDIUM, role=AGENT, req="-")),
]

# ---------------------------------------------------------------------------------
# A6 - Edge cases
# ---------------------------------------------------------------------------------
A6_AREA = "A6 Edge cases"

A6 = [
    ("A6.1", Case(
        area=A6_AREA, kind=EDGE,
        title="Phone number format - the boundary and what slips through it",
        pre=API,
        steps=[
            "Try +123456 (the shortest value the rule allows).",
            "Try 123456 - one character short.",
            "Try +()()() and a plus followed by six spaces.",
            "Try a number containing letters.",
        ],
        expected=(
            "The first is accepted and the short one and the lettered one are refused. The "
            "bracket-only and space-only values are currently ACCEPTED and are not phone "
            "numbers - raise this as a weak rule."
        ),
        priority=MEDIUM, role=AGENT, req="R36", ready=PARTLY,
        notes="The rule allows brackets, spaces and hyphens after the first character.")),
    ("A6.2", Case(
        area=A6_AREA, kind=EDGE,
        title="The form and the server disagree about what a valid email is",
        pre=SIGNED_IN,
        steps=[
            "Type an address the form accepts but a strict parser would not - try a@b..c, "
            "a quoted local part, and a non-Latin domain.",
            "Save and watch what the server says.",
        ],
        expected=(
            "Find any input where the form allows Create but the server then refuses. Each "
            "one is a user typing a value the screen told them was fine and then getting an "
            "error on save."
        ),
        priority=MEDIUM, role=AGENT, req="R36", ready=PARTLY,
        notes="The form uses a loose pattern; the server uses a full email parser.")),
    ("A6.3", Case(
        area=A6_AREA, kind=EDGE,
        title="Reference numbers restart correctly at the turn of the year",
        pre="You can set the system clock or the team can create tickets either side of midnight on 31 December.",
        steps=[
            "Create a ticket just before midnight on 31 December and note its number.",
            "Create another just after midnight on 1 January.",
            "Repeat for an enquiry, a complaint and a discarded ticket.",
        ],
        expected=(
            "The second number carries the new year and restarts at the configured starting "
            "number. Each of the three series counts independently - a complaint restarting "
            "must not affect the enquiry series."
        ),
        priority=HIGH, role=AGENT, req="R33, R34, R41")),
    ("A6.4", Case(
        area=A6_AREA, kind=EDGE,
        title="Numbering past four digits stays in order",
        pre="A series has been configured to start above 9999, or has reached it.",
        steps=[
            "Create tickets around the 9999/10000 boundary.",
            "Sort the ticket list by reference number and read the order.",
        ],
        expected=(
            "The number widens to five digits and the next one issued is genuinely the next, "
            "not a number already used. Ten thousand must rank above nine thousand nine "
            "hundred and ninety-nine."
        ),
        priority=MEDIUM, role=AGENT, req="R33, R41")),
    ("A6.5", Case(
        area=A6_AREA, kind=EDGE,
        title="A clash with a number the AI pipeline claimed at the same moment",
        pre="The team can arrange for the AI pipeline to insert a ticket at a chosen moment.",
        steps=[
            "Have the AI pipeline claim the exact number the manual create is about to use.",
            "Repeat so that it happens three times in a row.",
        ],
        expected=(
            "The first attempts retry and succeed with the next free number. Only after three "
            "failed attempts does the request give up, and then it must say the number could "
            "not be claimed - never a server error."
        ),
        priority=HIGH, role=AGENT, req="R33")),
    ("A6.6", Case(
        area=A6_AREA, kind=EDGE,
        title="Two agents creating a ticket at the same instant",
        pre="Two agents signed in on two machines.",
        steps=["Both click Create ticket for the same ticket type at the same moment."],
        expected="Both tickets are created, with different, consecutive reference numbers.",
        priority=HIGH, role="Two agents", req="R33")),
    ("A6.7", Case(
        area=A6_AREA, kind=EDGE,
        title="A routing with no SLA rule configured",
        pre="You know a department and ticket type combination that has no SLA row.",
        steps=[
            "Create a ticket on that combination.",
            "Open it and read the SLA panel.",
        ],
        expected=(
            "The ticket is created with no deadline and zero SLA days. Confirm the screen "
            "says the SLA is not configured rather than implying it is suspended - the two "
            "mean very different things."
        ),
        priority=HIGH, role=AGENT, req="R16")),
    ("A6.8", Case(
        area=A6_AREA, kind=EDGE,
        title="A reputational-risk ticket gets the shorter deadline, counted in business days",
        pre=SIGNED_IN,
        steps=[
            "Create two otherwise identical tickets, one flagged as a reputational risk.",
            "Compare the deadline and the SLA-days badge on both.",
        ],
        expected=(
            "The flagged ticket has the shorter deadline. The days badge and the actual "
            "deadline agree with each other - days are counted as nine-hour business days, "
            "not 24-hour days, so a 72-hour target is eight working days."
        ),
        priority=HIGH, role=AGENT, req="R16, R25")),
    ("A6.9", Case(
        area=A6_AREA, kind=EDGE,
        title="The ticket is still created when the AI platform is unreachable",
        pre="The team can take the AI platform offline or point it at an unreachable address.",
        steps=[
            "With the platform unreachable, create a ticket normally.",
            "Open it.",
        ],
        expected=(
            "The ticket is created. The customer-risk profile and the suggested next actions "
            "are simply absent - the agent is never blocked from logging a walk-in because a "
            "background service is down."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07")),
    ("A6.10", Case(
        area=A6_AREA, kind=EDGE,
        title="A slow enrichment response must not produce two tickets",
        pre="The team can make the AI platform respond slowly.",
        steps=[
            "With a deliberately slow response, click Create ticket.",
            "While it is still saving, click Create again and press Enter.",
            "Wait for it to finish, then search the ticket list.",
        ],
        expected="Exactly one ticket exists. The button does not accept a second click.",
        priority=HIGH, role=AGENT, req="R07")),
    ("A6.11", Case(
        area=A6_AREA, kind=EDGE,
        title="Notify the customer when there is no address to send to",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket with a customer who has no email on record, no alternate email, "
            "and no email thread behind the ticket.",
            "Tick 'Notify customer via email' before saving.",
        ],
        expected=(
            "The ticket is still created. No email is sent and nothing errors. Check the "
            "ticket's history shows the send was skipped rather than claiming it succeeded."
        ),
        priority=HIGH, role=AGENT, req="R07")),
    ("A6.12", Case(
        area=A6_AREA, kind=EDGE,
        title="Notify the customer when the email service is not configured",
        pre="The notification workflow setting is unset in this environment.",
        steps=["Create a ticket with the notify box ticked."],
        expected="The ticket is created and the outcome is recorded as not configured.",
        priority=MEDIUM, role=AGENT, req="R07")),
    ("A6.13", Case(
        area=A6_AREA, kind=EDGE,
        title="Whose name the acknowledgment email greets the customer with",
        pre="You can read the email the customer receives (test mailbox).",
        steps=[
            "Create a ticket with a CC Initiator assigned and the notify box ticked. Read the "
            "email.",
            "Create a second with no initiator but a department contact already set.",
            "Create a third with neither.",
        ],
        expected=(
            "The first greets with the initiator's name, the second with the contact's name, "
            "and the third falls back to 'our team'. None of them says 'None' or leaves a gap."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R07")),
    ("A6.14", Case(
        area=A6_AREA, kind=EDGE,
        title="An internal note written at creation, and one left blank",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket with an internal note filled in. Open the Audit tab.",
            "Create another leaving the note empty, and another with only spaces.",
        ],
        expected=(
            "The first shows the note as an entry in the ticket history. The other two write "
            "no note entry at all - an empty box must not produce a blank record."
        ),
        priority=MEDIUM, role=AGENT, req="R29")),
    ("A6.15", Case(
        area=A6_AREA, kind=EDGE,
        title="Double-clicking Create makes one ticket, not two",
        pre=SIGNED_IN,
        steps=[
            "Fill the form completely.",
            "Double-click Create ticket as fast as you can.",
            "Search the list for what was created.",
        ],
        expected="Exactly one ticket, with one reference number.",
        priority=HIGH, uat=True, role=AGENT, req="R07")),
    ("A6.16", Case(
        area=A6_AREA, kind=EDGE,
        title="Going back and choosing a different customer",
        pre=SIGNED_IN,
        steps=[
            "Search and pick customer A, then continue to the form.",
            "Use Change Customer to go back and pick customer B instead.",
            "Complete and save the ticket, then open it.",
        ],
        expected=(
            "The ticket carries only customer B's name, policy, claim and contact details. "
            "Nothing from customer A survives."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07, R21")),
    ("A6.17", Case(
        area=A6_AREA, kind=EDGE,
        title="A walk-in reason left behind after changing the source",
        pre=SIGNED_IN,
        steps=[
            "Set Source to Walk-in and type a reason.",
            "Change Source to Phone - the reason box disappears.",
            "Complete the form and save.",
        ],
        expected=(
            "The ticket saves and carries no walk-in reason. It must not be refused for a "
            "field the user can no longer see."
        ),
        priority=HIGH, role=AGENT, req="R43")),
    ("A6.18", Case(
        area=A6_AREA, kind=EDGE,
        title="Customer lookup unavailable",
        pre="The team can make the customer data source unavailable.",
        steps=[
            "Open the New Ticket screen and search for a customer.",
            "Then skip the search and create the ticket anyway.",
        ],
        expected=(
            "The search says the lookup is temporarily unavailable - distinct from 'no "
            "customer found' - and the agent can still continue and create the ticket with "
            "alternate contact details."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R21")),
    ("A6.19", Case(
        area=A6_AREA, kind=EDGE,
        title="A customer whose policy has expired or lapsed",
        pre=SIGNED_IN,
        steps=[
            "Search for a customer whose policy status is not active and pick them.",
            "Complete and save the ticket.",
        ],
        expected=(
            "The policy status is shown but is read-only and never blocks creation - a lapsed "
            "customer can still complain."
        ),
        priority=MEDIUM, role=AGENT, req="R21")),
    ("A6.20", Case(
        area=A6_AREA, kind=EDGE,
        title="The complaint form's dropdowns while the classification list is still loading",
        pre=SIGNED_IN,
        steps=[
            "Open the New Complaint form and immediately open the Department dropdown, before "
            "the page has settled.",
            "Wait a few seconds without closing it.",
            "Pick a value and continue through the rest of the cascade.",
        ],
        expected=(
            "The list fills in while the dropdown is open rather than staying empty, and the "
            "Create button re-evaluates once a value is chosen. Note how long it takes - this "
            "form downloads a very large classification list."
        ),
        priority=HIGH, role=AGENT, req="R23")),
    ("A6.21", Case(
        area=A6_AREA, kind=EDGE,
        title="Arabic, right-to-left text, emoji, quotes and ampersands",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket with Arabic text in the Subject and Description, an emoji and an "
            "ampersand in the customer name, and a quotation mark in the internal note.",
            "Open the ticket, the ticket list, the audit trail and the acknowledgment email.",
        ],
        expected=(
            "Every character is stored and shown exactly as typed, in the right reading "
            "direction, in all four places. Nothing is mangled or escaped into symbols."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R07")),
    ("A6.22", Case(
        area=A6_AREA, kind=EDGE,
        title="Very long free text",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket with a 2,000-character subject and a 50,000-character "
            "description.",
            "Open the ticket, the list view and the ticket card.",
        ],
        expected=(
            "Establish whether any limit exists. If the text is cut short, it must be cut "
            "predictably and the user must be told - silent truncation of a customer's own "
            "words is not acceptable."
        ),
        priority=MEDIUM, role=AGENT, req="R07", ready=PARTLY,
        notes="No length limit is enforced at the request layer; find the real boundary.")),
    ("A6.23", Case(
        area=A6_AREA, kind=EDGE,
        title="Customer type outside the allowed list",
        pre=API,
        steps=[
            "Create a ticket with a customer type that is neither Individual nor Corporate.",
            "Then open that ticket and try to save an edit.",
        ],
        expected=(
            "Creation accepts it but the later edit refuses it. The two sides disagree - "
            "raise it and decide which should change."
        ),
        priority=MEDIUM, role=AGENT, req="R23", ready=PARTLY,
        notes="Inconsistent: create does not validate this field, edit does.")),
    ("A6.24", Case(
        area=A6_AREA, kind=EDGE,
        title="Reclassifying a hand-typed ticket immediately after creating it",
        pre=SIGNED_IN,
        steps=[
            "Create an enquiry by hand and open it straight away.",
            "Open the More Actions menu and look at the reclassify options.",
        ],
        expected=(
            "The swap to Complaint is NOT offered as a clickable option. Because the agent "
            "chose the department on the form, the ticket counts as already routed, so the "
            "menu shows the reason instead. It must never offer a swap that then fails."
        ),
        priority=HIGH, uat=True, role=AGENT, req="R07")),
    ("A6.25", Case(
        area=A6_AREA, kind=EDGE,
        title="A hand-typed ticket never shows AI content",
        pre=SIGNED_IN,
        steps=[
            "Create a ticket by hand and open it.",
            "Look for the AI Generated badge, an Enquiry Summary, and the Recommended Action "
            "Plan tab.",
        ],
        expected=(
            "None of the three appear, even though background enrichment ran. A person typed "
            "this classification, so nothing may be presented as AI-generated."
        ),
        priority=CRITICAL, uat=True, role=AGENT, req="R07")),
]

ALL_A = A1 + A2 + A3 + A4 + A5 + A6
