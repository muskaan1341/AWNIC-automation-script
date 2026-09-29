"""Builds QA/AWNIC-Intake-Test-Matrix.xlsx - permutations, edge cases and negative
scenarios for the two intake paths (manual ticket creation, and email intake).

Same 16-column layout, styling and vocabulary as build.py's module-wise pack, so the two
workbooks can be run side by side. One difference, deliberate: rows here stay in
enumeration order (A1.1, A1.2, ...) rather than being regrouped positive-first, because
each block is a systematic permutation table and its order is part of the information.
Filter or sort on Scenario Type to get the usual grouping.

Run from the repo root:  python3 QA/selenium-py/tools/testcase_generator/build_intake_matrix.py
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from common import COLUMNS, TYPE_CODE, TYPE_ORDER
from intake_cases_a import ALL_A
from intake_cases_b import ALL_B

OUT = Path(__file__).resolve().parents[1] / "AWNIC-Intake-Test-Matrix.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUBHEAD_FONT = Font(bold=True, size=11, color="1F3864")
BAND_FILL = {
    "Positive": PatternFill("solid", fgColor="E2EFDA"),
    "Negative": PatternFill("solid", fgColor="FCE4D6"),
    "Edge Case": PatternFill("solid", fgColor="FFF2CC"),
    "Access & Permission": PatternFill("solid", fgColor="DDEBF7"),
}
PRIORITY_FONT = {
    "Critical": Font(bold=True, color="9C0006", size=10),
    "High": Font(bold=True, color="BF8F00", size=10),
    "Medium": Font(size=10),
    "Low": Font(size=10),
}
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

PART_NAME = {"A": "A Manual ticket creation", "B": "B Email intake"}


def style_header(ws, ncols: int, row: int = 1, *, filterable: bool = True) -> None:
    """Paint one header row. `filterable=False` for a reference sheet that carries more than
    one table - a second freeze/filter would silently replace the first one's."""
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = BORDER
    ws.row_dimensions[row].height = 32
    if filterable:
        ws.freeze_panes = ws.cell(row=row + 1, column=1)
        ws.auto_filter.ref = f"A{row}:{get_column_letter(ncols)}{ws.max_row}"


def to_row(test_id: str, case) -> list:
    part = test_id[0]
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(case.steps, start=1))
    return [
        test_id,
        PART_NAME[part],
        case.area,
        case.kind,
        case.priority,
        "Yes" if case.uat else "No",
        case.role,
        case.title,
        case.pre,
        steps,
        case.data,
        case.expected,
        case.req,
        case.ready,
        "",
        case.notes,
    ]


