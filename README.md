# AWNIC Case Management - UI Automation (Selenium + Python)

Browser tests for the AWNIC Case Management web app. The tests open Chrome, sign in as
different AWNIC users, and check the screens the way a user would.

This repository contains **only the tests**. The application itself lives in a separate
repository (`awinc-case-management`). You do not need that repository to run these tests
against the shared UAT site.

---

## 1. What you need

| Tool | Version | Check with |
| --- | --- | --- |
| Python | 3.11 or newer | `python3 --version` |
| Google Chrome | any recent version | open Chrome > About |
| Git | any | `git --version` |

- You do **not** need to download ChromeDriver. Selenium downloads the right one on the first run.
- Your network must be able to reach the UAT site: https://twu3nrmnmv.eu-west-1.awsapprunner.com

---

## 2. Setup (one time)

**macOS / Linux**

```bash
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

| File | Used when | Points to |
| --- | --- | --- |
| `config/config.deployed.properties` | you add `--env=deployed` | the shared UAT site |
| `config/config.properties` | you add nothing (default) | the app running on your own laptop (`http://localhost:3200`) |

Main settings in each file:

| Setting | Meaning |
| --- | --- |
| `baseUrl` | the website address the tests open |
| `timeoutSeconds` | how long to wait for a page or element |
| `headless` | `true` = run Chrome without a window |
| `adminEmail`, `agentEmail`, `hodEmail`, `managerEmail`, `supervisorEmail`, `complaintHandlerEmail`, `complianceEmail`, `deptPocEmail` | the test account used for each role |
| `writeTestsEnabled` | `false` = tests that create or change data are skipped (keep it `false` on UAT) |
| `missingAccountsAreSkipped` | `true` = if a role's account does not exist, its tests are skipped instead of failing |

You can change one setting for a single run with `-D`, without editing the file:

```bash
pytest --env=deployed -D headless=true
```

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

Only needed if you are developing the app. Start the app from the `awinc-case-management`
repository first (API on port 8010, web app on port 3200 - see that repository's README), then:

```bash
pytest -m smoke
```

The first visit to each page of a local dev server can take up to 40 seconds. That is normal.
If your web app uses another port: `pytest -D baseUrl=http://localhost:3300`.

---

## 5. Test groups (markers)

Each test has labels, so you can choose what to run with `-m`.

| Marker | Meaning |
| --- | --- |
| `smoke` | small "is the app working?" check |
| `sanity` | main areas, one check each |
| `regression` | the full protection suite |
| `phase1` / `phase2` | which project phase the feature belongs to |
| `p0` / `p1` / `p2` | priority (p0 = most important) |
| `blocked` | cannot run yet (for example, no account exists for that role). 29 tests. Shows the reason. |
| `quarantine` | a known defect - expected to fail until the app is fixed |
| `write` | changes data - skipped unless `writeTestsEnabled=true` |

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

| File | Area | Tests |
| --- | --- | --- |
| test_01_login.py | Login and logout | 15 |
| test_02_navigation.py | Side menu and breadcrumb | 10 |
| test_03_dashboard.py | Dashboard | 8 |
| test_04_ticket_list.py | Enquiries and Complaints lists | 22 |
| test_05_ticket_filter.py | Filtering the ticket list | 11 |
| test_06_ticket_detail.py | Ticket detail screen | 21 |
| test_06a_investigation.py | Investigation & Resolution tab | 11 |
| test_06b_customer_records.py | Customer & Records tab, customer history | 13 |
| test_07_kanban.py | Kanban board | 13 |
| test_07a_sla.py | SLA tab | 10 |
| test_07b_escalation.py | Manual escalation | 3 |
| test_08_create_ticket.py | Manual ticket creation | 22 |
| test_08b_reply_lifecycle.py | Ticket lifecycle via replies | 10 |
| test_08c_conditional_fields.py | Conditional fields on create/edit forms | 9 |
| test_09_form_validation.py | Form validation messages | 9 |
| test_10_modal_form_validation.py | Pop-up form validation | 5 |
| test_12_discarded.py | Discarded queue | 6 |
| test_13_admin.py | Users, roles and permissions | 12 |
| test_13a_notification.py | Notification bell | 11 |
| test_14_reports_audit.py | Reports, audit trail, ticket history | 18 |
| test_15_role_access.py | Access control | 9 |
| test_15_role_matrix.py | Every role vs every screen and action | 98 |
| test_16_department_isolation.py | Dept POC sees only own department | 8 |
| test_17_role_scope.py | Which tickets each role can see | 8 |
| test_18_fixed_bug_regression.py | Bugs already fixed | 5 |
| test_19_uat_regression.py | Reopened UAT items (U11, U12/U17, U15, U16, U22/U24) | 18 |
| test_20_admin_config.py | Phase 2 admin/config screens | 27 |
| **Total** | | **412** |

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
