"""
Suite-wide wiring: the command line, the settings, and the browser lifecycle.

WHAT REPLACED WHAT
    TestNG                          pytest
    ------------------------------  ----------------------------------------
    @BeforeClass openBrowser        the class-scoped `browser` fixture below
    @AfterClass  closeBrowser       the same fixture's teardown
    @BeforeMethod ensureBrowserAlive the function-scoped fixture below
    mvn test -Denv=deployed         pytest --env=deployed
    mvn test -Dheadless=true        pytest -D headless=true
    testng.xml ordering             the numbered test files (see tests/README.md)
"""

from __future__ import annotations

import logging
import re
import sys
import time
from pathlib import Path

import pytest
from selenium.common.exceptions import WebDriverException

#: Where failure screenshots land. Gitignored - see .gitignore in this folder.
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"

#: One logger for the suite. Business steps go through this rather than print(), so a CI run
#: has timestamps and levels instead of bare lines, and a failure can be found by grepping for
#: ERROR. Never log an email password or token - the dev login has neither, and it must stay
#: that way if real credentials ever arrive.
LOG = logging.getLogger("awnic_qa")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from awnic_qa import driver as driver_module  # noqa: E402
from awnic_qa.base_test import BaseTest  # noqa: E402
from awnic_qa.config import Config  # noqa: E402


# ======================================================================
# The command line
# ======================================================================


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default="local",
        choices=["local", "deployed"],
        help="Which settings file to read: local (your laptop) or deployed (the AWS site).",
    )
    parser.addoption(
        "-D",
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        dest="setting_overrides",
        help="Override one setting, e.g. -D headless=true. Repeatable. Wins over the file.",
    )


def pytest_configure(config: pytest.Config) -> None:
    overrides: dict[str, str] = {}
    for pair in config.getoption("setting_overrides"):
        if "=" not in pair:
            raise pytest.UsageError(f"-D expects KEY=VALUE, got {pair!r}")
        key, _, value = pair.partition("=")
        overrides[key.strip()] = value.strip()

    env = config.getoption("--env")
    Config.load(env=None if env == "local" else env, overrides=overrides)


# ======================================================================
# The browser
# ======================================================================


@pytest.fixture(scope="class", autouse=True)
def browser(request):
    """
    One browser per test class - opened before the first test, closed after the last.

    WHY PER CLASS AND NOT PER TEST: the sign-in endpoint is rate limited to 10 requests a
    minute per IP address. A fresh browser and login for every test method would trip that
    limit part way through a run and produce failures that say nothing about the product.
    """
    cls = request.cls
    if cls is None or not issubclass(cls, BaseTest):
        # A plain function-style test, or something that is not part of the UI suite.
        yield None
        return

    cls.base_url = Config.get("baseUrl")
    # Say out loud where this run is pointed. Nothing wastes more time than reading a
    # failure carefully and only then realising the tests were hitting the wrong site.
    print(f"\nRunning against {cls.base_url}  (settings: {Config.file_name})")

    cls.driver, cls.wait = driver_module.start_driver()
    cls.build_page_objects()
    cls.signed_in_as = None

    yield cls.driver

    # Always run, so a crashed test still closes its browser instead of leaving an orphan
    # Chrome process behind.
    driver_module.quietly_quit(cls.driver)
    cls.driver = None


# ======================================================================
# When something fails: a screenshot and the page's address
# ======================================================================


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Records each phase's outcome on the test item so the fixture below can see it.

    pytest does not otherwise tell a fixture whether its test passed - the report exists
    only inside the hook - so this is the documented way to make that fact available at
    teardown, which is the only moment a screenshot is still worth taking.
    """
    outcome = yield
    setattr(item, f"report_{call.when}", outcome.get_result())


@pytest.fixture(autouse=True)
def capture_evidence_on_failure(request):
    """
    On failure, saves a PNG and logs the URL that produced it.

    WHY THIS IS WORTH THE FEW LINES. A failure message says what was expected; it cannot say
    what the screen actually looked like, and against a shared environment that difference is
    usually the whole investigation - a modal still open, a toast covering the control, a row
    that never arrived. The URL is logged alongside because a screenshot of a ticket page
    without its id is much less useful than it looks.

    Never fails a test on its own account: a browser that has already died cannot be
    photographed, and reporting THAT on top of the real failure would bury it.
    """
    yield
    report = getattr(request.node, "report_call", None) or getattr(request.node, "report_setup", None)
    if report is None or not report.failed:
        return
    driver = getattr(request.cls, "driver", None)
    if not driver_module.is_driver_alive(driver):
        LOG.warning("%s failed, but the browser was gone - no screenshot.", request.node.name)
        return
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)[:120]
    path = SCREENSHOT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{safe}.png"
    try:
        driver.save_screenshot(str(path))
        LOG.error("FAILED %s | url=%s | screenshot=%s", request.node.name, driver.current_url, path)
    except WebDriverException as could_not_capture:
        LOG.warning("Could not screenshot %s: %s", request.node.name, could_not_capture)


@pytest.fixture(autouse=True)
def ensure_browser_alive(request, browser):
    """
    Makes sure there is a WORKING browser before every single test.

    This is the safety net the 2026-09-03 run needed and did not have. When a browser dies
    mid-class, every later test in that class - and in the 2026-09-03 run, every later CLASS
    - failed with "invalid session id" or "request timed out", none of which says anything
    about the application. Now a dead session is simply replaced and the test carries on.
    The sign-in is redone too, because a new browser has no cookies.
    """
    cls = request.cls
    if cls is None or not issubclass(cls, BaseTest) or browser is None:
        yield
        return

    if not driver_module.is_driver_alive(cls.driver):
        print("The browser had died. Starting a fresh one and signing back in.")
        was_signed_in_as = cls.signed_in_as
        driver_module.quietly_quit(cls.driver)
        cls.driver, cls.wait = driver_module.start_driver()
        cls.build_page_objects()
        cls.signed_in_as = None
        if was_signed_in_as is not None:
            request.instance.login_as(was_signed_in_as)

    yield
