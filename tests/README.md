# The test classes

## Ordering

`testng.xml` declared the order these classes run in, and that order was deliberate. pytest
collects files alphabetically instead, so the intent is carried in the FILE NAMES - the
numbers are the same ones `testng.xml` used:

| File | Tests |
|---|---|
| `test_01_login.py` | 15 |
| `test_02_navigation.py` | 13 |
| `test_03_dashboard.py` | 11 |
| `test_04_ticket_list.py` | 22 |
| `test_05_ticket_filter.py` | 11 |
| `test_06_ticket_detail.py` | 22 |
| `test_06a_investigation.py` | 13 |
| `test_06b_customer_records.py` | 13 |
| `test_07_kanban.py` | 13 |
| `test_07a_sla.py` | 12 |
| `test_07b_escalation.py` | 4 |
| `test_08_create_ticket.py` | 18 |
| `test_08b_reply_lifecycle.py` | 13 |
| `test_09_form_validation.py` | 10 |
| `test_10_modal_form_validation.py` | 9 |
| `test_12_discarded.py` | 6 |
| `test_13_admin.py` | 11 |
| `test_13a_notification.py` | 13 |
| `test_14_reports_audit.py` | 20 |
| `test_15_role_access.py` | 12 |
| `test_15_role_matrix.py` | 90 |
| `test_16_department_isolation.py` | 8 |
| `test_17_role_scope.py` | 9 |
| `test_18_fixed_bug_regression.py` | 5 |
| **Total** | **373** |

Sign-in comes first because if that is broken every later class would fail with a confusing
error rather than the real one. Access control runs LAST because it switches account several
times, which keeps the earlier classes' sign-ins simple and predictable.

## Never in parallel

Classes run ONE AFTER ANOTHER, exactly as under TestNG. Two reasons, both real:

1. each class opens its own browser and signs in, and the sign-in endpoint is rate limited to
   10 requests a minute per IP - running classes side by side would trip it,
2. a few tests write to the database (creating a ticket), and parallel runs would make the
   row counts other tests read unpredictable.

Do not add `pytest-xdist`.

## Running one group

    pytest tests/test_07_kanban.py          # one class
    pytest -m smoke                          # the short confidence run
    pytest -k "breadcrumb"                   # one behaviour across classes
