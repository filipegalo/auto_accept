"""Browser automation module for opening links and clicking elements."""

import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..utils import ui


class BrowserAutomation:
    """Handles browser automation using Selenium with Chrome."""

    def __init__(
        self,
        headless: bool = False,
    ) -> None:
        """Initialize browser automation.

        Args:
            headless: Run Chrome in headless mode (default: False for visible window)
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self._initialize_driver()

    def _initialize_driver(self) -> None:
        """Initialize Selenium WebDriver for Chrome."""
        try:
            options = webdriver.ChromeOptions()

            if self.headless:
                options.add_argument("--headless=new")

            # Hide the "Chrome is being controlled by automated test software" message
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # Additional options for stability
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Use system Chrome with Selenium
            self.driver = webdriver.Chrome(options=options)

            ui.print_success("Browser launched successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {e}") from e

    def open_url(self, url: str, timeout: int = 10) -> bool:
        """Open a URL in the browser.

        Args:
            url: URL to open
            timeout: Maximum time to wait for page load (seconds)

        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            print("  ✗ Browser not initialized")
            return False

        try:
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )

            print("  ✓ Link loaded in browser")
            return True
        except TimeoutException:
            print(f"  ✗ Page load timeout after {timeout} seconds")
            return False
        except Exception as e:
            print(f"  ✗ Error opening URL: {e}")
            return False

    def click_element_by_text(self, text: str, element_type: str = "*", timeout: int = 10) -> bool:
        """Click an element by its text content.

        Searches for any element (button, link, div, span, etc.) containing
        the specified text and clicks it. Smart element finder that works
        with any HTML element type, including Vue.js-rendered content.

        Args:
            text: Text content of the element to click
            element_type: Type of element to search for (default: "*" for any element)
            timeout: Maximum time to wait for element (seconds)

        Returns:
            True if element was clicked, False otherwise
        """
        if not self.driver:
            print("  ✗ Browser not initialized")
            return False

        try:
            # Wait a bit for Vue.js rendering to complete
            time.sleep(0.5)

            # Use JavaScript-based approach for better Vue.js compatibility
            return self._try_javascript_click(text, timeout)

        except Exception as e:
            print(f"  ✗ Error clicking element: {e}")
            return False

    def _try_javascript_click(self, text: str, timeout: int) -> bool:
        """Try clicking element using JavaScript-based search and click.

        This method finds clickable elements by exact text match and clicks them.
        Effective for Vue.js components and other dynamic content.

        Args:
            text: Text content to search for
            timeout: Wait timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Find the element with text matching
            js_find_and_click = f"""
            var searchText = '{text}';

            // Find button/link that contains this text
            var buttons = document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]');

            for (var btn of buttons) {{
                if (btn.textContent.trim() === searchText || btn.textContent.trim().includes(searchText)) {{
                    // Found it - now click it
                    btn.click();
                    return {{ found: true, tag: btn.tagName, text: btn.textContent.substring(0, 50) }};
                }}
            }}

            // If not found in obvious places, search all elements
            var allElements = document.querySelectorAll('*');
            for (var elem of allElements) {{
                var text = elem.textContent ? elem.textContent.trim() : '';

                // Check if this element's direct text matches (not including children)
                if (text.includes(searchText)) {{
                    // Check if it's clickable
                    var isClickable = elem.onclick !== null ||
                                     elem.getAttribute('onclick') !== null ||
                                     window.getComputedStyle(elem).cursor === 'pointer';

                    if (isClickable && elem.offsetParent !== null) {{
                        elem.click();
                        return {{ found: true, tag: elem.tagName, text: elem.textContent.substring(0, 50), method: 'found_clickable' }};
                    }}
                }}
            }}

            return {{ found: false }};
            """

            # Execute the click and get result
            assert self.driver is not None
            result = self.driver.execute_script(js_find_and_click)

            if result.get("found"):
                print(f"  ✓ Clicked element with text: '{text}' (Tag: {result.get('tag')})")
                time.sleep(0.5)  # Wait for Vue event to process
                return True
            else:
                print(f"  ✗ Element with text '{text}' not found")
                return False

        except Exception as e:
            print(f"  ✗ Error in JavaScript click: {e}")
            return False

    def login_smartcat(self, email: str, password: str) -> bool:
        """Login to Smartcat using automated email and password entry.

        Navigates to Smartcat sign-in page, fills email, clicks continue,
        fills password, and clicks sign-in button.

        Args:
            email: Email address for Smartcat account
            password: Password for Smartcat account

        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            ui.print_error("Browser not initialized")
            return False

        try:
            ui.print_header("Smartcat Login")

            # Navigate to Smartcat sign-in page
            ui.print_info("Navigating to Smartcat sign-in page...", indent=1)
            self.driver.get("https://smartcat.com/sign-in")

            # Wait for email input field to be visible
            wait = WebDriverWait(self.driver, 10)
            email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
            ui.print_success("Email input field found", indent=1)

            # Fill email field
            email_input.clear()
            email_input.send_keys(email)
            ui.print_success("Email entered", indent=1)

            # Click the "Continue with email" button
            email_submit_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="email-submit"]'))
            )
            email_submit_btn.click()
            ui.print_success("Clicked 'Continue with email' button", indent=1)

            # Wait for password input field to appear
            password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            ui.print_success("Password input field appeared", indent=1)

            # Brief pause for form transition
            time.sleep(1)

            # Fill password field
            password_input.clear()
            password_input.send_keys(password)
            ui.print_success("Password entered", indent=1)

            # Click the "Sign in" button
            signin_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="password-submit"]'))
            )
            signin_btn.click()
            ui.print_success("Clicked 'Sign in' button", indent=1)

            # Wait for login to complete (check if we're redirected from sign-in page)
            time.sleep(3)
            current_url = self.driver.current_url

            if "sign-in" not in current_url:
                ui.print_success("Login successful - redirected from sign-in page", indent=1)
                return True
            else:
                ui.print_warning(
                    "Still on sign-in page - login may have failed or is processing", indent=1
                )
                return False

        except TimeoutException:
            ui.print_error("Login timeout - element not found or page took too long to load")
            return False
        except Exception as e:
            ui.print_error(f"Login error: {e}")
            return False

    def debug_find_element(self, text: str) -> None:
        """Debug helper to find and log info about an element with given text.

        This is useful for troubleshooting why element clicking might not work.

        Args:
            text: Text to search for
        """
        if not self.driver:
            print("  ✗ Browser not initialized")
            return

        try:
            js_debug = f"""
            var searchText = '{text}';
            var results = [];
            var allElements = document.querySelectorAll('*');

            for (var elem of allElements) {{
                var textContent = elem.textContent ? elem.textContent.trim() : '';

                if (textContent.includes(searchText)) {{
                    var info = {{
                        tag: elem.tagName,
                        text: textContent.substring(0, 100),
                        visible: elem.offsetParent !== null,
                        clickable: elem.tagName === 'BUTTON' || elem.tagName === 'A' || !!elem.onclick || elem.hasAttribute('role'),
                        html: elem.outerHTML.substring(0, 200)
                    }};
                    results.push(info);
                }}
            }}
            return results;
            """

            results = self.driver.execute_script(js_debug)
            if results:
                print(f"  Found {len(results)} element(s) with text containing '{text}':")
                for i, elem_info in enumerate(results):
                    print(f"    [{i}] Tag: {elem_info['tag']}, Text: {elem_info['text'][:50]}")
                    print(
                        f"        Visible: {elem_info['visible']}, Clickable: {elem_info['clickable']}"
                    )
            else:
                print(f"  ✗ No elements found with text containing '{text}'")

        except Exception as e:
            print(f"  ✗ Error during debug: {e}")

    def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                ui.print_success("Browser closed")
            except Exception as e:
                ui.print_error(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
