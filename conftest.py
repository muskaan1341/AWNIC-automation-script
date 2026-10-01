"""
Suite-wide setup: command-line options, loading the settings, and opening/closing the browser.

    pytest                      -> uses config/config.properties
    pytest --env=deployed       -> uses config/config.deployed.properties
    pytest -D headless=true     -> overrides one setting
"""

import logging
import re
import sys
import time
from pathlib import Path

import pytest
from selenium.common.exceptions import WebDriverException

# Failure screenshots are saved here (the folder is gitignored).
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"

# The suite's logger. Never log a password or token.
LOG = logging.getLogger("awnic_qa")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from awnic_qa import driver as driver_module  # noqa: E402
from awnic_qa.base_test import BaseTest  # noqa: E402
from awnic_qa.config import Config  # noqa: E402


# ----------------------------------------------------------------------
# Command-line options
# ----------------------------------------------------------------------


def pytest_addoption(parser):
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


def pytest_configure(config):
    overrides = {}
    for pair in config.getoption("setting_overrides"):
        if "=" not in pair:
            raise pytest.UsageError(f"-D expects KEY=VALUE, got {pair!r}")
        key, _, value = pair.partition("=")
        overrides[key.strip()] = value.strip()

    env = config.getoption("--env")
    if env == "local":
        env = None
    Config.load(env=env, overrides=overrides)


def pytest_collection_modifyitems(config, items):
    """Skips every `blocked` test unless the run asks for them with -m "...blocked...".

    Blocked tests cannot run safely or usefully here yet (for example a Kanban drag that
    could move a real ticket on shared UAT). Skipping them by default makes the simple
    command `pytest --env=deployed -m regression` safe.
    """
    if "blocked" in (config.getoption("markexpr") or ""):
        return
    for item in items:
        marker = item.get_closest_marker("blocked")
        if marker is not None:
            reason = marker.args[0] if marker.args else "no reason given"
            item.add_marker(pytest.mark.skip(
                reason=f"Blocked ({reason}) - not run by default. Run it on purpose with -m blocked."
            ))


# ----------------------------------------------------------------------
# The browser
# ----------------------------------------------------------------------


@pytest.fixture(scope="class", autouse=True)
def browser(request):
    """
    One browser per test class: opened before the first test, closed after the last.
    Per class (not per test) because the sign-in endpoint allows only 10 requests a minute.
    """
    cls = request.cls
    if cls is None or not issubclass(cls, BaseTest):
        # Not a UI test class - nothing to open.
        yield None
        return

    cls.base_url = Config.get("baseUrl")
    print(f"\nRunning against {cls.base_url}  (settings: {Config.file_name})")

    cls.driver, cls.wait = driver_module.start_driver()
    cls.build_page_objects()
    cls.signed_in_as = None

    yield cls.driver

    # Runs even if a test crashed, so no Chrome process is left behind.
    driver_module.quietly_quit(cls.driver)
    cls.driver = None


# ----------------------------------------------------------------------
# On failure: save a screenshot and log the page URL
# ----------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Saves each phase's result (report_setup / report_call) on the test, for the fixture below."""
    outcome = yield
    setattr(item, f"report_{call.when}", outcome.get_result())


@pytest.fixture(autouse=True)
def capture_evidence_on_failure(request):
    """After a failed test, saves a PNG and logs the URL. Never fails the test itself."""
    yield

    report = getattr(request.node, "report_call", None)
    if report is None:
        report = getattr(request.node, "report_setup", None)
    if report is None or not report.failed:
        return

    driver = getattr(request.cls, "driver", None)
    if not driver_module.is_driver_alive(driver):
        LOG.warning("%s failed, but the browser was gone - no screenshot.", request.node.name)
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)[:120]
    path = SCREENSHOT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{safe_name}.png"
    try:
        driver.save_screenshot(str(path))
        LOG.error("FAILED %s | url=%s | screenshot=%s", request.node.name, driver.current_url, path)
    except WebDriverException as error:
        LOG.warning("Could not screenshot %s: %s", request.node.name, error)


@pytest.fixture(autouse=True)
def ensure_browser_alive(request, browser):
    """Before every test: if the browser has died, start a new one and sign back in."""
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