def write_case_sheet(ws, rows: list[list]) -> None:
    ws.append([c[0] for c in COLUMNS])
    for row in rows:
        ws.append(row)
    for idx, (_, width) in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    for r in range(2, ws.max_row + 1):
        kind = ws.cell(row=r, column=4).value
        for c in range(1, len(COLUMNS) + 1):
            cell = ws.cell(row=r, column=c)
            cell.alignment = WRAP
            cell.border = BORDER
            cell.font = Font(size=10)
        ws.cell(row=r, column=4).fill = BAND_FILL[kind]
        ws.cell(row=r, column=5).font = PRIORITY_FONT[ws.cell(row=r, column=5).value]
        ws.cell(row=r, column=1).font = Font(size=10, bold=True)
    style_header(ws, len(COLUMNS))
    result_col = get_column_letter(15)
    dv = DataValidation(type="list", formula1='"Pass,Fail,Blocked,Not Run"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{result_col}2:{result_col}{ws.max_row}")


# =====================================================================================
READ_ME = [
    ("AWNIC Case Management - Intake Test Matrix", ""),
    ("", ""),
    ("What this pack is",
     "Every combination, boundary and negative case for the two ways a ticket gets into the "
     "system: a Customer Care agent typing one by hand, and an email arriving in a watched "
     "AWNIC mailbox. It sits alongside the module-wise pack rather than replacing it - that "
     "one proves each feature works, this one attacks the two intake paths from every angle."),
    ("Where the expected results came from",
     "Each row's expected result was read off the code that actually enforces the rule, not "
     "off the specification. Where the two disagree, the row says so and the 'Ready to Test?' "
     "column is set to 'Partly' with an explanation in the comments column."),
    ("", ""),
    ("HOW THE SHEETS ARE ORDERED", ""),
    ("Enumeration order, not positive-first",
     "Unlike the module-wise pack, rows here stay in their numbered order (A1.1, A1.2, A1.3 "
     "...). Each block is a systematic table - every value of one thing crossed with every "
     "value of another - and shuffling it would hide the gaps. To get the familiar grouping, "
     "use the filter on the Scenario Type column."),
    ("Test ID", "The block number plus the row within it. A3.5 is the fifth row of block A3, "
     "Channel x CC Initiator. Quote this ID when you raise a bug."),
    ("", ""),
    ("THE BLOCKS", ""),
    ("A1 Source x Customer attached",
     "All five sources crossed with 'a customer was picked' and 'no customer was picked'. "
     "Skipping the customer makes both alternate contact fields compulsory - this block "
     "proves that both on screen and behind it."),
    ("A2 Ticket type x Classification path",
     "Enquiry and Complaint against a full path, a partial one, a single value and an "
     "incoherent combination. The system checks that the values you picked all belong to one "
     "real branch of the classification tree."),
    ("A3 Channel x CC Initiator",
     "The new two-step Assign-to picker. Covers no channel, channel without a person, both "
     "chosen, 'Other', and what happens when the person chosen is no longer active."),
    ("A4 Duplicate detection",
     "Which existing tickets count as a duplicate of a new one, and which deliberately do "
     "not - a closed case, and a complaint against an enquiry on the same policy."),
    ("A5 Access and transport",
     "Who may create a ticket and who may not, plus the checks that stop a request being "
     "forged or a caller setting fields they should not."),
    ("A6 Edge cases",
     "Boundaries and awkward realities - year-end numbering, two agents saving at once, the "
     "AI platform being down, very long text, Arabic, and double-clicking Create."),
    ("B1 Notification gate chain",
     "Eight checks run in order on every incoming notification, and any one of them stops it. "
     "One test per check. IMPORTANT: every one of these failures is silent - Microsoft is "
     "answered immediately, before any work starts, so there is nothing on screen. You need "
     "the application log to test this block."),
    ("B2 Thread resolution",
     "Whether an incoming email is a new case, a reply on one we already have, or the same "
     "notification arriving twice. This is where a duplicate ticket - and a duplicate "
     "acknowledgment to the customer - would come from."),
    ("B3 Sender routing on a reply",
     "Who sent the reply decides which clock stops and whether attachments are kept: the "
     "AWNIC mailbox itself, a department contact person, or the customer."),
    ("B4 Attachments and classification",
     "Files arriving with an email or a reply, and handing the ticket to the AI pipeline - "
     "including what must still happen when that pipeline is unavailable."),
    ("B5 Endpoint and subscription lifecycle",
     "The Microsoft handshake, malformed calls, the maintenance endpoints and their shared "
     "secret, and the mailbox subscription renewing or being recreated after it lapses."),
    ("B6 Message content",
     "Real email as it actually arrives - the external-sender warning banner, no subject, "
     "Arabic, auto-replies, forwards, and a thread with fifty messages on it."),
    ("", ""),
    ("BEFORE YOU START", ""),
    ("What you need for Part A",
     "A sign-in for each of the eight roles, a few test customers with policy and claim "
     "numbers, at least one open ticket whose policy number you know (for the duplicate "
     "block), and an API client such as Postman for the rows that bypass the form on purpose."),
    ("What you need for Part B",
     "A live watched mailbox, an outside email account to send from, read access to the "
     "application log, and a developer on hand - roughly a third of Part B needs someone able "
     "to break a service on purpose or replay a notification."),
    ("Rows marked 'Partly'",
     "These are cases where the system behaves as coded but the behaviour itself needs a "
     "decision. Run them, record what you see, and take the comment in the last column to the "
     "team. Do not raise them as ordinary bugs until that decision is made."),
    ("Do not use real customer data",
     "Use the test customers the team provides. Never paste a real policy number, Emirates ID "
     "or customer email into the system or into a bug report."),
]

BLOCKS = [
    ("A1", "Source x Customer attached", 16, "Full enumeration (5 sources x 2)"),
    ("A2", "Ticket type x Classification path", 16, "Full enumeration"),
    ("A3", "Channel x CC Initiator", 12, "Full enumeration"),
    ("A4", "Duplicate detection", 10, "Full enumeration"),
    ("A5", "Access and transport", 12, "One per role and per transport check"),
    ("A6", "Edge cases", 25, "Boundary and single-factor"),
    ("B1", "Notification gate chain", 10, "One per gate (sequential, not combined)"),
    ("B2", "Thread resolution", 13, "Full enumeration"),
    ("B3", "Sender routing on a reply", 10, "Full enumeration"),
    ("B4", "Attachments and classification", 16, "Full enumeration"),
    ("B5", "Endpoint and subscription lifecycle", 16, "One per behaviour"),
    ("B6", "Message content", 14, "Boundary and single-factor"),
]

A_AXES = [
    ("Reference type", 2, "Inquiry; Complaint"),
    ("Customer attached", 2, "picked from search; skipped"),
    ("Source", 5, "Walk-in; Phone; Email; Website Callback; Website Complaint"),
    ("Channel", 7, "5 initiator channels; Other; none picked"),
    ("CC Initiator", 2, "chosen; none"),
    ("Alternate contacts", 4, "both; email only; phone only; neither"),
    ("Classification path", 4, "full; partial (2+ coherent); single level; incoherent"),
    ("Notify customer", 2, "ticked; unticked"),
    ("Duplicate key", 4, "matches an open same-type ticket; matches a closed one; "
                         "matches the other type; no match"),
    ("Severity", 2, "set; unset"),
    ("Internal note", 2, "written; blank"),
    ("Caller role", 8, "3 roles may create; 5 may not"),
    ("SLA rule configured", 2, "a rule exists for this department and type; none"),
    ("Reputational risk", 2, "yes; no"),
]

B_AXES = [
    ("Request kind", 3, "validation handshake; notification batch; malformed body"),
    ("Subscription", 2, "known; unknown"),
    ("Shared secret", 3, "matches; wrong; missing"),
    ("Message id in notification", 2, "present; absent"),
    ("Mailbox record", 2, "exists; missing"),
    ("Team owning the mailbox", 3, "exactly one; none; two"),
    ("Message fetch", 2, "succeeds; fails"),
    ("Unique message id", 2, "present; absent"),
    ("Already ingested", 2, "yes; no"),
    ("Thread id", 3, "absent; matches a ticket; present but unmatched"),
    ("Reply headers", 2, "match a ticket; no match"),
    ("Redelivery", 2, "already recorded on the ticket; new"),
    ("Sender", 3, "the watched mailbox; a department contact; the customer"),
    ("Ticket department", 2, "set; not yet classified"),
    ("Attachments", 3, "none; saved; fetch fails"),
    ("Classification dispatch", 3, "accepted; refused; unexpected error"),
    ("Resolution check", 3, "not configured; says resolved; says not resolved"),
]


def build_read_me(wb) -> None:
    ws = wb.create_sheet("Read Me")
    for label, text in READ_ME:
        ws.append([label, text])
    ws["A1"].font = TITLE_FONT
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 118
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=2).value in ("", None) and ws.cell(row=r, column=1).value:
            ws.cell(row=r, column=1).font = SUBHEAD_FONT
        else:
            ws.cell(row=r, column=1).font = Font(bold=True, size=10)
        ws.cell(row=r, column=1).alignment = WRAP
        ws.cell(row=r, column=2).alignment = WRAP


