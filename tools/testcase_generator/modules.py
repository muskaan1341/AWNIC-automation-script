"""Assembles all 16 modules in order plus the end-to-end journeys, and the open
questions QA needs answered."""

from m01_m03 import M01, M02, M03
from m04_m06 import M04, M05, M06
from m07_m09 import M07, M08, M09
from m10_m12 import M10, M11, M12
from m13_m15 import M13, M14, M15

# Imported for their side effects - each appends a second wave of cases onto the
# module objects above. Must come after the imports that define them.
import extra_a  # noqa: F401,E402  isort:skip
import extra_b  # noqa: F401,E402  isort:skip
import extra_c  # noqa: F401,E402  isort:skip

from m16 import M16  # noqa: E402  isort:skip
from e2e import E2E  # noqa: E402  isort:skip

ALL_MODULES = [M01, M02, M03, M04, M05, M06, M07, M08, M09, M10, M11, M12, M13, M14, M15,
               M16, E2E]

# (module, question, why it matters, who can answer)
OPEN_QUESTIONS = [
    (
        "M01 Login and Access",
        "How long is a session before it expires, and how long before the silent renewal "
        "kicks in?",
        "Several cases say 'wait for the session to expire'. Without the real numbers a "
        "tester cannot tell a bug from normal behaviour.",
        "Development team",
    ),
    (
        "M02 Users, Roles and Permissions",
        "Is there a signed-off role matrix showing exactly which screens and actions each of "
        "the eight roles gets?",
        "Every Access & Permission case compares what is on screen against 'the agreed "
        "matrix'. Without one, a permission failure cannot be proved either way.",
        "AWNIC business + development team",
    ),
    (
        "M03 Email Intake",
        "What should happen to out-of-office replies, bounce messages and marketing email "
        "that reach the monitored mailboxes?",
        "Decides whether these becoming tickets is a defect or the intended behaviour.",
        "AWNIC Customer Care",
    ),
    (
        "M03 Email Intake",
        "What happens when a customer replies to a ticket that is already closed?",
        "Either the closed ticket reopens or a linked new ticket is created. Both are "
        "defensible, but the tester needs to know which one to expect.",
        "AWNIC Customer Care",
    ),
    (
        "M04 Manual Ticket Creation",
        "Can an agent attach a file when creating a ticket by hand?",
        "There is an attachment area on email tickets. If manual tickets need one too and it "
        "is missing, that is a gap rather than a bug.",
        "AWNIC Customer Care",
    ),
    (
        "M05 Ticket List and Details",
        "Should internal notes be editable or deletable after saving?",
        "The cases currently assume permanent. If notes should be correctable, the expected "
        "results change.",
        "AWNIC business",
    ),
    (
        "M07 Changing a Ticket Type",
        "Can a resolved or closed ticket be discarded?",
        "Affects whether the refusal in M07-NEG-06 is correct behaviour or a blocker.",
        "AWNIC business",
    ),
    (
        "M08 Ticket Stages and Kanban",
        "The stage list has nine names but the requirement is described as an eight-stage "
        "pipeline. Which is correct?",
        "A tester counting stages against the requirement will report a mismatch that may "
        "just be a naming difference. Worth settling before the pass starts.",
        "Development team + AWNIC business",
    ),
    (
        "M09 SLA Timers",
        "What are the exact working hours, weekend days and public holidays the deadline "
        "calculation uses?",
        "Roughly a third of the SLA cases need these numbers to work out the expected "
        "deadline by hand.",
        "AWNIC business",
    ),
    (
        "M09 SLA Timers",
        "If a deadline rule is changed, what happens to tickets that are already open?",
        "An existing ticket silently becoming breached because a rule changed would be a "
        "serious surprise for the business.",
        "AWNIC business",
    ),
    (
        "M09 SLA Timers",
        "Is the overall ceiling two working days or three, and does it differ by ticket type?",
        "The requirement mentions both. The escalation ceiling case cannot pass or fail "
        "without the exact number.",
        "AWNIC business",
    ),
    (
        "M10 Escalation",
        "When an escalated ticket is moved to a different department, does the escalation "
        "level carry over or restart?",
        "Both behaviours are defensible. The tester needs to know which to expect.",
        "AWNIC business",
    ),
    (
        "M10 Escalation",
        "How often does the scheduled deadline check run?",
        "Decides how long a tester should wait before declaring that an escalation failed.",
        "Development team",
    ),
    (
        "M11 Complaints Register",
        "Can a resolved complaint be reopened, and by which roles?",
        "Needed for the reopening case and for the wider complaint lifecycle.",
        "AWNIC business",
    ),
    (
        "M12 Duplicate Detection",
        "Once two tickets are confirmed as duplicates, what happens to the duplicate's "
        "deadline and to the SLA figures?",
        "If both keep counting, the breach numbers in the management report are inflated.",
        "AWNIC business",
    ),
    (
        "M13 Customer Information",
        "Should discarded tickets appear in a customer's history?",
        "Affects whether their absence is correct or a missing-data bug.",
        "AWNIC business",
    ),
    (
        "M15 Dashboard, Reports and Audit",
        "Should a head of department's report cover only their own department or the whole "
        "organisation?",
        "The screens are visible to them either way. Whichever it is, it must be deliberate - "
        "and it is a data-visibility question, not a cosmetic one.",
        "AWNIC business",
    ),
    (
        "M16 Website Form Intake",
        "Does the website form protect itself against a customer double-clicking Submit, or "
        "does that create two tickets?",
        "Double-clicking Submit is what customers actually do. Two tickets per submission "
        "would inflate volumes and annoy the customer with two acknowledgements.",
        "AWNIC business + development team",
    ),
    (
        "M16 Website Form Intake",
        "Does a customer who submits the website form receive an acknowledgement email with "
        "their reference number?",
        "Email intake sends one. If the website route does not, a customer who used the form "
        "has no reference number to quote when they call back.",
        "AWNIC Customer Care",
    ),
    (
        "M16 Website Form Intake",
        "Can QA get the website intake shared secret and a test submission address, or a "
        "WebEngage test environment?",
        "None of the M16 submission cases can be run without one of these. The endpoint is "
        "deliberately not reachable from a browser.",
        "Development team",
    ),
    (
        "All modules",
        "Can QA get one working sign-in per role, plus test tickets that are already "
        "breached, already escalated and already resolved?",
        "Around a quarter of the pack cannot be run without these. Breached and escalated "
        "states take real elapsed time to create naturally.",
        "Development team",
    ),
    (
        "All modules",
        "Is there a test customer set for the customer lookup, so nobody has to use real "
        "policy numbers or Emirates IDs?",
        "Testing with real customer data would put personal data into screenshots and bug "
        "reports.",
        "AWNIC business + development team",
    ),
]
