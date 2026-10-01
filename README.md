# AWNIC Case Management - UI Automation (Selenium + Python)

Browser tests for the AWNIC Case Management application, written in Python with Selenium and
pytest. They open a real Chrome window, sign in, and check what a real user would see.

> **New here?** Do the [Quick start](#quick-start) below. Everything after it is background
> reading, and you do not need it to run the tests.

---

## Quick start

**Read this first:** this repo contains **only the tests**. The application they test runs
somewhere else. Point the tests at the shared AWS test site by adding `--env=deployed` to every
command.

### A. One-time setup (after you clone)

You need **Python 3.11+** and **Google Chrome** installed. You do not need `chromedriver`.

```bash
git clone https://github.com/muskaan1341/AWNIC-automation-script.git
cd AWNIC-automation-script
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### B. Every time you run the tests

**1. Open a terminal in the repo folder and activate the environment:**

```bash
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

**2. Run the smoke tests first** (14 tests, about 3 minutes):

```bash
pytest --env=deployed -m smoke
```

✅ Expected: `14 passed`. If anything fails here, fix it before running anything bigger.

**3. Then run what you need:**


| I want to run…         | Command                                                 | Time    |
| ------------------------- | --------------------------------------------------------- | --------- |
| Sanity                  | `pytest --env=deployed -m sanity`                       | ~12 min |
| Regression (main run)   | `pytest --env=deployed -m "regression and not blocked"` | ~36 min |
| Everything              | `pytest --env=deployed`                                 | longest |
| One file                | `pytest --env=deployed tests/test_07_kanban.py`         | —      |
| Without a Chrome window | add`-D headless=true`                                   | —      |
| With an HTML report     | add`--html=report.html --self-contained-html`           | —      |

Some tests show as **skipped** on the shared site. That is expected: some accounts and data do
not exist there. The reason for each skip is printed at the end of the run.

### C. Running against your own laptop (optional)

Do this only if you also have the **AWNIC application repo** (`apps/api`, `apps/web`). Ask the
team for it.

1. In the **application repo**, start the database, API and web app, then load the test data:
   ```bash
   cd apps/api && docker compose up -d                                  # terminal 1
   cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8010   # terminal 2
   cd apps/web && npm run dev                                           # terminal 3
   make seed-demo                                                       # once
   ```
2. Open [http://localhost:3200](http://localhost:3200). You should see the sign-in page.
3. Back in **this repo**, run the tests **without** `--env`:
   ```bash
   pytest -m smoke
   ```

The first local run is slow: each page takes about 40 seconds the first time it opens.

### D. If something goes wrong


| Problem                                                                  | Fix                                                                                    |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Every test fails and the screenshots say*"localhost refused to connect"* | You forgot`--env=deployed`                                                             |
| `No module named pytest` or `No module named selenium`                   | Run`source .venv/bin/activate`, then `pip install -r requirements.txt`                 |
| Strange errors, and the run header shows`pytest-9.x`                     | The environment is not activated, so a different pytest ran. Activate`.venv`           |
| Chrome does not open                                                     | Install Google Chrome. The first run also needs internet access to download the driver |

### E. Don'ts

- ❌ Don't run without `--env=deployed`, unless the app is running on your laptop.
- ❌ Don't run tests in parallel (no `-n`, no `pytest-xdist`). Sign-in is limited to 10 per
  minute.
- ❌ Don't pass `-D writeTestsEnabled=true` on the shared site. Those tests change real data.

---

# Reference

Everything below explains how the suite is built and why. You do not need to read it to run the
tests.

Python + Selenium + pytest. **373 test cases across 24 classes** (285 test methods;
`test_15_role_matrix.py`'s two are parametrized and expand to 90 cases).

>>>>>>> b825aec1b2069ab8f94fc5f64384be27b1bd5da5
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>

This repository contains **only the tests**. The application itself lives in a separate
repository (`awinc-case-management`). You do not need that repository to run these tests
against the shared UAT site.

---

## 1. What you need

<<<<<<< HEAD
| Tool | Version | Check with |
| --- | --- | --- |
| Python | 3.11 or newer | `python3 --version` |
| Google Chrome | any recent version | open Chrome > About |
| Git | any | `git --version` |
===============================

```
AWNIC-automation-script/
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

>>>>>>> b825aec1b2069ab8f94fc5f64384be27b1bd5da5
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>

- You do **not** need to download ChromeDriver. Selenium downloads the right one on the first run.
- Your network must be able to reach the UAT site: https://twu3nrmnmv.eu-west-1.awsapprunner.com

---

## 2. Setup (one time)

**macOS / Linux**

```bash
<<<<<<< HEAD
git clone https://github.com/muskaan1341/AWNIC-automation-script.git
cd AWNIC-automation-script
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/muskaan1341/AWNIC-automation-script.git
cd AWNIC-automation-script
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Check that everything is installed. This lists the tests without opening a browser:

```bash
pytest --collect-only -q --env=deployed
```

You should see `412 tests collected`.

> Every time you open a new terminal, activate the virtual environment again
> (`source .venv/bin/activate` or `.venv\Scripts\Activate.ps1`) before running `pytest`.

---

## 3. Settings

All settings are in the `config/` folder. There are no passwords: the app's test login only
needs an email address.


| File                                | Used when                 | Points to                                                    |
| ------------------------------------- | --------------------------- | -------------------------------------------------------------- |
| `config/config.deployed.properties` | you add`--env=deployed`   | the shared UAT site                                          |
| `config/config.properties`          | you add nothing (default) | the app running on your own laptop (`http://localhost:3200`) |

Main settings in each file:


| Setting                                                                                                                               | Meaning                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `baseUrl`                                                                                                                             | the website address the tests open                                                    |
| `timeoutSeconds`                                                                                                                      | how long to wait for a page or element                                                |
| `headless`                                                                                                                            | `true` = run Chrome without a window                                                  |
| `adminEmail`, `agentEmail`, `hodEmail`, `managerEmail`, `supervisorEmail`, `complaintHandlerEmail`, `complianceEmail`, `deptPocEmail` | the test account used for each role                                                   |
| `writeTestsEnabled`                                                                                                                   | `false` = tests that create or change data are skipped (keep it `false` on UAT)       |
| `missingAccountsAreSkipped`                                                                                                           | `true` = if a role's account does not exist, its tests are skipped instead of failing |

You can change one setting for a single run with `-D`, without editing the file:

```bash
pytest --env=deployed -D headless=true
```

=======
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

The step-by-step instructions are in [Quick start, section C](#c-running-against-your-own-laptop-optional).
In short: start the database, the API (port 8010) and the web app (port 3200) from the AWNIC
application repository, run `make seed-demo` once, then run `.venv/bin/python -m pytest` from
this repository without `--env`.
>>>>>>> b825aec1b2069ab8f94fc5f64384be27b1bd5da5

---

## 4. Running the tests

Run these from the repository folder, with the virtual environment active.

| What | Command |
| --- | --- |
| Quick check (14 tests) | `pytest --env=deployed -m smoke` |
| Sanity check (61 tests) | `pytest --env=deployed -m sanity` |
| Full regression (359 tests) | `pytest --env=deployed -m "regression and not blocked"` |
| Same, without a Chrome window | add `-D headless=true` |
| One file | `pytest --env=deployed tests/test_07_kanban.py` |
| Tests whose name contains a word | `pytest --env=deployed -k "unknown_email"` |
| Save an HTML report | add `--html=report.html --self-contained-html` |

**Start with the smoke run.** If it passes, sign-in and the main screens work.

### Rules for the shared UAT site

1. **Never run two test runs at the same time.** Sign-in is limited to 10 per minute; two runs
   together cause false failures.
2. **Keep `writeTestsEnabled = false` on UAT.** Only 3 tests change data, and they are skipped by
   default.
3. Other people use UAT too, so data can change during a run. Some tests **skip** when the data or
   account they need is not there - the skip message says why. A skip is not a failure.

### Running against a local copy of the app (optional)

<<<<<<< HEAD
Only needed if you are developing the app. Start the app from the `awinc-case-management`
repository first (API on port 8010, web app on port 3200 - see that repository's README), then:
=======
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

*Added 2026-09-29. Everything above this line is the original README, apart from the Quick
start and the §4 pointer added on 2026-10-01.*

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
>>>>>>> b825aec1b2069ab8f94fc5f64384be27b1bd5da5

```bash
pytest -m smoke
```

The first visit to each page of a local dev server can take up to 40 seconds. That is normal.
If your web app uses another port: `pytest -D baseUrl=http://localhost:3300`.

---

## 5. Test groups (markers)

Each test has labels, so you can choose what to run with `-m`.


| Marker              | Meaning                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `smoke`             | small "is the app working?" check                                                          |
| `sanity`            | main areas, one check each                                                                 |
| `regression`        | the full protection suite                                                                  |
| `phase1` / `phase2` | which project phase the feature belongs to                                                 |
| `p0` / `p1` / `p2`  | priority (p0 = most important)                                                             |
| `blocked`           | cannot run yet (for example, no account exists for that role). 29 tests. Shows the reason. |
| `quarantine`        | a known defect - expected to fail until the app is fixed                                   |
| `write`             | changes data - skipped unless`writeTestsEnabled=true`                                      |

The full list is in `pytest.ini`.

---

## 6. Folder structure

```
AWNIC-automation-script/
├── config/              settings for UAT and local runs
├── awnic_qa/
│   ├── pages/           page objects: one file per screen (locators + actions)
│   ├── base_test.py     common test steps (sign in, open a page, etc.)
│   ├── users.py         test accounts and their roles
│   └── customers.py     test customer reference numbers (Data Mart test data)
├── tests/               the test files, numbered in the order they run
├── tools/               helper scripts for the QA team (not needed to run the tests)
├── conftest.py          starts/stops Chrome, reads settings, screenshots on failure
├── pytest.ini           markers and pytest options
└── requirements.txt     Python packages
```

### What each test file covers


| File                             | Area                                                 | Tests   |
| ---------------------------------- | ------------------------------------------------------ | --------- |
| test_01_login.py                 | Login and logout                                     | 15      |
| test_02_navigation.py            | Side menu and breadcrumb                             | 10      |
| test_03_dashboard.py             | Dashboard                                            | 8       |
| test_04_ticket_list.py           | Enquiries and Complaints lists                       | 22      |
| test_05_ticket_filter.py         | Filtering the ticket list                            | 11      |
| test_06_ticket_detail.py         | Ticket detail screen                                 | 21      |
| test_06a_investigation.py        | Investigation & Resolution tab                       | 11      |
| test_06b_customer_records.py     | Customer & Records tab, customer history             | 13      |
| test_07_kanban.py                | Kanban board                                         | 13      |
| test_07a_sla.py                  | SLA tab                                              | 10      |
| test_07b_escalation.py           | Manual escalation                                    | 3       |
| test_08_create_ticket.py         | Manual ticket creation                               | 22      |
| test_08b_reply_lifecycle.py      | Ticket lifecycle via replies                         | 10      |
| test_08c_conditional_fields.py   | Conditional fields on create/edit forms              | 9       |
| test_09_form_validation.py       | Form validation messages                             | 9       |
| test_10_modal_form_validation.py | Pop-up form validation                               | 5       |
| test_12_discarded.py             | Discarded queue                                      | 6       |
| test_13_admin.py                 | Users, roles and permissions                         | 12      |
| test_13a_notification.py         | Notification bell                                    | 11      |
| test_14_reports_audit.py         | Reports, audit trail, ticket history                 | 18      |
| test_15_role_access.py           | Access control                                       | 9       |
| test_15_role_matrix.py           | Every role vs every screen and action                | 98      |
| test_16_department_isolation.py  | Dept POC sees only own department                    | 8       |
| test_17_role_scope.py            | Which tickets each role can see                      | 8       |
| test_18_fixed_bug_regression.py  | Bugs already fixed                                   | 5       |
| test_19_uat_regression.py        | Reopened UAT items (U11, U12/U17, U15, U16, U22/U24) | 18      |
| test_20_admin_config.py          | Phase 2 admin/config screens                         | 27      |
| **Total**                        |                                                      | **412** |

---

## 7. When a test fails

1. Read the assertion message and the page URL printed in the output.
2. Open the screenshot in the `screenshots/` folder (one is saved for every failure).
3. Check the address printed at the start of the run - make sure you ran against the site you meant.
4. Re-run just that test: `pytest --env=deployed -k "<test name>"`.
5. If the smoke run also fails, the site or your network is probably down, not the test.

---

## 8. Adding a new test

1. If you need a new locator or action, add it to the right file in `awnic_qa/pages/`.
2. Write the test in the right file in `tests/` - open the page, do the action, `assert` the result.
3. Do not put locators directly in test files.
4. Add markers (at least `regression`, a phase and a priority).
5. If the test creates or changes data, mark it `@pytest.mark.write`.
6. Do not use `time.sleep()` - use the wait helpers in `awnic_qa/pages/base_page.py`.
7. Check it is picked up: `pytest --collect-only -q --env=deployed`.

Useful helpers:

- `BasePage.clear_box()` to empty a text box (plain `clear()` does not work on this app's inputs).
- `BaseTest.drag_card()` to drag a card on the Kanban board.
- The dashboard is at `/`, not `/dashboard`.
- `/webform-test` is public on purpose (no login needed).
