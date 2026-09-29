"""
Starting and stopping Chrome.

Kept apart from BaseTest so that "how is the browser configured" is one short file. Every
flag below was added because a real run failed without it - see the notes on each.
"""

from __future__ import annotations

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from awnic_qa.config import Config

#: How many times to try opening Chrome before giving up. See start_driver().
DRIVER_START_ATTEMPTS = 3


def chrome_options() -> Options:
    """
    Builds the Chrome settings the suite runs with.

    WHY SO MANY FLAGS? A run of this suite lasts over two hours and opens fifteen browsers
    one after another. In the 2026-09-03 run Chrome ran out of shared memory part way
    through, the renderer stopped answering ("Unable to receive message from renderer"), and
    every class after that point could not start a browser at all - 85 of the 90 skipped
    tests came from that ONE crash, not from anything the product did. The flags below
    remove the causes of that crash:

      --disable-dev-shm-usage    Chrome's default /dev/shm is small; when it fills, the
                                 renderer is killed. This puts the same data in /tmp.
      --no-sandbox               the sandbox needs resources this crash had exhausted.
      --disable-gpu              nothing here renders 3D; the GPU process is one more thing
                                 that can die and take the session with it.
      --disable-extensions       a clean profile every time, nothing else running.
      the three throttling flags Chrome slows down or suspends a window it thinks is in the
                                 background. Headless windows always look backgrounded, which
                                 makes a 30-second poll (the notification bell) stop firing
                                 and the test wait for something that will never come.
    """
    options = Options()
    if Config.get_bool("headless"):
        options.add_argument("--headless=new")
    # A wide window on purpose: the ticket table is 18 columns (min-width 2400px), the
    # Kanban board is four columns side by side, and the notification panel is clipped
    # below about 800px. A small window hides elements the tests assert on.
    options.add_argument("--window-size=1600,1000")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    return options


def start_driver() -> tuple[webdriver.Chrome, WebDriverWait]:
    """
    Opens a browser, trying up to three times.

    Starting Chrome is itself something that can fail on a busy machine - the driver server
    has a fixed startup timeout, and when the previous class's browser is still shutting down
    the new one can miss it ("request timed out"). Trying again after a short wait turns that
    into a slower start instead of a whole class of skipped tests.
    """
    last_failure: Exception | None = None
    for attempt in range(1, DRIVER_START_ATTEMPTS + 1):
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options())
            # ONE explicit wait, reused everywhere. Deliberately NO implicit wait: mixing
            # the two makes waiting times unpredictable and very hard to debug.
            wait = WebDriverWait(driver, Config.get_int("timeoutSeconds"))
            return driver, wait
        except Exception as could_not_start:  # noqa: BLE001 - any driver failure is retried
            last_failure = could_not_start
            print(
                f"Chrome did not start (attempt {attempt} of {DRIVER_START_ATTEMPTS}): "
                f"{could_not_start}"
            )
            quietly_quit(driver)
            time.sleep(5)
    raise RuntimeError(
        f"Could not start Chrome after {DRIVER_START_ATTEMPTS} attempts"
    ) from last_failure


def quietly_quit(driver) -> None:
    """
    Closes the browser and never raises.

    quit() on a session that has ALREADY died raises "Timed out waiting for driver server to
    stop", which pytest reports as a second error on top of the real one - two red lines for
    one problem, and the second one tells you nothing. There is nothing useful to do about a
    browser that is already gone, so this swallows it.
    """
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:  # noqa: BLE001 - the browser we wanted to close has closed itself
        pass


def is_driver_alive(driver) -> bool:
    """A cheap round trip to the browser. False means the session is gone."""
    if driver is None:
        return False
    try:
        driver.current_url
        return True
    except Exception:  # noqa: BLE001 - session is gone
        return False
