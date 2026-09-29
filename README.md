# AWNIC Case Management — Selenium UI tests

Python + Selenium + pytest. **373 test cases across 24 classes** (285 test methods;
`test_15_role_matrix.py`'s two are parametrized and expand to 90 cases).

Ported from the Java/TestNG/Maven suite that used to live in `QA/selenium/`. Every test, page
object and comment came across — the two had exact method parity (284 each, file by file) at
the point the Java was removed.

This suite drives a real Chrome browser through the real application and checks what a real
user would see. It is deliberately plain: page objects hold the locators, test classes hold the
assertions, and one shared parent class holds everything both would otherwise repeat. No driver
factory, no listeners, no retry framework, no reporting plugin.

---

## 1. How it is put together

```
QA/selenium-py/
├── requirements.txt         two real dependencies: selenium + pytest
├── pytest.ini               markers, test paths, the 300s per-test backstop
├── conftest.py              CLI options, settings loading, the browser lifecycle
├── config/
│   ├── config.properties           your laptop
│   └── config.deployed.properties  the shared AWS test site
├── awnic_qa/
│   ├── config.py            reads the .properties files (and -D overrides)
│   ├── driver.py            Chrome options + the 3-attempt start retry
│   ├── base_test.py         signs in, holds every page object and shared helper
│   └── pages/               ONE MODULE PER SCREEN — locators and actions live here
│       ├── base_page.py         ← the shared Selenium helpers everything else uses
│       ├── login_page.py
│       ├── side_nav_page.py
│       ├── top_bar_page.py
│       ├── dashboard_page.py
│       ├── ticket_list_page.py
│       ├── ticket_detail_page.py
│       ├── new_ticket_page.py
│       ├── ticket_edit_page.py
│       ├── kanban_page.py
│       ├── discarded_list_page.py
│       ├── admin_page.py
│       ├── reports_page.py
│       ├── investigation_page.py
│       ├── customer_records_page.py
│       ├── reply_page.py
│       └── sla_page.py
├── tests/                   ONE MODULE PER AREA - assertions only, no locators
│                            (24 files - see tests/README.md for the list and run order)
└── tools/
    ├── check_intake_results.py    read-only: what the live pipeline did with a test email
    └── testcase_generator/        builds the QA .xlsx test-case packs
```

### Why the split into `pages/` and `tests/` (the Page Object Model)

Locators — the CSS and XPath strings that find things on screen — are the most fragile part of
any UI test. When a developer renames a button, you want **one** line to change, not forty.

So the rule is:

- **`pages/` knows HOW.** How to find the search box, how to open the filter drawer.
- **`tests/` knows WHAT.** What should be true afterwards.

Open `tests/test_04_ticket_list.py` and you will not find a single `By.XPATH`. It reads almost
like English. That is the payoff.

### Why there is a `BasePage`

Before it, the same handful of lines was copy-pasted into every page object: "wait until
clickable then click", "does this element exist", the XPath for a button with some text. All of
that now lives once in `awnic_qa/pages/base_page.py`, so each page object contains only what is
genuinely special about its own screen.

### Why there is a `BaseTest`

It signs in and **holds every page object**, built once by the `browser` fixture. That is why a
test class is only ever three lines of setup, and why no test ever writes `SomethingPage(...)`.

---

## 2. How a test run actually works

```
you type:  pytest
   │
   ▼
pytest_configure  →  loads config.properties (or config.deployed.properties)
   │
   ▼
pytest runs the 24 classes ONE AFTER ANOTHER (never in parallel)
   │
   ▼
for each class:
   browser fixture (class-scoped)     ← launches Chrome, builds the page objects
   sign_in fixture (class-scoped)     ← signs in ONCE for the whole class
   ensure_browser_alive (per test)    ← replaces a dead session before each test
   test  test  test  …                ← each test navigates to the page it needs
   browser fixture teardown           ← quits Chrome, even if a test crashed
```

**Why one browser per CLASS and not per test?** The sign-in endpoint is rate limited to
**10 requests a minute**. A fresh browser and a fresh sign-in for all 373 tests would trip that
limit part way through and produce a pile of failures that say nothing about the product. One
sign-in per class keeps the suite honest. (If it is tripped anyway, `login_as` waits a minute
and tries once more before giving up — see `base_test.py`.)

**Why never in parallel?** Same rate limit, plus a few tests create a ticket, and parallel runs
would make the row counts other tests read unpredictable. **Do not add `pytest-xdist`.**

### What replaced what

| Java / TestNG / Maven | Python / pytest |
|---|---|
| `mvn clean test` | `pytest` |
| `mvn test -Denv=deployed` | `pytest --env=deployed` |
| `mvn test -Dheadless=true` | `pytest -D headless=true` |
| `mvn test -Dtest=KanbanTest` | `pytest tests/test_07_kanban.py` |
| `mvn test -Dtest='LoginTest#unknownEmailIsRejected'` | `pytest tests/test_01_login.py -k unknown_email` |
| `testng.xml` (whole suite, ordered) | `pytest` + the numbered file names |
| `testng-smoke.xml` | `pytest -m smoke` |
| `testng-flow.xml` | `pytest -m flow` |
| `@BeforeClass` / `@AfterClass` | the class-scoped `browser` fixture in `conftest.py` |
| `@BeforeMethod` | the function-scoped `ensure_browser_alive` fixture |
| `@Test(priority = N)` | definition order (pytest runs methods as written) |
| `@DataProvider` | `@pytest.mark.parametrize` |
| `SkipException` | `pytest.skip()` |
| `Assert.assertTrue(x, msg)` | `assert x, msg` |

The two settings files are the SAME `.properties` files the Java suite used, copied across
unchanged — they carry a lot of hard-won knowledge about the environments in their comments.

### Two renames the port forced

Python has no method overloading and `type` is a builtin. Both are documented in the files:

- `BasePage.type(By, String)` → `BasePage.type_into(locator, text)`
- the field-oriented `typeInto(fieldKey, text)` on `TicketEditPage` / `NewTicketPage` →
  `fill(field_key, text)` (and `fill_textarea`). In Java these overloaded `type`; in Python
  they would have *overridden* the parent method instead.

---

## 3. Two environments

The suite runs against either your own laptop or the shared AWS test site. You choose with
`--env`, and each has its own settings file:

| | Your laptop | The shared AWS test site |
|---|---|---|
| Command | `pytest` | `pytest --env=deployed` |
| Settings file | `config/config.properties` | `config/config.deployed.properties` |
| Web | `http://localhost:3200` | `https://twu3nrmnmv.eu-west-1.awsapprunner.com` |
| API | `http://localhost:8010` | `https://ttg9m2zhsm.eu-west-1.awsapprunner.com` |
| Page speed | ~40 s on first visit (it compiles) | ~1 s (already built) |
| Missing account | **fails** — everything is seeded, so it is a real problem | **skips** — only some roles exist there |
| Tests that create a ticket | run | **skipped** unless you pass `-D writeTestsEnabled=true` |

Every run prints where it is pointed, so you can never misread a failure:

```
Running against https://twu3nrmnmv.eu-west-1.awsapprunner.com  (settings: config.deployed.properties)
```

### Start with the smoke suite

Fourteen tests, a couple of minutes — they check that the site is up, that the login form
renders, that signing in works and lands on the dashboard, that no protected page opens without
a session, and that the one page which *must* stay public (the customer intake form) still
does. Most need no account at all; the handful that do use only the two accounts that are
verified on every environment — the CC agent (`agentEmail`) for sign-in, sign-out and the
dashboard, and the administrator (`adminEmail`) for the admin landing checks:

```bash
pytest --env=deployed -m smoke
```

If that is red, do not bother with the full suite yet. If it is green, the deployment is alive
and the login gate is working.

### A warning about the shared site

Other people are testing on it at the same time, and the `testaiagent@awnic.com` email testing
is creating real tickets on it. So tests there **never assert a fixed number** — they assert
relationships that must hold whatever the data is doing ("Open Cases can never exceed Total",
"one month cannot hold more tickets than exist altogether").

---

## 4. Running it locally

Install once:

```bash
cd QA/selenium-py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Chrome's driver is downloaded automatically by Selenium Manager, built into Selenium 4. There
is no `chromedriver` to install.

The application has to be running locally first:

```bash
# terminal 1 — database
cd apps/api && docker compose up -d

# terminal 2 — API   (port 8010, not 8000)
cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8010

# terminal 3 — web   (port 3200)
cd apps/web && npm run dev

# once, to put the test data in place
make seed-demo
```

Then:

```bash
cd QA/selenium-py

.venv/bin/python -m pytest                              # the whole suite
.venv/bin/python -m pytest -D headless=true             # no visible window (use in CI)
.venv/bin/python -m pytest tests/test_07_kanban.py      # one class
.venv/bin/python -m pytest -k unknown_email             # one test
.venv/bin/python -m pytest -D baseUrl=http://localhost:3300   # a different port
.venv/bin/python -m pytest -D timeoutSeconds=15         # faster, once the app is warm
.venv/bin/python -m pytest -m smoke                     # the short confidence run
```

---

## 5. Things about this application that will bite you

Each one cost a debugging session. They are the reason some of the code looks the way it does.

1. **The dashboard is at `/`, not `/dashboard`.** There is no `/dashboard` route at all.

2. **The first visit to any page takes about 40 seconds.** The development server compiles each
   page the first time somebody opens it — the dashboard measured 41 seconds cold and under a
   second warm. That is why `timeoutSeconds` is 40 and not 15. Against a built (production)
   app, pass `-D timeoutSeconds=15`.

3. **Sign-in is rate limited to 10 a minute.** Hence one sign-in per class, `login_once(...)`
   for classes that switch roles, and the one automatic retry in `login_as`.

4. **Signing out needs TWO cookie deletes.** `access_token` lives on path `/`, but
   `refresh_token` lives on `/api/v1/auth`. Chrome only deletes cookies visible to the current
   page, so clearing from `/login` alone leaves the refresh cookie behind — and the login page
   silently uses it to sign you straight back in. Every "signed out" test would then pass while
   testing nothing. See `BaseTest.clear_session()`.

5. **`element.clear()` does not work on this app's inputs.** They are React inputs; `clear()`
   wipes the value without telling React, so nothing re-renders and the search does not re-run.
   `BasePage.clear_box()` presses Backspace instead, like a person would.

6. **Dragging a Kanban card needs pointer events.** Selenium's `ActionChains.drag_and_drop`
   speaks the older HTML5 drag protocol, which this board ignores completely — the card simply
   does not move. Use `BaseTest.drag_card(...)`, and read the comment on it.

7. **The create-ticket form has a toolbar fixed to the bottom of the screen.** A field low on
   the page sits underneath it and the click lands on the toolbar instead. Every helper in
   `BasePage` scrolls the element to the middle of the window first.

8. **`"6 results"` is three separate pieces of text in the page** — `"6"`, `" result"`, `"s"`.
   `contains(text(),'result')` looks only at the first piece and never matches. The locator
   asks "does *any* piece of text contain it" instead.

9. **That count is the TOTAL, not the rows on screen.** The list pages at ten, so "28 results"
   above ten rows is correct, not a bug.

10. **The sort direction is left out of the URL when it is the default.** The first click gives
    `?sort=<column>` with no `order` at all. Never wait for `order=desc`.

11. **The scope tabs write nothing to the URL.** They are client-side only, so wait for the
    rows to change, never for a query parameter.

12. **The form gives no validation messages.** It keeps the submit button disabled instead.
    That is what the validation tests assert — far more reliable than matching text.

13. **There are two "not found" wordings.** A bad URL gives *"Page not found"*; a ticket you may
    not see gives *"Ticket not available"* — deliberately the same message whether it exists or
    not, so nobody can discover tickets by guessing ids.

14. **The management report covers ONE CALENDAR MONTH, and by default the PREVIOUS one.** It
    used to total every ticket that had ever existed. So its "Total Tickets" is normally
    *smaller* than the ticket lists, not bigger — a ticket created today is deliberately absent
    from last month's report. Any comparison between the two must run "one month cannot exceed
    all time", never the other way round. The month boundaries are Dubai-local midnight, so work
    the expected month out in `Asia/Dubai` or the tests go wrong for four hours a day at the
    turn of a month.

15. **The report's page heading is "Team Performance Report", not "Reports".** "Reports" is only
    the menu label and the breadcrumb now.

16. **`/webform-test` is public ON PURPOSE, and must never join the protected-paths list.**
    Customer intake never gets a login wall (R03), so it sits in apps/web's middleware
    `PUBLIC_PATHS` beside `/login`.
    `test_01_login.py::test_the_customer_intake_form_is_deliberately_public` asserts the
    exception so nobody "fixes" it.

17. **There are now TWO things called "Enquiry Summary" and they are different.** A standalone
    CARD carrying the AI Generated badge (pure AI output, hidden on a manual ticket) and a FIELD
    inside TICKET INFORMATION (part of the classified field set, present on every enquiry, reads
    as an em dash when empty). Searching the page for the text cannot tell them apart — the
    card's title is an `<h3>`, the field's label is a `<div>`. A test that ignored this went red
    the day the field was added.

18. **The whole action header VANISHES on a Resolved or Closed ticket.** `TicketHeaderActions`
    starts with `if (isClosed) return null` — so More Action, Change Status, all of it, is gone.
    Correct behaviour (there is nothing left to do to a finished ticket), but it means a
    permissions test that opens "the first ticket in the list" can land on a Resolved one and
    read "no menu" as "this role is not allowed", when in fact nobody is. Take the ticket from
    the board's New or In Progress column instead — those are open by definition.
    `BaseTest.open_an_open_ticket_from` and `test_15_role_matrix.py`'s `open_an_open_ticket` do
    exactly this, and the first run of that class failed for precisely this reason.

19. **User Management admits the HOD and the Complaints Manager, not only the Admin.** It gates
    on `canManageUsers` — org-wide OR own-department — and both hold the own-department key. The
    screen is not the boundary; the API scopes what they can actually change. Do not "tighten" a
    test to expect a refusal here.

---

## 6. Test accounts

Dev sign-in takes an email and no password, so there is no secret in `config.properties`. Which
account you use decides what you can see. All eight are seeded by
`apps/api/scripts/seed_local_dev.py`.

| Account | Role | Ticket queues | Create | User admin |
|---|---|---|---|---|
| `agent@awnic.ae` | cc_initiator | all three | yes | no |
| `supervisor@awnic.ae` | cc_supervisor | all three | yes | no |
| `complaints.officer@awnic.ae` | complaint_handler | complaints **assigned to them only** | yes | no |
| `dept.poc@awnic.ae` | dept_poc | **own department only** (Medical Claims) | no | no |
| `complaints.manager@awnic.ae` | manager | all, organisation-wide | yes | no |
| `hod@awnic.ae` | head_of_department | all three | **no** | own department |
| `compliance@awnic.ae` | compliance_officer | read-only | no | no |
| `admin@awnic.ae` | admin | **none** — `/` redirects to `/admin` | no | organisation-wide |

Do not use `dev@awnic.ae` — it is reserved.

---

## 7. What is covered, and what is not

The suite is built from the module-wise test-case pack
(`QA/AWNIC-Module-Wise-Test-Cases.xlsx`, generated from `tools/testcase_generator/`). Not every
one of its 563 cases can be driven through a browser, so the automation covers the ones that
can:

| Module | Class | Notes |
|---|---|---|
| M01 Login and access | `test_01_login.py`, `test_02_navigation.py` | menu shape per role, deep links, sign-out |
| M02 Users, roles, permissions | `test_13_admin.py` | list, search, add-user validation, role matrix |
| M04 Manual ticket creation | `test_08_create_ticket.py` | every validation rule, Arabic, long text, happy path |
| M05 Website form intake | ~~`test_11_webform_intake.py`~~ | **Removed 2026-09-09** — it created real tickets and needed `WEBFORM_INTAKE_SERVICE_TOKEN` on both apps (see §9). The one access-control check it is worth keeping — that the intake form stays reachable signed out — lives in `test_01_login.py` |
| M05 Ticket list and details | `test_04_ticket_list.py`, `test_05_ticket_filter.py`, `test_06_ticket_detail.py` | search, sort, paging, filters, tabs, notes |
| M07 Changing a ticket type | `test_06_ticket_detail.py`, `test_12_discarded.py` | discard confirm + reason list, the proactive reclassification window, restore, the discarded queue |
| M08 Stages and Kanban | `test_07_kanban.py` | columns, counts, drag, illegal moves, resolve guard |
| M09 SLA timers | `test_07a_sla.py` | the three cards, the ladder, the motor-only rung |
| M10 Escalation | `test_07b_escalation.py` | who may force it, the modal's guards |
| M11 Complaints Register | `test_06a_investigation.py` | the register record, the append-only remarks trail, who may write into it |
| M13 Customer Information | `test_06b_customer_records.py` | the three record tables, "no records" vs "lookup failed", the customer's case history |
| M14 Notifications | `test_13a_notification.py` | the bell, the empty state, the unread badge, where a notification takes you |
| M15 Dashboard, reports, audit | `test_03_dashboard.py`, `test_14_reports_audit.py` | figures agree, the month window, the org tree, the ranked employee table, report proved against the lists |
| End to end (cuts across all) | ~~`test_08a_ticket_lifecycle.py`~~ | **Removed 2026-09-09** — every step depended on step 1 creating a real ticket (see §9). The reply-driven journey below is the surviving end-to-end path |
| End to end, the reply path | `test_08b_reply_lifecycle.py` | the same journey by its REAL road: the ticket moves because somebody replies, not because somebody sets a status |
| Form validation | `test_09_form_validation.py`, `test_10_modal_form_validation.py` | the exact sentence each rule is documented to produce |
| Access control (cuts across all) | `test_15_role_access.py`, `test_15_role_matrix.py` | type × scope visibility, hidden **and** typed-URL |

**Not automated here, on purpose:**

- **M03 Email intake, M06 AI classification.** These are driven by background jobs and by the AI
  pipeline, not by anything you can click. They are tested at the API level, and manually from
  the workbook. The **"Attachment(s) Received"** audit entry belongs to this group: it only ever
  appears on a ticket that arrived by email with a reply attachment, which no browser test can
  arrange.
- **M12 Duplicate detection.** Needs a specific data situation to be set up first (two matching
  tickets). Worth automating once there is a seed script that guarantees the setup.
- **The reply-template library (part of M14).** There is no template-library UI in `apps/web`
  yet — the reply composer takes free text only — so its eight cases have nothing to drive.
  Add them when the library ships.
- **Anything needing a second browser at the same time** — "two people editing the same ticket",
  "signing out in one tab signs you out in the others". Possible, but it needs a second driver,
  which this deliberately simple suite does not have.

Where a test needs data that may not be seeded, it **skips with an explanation** rather than
failing — for example "No cards in the New column, run `make seed-demo`". A skip tells you
something is missing; a red failure would tell you something is broken, which is not the same
thing. `pytest.ini` sets `-ra` so every skip reason is printed rather than hidden behind an `s`.

---

## 8. Open questions and known defects

### A. "Change Status" is offered to people who cannot use it — **defect**

Every action on the ticket header is hidden from a role that cannot use it. `More Action` checks
`canReclassify` / `canDiscard` / `canReassign` / `canManualEscalate` / `canEdit`.
**`Change Status` is gated on nothing at all** — it is hidden only when the ticket is escalated
or already closed.

So a Compliance Officer, who is read-only, is shown a button that the API refuses with a 403. It
is not a security hole — the API is the real boundary — but it invites a user to press something
guaranteed to fail, and it breaks the rule in `docs/rbac.md` that every in-page action mirrors
its permission.

*Fix:* pass a `canMoveStage` prop into `TicketHeaderActions.tsx`, exactly the way `canEdit`
already is.

*Test:* `test_06_ticket_detail.py::test_a_compliance_officer_is_not_offered_the_change_status_button`
asserts the correct behaviour on purpose and **fails until this is fixed** — the same convention
the suite used for the old dashboard defect, which has since been fixed.

### B. Can a Compliance Officer read the audit trail? — **needs a decision**

The two sources disagree:

- **The permission matrix** (`apps/api/app/teams/seed_data.py`) grants `compliance_officer` only
  four things — customer history, the three ticket types, organisation-wide ticket scope, and
  resolution notes. **No audit-trail permission**, so `/audit-trail` refuses them.
- **The test-case pack** (M15, "A compliance officer can read the full audit trail") expects the
  opposite.

One of the two is wrong, and it is a business decision which. The suite currently asserts what
the system actually **does**
(`test_15_role_access.py::test_compliance_officer_cannot_open_the_organisation_wide_audit_trail`),
so it does not sit red on an unresolved question — but the question is real, and for a compliance
role it is not a small one.

---

## 9. This suite writes NOTHING

**Every test here is read-only.** As of 2026-09-09 the suite creates no tickets, sends no email,
and touches no external system — so it is safe to run against a shared environment, on repeat,
without leaving anything behind.

What was removed to get here, and why:

| Removed | Why |
|---|---|
| `test_11_webform_intake.py` (14 tests) | Website intake — created real tickets, and needed `WEBFORM_INTAKE_SERVICE_TOKEN` on both apps |
| `test_08a_ticket_lifecycle.py` (13 tests) | Every step depended on step 1 creating a real ticket |
| 5 `@pytest.mark.write` tests across 5 files | Created tickets, appended append-only register remarks, or saved edits |
| 1 reply-send test | Emailed a **real customer** through Graph |

Email intake (M03) was never in this suite — it has no browser surface at all. It is covered at
the service level in `apps/api/tests/e2e_qa/test_e2e_intake_flow.py`, and
`tools/check_intake_results.py` reads back what the live pipeline did.

`require_write_tests()` and the `write` marker are in use: **3 tests currently carry the `write`
marker** — the Kanban drag in `test_07_kanban.py`, and the two notification tests in
`test_13a_notification.py` that mark a notification read. **Write tests remain disabled by
default**: `writeTestsEnabled` is false, and each test also calls `require_write_tests()`, so
`pytest -m write` selects exactly those three and they skip. Enable them only deliberately, and
never against a shared environment without approval — they move a real ticket and mark real
notifications read on a shared account. If you add another, gate it the same way and keep it
out of the default run.

---

# QA Automation Execution & Progress

*Added 2026-09-29. Everything above this line is the original README and is unchanged.*

This section is the record of the Smoke / Sanity / Regression work: how the suite is
organised now, what has actually been run, what was fixed, and what is still open. Every
number here comes from a run that happened or a `--collect-only` count taken after the change
it describes. A fuller narrative lives in `QA_AUTOMATION_PROGRESS.md` at the repository root.

**All runs recorded here used `--env=deployed` (UAT).**

## 1. Objective

Organise the existing Phase 1 Selenium automation into three usable suites — **Smoke**,
**Sanity** and **Regression** — and then add Phase 2 into the **same framework** without
duplicating the Phase 1 coverage that already exists.

Two consequences shape everything below:

- The suite must say honestly what it cannot check today, so that a green run means something.
  Tests that cannot execute are kept and labelled, never deleted and never left to fail.
- Phase 2 joins by adding markers to this repository, not by forking a second suite.

## 2. Test Marker Architecture

Four **independent** axes. A test carries one value from each axis that applies to it.

### Suite markers

| Marker | Meaning |
|---|---|
| `smoke` | The short confidence run — is the application fundamentally working? |
| `sanity` | Focused re-check of the major modules |
| `regression` | Full protective coverage |

### Phase markers

| Marker | Meaning |
|---|---|
| `phase1` | Phase 1 behaviour, or platform-wide behaviour Phase 1 relies on |
| `phase2` | Phase 2 behaviour |

### Execution-state markers

| Marker | Meaning |
|---|---|
| `blocked` | Valid coverage that cannot run here yet; the argument names the blocker (`cc_supervisor`, `compliance_officer`, `roleless_account`, `tier1_window`) |
| `quarantine` | Known defect or unexplained failure; the argument names it (`TKT-03`, `FUNC_011/FUNC_045`, `unexplained-<date>`, `no-failing-path`) |
| `api_candidate` | Better asserted at the API layer; held here unchanged until that tier exists |
| `write` | Changes real data; skipped unless `writeTestsEnabled=true` |
| `env_check` | A statement about the environment or the test data, not about the product |

### Existing priority markers

`p0`, `p1`, `p2` — unchanged, from `QA/qa-priority-test-matrix.md`.

### These are separate axes — do not merge them

They answer different questions, and the useful selections combine them:

- `-m "p0 and not blocked"` — everything critical that can actually run
- `-m "phase1 and regression"` — one phase's protective suite
- `-m "regression and not blocked"` — **the gating run**

A single combined "tier" marker cannot express any of those.

**Invariants, verified at collection — keep them true:**

| Invariant | Why |
|---|---|
| `smoke ⊂ sanity ⊂ regression` | A gate must not check less than the suite below it |
| `sanity and blocked` = 0 | Sanity must be fully runnable or its result means nothing |
| `phase1 and phase2` = 0 | One phase per test |
| `not phase1 and not phase2` = 0 | No test without a phase |
| `write and regression` = 0 | Write tests never enter a normal run |

## 3. Current Test Counts

| Category | Count |
|---|---:|
| Total | 342 |
| Smoke | 14 |
| Sanity | 59 |
| Regression | 317 |
| Runnable Regression | 209 |
| Blocked | 111 |
| Quarantine | 10 |
| API candidates | 10 |
| Write | 3 |
| Phase 1 | 338 |
| Phase 2 | 4 |

Smoke and Sanity are **subsets** of Regression, not extra tests. The 342 is a count of *cases*:
246 test functions, with the role-matrix grid contributing 90 parametrised cases. Blocked tests
are counted inside Regression (317 = 209 runnable + 108 blocked); the remaining 3 blocked cases
are also quarantined and so sit outside Regression.

The 4 Phase 2 cases are the two R20 manual-escalation modal tests (`test_07b`) and the two R22
customer-history tests (`test_06b`).

## 4. Commands

```bash
pytest -m smoke --env=deployed                          # 14  — the gate, must be 100% green
pytest -m sanity --env=deployed                         # 59  — per-module re-check
pytest -m "regression and not blocked" --env=deployed   # 209 — the gating regression run
pytest -m "phase1 and regression" --env=deployed        # 317
pytest -m "phase2 and regression" --env=deployed        # 4
pytest -m blocked --env=deployed                        # 111 — waiting on accounts/data
pytest -m quarantine --env=deployed                     # 10  — must stay red, never gates
pytest -m api_candidate --env=deployed                  # 10
pytest -m write --env=deployed                          # 3   — skipped unless enabled
pytest --collect-only -q                                # 342
```

**Write tests stay disabled by default** (`writeTestsEnabled=false`, plus
`require_write_tests()` in each). Do not enable them against UAT without deliberate approval —
they move a real ticket and mark real notifications read on a shared account.

## 5. Smoke

| Run | Result |
|---|---|
| Initial | 13 passed, 1 failed (196s) |
| After fix | **14 passed, 0 failed** (163s) |

**Failure:** `test_07a_sla::test_the_sla_tab_shows_its_three_cards` — timed out waiting for the
ticket URL. `open_first_row()` assumed row 1 was clickable, but UAT's row 1 was a **merged
duplicate**, which `DataTable` renders inert (`rowDisabled={(t) => t.is_duplicate}`), so the
click did nothing. The product was correct.

**Fix:** `TicketListPage.open_first_row()` now opens the first row the application will
actually open — decided from the product's own rendering (`cursor-pointer` vs
`cursor-not-allowed`) — returns that row's reference, and fails immediately with a diagnostic
when nothing is openable instead of waiting out a 40-second timeout. It is used by 18 call
sites across 12 modules, so the same latent failure existed suite-wide.

**Status: FROZEN / GREEN — 14/14.**

## 6. Sanity

| Run | Result |
|---|---|
| Initial | 55 passed, 3 failed, 2 skipped (736s) |
| After 3 fixes | 57 passed, 1 failed, 2 skipped (704s) |
| Final (59 selected) | **58 passed, 0 failed, 1 skipped** (684s) |

**The three failures, all automation, none a product defect:**

1. **My Tickets ownership** — the Current Handler reader returned the **avatar initials**
   (`"AN"`), never the handler's name. Fixed by `_cell_value()` in `ticket_list_page.py`, which
   skips text belonging to an avatar (identified by `span[aria-label][title]`, what `Avatar.tsx`
   itself renders). No test changed; other columns unaffected.
2. **Notification panel** — the test pressed **Escape**, but `TopBar` has no key handling and
   closes via an outside-click catcher. Fixed by `TopBarPage.close_notifications()`, which
   clicks the product's own catcher. No Escape support was added to the product.
3. **Cross-department direct URL** — the assertion ran while the Next.js route skeleton was
   still up. Fixed by `BaseTest.wait_for_page_content()`, which waits for no `aria-busy="true"`
   **and** an `<h1>`, so it settles on either outcome — the ticket or the refusal.

Failure 3 was verified against the API before classification, because the alternative reading
was a data leak:

| Account | `GET /api/v1/tickets/e338584f-…` |
|---|---|
| `m_mohanan@awnic.com` (Finance & Accounts) | **404 — Ticket not found** |
| `a_shalaby@awnic.com` (Medical Operations) | 200 — `INQ-2026-0066` |

**Department isolation is intact.**

**Toast interference.** `test_08_create_ticket::test_submit_stays_disabled_until_every_required_field_is_filled`
failed when four in-app notification toasts covered the Source dropdown. `BasePage.click()`
already called `wait_for_toasts_to_clear()` and its selector was still correct — the gap was
timing: TopBar polls every 30 seconds, so a batch landed between that single check and the
click, and the three retries fired back-to-back into the same toast.
`BasePage.click_without_scrolling()` now calls the **existing** helper between retry attempts.
No duplicate helper, no sleep, notifications neither disabled nor cleared. Targeted test PASSED.

**`test_07b` classification correction.** `TestEscalation.sign_in` is a **class-scoped autouse**
fixture signing in as `supervisorEmail`. That account does not exist on UAT, and a skip raised
in a class-scoped fixture **skips every test in the file** — including
`test_an_escalated_ticket_cannot_be_moved_by_hand`, which signs in as the CC Initiator and
needs nothing from the Supervisor. Its `sanity` marker was removed and
`blocked("cc_supervisor")` added; `phase1` and `regression` kept.
**Counts:** Sanity 60 → 59, Blocked 110 → 111, Runnable Regression 210 → 209.

**The one remaining skip** is a data condition the test reports itself: *"a_shalaby@awnic.com
sees no rows in /tickets/complaints, so there is nothing to check. That is consistent with the
scoping, but it does not prove it."* `sanity and blocked` = 0.

**Status: FROZEN / GREEN WITH ONE KNOWN DATA SKIP.**

## 7. Regression baseline

`pytest -m "regression and not blocked" -v --env=deployed`

| | |
|---|---:|
| Selected | 209 |
| Passed | **199** |
| Failed | **6** |
| Skipped | 4 |
| Errors | 0 |
| Duration | 2178s (36m 18s) |

Pass rate on the runnable set: **95.2%**. No confirmed product defect.

| # | Test | Cause | Fix | Result |
|---|---|---|---|---|
| F1 | `test_02::opening_a_ticket_adds_its_reference_to_the_breadcrumb` | Read row 1's reference separately while `open_first_row()` correctly opened row 2 | Use the reference `open_first_row()` returns | **PASS** |
| F2 | `test_04::sorting_twice_reverses_the_order` | Empty `reference_number` (`''`) sorts before `INQ-*` | **NOT FIXED — open** | **FAIL** |
| F3 | `test_08::every_manual_channel_can_be_chosen` | Page Object expected 5 Source options; product exposes 7 | Added SANADAK and Social Media | **PASS** |
| F4 | `test_13::searching_for_somebody_who_does_not_exist_shows_an_empty_list` | Wait condition was already true of the unfiltered table | Wait for the row set to change | **PASS** |
| F5 | `test_13a::mark_all_read_is_only_offered_when_something_is_actually_unread` | Locator matched `'Mark all'`; UI renders **"Mark as read all"** | Exact-text locator | **PASS** |
| F6 | `test_18::func_050_search_returns_every_matching_user_not_just_one` | Stale elements after pagination | `get_listed_emails()` re-finds rows and retries | **PASS** |

> **Five automation failures from the baseline have been fixed and individually validated.
> F2 remains open pending product/business clarification.**

The full Regression suite has **not** been re-run since these fixes.

### F2 — open, do not "fix" it

Established by read-only API queries, no test rerun:

- The leading row's `reference_number` is **`''` — an empty string, not NULL**.
- The backend orders with `nullslast()` (`app/tickets/repository.py:572`), which does not apply
  to an empty string, so `''` sorts before `'INQ'`. **The ordering is correct for the value
  stored.**
- **About 20 of the first 200 tickets have an empty reference number.** A sampled one:
  `source 'Email'`, `ai_processed true`, `department ''`, `email_subject None`,
  `status 'New - Unassigned'` — the shape of an email-intake ticket whose classification never
  completed.

**Open question for the product owner: does email intake number a ticket at creation, or only
at classification?** That decides whether those 20 tickets are a normal interim state or a
numbering gap against R33/R34/R41. Until it is answered: do not change the test, do not filter
out empty references, do not change the backend, do not quarantine it.

### Skips in the baseline — 4, all expected

| Test | Reason |
|---|---|
| `test_09::sub_product_line_is_hidden_rather_than_shown_empty` | No Product Line values configured on this environment |
| `test_13a::an_empty_panel_says_so_rather_than_showing_nothing` | The account has notifications, so the empty state is not on screen |
| `test_15_role_access::complaint_handler_sees_only_complaints_assigned_to_them` | `complaints.officer@awnic.ae` has no complaints assigned |
| `test_16::…[/tickets/complaints-Medical Operations]` | `a_shalaby@awnic.com` sees no complaint rows |

Two of those are coverage gaps rather than noise: with **no Product Line values** the complaint
cascade is untested on UAT, and with the **Complaint Handler owning no complaints** the
own-assigned scope rule is never actually exercised.

## 8. Environment and account blockers

| Blocker | Effect |
|---|---|
| `supervisor@awnic.ae` **does not exist on UAT** — sign-in returns "No matching account for this email" | 84 blocked cases. Harder than "exists but holds no role": the account must be **created**, not merely granted |
| Compliance Officer account unavailable | 18 blocked cases |
| No role-less account available | 4 blocked cases (`test_17` fail-closed check) |
| Complaint Handler has no assigned complaints | Own-assigned scope cannot be proved |
| No complaints visible to the Medical Operations POC | 1 skip in Sanity and Regression |
| Product Line complaint taxonomy not seeded | Complaint cascade untested |
| Tier-1 window state | 4 cases (`test_06`, `test_10` reclassify guards) |
| External dependencies — MagOneAI acknowledgment, Data Mart records, the SLA breach scan | Outside normal runnable coverage |

**One account unblocks 84 of the 111 blocked cases.** Restoring `supervisor@awnic.ae` is the
single highest-leverage environment action available.

## 9. Quarantine, API candidates, write tests

**Quarantine — 10 tests.** They stay visible and must not gate a normal Regression run:
4 × `FUNC_011/FUNC_045` (the `test_04` search tests, which *are* the automation for that defect
and must stay red until it is fixed), 3 × `unexplained-2026-09-09`, 1 × `unexplained-2026-09`,
1 × `TKT-03` (deliberately red), 1 × `no-failing-path`.

**API candidates — 10 tests**, retained unchanged and excluded from `regression` so migration is
a single scope change: `test_03` ×1, `test_04` ×3, `test_06b` ×1, `test_07a` ×1, `test_14` ×4.
Each asserts something the endpoint owns — arithmetic, ordering, pagination, input handling.

**Write — 3 tests**, all gated: the Kanban drag in `test_07`, and the two notification tests in
`test_13a`. See §4.

## 10. Design decisions

1. **One framework and repository for Phase 1 and Phase 2.** Two suites would drift and
   duplicate the Page Object layer.
2. **Reuse the existing Page Objects, fixtures and utilities.** Shared behaviour (waits,
   sign-in, toast handling) is then fixed once, for everyone.
3. **Do not duplicate Phase 1 tests for Phase 2.** Where Phase 2 changes a Phase 1 rule, update
   and re-mark the existing test rather than copying it.
4. **Use markers for phase separation** rather than separate directories, so any suite can be
   sliced: `-m "phase2 and regression"`.
5. **Keep the four axes independent** (see §2).
6. **Regression membership is explicit** (`@pytest.mark.regression`), not defined by
   subtraction, so a Phase 2 test joins by declaring it.
7. **Blocked tests stay in the repository and skip themselves.** "Green with N skips" is honest;
   a deleted test is coverage silently lost.
8. **Quarantine requires a reference** — a ticket id or a dated note. Without one it becomes
   permanent.
9. **Fix shared defects in the shared layer.** Five of the seven failures found in these runs
   were Page Object or wait defects affecting many tests; each was fixed once in the helper.

## 11. Remaining work

**Needs a product decision**

1. **F2 / empty reference numbers** — see §7.

**Needs an environment or data change**

2. Create `supervisor@awnic.ae` on UAT (unblocks 84 cases).
3. Provide a Compliance Officer account (18 cases).
4. Provide a role-less account (4 cases).
5. Confirm `complaints.officer@awnic.ae` is the intended Complaint Handler, and assign it at
   least one complaint.
6. Seed Product Line values so the complaint cascade can be exercised.

**Automation work not yet started**

7. Re-run the full Runnable Regression suite to confirm the five fixes in situ. Expect 204/209
   with F2 as the only failure — a projection, not a measured result.
8. Two known-weak tests were left deliberately: `test_06b`'s history test (no failing path,
   quarantined) and `test_17`'s stale coverage xfail (`env_check`).
9. The API tier for the 10 `api_candidate` tests.
10. Phase 2 test authoring, once the above is settled.

## 12. Corrections to earlier sections of this README

Three statements in the original sections had gone stale against this work. **All three were
corrected in place on 2026-09-29**; this log is kept so the change is traceable rather than
silent.

| Section | Used to say | Corrected to | Status |
|---|---|---|---|
| §3 "Start with the smoke suite" | "Eleven tests … none of them need an account" | 14 tests; most need no account, the few that do use only the verified agent and admin accounts | Applied |
| §7 "What is covered" | Listed `test_11_webform_intake.py` and `test_08a_ticket_lifecycle.py` as covered | Both rows now marked **Removed 2026-09-09**, matching §9 | Applied |
| §9 | "the `write` marker [is] still defined but currently unused" | 3 tests carry the `write` marker; write tests remain disabled by default | Applied |

## 13. Run history

| Date | Run | Result | Duration |
|---|---|---|---:|
| 2026-09-29 | Smoke (initial) | 13 passed, 1 failed | 196s |
| 2026-09-29 | Smoke (after fix) | **14 passed** | 163s |
| 2026-09-29 | Sanity (initial) | 55 passed, 3 failed, 2 skipped | 736s |
| 2026-09-29 | Sanity (after 3 fixes) | 57 passed, 1 failed, 2 skipped | 704s |
| 2026-09-29 | Sanity (final, 59 selected) | **58 passed, 0 failed, 1 skipped** | 684s |
| 2026-09-29 | Runnable Regression (baseline) | 199 passed, 6 failed, 4 skipped | 2178s |
| 2026-09-29 | Targeted re-run of the 6 failures | 5 passed, F2 unchanged | — |