def build_summary(wb, rows) -> None:
    ws = wb.create_sheet("Coverage Summary")
    ws.append(["AWNIC intake test matrix - coverage by block"])
    ws["A1"].font = TITLE_FONT
    ws.append([])
    header = ["Block", "What it covers", "How it was reduced", "Positive", "Negative",
              "Edge Case", "Access & Permission", "Total", "Critical", "High",
              "Business sign-off"]
    ws.append(header)
    hdr = ws.max_row
    by_block = {}
    for row in rows:
        block = row[0].split(".")[0]
        by_block.setdefault(block, []).append(row)
    totals = [0] * 8
    for code, name, _declared, reduction in BLOCKS:
        block_rows = by_block.get(code, [])
        counts = {k: sum(1 for r in block_rows if r[3] == k) for k in TYPE_ORDER}
        crit = sum(1 for r in block_rows if r[4] == "Critical")
        high = sum(1 for r in block_rows if r[4] == "High")
        uat = sum(1 for r in block_rows if r[5] == "Yes")
        vals = [counts["Positive"], counts["Negative"], counts["Edge Case"],
                counts["Access & Permission"], len(block_rows), crit, high, uat]
        ws.append([code, name, reduction, *vals])
        totals = [t + v for t, v in zip(totals, vals)]
    ws.append(["", "TOTAL", "", *totals])
    for c in range(1, len(header) + 1):
        ws.cell(row=ws.max_row, column=c).font = Font(bold=True)
    for idx, w in enumerate([8, 38, 40, 10, 10, 11, 20, 8, 10, 8, 17], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for r in range(hdr, ws.max_row + 1):
        for c in range(1, len(header) + 1):
            ws.cell(row=r, column=c).alignment = WRAP
            ws.cell(row=r, column=c).border = BORDER
    style_header(ws, len(header), row=hdr)


def _axis_table(ws, title, axes, note_lines):
    ws.append([title])
    ws.cell(row=ws.max_row, column=1).font = SUBHEAD_FONT
    ws.append(["Variable", "Values", "What the values are"])
    hdr = ws.max_row
    for name, count, values in axes:
        ws.append([name, count, values])
    product = 1
    for _, count, _ in axes:
        product *= count
    ws.append(["Full cartesian product", product, "every combination of every variable"])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True, size=10)
    ws.cell(row=ws.max_row, column=2).font = Font(bold=True, size=10)
    for line in note_lines:
        ws.append(["", "", line])
    ws.append([])
    for r in range(hdr, ws.max_row + 1):
        for c in range(1, 4):
            ws.cell(row=r, column=c).alignment = WRAP
            ws.cell(row=r, column=c).border = BORDER
    style_header(ws, 3, row=hdr, filterable=False)
    return product


