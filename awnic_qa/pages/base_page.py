"""
The parent of every page object. Holds the small helpers every page needs:
click(), type_into(), exists(), choose_option(), and so on.

A locator is a (By.<strategy>, "value") tuple, passed to Selenium as *locator.
Never use time.sleep - wait for a condition instead.
"""

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

# A locator: (By.XPATH, "//button"). Other page files import this name.
Locator = tuple[str, str]

_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWER = "abcdefghijklmnopqrstuvwxyz"


class BasePage:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    # ------------------------------------------------------------------
    # Locator builders
    # ------------------------------------------------------------------

    @staticmethod
    def button(text):
        """A <button> whose visible text is exactly this."""
        return (By.XPATH, f"//button[normalize-space()='{text}']")

    @staticmethod
    def link(text):
        """An <a> link whose visible text is exactly this."""
        return (By.XPATH, f"//a[normalize-space()='{text}']")

    @staticmethod
    def exact_text(text):
        """Any element whose own text is exactly this."""
        return (By.XPATH, f"//*[normalize-space(text())='{text}']")

    @staticmethod
    def text_ignoring_case(text):
        """Any element whose own text is this, ignoring case (some titles are CSS-uppercased)."""
        return (
            By.XPATH,
            f"//*[normalize-space(translate(text(),'{_UPPER}','{_LOWER}'))='{text.lower()}']",
        )

    @staticmethod
    def innermost_containing(text):
        """The innermost element containing this text (not its wrappers)."""
        return (
            By.XPATH,
            f'//*[contains(normalize-space(.),"{text}")'
            f' and not(.//*[contains(normalize-space(.),"{text}")])]',
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    # How many times click_without_scrolling() retries a blocked click.
    CLICK_ATTEMPTS = 3

    # JavaScript that says what element is on top of the given element's centre.
    _BLOCKER_SCRIPT = r"""
        const box = arguments[0].getBoundingClientRect();
        const top = document.elementFromPoint(
            box.left + box.width / 2, box.top + box.height / 2);
        if (!top) return "OUTSIDE_WINDOW";
        if (top === arguments[0] || arguments[0].contains(top)) return "";
        const cls = typeof top.className === "string" ? top.className.trim() : "";
        return top.tagName.toLowerCase()
            + (top.id ? "#" + top.id : "")
            + (cls ? "." + cls.split(/\s+/).slice(0, 4).join(".") : "");
    """

    def click(self, locator, scroll=True):
        """
        Waits for toasts to clear, scrolls the element to the middle, then clicks it.
        Pass scroll=False for options inside an open dropdown - the panel moves when the
        page scrolls.
        """
        self.wait_for_toasts_to_clear()
        if scroll:
            element = self.wait.until(EC.element_to_be_clickable(locator))
            self.scroll_to_middle(element)
        self.click_without_scrolling(locator)

    def click_without_scrolling(self, locator):
        """
        Clicks the element, finding it again on each try (up to CLICK_ATTEMPTS).
        Between tries it waits for toasts to clear. If it still fails, the error says what
        was covering the element.
        """
        last_failure = None
        for _ in range(self.CLICK_ATTEMPTS):
            try:
                self.wait.until(EC.element_to_be_clickable(locator)).click()
                return
            except (ElementClickInterceptedException, StaleElementReferenceException) as failure:
                last_failure = failure
                self.wait_for_toasts_to_clear()
        raise ElementClickInterceptedException(
            f"Could not click {locator} after {self.CLICK_ATTEMPTS} attempts. "
            f"{self.describe_click_blocker(locator)} Underlying error: {last_failure}"
        ) from last_failure

    def describe_click_blocker(self, locator):
        """Names whatever is on top of the element, for the failure message."""
        try:
            element = self.driver.find_element(*locator)
            on_top = self.driver.execute_script(self._BLOCKER_SCRIPT, element)
        except WebDriverException:
            return "Could not work out what was blocking the click."
        if on_top == "OUTSIDE_WINDOW":
            return "The element's centre is outside the window, so nothing can click it."
        if not on_top:
            return "Nothing appears to be covering it now (the page moved mid-click)."
        return f"Blocked by: <{on_top}>."

    def wait_for_toasts_to_clear(self):
        """
        Waits (up to 10 seconds) for the notification toasts in the top-right corner to go.
        They cover buttons such as "More Action". Never fails the test.
        """
        toast_stack = (By.CSS_SELECTOR, "div.fixed.top-20.right-6")
        if not self.exists(toast_stack):
            return
        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(toast_stack)
            )
        except TimeoutException:
            # Carry on - if the toast really blocks the click, the click reports it.
            pass

    def click_button(self, text):
        """Clicks the button with this exact text."""
        self.click(self.button(text))

    def type_into(self, locator, text):
        """Clears a text box and types into it."""
        box = self.wait_visible(locator)
        self.scroll_to_middle(box)
        self.clear_box(box)
        box.send_keys(text)

    def clear_box(self, box):
        """
        Empties a text box by pressing Backspace.
        box.clear() is not used because React does not notice it.
        """
        existing = box.get_attribute("value")
        if not existing:
            return
        box.click()
        box.send_keys(Keys.END)
        for _ in range(len(existing)):
            box.send_keys(Keys.BACK_SPACE)

    def scroll_to_middle(self, element):
        """Scrolls the element to the middle of the window (away from fixed headers/footers)."""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    # ------------------------------------------------------------------
    # Waits
    # ------------------------------------------------------------------

    def wait_visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_gone(self, locator):
        self.wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_count(self, locator, expected):
        """Waits until exactly this many elements match."""
        self.wait.until(lambda driver: len(driver.find_elements(*locator)) == expected)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def exists(self, locator):
        """True if the element is on the page."""
        return len(self.driver.find_elements(*locator)) > 0

    def count(self, locator):
        return len(self.driver.find_elements(*locator))

    def text_of(self, locator):
        """The element's text, or "" when it is not there."""
        try:
            return self.driver.find_element(*locator).text.strip()
        except NoSuchElementException:
            return ""

    def texts_of(self, locator):
        """The text of every matching element, in page order."""
        texts = []
        for element in self.driver.find_elements(*locator):
            texts.append(element.text.strip())
        return texts

    def has_button(self, text):
        return self.exists(self.button(text))

    def has_link(self, text):
        return self.exists(self.link(text))

    # ------------------------------------------------------------------
    # Validation messages
    # ------------------------------------------------------------------

    def modal_error(self):
        """The error at the bottom of a modal, or "" when there is none."""
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] p[role='alert']"))

    def has_modal_error(self):
        return self.modal_error() != ""

    def field_error(self, field_id):
        """The error shown under the field with this id."""
        return self.text_of(
            (By.XPATH, f"//*[@id='{field_id}']/following::p[contains(@class,'text-danger')][1]")
        )

    def all_field_errors(self):
        """Every field error on screen, in page order."""
        errors = []
        for text in self.texts_of((By.CSS_SELECTOR, "p.text-danger, p.text-xs.text-danger")):
            if text:
                errors.append(text)
        return errors

    def shows_message(self, message):
        """True when this exact sentence is shown anywhere on the page."""
        return self.exists((By.XPATH, f'//*[normalize-space(text())="{message}"]'))

    # ------------------------------------------------------------------
    # Dropdowns (the app's own dropdown: a button that opens a list of options)
    # ------------------------------------------------------------------

    OPEN_LISTBOX: Locator = (By.CSS_SELECTOR, "ul[role='listbox']")
    OPEN_OPTIONS: Locator = (By.CSS_SELECTOR, "ul[role='listbox'] button[role='option']")

    def open_dropdown(self, trigger):
        """Closes any other open dropdown, then opens this one."""
        self.close_any_open_dropdown()
        self.click(trigger)
        self.wait_visible(self.OPEN_LISTBOX)

    def close_any_open_dropdown(self):
        """
        Closes any open dropdown with Escape.
        Careful: Escape also closes a drawer. When you know the trigger, use
        _close_dropdown_if_still_open(trigger) instead.
        """
        if not self.exists(self.OPEN_LISTBOX):
            return
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_gone(self.OPEN_LISTBOX)

    def choose_option(self, trigger, option_label):
        """
        Opens a dropdown and picks the option with this exact text.
        scroll=False on purpose: the option panel moves whenever the page scrolls.
        """
        self.open_dropdown(trigger)
        option = (
            By.XPATH,
            "//ul[@role='listbox']//button[@role='option']"
            f"[normalize-space()='{option_label}']",
        )
        self._scroll_within_listbox(self.wait_visible(option))
        self.click(option, scroll=False)
        self._close_dropdown_if_still_open(trigger)

    def _scroll_within_listbox(self, option):
        """Scrolls the option list itself (never the page) so the option is visible."""
        self.driver.execute_script(
            """
            const option = arguments[0];
            const list = option.closest("ul[role='listbox']");
            if (!list) return;
            const item = option.getBoundingClientRect();
            const box = list.getBoundingClientRect();
            if (item.top < box.top) list.scrollTop -= (box.top - item.top);
            else if (item.bottom > box.bottom) list.scrollTop += (item.bottom - box.bottom);
            """,
            option,
        )

    def _close_dropdown_if_still_open(self, trigger):
        """
        Closes the dropdown by clicking its trigger, only if it is still open.
        (Not Escape - that would also close a filter drawer.)
        """
        if not self.exists(self.OPEN_LISTBOX):
            return
        self.click(trigger, scroll=False)
        self.wait_gone(self.OPEN_LISTBOX)

    def choose_first_option(self, trigger):
        """Opens a dropdown, picks the first option, and returns its text."""
        self.open_dropdown(trigger)
        options = self.wait.until(EC.visibility_of_all_elements_located(self.OPEN_OPTIONS))
        label = options[0].text.strip()
        # Click by label (found again), because the element above may have gone stale.
        self.click(
            (
                By.XPATH,
                "//ul[@role='listbox']//button[@role='option']"
                f"[normalize-space()='{label}']",
            ),
            scroll=False,
        )
        self._close_dropdown_if_still_open(trigger)
        return label

    # ------------------------------------------------------------------
    # Native <select> boxes (used on the admin screens)
    # ------------------------------------------------------------------

    def select_native(self, locator, visible_text):
        Select(self.wait_visible(locator)).select_by_visible_text(visible_text)

    def native_select_options(self, locator):
        texts = []
        for option in Select(self.wait_visible(locator)).options:
            texts.append(option.text.strip())
        return texts

    def read_dropdown_options_when_loaded(self, trigger):
        """
        Like read_dropdown_options(), but keeps trying until the list has options
        (the options load from the server). Returns [] if none arrive in time.
        """
        try:
            return self.wait.until(lambda d: self.read_dropdown_options(trigger) or False)
        except TimeoutException:
            return []

    def choose_cascade_path_to(self, triggers, wanted):
        """
        Works through a chain of dropdowns (parent -> child) until the last one offers a
        value in `wanted`, and picks it. Returns that value, or "" if none is found.
        """

        def walk(level):
            options = self.read_dropdown_options(triggers[level])
            if level == len(triggers) - 1:
                for option in options:
                    if option in wanted:
                        if option:
                            self.choose_option(triggers[level], option)
                        return option
                return ""
            for option in options:
                self.choose_option(triggers[level], option)
                found = walk(level + 1)
                if found:
                    return found
            return ""

        return walk(0)

    def read_dropdown_options(self, trigger):
        """
        Every option a dropdown offers, without choosing one.
        Returns [] if the dropdown is empty (waits only 3 seconds).
        """
        self.open_dropdown(trigger)
        labels = []
        try:
            options = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_all_elements_located(self.OPEN_OPTIONS)
            )
            for option in options:
                labels.append(option.text.strip())
        except TimeoutException:
            pass
        self._close_dropdown_if_still_open(trigger)
        return labels
