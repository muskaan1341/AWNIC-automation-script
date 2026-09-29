"""
The /login page.

In production the real login is AWNIC One single sign-on, and this page redirects there
on its own. On a laptop that redirect cannot work (AWNIC's portal only accepts requests
from one approved machine), so the page shows a "dev login" form instead: an email box
and nothing else. There is NO password field anywhere in this application.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage


class LoginPage(BasePage):
    # ---------- LOCATORS ----------
    # Best kind of locator there is: the app gives this input a real id.
    EMAIL_INPUT = (By.ID, "dev-login-email")

    # The only submit button inside the login form.
    SIGN_IN_BUTTON = (By.CSS_SELECTOR, "form button[type='submit']")

    # The error the form shows when sign-in fails. role="alert" exists for screen readers,
    # which makes it a far more stable hook than a CSS class a designer might rename.
    ERROR_MESSAGE = (By.CSS_SELECTOR, "p[role='alert']")

    HEADING = (By.XPATH, "//h2[normalize-space()='Welcome back']")
    SSO_PILL = (By.XPATH, "//*[normalize-space()='Login with AWNIC One']")

    def __init__(self, driver, wait, base_url: str) -> None:
        super().__init__(driver, wait)
        self.base_url = base_url

    # ---------- ACTIONS ----------

    def open(self) -> None:
        self.driver.get(self.base_url + "/login")
        self.wait_visible(self.EMAIL_INPUT)

    def enter_email(self, email: str) -> None:
        self.type_into(self.EMAIL_INPUT, email)

    def click_sign_in(self) -> None:
        self.driver.find_element(*self.SIGN_IN_BUTTON).click()

    def sign_in(self, email: str) -> None:
        """The two steps almost every test needs together."""
        self.enter_email(email)
        self.click_sign_in()

    def sign_in_with_keyboard_only(self, email: str) -> None:
        """Types the email and presses Enter - proves the form works without a mouse."""
        box = self.wait_visible(self.EMAIL_INPUT)
        box.clear()
        box.send_keys(email)
        box.send_keys(Keys.ENTER)

    # ---------- CHECKS ----------

    def is_heading_displayed(self) -> bool:
        return self.exists(self.HEADING)

    def is_email_input_displayed(self) -> bool:
        return self.exists(self.EMAIL_INPUT)

    def get_sign_in_button_text(self) -> str:
        return self.text_of(self.SIGN_IN_BUTTON)

    def get_error_message(self) -> str:
        """Waits for the error to appear, then returns its text."""
        return self.wait_visible(self.ERROR_MESSAGE).text

    def has_error_message(self) -> bool:
        return self.exists(self.ERROR_MESSAGE)

    def get_email_validation_message(self) -> str:
        """
        The browser's OWN "please fill in this field" message for a required input.
        An empty string means the browser considers the field valid.
        """
        return self.driver.find_element(*self.EMAIL_INPUT).get_attribute("validationMessage")

    def get_email_input_type(self) -> str:
        return self.driver.find_element(*self.EMAIL_INPUT).get_attribute("type")

    def is_sso_pill_displayed(self) -> bool:
        """The single-sign-on pill shown when the dev form is switched off."""
        return self.exists(self.SSO_PILL)

    def is_email_input_focused(self) -> bool:
        """True when the email box currently has keyboard focus (the page autofocuses it)."""
        active = self.driver.switch_to.active_element
        return active.get_attribute("id") == "dev-login-email"
