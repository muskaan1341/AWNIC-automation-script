"""Builds QA/AWNIC-Module-Wise-Test-Cases.xlsx from the per-module case files.

Run from the repo root:  python3 QA/selenium-py/tools/testcase_generator/build.py
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from common import COLUMNS, TYPE_ORDER, numbered_rows
from modules import ALL_MODULES, OPEN_QUESTIONS

OUT = Path(__file__).resolve().parents[1] / "AWNIC-Module-Wise-Test-Cases.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
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


def style_header(ws, ncols: int, row: int = 1) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = BORDER
    ws.row_dimensions[row].height = 32
    ws.freeze_panes = ws.cell(row=row + 1, column=1)
    ws.auto_filter.ref = f"A{row}:{get_column_letter(ncols)}{ws.max_row}"


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
        ws.row_dimensions[r].height = None
    style_header(ws, len(COLUMNS))
    result_col = get_column_letter(15)
    dv = DataValidation(type="list", formula1='"Pass,Fail,Blocked,Not Run"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{result_col}2:{result_col}{ws.max_row}")


def build_read_me(wb) -> None:
    ws = wb.create_sheet("Read Me")
    lines = [
        ("AWNIC Case Management - Module-wise Test Cases", ""),
        ("", ""),
        ("What this pack is", "Every test case for the platform, split into the 15 modules the "
         "system is made of. One sheet per module. Written in plain English so a business "
         "user can run a case without knowing how the system is built."),
        ("Who it is for", "AWNIC business users doing UAT sign-off, and the QA team running "
         "functional and regression passes. Both use the same sheets."),
        ("", ""),
        ("HOW EACH SHEET IS ORDERED", ""),
        ("1. Positive first", "The normal, everyday way the feature is meant to work. Run these "
         "first - if a positive case fails, the negative ones below it are not worth running yet."),
        ("2. Negative", "Wrong input, missing input, and things the user is not allowed to do. "
         "The system must refuse politely and explain why."),
        ("3. Edge Case", "Unusual but real situations - very long text, zero results, two people "
         "acting at the same time, a deadline landing on a weekend, the last day of the year."),
        ("4. Access & Permission", "The same screen seen by a different job role. This is where "
         "data leaks show up, so treat every failure here as serious."),
        ("", ""),
        ("COLUMNS EXPLAINED", ""),
        ("Test ID", "Module code + scenario type + number. M04-NEG-03 is the third negative case "
         "in module 4. Quote this ID when you raise a bug."),
        ("Scenario Type", "Positive / Negative / Edge Case / Access & Permission - see above."),
        ("Priority", "Critical = stop-the-release. High = must be fixed before go-live. "
         "Medium = fix soon. Low = cosmetic or rare."),
        ("UAT / Business Sign-off", "Yes = this case is part of the business acceptance pack. "
         "Filter this column to 'Yes' to get the shortest run that proves the system does its job."),
        ("Who runs it (Role)", "Sign in as somebody with this job. This matters - the system "
         "deliberately shows different screens to different roles."),
        ("Before you start", "What must already be true. If it is not, set it up first or the "
         "result is meaningless."),
        ("Ready to Test?", "Yes = built, run it. Partly = some of it works, read the comments "
         "column. Not yet = the feature does not exist, do NOT run it and do NOT log a bug."),
        ("Result / Comments", "Write Pass or Fail, then say what you actually saw."),
        ("", ""),
        ("SUGGESTED RUN ORDER", ""),
        ("Pass 1 - Business journeys", "Run the E2E Business Journeys sheet FIRST. Each one "
         "follows a complete case from the customer's first contact to closure, crossing "
         "several modules. They prove the system does the job. If a journey fails, the "
         "module sheets tell you which step broke."),
        ("Pass 2 - Business sign-off", "Filter UAT column = Yes across all sheets. This is the "
         "AWNIC acceptance run."),
        ("Pass 3 - Critical + High", "Everything marked Critical or High, module by module."),
        ("Pass 4 - Everything else", "Medium and Low, plus all remaining edge cases."),
        ("", ""),
        ("BEFORE YOU START ANY MODULE", ""),
        ("Test accounts", "You need one sign-in per role: admin, head of department, manager, "
         "customer care supervisor, customer care initiator, complaint handler, department "
         "contact person, compliance officer. Ask the team for these before day one."),
        ("Test data", "Ask for a small set of test tickets that are already past their deadline, "
         "already escalated, and already resolved. Several cases need these and they take days "
         "to create naturally."),
        ("Do not use real customer data", "Use the test customers the team provides. Do not paste "
         "real policy numbers or Emirates IDs into the system or into a bug report."),
    ]
    for label, text in lines:
        ws.append([label, text])
    ws["A1"].font = TITLE_FONT
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 118
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=2).value in ("", None) and ws.cell(row=r, column=1).value:
            ws.cell(row=r, column=1).font = Font(bold=True, color="1F3864", size=11)
        else:
            ws.cell(row=r, column=1).font = Font(bold=True, size=10)
        ws.cell(row=r, column=1).alignment = WRAP
        ws.cell(row=r, column=2).alignment = WRAP


def build_summary(wb, modules) -> None:
    ws = wb.create_sheet("Module Summary")
    ws.append(["AWNIC Case Management - coverage by module"])
    ws["A1"].font = TITLE_FONT
    ws.append([])
    header = ["#", "Module", "What this module does (plain English)", "Positive",
              "Negative", "Edge Case", "Access & Permission", "Total",
              "Critical", "High", "UAT cases"]
    ws.append(header)
    hdr_row = ws.max_row
    totals = [0] * 8
    for mod in modules:
        counts = {k: sum(1 for c in mod.cases if c.kind == k) for k in TYPE_ORDER}
        crit = sum(1 for c in mod.cases if c.priority == "Critical")
        high = sum(1 for c in mod.cases if c.priority == "High")
        uat = sum(1 for c in mod.cases if c.uat)
        ws.append([mod.code, mod.name, mod.plain_summary, counts["Positive"],
                   counts["Negative"], counts["Edge Case"], counts["Access & Permission"],
                   len(mod.cases), crit, high, uat])
        vals = [counts["Positive"], counts["Negative"], counts["Edge Case"],
                counts["Access & Permission"], len(mod.cases), crit, high, uat]
        totals = [t + v for t, v in zip(totals, vals)]
    ws.append(["", "TOTAL", "", *totals])
    for c in range(1, len(header) + 1):
        ws.cell(row=ws.max_row, column=c).font = Font(bold=True)
    widths = [6, 30, 74, 10, 10, 11, 20, 8, 10, 8, 11]
    for idx, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for r in range(hdr_row, ws.max_row + 1):
        for c in range(1, len(header) + 1):
            ws.cell(row=r, column=c).alignment = WRAP
            ws.cell(row=r, column=c).border = BORDER
    style_header(ws, len(header), row=hdr_row)


def build_questions(wb) -> None:
    ws = wb.create_sheet("Open Questions")
    ws.append(["Things QA needs answered before these cases can be signed off"])
    ws["A1"].font = TITLE_FONT
    ws.append([])
    ws.append(["#", "Module", "The question", "Why it matters", "Who can answer"])
    hdr = ws.max_row
    for i, q in enumerate(OPEN_QUESTIONS, start=1):
        ws.append([i, *q])
    for idx, w in enumerate([5, 26, 62, 62, 22], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for r in range(hdr, ws.max_row + 1):
        for c in range(1, 6):
            ws.cell(row=r, column=c).alignment = WRAP
            ws.cell(row=r, column=c).border = BORDER
    style_header(ws, 5, row=hdr)


def main() -> None:
    wb = Workbook()
    wb.remove(wb.active)
    build_read_me(wb)
    build_summary(wb, ALL_MODULES)

    master = wb.create_sheet("All Test Cases")
    all_rows: list[list] = []
    for mod in ALL_MODULES:
        rows = numbered_rows(mod)
        all_rows.extend(rows)
        write_case_sheet(wb.create_sheet(mod.sheet_name), rows)
    write_case_sheet(master, all_rows)
    # keep the master sheet third, right after Read Me and Module Summary
    wb._sheets.remove(master)
    wb._sheets.insert(2, master)

    build_questions(wb)
    wb.save(OUT)

    print(f"Wrote {OUT}")
    print(f"  modules: {len(ALL_MODULES)}")
    print(f"  test cases: {len(all_rows)}")
    for kind in TYPE_ORDER:
        n = sum(1 for m in ALL_MODULES for c in m.cases if c.kind == kind)
        print(f"    {kind:22} {n}")
    print(f"  UAT / business sign-off: "
          f"{sum(1 for m in ALL_MODULES for c in m.cases if c.uat)}")


if __name__ == "__main__":
    main()
