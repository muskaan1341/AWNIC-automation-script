"""Shared structures for the AWNIC module-wise test case pack.

One `Case` per test case. Cases are written per module in the m01_*.py .. m15_*.py
data files and assembled into the workbook by build.py.

Ordering rule (asked for by the business): POSITIVE scenarios come first in every
module sheet, then Negative, then Edge Case, then Access & Permission. Within each
block, Critical first, then High, Medium, Low.
"""

from dataclasses import dataclass, field

# --- scenario types, in the order they must appear in every sheet -------------------
POSITIVE = "Positive"
NEGATIVE = "Negative"
EDGE = "Edge Case"
ACCESS = "Access & Permission"

TYPE_ORDER = [POSITIVE, NEGATIVE, EDGE, ACCESS]
TYPE_CODE = {POSITIVE: "POS", NEGATIVE: "NEG", EDGE: "EDG", ACCESS: "ACC"}

# --- priority -----------------------------------------------------------------------
CRITICAL = "Critical"
HIGH = "High"
MEDIUM = "Medium"
LOW = "Low"
PRIORITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}

# --- readiness ----------------------------------------------------------------------
READY = "Yes"
PARTLY = "Partly - see notes"
NOT_BUILT = "Not yet - feature not built"

COLUMNS = [
    ("Test ID", 14),
    ("Module", 24),
    ("Feature / Area", 24),
    ("Scenario Type", 16),
    ("Priority", 10),
    ("UAT / Business Sign-off", 12),
    ("Who runs it (Role)", 22),
    ("What we are testing", 52),
    ("Before you start", 46),
    ("Steps", 62),
    ("Test Data", 30),
    ("What should happen", 62),
    ("Requirement", 12),
    ("Ready to Test?", 18),
    ("Result (Pass / Fail)", 14),
    ("What actually happened / Comments", 34),
]


@dataclass
class Case:
    """A single test case, in business-readable English."""

    area: str
    title: str
    steps: list[str]
    expected: str
    kind: str = POSITIVE
    priority: str = HIGH
    uat: bool = False
    role: str = "Any signed-in staff member"
    pre: str = "You are signed in."
    data: str = "-"
    req: str = "-"
    ready: str = READY
    notes: str = ""


@dataclass
class Module:
    """One of the 15 high-level modules. Becomes one sheet in the workbook."""

    code: str
    name: str
    plain_summary: str
    cases: list[Case] = field(default_factory=list)
    short: str = ""

    @property
    def sheet_name(self) -> str:
        # Excel caps sheet names at 31 characters, so long names get a short tab label.
        return f"{self.code} {self.short or self.name}"[:31]


def sort_key(case: Case):
    return (TYPE_ORDER.index(case.kind), PRIORITY_ORDER[case.priority])


def numbered_rows(module: Module) -> list[list]:
    """Sort a module's cases into the required order and stamp Test IDs."""
    ordered = sorted(module.cases, key=sort_key)
    counters: dict[str, int] = {}
    rows = []
    for case in ordered:
        code = TYPE_CODE[case.kind]
        counters[code] = counters.get(code, 0) + 1
        test_id = f"{module.code}-{code}-{counters[code]:02d}"
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(case.steps, start=1))
        rows.append(
            [
                test_id,
                f"{module.code} {module.name}",
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
        )
    return rows