def build_axes(wb) -> None:
    ws = wb.create_sheet("Axes and Combinations")
    ws.append(["Why these blocks, and why this many cases"])
    ws["A1"].font = TITLE_FONT
    ws.append([])
    ws.append(["", "", "Each intake path has a set of independent variables. Multiplying "
                       "them out shows why exhaustive testing is not an option, and what "
                       "reduction is being used instead."])
    ws.cell(row=ws.max_row, column=3).alignment = WRAP
    ws.append([])

    _axis_table(
        ws, "PART A - Manual ticket creation", A_AXES,
        ["Reduction used: all-pairs (pairwise). Every two-variable interaction is covered "
         "in roughly 55-70 cases instead of 4.5 million.",
         "Three interactions are enumerated in FULL instead of sampled, because a gap in "
         "them would be a released bug: A1 Source x Customer, A2 Type x Classification, "
         "A3 Channel x Initiator.",
         "Channel and initiator are not fully independent (no initiator without a channel), "
         "and neither are customer-attached and the alternate-contact rule - so the truly "
         "reachable space is smaller than the raw product, though not by an order of "
         "magnitude."],
    )
    _axis_table(
        ws, "PART B - Email intake", B_AXES,
        ["This path is NOT a flat product. The first eight variables are sequential gates: "
         "each one stops the notification outright, so they form a chain - one test per "
         "gate, not a combination.",
         "Downstream of the last gate it is a genuine product: thread id (3) x reply headers "
         "(2) x redelivery (2) x sender (3) x department set (2) x attachments (3) x "
         "dispatch (3) x resolution check (3) = 1,944 combinations, reduced by all-pairs to "
         "roughly 15-20 cases.",
         "Testing note: almost every failure in Part B is SILENT. Microsoft is answered "
         "before any work begins, so a rejected notification produces no error anywhere. "
         "Every negative case in Part B is checked in the log, not on screen."],
    )
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 96


