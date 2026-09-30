"""
The parent of every page object.

WHY THIS EXISTS
Before this class, the same six or seven lines of Selenium were copy-pasted into every
page object: "wait until clickable, then click", "find_elements(...) == []", the XPath
for a button with some text, and so on. All of that now lives here ONCE, and each page
object is left with only the things that are actually special about its own screen.

HOW TO USE IT
A page object writes:      class SomePage(BasePage)
and then calls the small helpers below - click(...), type_into(...), exists(...) -
instead of touching `driver` directly. You can still use `self.driver` when you need
something unusual.

THE ONE RULE WORTH REMEMBERING
Never use time.sleep. Always wait for a CONDITION (see wait_visible / wait_gone). A sleep
is either too short, which makes the test flaky, or too long, which makes the suite slow.

A NOTE ON LOCATORS
In the Java binding a locator was a `By` object. Python's binding takes a (strategy, value)
pair instead, so a locator here is a plain tuple and is passed on with `*locator`. The
`Locator` alias below is only there to make that readable in signatures.
"""

from __future__ import annotations

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

Locator = tuple[str, str]

_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LOWER = "abcdefghijklmnopqrstuvwxyz"


class BasePage:
    def __init__(self, driver, wait: WebDriverWait) -> None:
        self.driver = driver
        self.wait = wait

    # ------------------------------------------------------------------
    # Locator builders - short names for XPath we would otherwise repeat
    # ------------------------------------------------------------------

    @staticmethod
    def button(text: str) -> Locator:
        """A <button> whose visible text is exactly this."""
        return (By.XPATH, f"//button[normalize-space()='{text}']")

    @staticmethod
    def link(text: str) -> Locator:
        """An <a> link whose visible text is exactly this."""
        return (By.XPATH, f"//a[normalize-space()='{text}']")

    @staticmethod
    def exact_text(text: str) -> Locator:
        """Any element whose own text is exactly this (a heading, a label, a card title)."""
        return (By.XPATH, f"//*[normalize-space(text())='{text}']")

    @staticmethod
    def text_ignoring_case(text: str) -> Locator:
        """
        Any element whose own text is this, IGNORING upper/lower case.

        Needed because several card titles are styled uppercase by CSS. Selenium reads the
        text the user actually sees, so "Enquiry Summary" in the source can come back as
        "ENQUIRY SUMMARY". XPath 1.0 has no lower-case() function, so translate() does the
        job by hand.
        """
        return (
            By.XPATH,
            f"//*[normalize-space(translate(text(),'{_UPPER}','{_LOWER}'))='{text.lower()}']",
        )

    @staticmethod
    def innermost_containing(text: str) -> Locator:
        """
        The INNERMOST element containing this text.

        Plain contains(.,'x') also matches <body>, <div>, and every wrapper in between, so
        it can report "found" for something that is nowhere near where you think. The second
        half of this XPath says "and no child of mine contains it too", which leaves exactly
        the element the text really belongs to.
        """
        return (
            By.XPATH,
            f'//*[contains(normalize-space(.),"{text}")'
            f' and not(.//*[contains(normalize-space(.),"{text}")])]',
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    #: How many times a click is retried when the page moves under it mid-flight. Three is
    #: enough for a re-render; more would only slow a genuine failure down.
    CLICK_ATTEMPTS = 3

    #: Asks the browser what is really at an element's centre point. Kept as a constant so
    #: describe_click_blocker() stays readable.
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

    def click(self, locator: Locator, scroll: bool = True) -> None:
        """
        Waits until the element can really be clicked, SCROLLS IT CLEAR, then clicks it.

        PASS scroll=False FOR ANYTHING INSIDE AN OPEN DROPDOWN PANEL. That panel is
        `position: fixed`, portaled to <body>, and it RE-ANCHORS ITSELF ON EVERY SCROLL
        EVENT, so scrolling the page to "reach" an option moves the option rather than the
        window - see choose_option() for the whole story.

        The scroll is not optional. Several screens have a toolbar fixed to the bottom and a
        header fixed to the top; an element under either one is "clickable" as far as
        Selenium's own check is concerned, but the click lands on the toolbar instead -
        Chrome reports "element click intercepted". type_into() has always centred the
        element first for exactly this reason; click() did not, and that asymmetry produced
        a run of seven intercepted clicks on the More Action button against the deployed
        site, where the header is sticky.

        Re-finding the element after the scroll matters too: scrolling can re-render a
        virtualised row or a sticky container, which would make an element captured
        beforehand stale.
        """
        self.wait_for_toasts_to_clear()
        if scroll:
            self.scroll_to_middle(self.wait.until(EC.element_to_be_clickable(locator)))
        self.click_without_scrolling(locator)

    def click_without_scrolling(self, locator: Locator) -> None:
        """
        Clicks where the element ALREADY IS, re-finding it on every attempt.

        WHY RETRY RATHER THAN SLEEP. Selenium measures an element, then sends the click as a
        SEPARATE round trip. If the page re-renders in between - a floating panel re-anchoring,
        a row redrawing, a toast expiring - the click lands at coordinates that now belong to
        something else, and Chrome refuses it. That is a race, not a slow page, so waiting
        longer does not help. Re-finding and trying again does.

        A click still refused after every attempt fails the test, and says WHAT was on top -
        the one fact Selenium's own message leaves out.

        THE RETRIES WAIT OUT A TOAST between attempts. click() already clears the stack before
        the first try, but the toasts are pushed by a 30-SECOND POLL (TopBar), so a fresh batch
        can land in the moment between that check and the click - and then three immediate
        retries all hit the same toast and the test fails on a notification that was about to
        disappear anyway. That is what happened to the Create Ticket form on 2026-09-29, where
        four toasts covered the Source dropdown. wait_for_toasts_to_clear() returns at once
        when no stack is up, so this costs nothing when the blocker is something else.
        """
        last_failure: WebDriverException | None = None
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

    def describe_click_blocker(self, locator: Locator) -> str:
        """
        Names whatever is sitting on top of this element, for the failure message.

        "element click intercepted" says a click was blocked, but never by what. Asking the
        browser what is at the element's centre point turns a guessing game into a sentence -
        the fixed footer, a toast, a modal backdrop - which is usually the whole diagnosis.
        """
        try:
            element = self.driver.find_element(*locator)
            on_top = self.driver.execute_script(
                self._BLOCKER_SCRIPT,
                element,
            )
        except WebDriverException:
            return "Could not work out what was blocking the click."
        if on_top == "OUTSIDE_WINDOW":
            return "The element's centre is outside the window, so nothing can click it."
        if not on_top:
            return "Nothing appears to be covering it now (the page moved mid-click)."
        return f"Blocked by: <{on_top}>."

    def wait_for_toasts_to_clear(self) -> None:
        """
        The notification toast stack, which sits over the top-right of every page.

        TopBar pops unread notifications as toasts the moment you sign in, into a
        `fixed top-20 right-6 z-50` stack that auto-clears after six seconds. For those six
        seconds it covers the top-right corner - which is exactly where the Reports month
        selector and the ticket header's "More Action" button live. Chrome refuses the click
        with "element click intercepted ... other element would receive the click:
        <p class='...line-clamp-2 pr-4'>", which is the toast's own body text.

        This is a real thing a USER hits too, not only a test: for six seconds after signing
        in, those controls genuinely cannot be clicked. Worth fixing in the product (the
        stack wants `pointer-events-none` on the container with it re-enabled on the toast
        itself, or simply to not overlap interactive chrome). Until then, waiting the stack
        out is the honest thing for a test to do - it reproduces what a user does, which is
        wait a moment and click again.
        """
        toast_stack = (By.CSS_SELECTOR, "div.fixed.top-20.right-6")
        if not self.exists(toast_stack):
            return
        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(toast_stack)
            )
        except TimeoutException:
            # Never fail a test for this - the click below will report the real problem if
            # the toast genuinely blocks it, and that is a better failure message than this.
            pass

    def click_button(self, text: str) -> None:
        """Clicks the button with this exact text."""
        self.click(self.button(text))

    def type_into(self, locator: Locator, text: str) -> None:
        """
        Clears a box and types into it.

        Named type_into rather than type because `type` is a Python builtin.
        """
        box = self.wait_visible(locator)
        self.scroll_to_middle(box)
        self.clear_box(box)
        box.send_keys(text)

    def clear_box(self, box) -> None:
        """
        Empties a text box the way a PERSON would - by pressing Backspace.

        Why not just call box.clear()? Because these are React inputs. clear() wipes the
        value straight out of the DOM without telling React anything, so React does not
        re-render, the search does not re-run, and a controlled input can even put the old
        value straight back. Real key presses raise the events React is listening for.

        This cost a debugging session: "clear the search box" appeared to do nothing at all,
        and the list stayed filtered.
        """
        existing = box.get_attribute("value")
        if not existing:
            return
        box.click()
        box.send_keys(Keys.END)
        for _ in range(len(existing)):
            box.send_keys(Keys.BACK_SPACE)

    def scroll_to_middle(self, element) -> None:
        """
        Scrolls an element into the middle of the window before we touch it.

        Several screens have a toolbar fixed to the bottom. An element sitting low on the
        page is underneath that toolbar, and the click lands on the toolbar instead -
        Selenium calls this "element click intercepted". Centring the element first moves it
        clear.
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )

    # ------------------------------------------------------------------
    # Waits
    # ------------------------------------------------------------------

    def wait_visible(self, locator: Locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_gone(self, locator: Locator) -> None:
        self.wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_count(self, locator: Locator, expected: int) -> None:
        """
        Waits until exactly this many elements match.

        WHY NOT EC.number_of_elements_to_be? BECAUSE IT DOES NOT EXIST. Selenium's Python
        binding has never shipped that condition - the name comes from the Java binding - so
        every call raised `AttributeError: module ... has no attribute
        'number_of_elements_to_be'` rather than waiting for anything.

        It went unnoticed because the only callers (wait_for_row_count) sit in tests that are
        skipped unless writeTestsEnabled is true. The first write-enabled run failed here
        immediately, and the AttributeError looked exactly like a broken search feature.

        A plain lambda is the condition; WebDriverWait accepts any callable.
        """
        self.wait.until(lambda driver: len(driver.find_elements(*locator)) == expected)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def exists(self, locator: Locator) -> bool:
        """
        Is this element on the page at all?

        find_elements (PLURAL) returns an empty list when nothing matches.
        find_element (SINGULAR) raises instead. So for "is it absent?" questions - which is
        most of the access-control testing - the plural form is the clean way to ask.
        """
        return len(self.driver.find_elements(*locator)) > 0

    def count(self, locator: Locator) -> int:
        return len(self.driver.find_elements(*locator))

    def text_of(self, locator: Locator) -> str:
        """The element's text, or "" when the element is not there. Never raises."""
        try:
            return self.driver.find_element(*locator).text.strip()
        except NoSuchElementException:
            return ""

    def texts_of(self, locator: Locator) -> list[str]:
        """The text of every matching element, in page order."""
        return [element.text.strip() for element in self.driver.find_elements(*locator)]

    def has_button(self, text: str) -> bool:
        """True when the button with this text is on the page."""
        return self.exists(self.button(text))

    def has_link(self, text: str) -> bool:
        """True when the link with this text is on the page."""
        return self.exists(self.link(text))

    # ------------------------------------------------------------------
    # Inline validation messages
    # ------------------------------------------------------------------
    # Every form in this application reports a problem the same two ways, so these live
    # here once rather than in each page object:
    #   * a MODAL puts one message at the bottom, as <p role="alert">
    #   * a FIELD puts its own message directly under the control, as <p class="…text-danger">
    # Asserting on the exact wording matters: the QA documentation lists the sentence each
    # rule is supposed to produce, and a form that blocks you with the WRONG explanation is
    # still a form nobody can get past.

    def modal_error(self) -> str:
        """The single error a modal shows at the bottom, or "" when there is none."""
        return self.text_of((By.CSS_SELECTOR, "div[role='dialog'] p[role='alert']"))

    def has_modal_error(self) -> bool:
        return self.modal_error() != ""

    def field_error(self, field_id: str) -> str:
        """The message shown under one field, found by the control's id."""
        return self.text_of(
            (
                By.XPATH,
                f"//*[@id='{field_id}']/following::p[contains(@class,'text-danger')][1]",
            )
        )

    def all_field_errors(self) -> list[str]:
        """Every inline field message currently on screen, in page order."""
        found = self.texts_of((By.CSS_SELECTOR, "p.text-danger, p.text-xs.text-danger"))
        return [text for text in found if text]

    def shows_message(self, message: str) -> bool:
        """True when this exact sentence is showing anywhere on the page."""
        return self.exists((By.XPATH, f'//*[normalize-space(text())="{message}"]'))

    # ------------------------------------------------------------------
    # Dropdowns (the app's CustomSelect component)
    # ------------------------------------------------------------------
    # The app never uses a native <select>, so Selenium's Select class does not work here.
    # Every dropdown is a button that opens a <ul role="listbox"> of <button role="option">.
    # The methods below are the only place that knowledge lives.

    OPEN_LISTBOX: Locator = (By.CSS_SELECTOR, "ul[role='listbox']")
    OPEN_OPTIONS: Locator = (By.CSS_SELECTOR, "ul[role='listbox'] button[role='option']")

    def open_dropdown(self, trigger: Locator) -> None:
        """Opens a dropdown by clicking its trigger button."""
        # Make sure no OTHER option panel is still on screen first. These panels are floated
        # over the page, so one that is still closing sits on top of the next trigger and
        # swallows the click - the panel then never opens and the test times out waiting for
        # it, which reads as "the dropdown is broken" when nothing is wrong at all.
        self.close_any_open_dropdown()
        # Go through click() rather than calling .click() on the element directly. Doing it by
        # hand skipped BOTH of click()'s protections, and the trigger needs them more than
        # most controls do:
        #   * wait_for_toasts_to_clear - the notification stack sits at `fixed top-20 right-6`,
        #     which is exactly where the Reports month selector lives. Chrome refused the click
        #     with "Other element would receive the click: <p class='...line-clamp-2 pr-4'>",
        #     the toast's own body text, and both month-selector tests failed on it.
        #   * the retry - a trigger high on the page is also the first thing a late re-render
        #     moves.
        self.click(trigger)
        self.wait_visible(self.OPEN_LISTBOX)

    def close_any_open_dropdown(self) -> None:
        """
        Shuts whatever option panel happens to be open, with the Escape key.

        WHY NOT CLICK THE PAGE BACKGROUND? This used to do
        `find_element(By.TAG_NAME, "body").click()`, which does NOT click empty space - it
        clicks the CENTRE OF THE BODY ELEMENT. On a long form that centre point is some
        arbitrary control, so "close the dropdown" could silently tick a checkbox, open
        another dropdown, or land on the fixed footer and be refused outright.

        The component itself listens for Escape (CustomSelect's `handleKeyDown`), so Escape
        is the gesture the application actually supports.

        CAUTION: Escape also closes a Drawer that hosts the dropdown. When the trigger is known,
        use _close_dropdown_if_still_open(trigger) instead, which does not send Escape.
        """
        if not self.exists(self.OPEN_LISTBOX):
            return
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_gone(self.OPEN_LISTBOX)

    def choose_option(self, trigger: Locator, option_label: str) -> None:
        """
        Opens a dropdown and picks the option with this exact text.

        THE ONE THING NOT TO "TIDY UP" HERE - scroll=False.

        The option panel is `position: fixed` and PORTALED TO <body> (CustomSelect renders it
        through createPortal), and useAnchoredPosition re-computes its coordinates on EVERY
        scroll event - `document.addEventListener("scroll", update, true)` - and flips the
        panel above the trigger when there is no room below.

        So scrolling in order to "reach" an option is self-defeating. scrollIntoView cannot
        move a viewport-fixed element, so the browser scrolls the DOCUMENT instead; that moves
        the trigger; the scroll listener then re-anchors the panel to the trigger's new
        position - possibly flipping it to the other side. The coordinates Selenium measured a
        moment earlier now belong to whatever slid underneath, and Chrome reports "element
        click intercepted", frequently naming the form's fixed bottom action bar.

        The option is already inside the viewport by construction, so it never needs the page
        scrolled at all. Only the panel's OWN list may need scrolling, which is what
        _scroll_within_listbox does - it moves the <ul>, never the page.
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

    def _scroll_within_listbox(self, option) -> None:
        """
        Brings an option into view by scrolling THE LIST, never the page.

        The panel's <ul> is `max-h-60 overflow-auto`, so a long list scrolls inside itself.
        Adjusting that element's own scrollTop leaves the document - and therefore the
        trigger, and therefore the panel's anchor - exactly where it was.
        """
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

    def _close_dropdown_if_still_open(self, trigger: Locator) -> None:
        """
        Shuts the option panel if it is still showing.

        A single-choice dropdown closes itself the moment you pick something. A MULTI-choice
        one (every filter in the Filter drawer) deliberately stays open so you can tick
        several values.

        WHY THE TRIGGER, AND ONLY IF STILL OPEN. The trigger is a TOGGLE (`setOpen(o => !o)`).
        A single-select panel has usually already closed itself by the time we look, so an
        unconditional click would RE-OPEN it - hence the check first.

        WHY NOT ESCAPE? Escape is heard by EVERY document-level keydown listener, not just the
        dropdown's. The filter Drawer (components/ui/Drawer.tsx) also closes on Escape, so
        closing a filter's option panel with Escape threw away the whole drawer before "Apply
        Filter" could be pressed - 9 of 11 filter tests failed on that (verified 2026-09-17).
        The trigger click is local to the dropdown; its pointerdown counts as "inside", so it
        only toggles this panel shut.
        """
        if not self.exists(self.OPEN_LISTBOX):
            return
        self.click(trigger, scroll=False)
        self.wait_gone(self.OPEN_LISTBOX)

    def choose_first_option(self, trigger: Locator) -> str:
        """
        Opens a dropdown and picks whatever the FIRST option happens to be.

        Used for Department, Priority and similar lists whose values come from the database.
        Hard-coding a value would make the test fail whenever the seed data changes, which is
        a failure about the test, not about the product.
        """
        self.open_dropdown(trigger)
        first = self.wait.until(
            EC.visibility_of_all_elements_located(self.OPEN_OPTIONS)
        )[0]
        label = first.text.strip()
        # Click by LABEL rather than through the element handle captured above. Reading
        # `.text` can be enough on its own to let React re-render, which makes that handle
        # stale; choose_option re-finds it, and shares the no-scroll rule this panel needs.
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
    # Native <select> boxes
    # ------------------------------------------------------------------
    # Most of the app uses the CustomSelect above, but the admin screens use real HTML
    # <select> elements. Those are the one place Selenium's own Select class works.

    def select_native(self, locator: Locator, visible_text: str) -> None:
        Select(self.wait_visible(locator)).select_by_visible_text(visible_text)

    def native_select_options(self, locator: Locator) -> list[str]:
        return [
            option.text.strip()
            for option in Select(self.wait_visible(locator)).options
        ]

    def read_dropdown_options_when_loaded(self, trigger: Locator) -> list[str]:
        """
        read_dropdown_options(), polled until it offers something (up to the normal timeout).

        For a dropdown fed by a fetch that starts on mount - the create and edit forms load the
        classification taxonomy asynchronously (NewTicketForm's Promise.all, TicketEditForm's
        getComplaintTaxonomyPaths) - reading it the instant the form appears returns [] and a
        test would wrongly conclude "not configured here". Still returns [] if nothing arrives.
        """
        try:
            return self.wait.until(lambda d: self.read_dropdown_options(trigger) or False)
        except TimeoutException:
            return []

    def choose_cascade_path_to(self, triggers: list[Locator], wanted: list[str]) -> str:
        """
        Walks a cascade of dropdowns (parent -> child) until the LAST one offers a value in
        `wanted`, leaving that path selected. Returns the value chosen, or "" if no path leads
        to one.

        Exists so a test can reach a rule-bearing leaf (e.g. a garage complaint sub-type)
        without hard-coding the taxonomy path above it: the path is discovered from whatever
        the environment's taxonomy offers, depth-first, in the order the dropdowns list it.
        """

        def walk(level: int) -> str:
            options = self.read_dropdown_options(triggers[level])
            if level == len(triggers) - 1:
                hit = next((o for o in options if o in wanted), "")
                if hit:
                    self.choose_option(triggers[level], hit)
                return hit
            for option in options:
                self.choose_option(triggers[level], option)
                hit = walk(level + 1)
                if hit:
                    return hit
            return ""

        return walk(0)

    def read_dropdown_options(self, trigger: Locator) -> list[str]:
        """
        Every option a dropdown offers, without choosing any of them.

        Returns an EMPTY LIST when the dropdown has nothing to offer, rather than waiting the
        full timeout and then failing. "This list is empty" is a real, legitimate answer - a
        cascade level whose parent has no children underneath it, or a taxonomy that has not
        been seeded on this environment - and a test needs to be able to ask the question
        without being punished for the answer.
        """
        self.open_dropdown(trigger)
        labels: list[str] = []
        # A short look, not the full timeout: the options render with the panel, so if they
        # are not there within a couple of seconds they are not coming.
        try:
            for option in WebDriverWait(self.driver, 3).until(
                EC.visibility_of_all_elements_located(self.OPEN_OPTIONS)
            ):
                labels.append(option.text.strip())
        except TimeoutException:
            # Left empty on purpose - see the note above.
            pass
        self._close_dropdown_if_still_open(trigger)
        return labels
