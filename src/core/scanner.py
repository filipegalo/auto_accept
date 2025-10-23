"""Email scanning module for continuous mailbox monitoring."""

import time
from typing import Optional

from ..config import DEFAULT_SCAN_INTERVAL
from ..utils import ui
from ..utils.tracker import EmailTracker
from .browser import BrowserAutomation
from .gmail import GmailHandler


class EmailScanner:
    """Continuously scans Gmail mailbox for emails matching subject criteria."""

    def __init__(
        self,
        email: str,
        password: str,
        platform: str,
        platform_email: str,
        platform_password: str,
        subject: str,
        link_filter_text: Optional[str] = None,
        link_text: Optional[str] = None,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize email scanner.

        Args:
            email: Gmail email address for scanning
            password: Gmail password or app-specific password
            platform: Platform to login to (e.g., 'smartcat')
            platform_email: Email for platform login
            platform_password: Password for platform login
            subject: Subject text to search for (substring match)
            link_filter_text: Filter links by their text (e.g., 'Go to task') - optional
            link_text: Text of button/element to click in opened links (optional)
            scan_interval: Interval between scans in seconds (default: 5)

        Raises:
            RuntimeError: If Gmail connection fails
        """
        self.email = email
        self.password = password
        self.platform = platform
        self.platform_email = platform_email
        self.platform_password = platform_password
        self.subject = subject
        self.link_filter_text = link_filter_text
        self.link_text = link_text
        self.scan_interval = scan_interval
        self.gmail = GmailHandler(email, password)
        self.tracker = EmailTracker()
        self.browser: Optional[BrowserAutomation] = None
        self.running = False
        self._initialize_browser()

    def _initialize_browser(self) -> None:
        """Initialize browser automation.

        Prints info about configured link filtering and button clicking.
        """
        try:
            self.browser = BrowserAutomation()
            if self.link_filter_text:
                ui.print_info(
                    f"Link filtering enabled: Will only open links with text '{self.link_filter_text}'"
                )
            if not self.link_text:
                ui.print_info("No button text configured - will only open links without clicking")
        except RuntimeError as e:
            ui.print_warning(f"Browser initialization failed: {e}")
            ui.print_warning("Will continue without browser automation")
            self.browser = None

    def _process_email(self, message: dict) -> None:
        """Process email by opening links and clicking buttons.

        Filters links by configured text if link_filter_text is set.

        Args:
            message: Email message dictionary
        """
        self._print_processed_status(message)

        # Extract links with their associated text from email body
        links_with_text = self.gmail.extract_links_with_text(message["body"])

        if not links_with_text:
            ui.print_warning("No links found in email body", indent=1)
            return

        # Filter links if link_filter_text is configured
        filtered_links = self._filter_links(links_with_text)

        if not filtered_links:
            if self.link_filter_text:
                ui.print_warning(
                    f"No links found matching filter text '{self.link_filter_text}'", indent=1
                )
            else:
                ui.print_warning("No links available after filtering", indent=1)
            return

        ui.print_success(f"Found {len(filtered_links)} link(s)", indent=1)

        # Open each link and click button if configured
        for link in filtered_links:
            self._open_and_process_link(link)

    def _filter_links(self, links_with_text: list[tuple[str, str]]) -> list[str]:
        """Filter links based on configured link_filter_text.

        If link_filter_text is not configured, returns all links.
        Otherwise, returns only links whose text contains the filter text (case-insensitive).

        Args:
            links_with_text: List of (url, link_text) tuples

        Returns:
            List of filtered URLs
        """
        # If no filter is configured, return all links
        if not self.link_filter_text:
            return [url for url, _ in links_with_text]

        # Filter links by text match
        filtered = []
        filter_text_lower = self.link_filter_text.lower()

        for url, link_text in links_with_text:
            # Check if link_text matches the filter (case-insensitive substring match)
            if link_text and filter_text_lower in link_text.lower():
                filtered.append(url)
                ui.print_info(f"Link matched filter: '{link_text}' → {url}", indent=1)

        return filtered

    def _open_and_process_link(self, link: str) -> None:
        """Open a link and click element if configured.

        Finds and clicks any element (button, link, div, etc.) containing
        the configured text. If no text is configured, just opens the link.

        Args:
            link: URL to open
        """
        if not self.browser:
            ui.print_warning("Browser not available - skipping automation", indent=2)
            return

        try:
            # Open the URL in browser (handles its own logging)
            if not self.browser.open_url(link, timeout=10):
                ui.print_error("Failed to open link", indent=2)
                return

            # Wait for page to load
            time.sleep(2)

            # Click element if configured
            if self.link_text:
                ui.print_info(f"Searching for element: '{self.link_text}'...", indent=2)
                if self.browser.click_element_by_text(self.link_text, timeout=10):
                    # Browser already logged the success
                    pass
                else:
                    ui.print_warning(f"Element '{self.link_text}' not found", indent=2)
                    # Enable debug mode to see what elements are on the page
                    ui.print_info("Running debug to see what's on the page...", indent=2)
                    self.browser.debug_find_element(self.link_text)

            # Brief pause after interaction
            time.sleep(1)

        except Exception as e:
            ui.print_error(f"Error processing link: {e}", indent=2)

    def _scan_once(self) -> list[str]:
        """Perform a single scan iteration of the mailbox.

        Searches for unread emails matching the subject, marks them as read,
        opens links, clicks buttons if configured, and tracks emails to
        avoid re-processing.

        Returns:
            List of newly processed email IDs
        """
        messages = self.gmail.search_emails(self.subject, unread_only=True)
        processed_ids = []

        for message in messages:
            message_id = str(message["id"])

            # Skip if already processed in previous sessions
            if self.tracker.is_processed(message_id):
                continue

            # Mark as read in Gmail
            if self.gmail.mark_as_read([message["id"]]):
                # Track as processed locally
                self.tracker.mark_as_processed(message_id)
                processed_ids.append(message_id)

                # Process email (open links and click buttons)
                self._process_email(message)

        return processed_ids

    def _print_processed_status(self, message: dict) -> None:
        """Print status of processed email.

        Args:
            message: Email message dictionary
        """
        ui.print_email_status(message["sender"], message["subject"], 0)

    def start(self) -> None:
        """Start continuous scanning of mailbox.

        Logs into configured platform first, then scans at regular intervals defined by scan_interval.
        Opens links and clicks buttons as configured.
        Stops on KeyboardInterrupt (Ctrl+C).
        """
        self.running = True
        self._print_startup_message()

        # Login to platform before starting email scanning
        if not self._login_to_platform():
            ui.print_error(f"Failed to login to {self.platform} - aborting email scanning")
            self._cleanup()
            return

        try:
            while self.running:
                self._scan_once()
                time.sleep(self.scan_interval)
        except KeyboardInterrupt:
            ui.console.print("\n\n[yellow]Email scanner stopped.[/yellow]")
            self.running = False
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        self.gmail.close()
        if self.browser:
            self.browser.close()

    def _print_startup_message(self) -> None:
        """Print startup information."""
        ui.print_startup_info(self.platform, self.subject, self.link_text, self.scan_interval)

    def _login_to_platform(self) -> bool:
        """Login to configured platform using configured credentials.

        Returns:
            True if login successful, False otherwise
        """
        if not self.browser:
            print("✗ Browser not available - cannot login to platform")
            return False

        if self.platform.lower() == "smartcat":
            return self.browser.login_smartcat(self.platform_email, self.platform_password)
        else:
            print(f"✗ Unsupported platform: {self.platform}")
            return False

    def stop(self) -> None:
        """Stop the email scanner."""
        self.running = False
        self._cleanup()
