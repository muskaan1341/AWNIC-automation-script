"""Read-only: after the out-of-taxonomy emails are sent to testaiagent@awnic.com,
show what the live pipeline actually did with them.

Run from apps/api so it picks up .env:
    cd apps/api && .venv/bin/python ../QA/selenium-py/tools/check_intake_results.py [minutes]

Reads only. Never writes. `minutes` (default 60) is the lookback window.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

SUBJECT_HINTS = (
    "cancelled trip",
    "multiple covers",
    "Injury claim",
    "Professional Indemnity",
    "Extension of CAR",
    "No claims certificate",
)

TICKETS_SQL = """
SELECT id, created_at, email_subject, email_from, status, priority,
       reference_type, department, enquiry, sub_enquiry,
       classification_dispatch_status, classification_dispatch_error,
       ai_processed, reference_number, sla_deadline, assigned_poc_email
FROM tickets
WHERE source_message_id IS NOT NULL
  AND created_at > now() - make_interval(mins => :mins)
ORDER BY created_at
"""

# Every (type, department, enquiry, sub_enquiry) the classifier is allowed to write.
TAXONOMY_SQL = """
SELECT type, department, enquiry, sub_enquiry FROM inquiry_classification_taxonomy
"""


def _fmt(value) -> str:
    return "-" if value is None else str(value)


async def main() -> None:
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    load_dotenv()
    url = os.environ["DATABASE_URL"]

    engine = create_async_engine(url, echo=False)
    async with engine.connect() as conn:
        rows = (await conn.execute(text(TICKETS_SQL), {"mins": minutes})).mappings().all()
        taxonomy = {
            (r["type"], r["department"], r["enquiry"], r["sub_enquiry"])
            for r in (await conn.execute(text(TAXONOMY_SQL))).mappings().all()
        }
    await engine.dispose()

    print(f"\n{len(rows)} email-intake ticket(s) in the last {minutes} min\n")
    if not rows:
        print("  Nothing yet. Graph webhook delivery is usually seconds; "
              "classification write-back takes ~1-2 min.\n")
        return

    for r in rows:
        mine = any(h.lower() in (r["email_subject"] or "").lower() for h in SUBJECT_HINTS)
        print(f"{'>>' if mine else '  '} {r['email_subject']}")
        print(f"     id            {r['id']}")
        print(f"     from          {_fmt(r['email_from'])}")
        print(f"     created       {r['created_at']}")
        print(f"     status        {_fmt(r['status'])}   priority: {_fmt(r['priority'])}")
        print(f"     dispatch      {_fmt(r['classification_dispatch_status'])}"
              f"{'  error: ' + r['classification_dispatch_error'] if r['classification_dispatch_error'] else ''}")
        print(f"     ai_processed  {r['ai_processed']}   reference_number: {_fmt(r['reference_number'])}")
        print(f"     classified    type={_fmt(r['reference_type'])} | dept={_fmt(r['department'])} "
              f"| enquiry={_fmt(r['enquiry'])} | sub={_fmt(r['sub_enquiry'])}")
        print(f"     assigned_poc  {_fmt(r['assigned_poc_email'])}   sla_deadline: {_fmt(r['sla_deadline'])}")

        # The point of the exercise: did it invent a value?
        if r["department"] or r["enquiry"] or r["sub_enquiry"]:
            key = (r["reference_type"], r["department"], r["enquiry"], r["sub_enquiry"])
            partial = any(
                t[1] == r["department"] and t[2] == r["enquiry"] and t[3] == r["sub_enquiry"]
                for t in taxonomy
            )
            if key in taxonomy or partial:
                print("     VERDICT       on-taxonomy (a real row) - check if it is the RIGHT row")
            else:
                print("     VERDICT       *** OFF-TAXONOMY VALUE WRITTEN - P0 regression ***")
        else:
            print("     VERDICT       left unclassified (no invented value) - expected outcome")
        print()


if __name__ == "__main__":
    asyncio.run(main())
