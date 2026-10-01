# AWNIC Case Management - UI Tests (Selenium + Python)

These tests open Chrome, sign in as different AWNIC users, and check the screens of the AWNIC
Case Management web app - the same way a person would.

This repository contains **only the tests**. The app itself lives in another repository
(`awinc-case-management`). You don't need it to run the tests against the shared UAT site.

---

## Quick start (5 minutes)

```bash
# 1. Get the code
git clone https://github.com/muskaan1341/AWNIC-automation-script.git
cd AWNIC-automation-script

# 2. Create a Python environment and install the packages (one time)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Run the smoke tests against UAT
pytest --env=deployed -m smoke
```

Expected result: **`25 passed`** (about 6 minutes). If that works, your setup is done.

> Every time you open a new terminal, run `source .venv/bin/activate` again before `pytest`.

---

## 1. What you need


| Tool          | Version                             |
| --------------- | ------------------------------------- |
| Python        | 3.11 or newer (`python3 --version`) |
| Google Chrome | any recent version                  |
| Git           | any                                 |

- You do **not** need to download ChromeDriver - Selenium gets the right one automatically.
- Your network must reach the UAT site: [https://twu3nrmnmv.eu-west-1.awsapprunner.com](https://twu3nrmnmv.eu-west-1.awsapprunner.com)

---

## 2. How to run the tests

Always run from the repository folder, with the environment activated.


| I want to...                         | UAT site (deployed)                                     | laptop /local system(localhost)               |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------- |
| Quick check that the app works       | `pytest --env=deployed -m smoke`                        | `pytest -m smoke`                             |
| Check every main area once           | `pytest --env=deployed -m sanity`                       | `pytest -m sanity`                            |
| Run the full regression              | `pytest --env=deployed -m "regression and not blocked"` | `pytest -m "regression and not blocked"`      |
| Run one file                         | `pytest --env=deployed tests/test_07_kanban.py`         | `pytest tests/test_07_kanban.py`              |
| Run tests whose name contains a word | `pytest --env=deployed -k "kanban"`                     | `pytest -k "kanban"`                          |
| Run without a Chrome window          | add `-D headless=true`                                   | add `-D headless=true`                         |
| Save an HTML report                  | add `--html=report.html --self-contained-html`           | add `--html=report.html --self-contained-html` |
| Only list the tests (no browser)     | `pytest --collect-only -q --env=deployed`               | `pytest --collect-only -q`                    |
| Web app on a different port          | -                                                       | add `-D baseUrl=http://localhost:3300`         |

- **UAT:** add `--env=deployed`. It uses `config/config.deployed.properties`.
- **Localhost:** add nothing. It uses `config/config.properties` and opens
  `http://localhost:3200`. The app must be running first (see section 2a below).

### Rules for the shared UAT site

1. **Never run two test runs at the same time.** Sign-in allows only 10 logins per minute;
   two runs together cause false failures.
2. **Never turn on `writeTestsEnabled` on UAT.** All tests only *look* at the app. The 3 tests
   that would change data are switched off by default.
3. Other people use UAT too, so data changes. When a test needs data that isn't there, it
   **skips** and prints why. A skip is not a failure.

---

## 2a. Localhost setup (only if you want to test the app on your laptop)

For localhost the tests need the **app itself** running on your laptop. The app is in a
different repository: `awinc-case-management`. Ask the dev team for access to it.

**You need:** Python 3.12, Node.js (with npm), Git, and the `apps/api/.env` values from the dev
team (database address and keys - they are secrets, so they are not written here).

### Step 1 - Start the API (port 8010)

Open a terminal:

```bash
cd awinc-case-management/apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"            # one time
```

Create the file `apps/api/.env` with the values the dev team gives you. It must also contain:

```text
DEV_LOGIN_ENABLED=true
```

This turns on the email-only test login the tests use. Then start the API:

```bash
uvicorn app.main:app --reload --port 8010
```

Leave this terminal open.

### Step 2 - Start the web app (port 3200)

Open a second terminal:

```bash
cd awinc-case-management/apps/web
npm install                        # one time, and again after pulling new code
cp .env.example .env.local         # one time
npm run dev
```

`.env.local` must contain `NEXT_PUBLIC_API_URL=http://localhost:8010` and
`NEXT_PUBLIC_DEV_LOGIN_ENABLED=true` (the example file already has both).

Leave this terminal open too.

### Step 3 - Check the app works

Open [http://localhost:3200](http://localhost:3200) in Chrome and sign in with `admin@awnic.ae`. If you see the admin
dashboard, the app is ready.

### Step 4 - Run the tests

In a third terminal, inside this repository:

```bash
source .venv/bin/activate
pytest -m smoke
```

### Good to know

- **The first visit to each page is slow** (up to about a minute) because the dev server
  builds the page. That is normal; the local wait time is 60 seconds for this reason. The
  second run is much faster.
- **Which data you see depends on the database in `apps/api/.env`.** If it points to the UAT
  database, the accounts in `config/config.properties` work as they are. If you use a fresh
  local database instead, those accounts won't exist - change the emails in
  `config/config.properties` to accounts that exist in your database.
- **Keep `writeTestsEnabled = false`** - if your API uses the UAT database, a "write" test would
  change real UAT data.
- **"localhost refused to connect"** means the API or web app is not running - check both
  terminals.

---

## 3. Settings

Settings live in the `config/` folder. There are **no passwords** - the test login only needs an
email address.


| File                                | Used when               | Opens                   |
| ------------------------------------- | ------------------------- | ------------------------- |
| `config/config.deployed.properties` | you add `--env=deployed` | the UAT site            |
| `config/config.properties`          | you add nothing         | `http://localhost:3200` |


| Setting                     | Meaning                                                    |
| ----------------------------- | ------------------------------------------------------------ |
| `baseUrl`                   | the website address the tests open                         |
| `timeoutSeconds`            | how long to wait for a page (UAT 20, local 60)             |
| `headless`                  | `true` = no Chrome window                                  |
| `writeTestsEnabled`         | keep`false` - `true` lets 3 tests change real data         |
| `missingAccountsAreSkipped` | `true` = if a role's account doesn't exist, its tests skip |

Change one setting for one run, without editing the file: `-D headless=true`

### Test accounts (one per role)

Both settings files use the same accounts. All are active and hold exactly one role
(checked 1 Oct 2026).


| Setting                 | Account                       | Role                                                                  |
| ------------------------- | ------------------------------- | ----------------------------------------------------------------------- |
| `adminEmail`            | `admin@awnic.ae`              | Admin                                                                 |
| `ccInitiatorEmail`      | `a_hassouna@awnic.com`        | CC Initiator                                                          |
| `supervisorEmail`       | `supervisor-gen@awnic.com`    | CC Supervisor                                                         |
| `complaintHandlerEmail` | `complaints.officer@awnic.ae` | Complaint Handler                                                     |
| `hodEmail`              | `v_mertia@awnic.com`          | Head of Department (Broker & Motor Underwriting)                      |
| `managerEmail`          | `c_chiong@awnic.com`          | Manager (Business Support)                                            |
| `deptPocEmail`          | `a_shalaby@awnic.com`         | Dept POC (Medical Operations)                                         |
| `complianceEmail`       | `compliance@awnic.ae`         | Compliance Officer -**account does not exist yet**, so its tests skip |

To use a different person for a role, change the email in the settings file **and** add that
email to `_KNOWN_ACCOUNTS` in `awnic_qa/users.py` (name, role, department). Pick someone who is
active and has signed in before.

Never use `dev@awnic.ae` - it is reserved.

---

## 4. Test groups

Every test has labels (markers). Use `-m` to choose which ones run.


| Marker                       | Meaning                                                          | Tests    |
| ------------------------------ | ------------------------------------------------------------------ | ---------- |
| `smoke`                      | "is the app working?" - quick check                              | 25       |
| `sanity`                     | each main area once (includes smoke)                             | 67       |
| `regression`                 | the full suite                                                   | 387      |
| `regression and not blocked` | the full run you can actually execute                            | 359      |
| `phase1` / `phase2`          | which project phase the feature belongs to                       | 357 / 55 |
| `p0` / `p1` / `p2`           | priority (p0 = most important)                                   |          |
| `blocked`                    | can't run yet (e.g. no account for that role) - shows the reason | 29       |
| `quarantine`                 | a known app defect - expected to fail until it is fixed          | 11       |
| `write`                      | changes data - always skipped unless`writeTestsEnabled=true`     | 3        |

**Total: 412 tests.** The full list of markers is in `pytest.ini`.

---

## 5. What is tested


| File                             | Area                                                                | Tests |
| ---------------------------------- | --------------------------------------------------------------------- | ------- |
| test_01_login.py                 | Login and logout                                                    | 15    |
| test_02_navigation.py            | Side menu and breadcrumb                                            | 10    |
| test_03_dashboard.py             | Dashboard                                                           | 8     |
| test_04_ticket_list.py           | Enquiries and Complaints lists                                      | 22    |
| test_05_ticket_filter.py         | Filtering the lists                                                 | 11    |
| test_06_ticket_detail.py         | Ticket detail screen                                                | 21    |
| test_06a_investigation.py        | Investigation & Resolution tab                                      | 11    |
| test_06b_customer_records.py     | Customer records and customer history                               | 13    |
| test_07_kanban.py                | Kanban board                                                        | 13    |
| test_07a_sla.py                  | SLA tab                                                             | 10    |
| test_07b_escalation.py           | Manual escalation                                                   | 3     |
| test_08_create_ticket.py         | Creating a ticket, CC Initiator picker                              | 22    |
| test_08b_reply_lifecycle.py      | Ticket lifecycle through replies                                    | 10    |
| test_08c_conditional_fields.py   | Fields that appear only in some cases                               | 9     |
| test_09_form_validation.py       | Form error messages                                                 | 9     |
| test_10_modal_form_validation.py | Pop-up form validation                                              | 5     |
| test_12_discarded.py             | Discarded tickets                                                   | 6     |
| test_13_admin.py                 | Users, roles, Activity Log                                          | 12    |
| test_13a_notification.py         | Notification bell                                                   | 11    |
| test_14_reports_audit.py         | Reports and audit trail                                             | 18    |
| test_15_role_access.py           | Who can open what                                                   | 9     |
| test_15_role_matrix.py           | Every role against every screen and action                          | 98    |
| test_16_department_isolation.py  | Dept POC sees only their own department                             | 8     |
| test_17_role_scope.py            | Which tickets each role sees                                        | 8     |
| test_18_fixed_bug_regression.py  | Bugs that were fixed                                                | 5     |
| test_19_uat_regression.py        | UAT feedback items (U11, U12, U15, U16, U22)                        | 18    |
| test_20_admin_config.py          | Teams & SLA, escalation ladder, historical archive, System Settings | 27    |

---

## 6. Folder structure

```
AWNIC-automation-script/
├── config/           settings for UAT and local runs
├── awnic_qa/
│   ├── pages/        one file per screen: where things are + what you can do there
│   ├── base_test.py  shared test steps (sign in, open a page, ...)
│   ├── users.py      the test accounts and their roles
│   └── customers.py  test customer numbers (Data Mart test data)
├── tests/            the tests, numbered in the order they run
├── tools/            extra QA scripts (not needed to run the tests)
├── conftest.py       starts and closes Chrome, reads settings, screenshots on failure
├── pytest.ini        markers and pytest options
└── requirements.txt  Python packages
```

---

## 7. When a test fails

1. Read the failure message - it says what was expected and what was found.
2. Open the screenshot in `screenshots/` (one is saved for every failure).
3. Check the address printed at the start of the run - did you test the site you meant?
4. Run just that test again: `pytest --env=deployed -k "<test name>"`
5. If smoke also fails, the site or your network is probably down - not the test.


| Problem                                              | Fix                                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------------------ |
| Every test fails with "localhost refused to connect" | You forgot `--env=deployed`                                             |
| `No module named pytest` / `selenium`                | Run `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| `Missing required plugins: pytest-timeout` or `Unknown config option: timeout` | You ran a pytest that is not this project's. Run `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| Chrome does not open                                 | Install Google Chrome; the first run also needs internet               |
| Many sign-in failures at once                        | Someone else is running the tests on UAT - wait and run again          |

---

## 8. Adding a new test

1. Put locators and actions in the right file under `awnic_qa/pages/` (never in the test file).
2. Write the test in the right file under `tests/`: open the page, do the action, `assert` the
   result.
3. Add markers: `regression`, a phase (`phase1`/`phase2`) and a priority (`p0`/`p1`/`p2`).
   Add `smoke`/`sanity` only for quick, important checks (a smoke test must also be sanity).
4. If the test changes data, mark it `@pytest.mark.write` and call `self.require_write_tests()`.
5. Don't use `time.sleep()` - use the wait helpers in `awnic_qa/pages/base_page.py`.
6. Check it is picked up: `pytest --collect-only -q --env=deployed`

Helpful to know:

- Use `clear_box()` to empty a text box (plain `clear()` doesn't work on this app).
- Use `drag_card()` to drag a card on the Kanban board.
- The dashboard is at `/`, not `/dashboard`.
- `/webform-test` is public on purpose (no login needed).

---

## 9. Known issues (1 Oct 2026)


| Issue                                                                                                               | Effect on the tests                               |
| --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| System Settings (`/admin/settings`) shows "Something went wrong" on UAT - the ticket-numbering API returns an error | 1 test is quarantined (`SETTINGS-500`)            |
| No account has the Compliance Officer role                                                                          | Compliance Officer tests skip                     |
| Right now no CC Initiator is paused, at the daily limit or deactivated, and the historical archive is empty         | Those picker and archive tests skip with a reason |
| The complaint handler has no complaint assigned                                                                     | Its "own complaints" tests skip                   |
