"""
Starting and stopping Chrome.
"""

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from awnic_qa.config import Config

# How many times to try opening Chrome before giving up.
DRIVER_START_ATTEMPTS = 3


def chrome_options():
    """The Chrome settings the suite runs with. These flags keep Chrome stable on long runs."""
    options = Options()
    if Config.get_bool("headless"):
        options.add_argument("--headless=new")
    # Wide window: the ticket table and Kanban board are wide and hide columns in a small window.
    options.add_argument("--window-size=1600,1000")
    # Stop Chrome running out of shared memory and crashing part way through a run.
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    # Headless windows look "in the background"; stop Chrome slowing down their timers.
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    return options


def start_driver():
    """Opens a browser (trying up to 3 times) and returns (driver, wait)."""
    last_failure = None
    for attempt in range(1, DRIVER_START_ATTEMPTS + 1):
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options())
            # One explicit wait used everywhere. No implicit wait on purpose.
            wait = WebDriverWait(driver, Config.get_int("timeoutSeconds"))
            return driver, wait
        except Exception as error:  # noqa: BLE001 - any start-up failure is retried
            last_failure = error
            print(f"Chrome did not start (attempt {attempt} of {DRIVER_START_ATTEMPTS}): {error}")
            quietly_quit(driver)
            time.sleep(5)
    raise RuntimeError(
        f"Could not start Chrome after {DRIVER_START_ATTEMPTS} attempts"
    ) from last_failure


def quietly_quit(driver):
    """Closes the browser. Never raises, even if the browser has already died."""
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:  # noqa: BLE001 - the browser is already gone
        pass


def is_driver_alive(driver):
    """True if the browser still answers."""
    if driver is None:
        return False
    try:
        driver.current_url
        return True
    except Exception:  # noqa: BLE001 - session is gone
        return False