OPEN_QUESTIONS = [
    ("A2 / A6 Manual creation",
     "Should a department made only of spaces be accepted?",
     "It passes the required-field check and then reads as absent, so the ticket is created "
     "with no SLA deadline and is invisible to the breach scanners.",
     "Development team"),
    ("A3 Channel x CC Initiator",
     "Should the server check the chosen CC Initiator is really an active member of that "
     "channel's pool?",
     "It does not today. A stale screen can assign a deactivated person, and a direct API "
     "call can assign an address with no account at all - which then locks the ticket so "
     "only supervisors can touch it.",
     "Development team + AWNIC business"),
    ("A4 Duplicate detection",
     "When several open tickets share a policy number, should the agent see all of them or "
     "just one?",
     "Only the first match is recorded and shown.",
     "AWNIC business"),
    ("A6 Manual creation",
     "Is there a maximum length for the subject and description, and what should the user see "
     "when they exceed it?",
     "No limit is enforced at the request layer, so the real boundary is wherever the database "
     "or the screen gives way - which is not a behaviour anyone has chosen.",
     "Development team"),
    ("A6 Manual creation",
     "Should the customer type be restricted to Individual and Corporate on creation?",
     "Creating a ticket accepts any value; editing the same ticket later refuses anything else. "
     "The two sides disagree.",
     "Development team"),
    ("B1 Email intake",
     "What should happen to an email whose fetch from Microsoft fails?",
     "Today the notification is dropped with a log line and no retry, so that customer's email "
     "is lost with nobody aware of it.",
     "Development team + AWNIC business"),
    ("B2 Email intake",
     "Should a customer replying to a closed - or discarded - ticket reopen it?",
     "The reply is recorded on the closed ticket and nothing else happens, so a customer coming "
     "back gets no response. This was deferred deliberately, not missed.",
     "AWNIC business"),
    ("B3 Email intake",
     "Should a department contact's reply be recognised before the ticket has been classified?",
     "With no department yet there is no contact list to match against, so their reply is "
     "recorded as a customer reply and stops the wrong clock.",
     "Development team"),
    ("B3 Email intake",
     "Is it acceptable that the direction of a reply is decided by the sender address alone?",
     "A forged sender claiming to be the AWNIC mailbox would be recorded as the agent answering "
     "and would stop the SLA clock.",
     "Development team + security"),
    ("B5 Email intake",
     "Is the anonymous notification endpoint accepted as a known, signed-off risk?",
     "Microsoft cannot sign or add headers to its own calls, so the shared secret inside each "
     "notification is the only protection the endpoint has.",
     "Development team + AWNIC business"),
    ("B6 Email intake",
     "Should automatic replies, bounce notices and newsletters create tickets?",
     "All three do today. Every one of them becomes a case the Customer Care team has to clear "
     "by hand.",
     "AWNIC business"),
    ("B6 Email intake",
     "Should an email sent to two watched mailboxes be recognised as one case?",
     "It creates two tickets on two teams, and duplicate detection does not link them.",
     "AWNIC business"),
    ("B6 Email intake",
     "Why does an email ticket that has been assigned an initiator still read 'New - "
     "Unassigned'?",
     "The rule that an initiator means 'New - Assigned' lives only in the manual-creation path. "
     "The automatic round-robin assignment on email does not update the status, so the pill "
     "contradicts the assignment on the highest-volume channel.",
     "Development team (AI platform side)"),
]


def build_questions(wb) -> None:
    ws = wb.create_sheet("Open Questions")
    ws.append(["Decisions needed before these rows can be signed off"])
    ws["A1"].font = TITLE_FONT
    ws.append([])
    ws.append(["#", "Block", "The question", "Why it matters", "Who can answer"])
    hdr = ws.max_row
    for i, q in enumerate(OPEN_QUESTIONS, start=1):
        ws.append([i, *q])
    for idx, w in enumerate([5, 26, 62, 62, 24], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for r in range(hdr, ws.max_row + 1):
        for c in range(1, 6):
            ws.cell(row=r, column=c).alignment = WRAP
            ws.cell(row=r, column=c).border = BORDER
    style_header(ws, 5, row=hdr)


def main() -> None:
    a_rows = [to_row(tid, case) for tid, case in ALL_A]
    b_rows = [to_row(tid, case) for tid, case in ALL_B]
    all_rows = a_rows + b_rows

    wb = Workbook()
    wb.remove(wb.active)
    build_read_me(wb)
    build_summary(wb, all_rows)
    build_axes(wb)
    write_case_sheet(wb.create_sheet("All Cases"), all_rows)
    write_case_sheet(wb.create_sheet("A Manual Create"), a_rows)
    write_case_sheet(wb.create_sheet("B Email Intake"), b_rows)
    build_questions(wb)
    wb.save(OUT)

    print(f"Wrote {OUT}")
    print(f"  test cases: {len(all_rows)}  (A {len(a_rows)}, B {len(b_rows)})")
    for kind in TYPE_ORDER:
        print(f"    {kind:22} {sum(1 for r in all_rows if r[3] == kind)}")
    print(f"  business sign-off: {sum(1 for r in all_rows if r[5] == 'Yes')}")
    print(f"  needs a decision (Partly): {sum(1 for r in all_rows if r[13] != 'Yes')}")
    assert len({r[0] for r in all_rows}) == len(all_rows), "duplicate Test ID"
    _ = TYPE_CODE  # imported for parity with build.py's vocabulary


if __name__ == "__main__":
    main()
