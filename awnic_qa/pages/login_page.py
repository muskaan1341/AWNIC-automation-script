"""
The /login page.

Outside production the page shows a "dev login" form: just an email box, no password.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from awnic_qa.pages.base_page import BasePage


class LoginPage(BasePage):
    # ---------- LOCATORS ----------
    EMAIL_INPUT = (By.ID, "dev-login-email")
    SIGN_IN_BUTTON = (By.CSS_SELECTOR, "form button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "p[role='alert']")
    HEADING = (By.XPATH, "//h2[normalize-space()='Welcome back']")
    SSO_PILL = (By.XPATH, "//*[normalize-space()='Login with AWNIC One']")

    def __init__(self, driver, wait, base_url):
        super().__init__(driver, wait)
        self.base_url = base_url

    # ---------- ACTIONS ----------

    def open(self):
        self.driver.get(self.base_url + "/login")
        self.wait_visible(self.EMAIL_INPUT)

    def enter_email(self, email):
        self.type_into(self.EMAIL_INPUT, email)

    def click_sign_in(self):
        self.driver.find_element(*self.SIGN_IN_BUTTON).click()

    def sign_in(self, email):
        """Types the email and clicks Sign in."""
        self.enter_email(email)
        self.click_sign_in()

    def sign_in_with_keyboard_only(self, email):
        """Types the email and presses Enter (no mouse)."""
        box = self.wait_visible(self.EMAIL_INPUT)
        box.clear()
        box.send_keys(email)
        box.send_keys(Keys.ENTER)

    # ---------- CHECKS ----------

    def is_heading_displayed(self):
        return self.exists(self.HEADING)

    def is_email_input_displayed(self):
        return self.exists(self.EMAIL_INPUT)

    def get_sign_in_button_text(self):
        return self.text_of(self.SIGN_IN_BUTTON)

    def get_error_message(self):
        """Waits for the error to appear, then returns its text."""
        return self.wait_visible(self.ERROR_MESSAGE).text

    def has_error_message(self):
        return self.exists(self.ERROR_MESSAGE)

    def get_email_validation_message(self):
        """The browser's own validation message for the email box ("" means valid)."""
        return self.driver.find_element(*self.EMAIL_INPUT).get_attribute("validationMessage")

    def get_email_input_type(self):
        return self.driver.find_element(*self.EMAIL_INPUT).get_attribute("type")

    def is_sso_pill_displayed(self):
        """The "Login with AWNIC One" pill, shown when the dev form is switched off."""
        return self.exists(self.SSO_PILL)

    def is_email_input_focused(self):
        """True when the email box has keyboard focus."""
        active = self.driver.switch_to.active_element
        return active.get_attribute("id") == "dev-login-email"
