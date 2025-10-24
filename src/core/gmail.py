"""Gmail IMAP integration module."""

import email
import imaplib
import re
import socket
import time
from typing import Optional

from ..config import GMAIL_IMAP_PORT, GMAIL_IMAP_SERVER


class GmailHandler:
    """Handles Gmail operations using IMAP protocol."""

    # Connection refresh interval in seconds (20 minutes)
    CONNECTION_REFRESH_INTERVAL = 20 * 60
    # Keep-alive check interval in seconds (5 minutes)
    KEEP_ALIVE_INTERVAL = 5 * 60

    def __init__(self, email_address: str, password: str) -> None:
        """Initialize Gmail handler with credentials.

        Args:
            email_address: Gmail email address
            password: Gmail password or app-specific password

        Raises:
            RuntimeError: If connection to Gmail fails
        """
        self.email_address = email_address
        self.password = password
        self.client: Optional[imaplib.IMAP4_SSL] = None
        self._connection_time = 0.0
        self._last_keep_alive = 0.0
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Gmail IMAP server.

        Raises:
            RuntimeError: If authentication fails
        """
        try:
            self.client = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
            self.client.login(self.email_address, self.password)
            self._connection_time = time.time()
            self._last_keep_alive = time.time()
            print("✓ Gmail IMAP connection successful")
        except imaplib.IMAP4.error as e:
            raise RuntimeError(f"Failed to connect to Gmail: {e}") from e

    def _is_connection_stale(self) -> bool:
        """Check if connection needs to be refreshed.

        Returns:
            True if connection is older than CONNECTION_REFRESH_INTERVAL
        """
        if self._connection_time == 0:
            return False
        return time.time() - self._connection_time > self.CONNECTION_REFRESH_INTERVAL

    def _should_keep_alive(self) -> bool:
        """Check if keep-alive ping is needed.

        Returns:
            True if time since last keep-alive exceeds KEEP_ALIVE_INTERVAL
        """
        return time.time() - self._last_keep_alive > self.KEEP_ALIVE_INTERVAL

    def _keep_alive(self) -> bool:
        """Send NOOP command to keep connection alive.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.client:
                self.client.noop()
                self._last_keep_alive = time.time()
                return True
        except (socket.error, imaplib.IMAP4.error, EOFError):
            # Connection is stale, will need to refresh
            return False
        return False

    def refresh_connection(self) -> None:
        """Refresh the Gmail connection by closing and reconnecting.

        Useful for maintaining a healthy connection during long-running operations.
        """
        try:
            if self.client:
                try:
                    self.client.logout()
                except Exception:
                    pass
                self.client = None
            self._connect()
            print("✓ Connection refreshed")
        except RuntimeError as e:
            print(f"✗ Failed to refresh connection: {e}")
            raise

    def _ensure_connection(self) -> None:
        """Ensure connection is healthy, refreshing if needed.

        Automatically refreshes connection if it's stale or keep-alive fails.
        """
        # Check if connection needs refresh
        if self._is_connection_stale():
            print("↻ Refreshing stale connection...")
            try:
                self.refresh_connection()
            except RuntimeError:
                raise

        # Check if keep-alive is needed
        if self._should_keep_alive():
            if not self._keep_alive():
                print("↻ Keep-alive ping failed, refreshing connection...")
                try:
                    self.refresh_connection()
                except RuntimeError:
                    raise

    def search_emails(self, subject: str, unread_only: bool = True) -> list[dict]:
        """Search for emails with subject containing the given text.

        Uses IMAP SUBJECT search which does case-insensitive substring matching.
        Automatically handles connection refresh and retry logic.

        Args:
            subject: Text to search for in subject line (substring match)
            unread_only: Only return unread emails (default: True)

        Returns:
            List of email metadata dictionaries with keys:
            - id: Message ID (int)
            - subject: Email subject (str)
            - sender: Email sender (str)
            - body: Email body content (str)
        """
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Ensure connection is healthy
                self._ensure_connection()

                assert self.client is not None
                self.client.select("INBOX")

                # Build IMAP search criteria (SUBJECT does substring matching)
                search_criteria = self._build_search_criteria(subject, unread_only)
                status, message_ids = self.client.search(None, search_criteria)

                if status != "OK":
                    return []

                return self._fetch_messages(message_ids[0].split())

            except (socket.error, EOFError) as e:
                # Socket/SSL error - connection issue
                if attempt < max_retries - 1:
                    print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    try:
                        self.refresh_connection()
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    except RuntimeError:
                        continue
                else:
                    print(f"Error searching emails after {max_retries} attempts: {e}")
                    return []
            except imaplib.IMAP4.error as e:
                # IMAP protocol error
                if attempt < max_retries - 1:
                    print(f"IMAP error (attempt {attempt + 1}/{max_retries}): {e}")
                    try:
                        self.refresh_connection()
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    except RuntimeError:
                        continue
                else:
                    print(f"Error searching emails after {max_retries} attempts: {e}")
                    return []
            except Exception as e:
                # Unexpected error
                print(f"Unexpected error searching emails: {e}")
                return []

        return []

    def _build_search_criteria(self, subject: str, unread_only: bool) -> str:
        """Build IMAP search criteria string.

        Args:
            subject: Subject text to search for
            unread_only: Whether to only search unread emails

        Returns:
            IMAP search criteria string
        """
        if unread_only:
            return f'UNSEEN SUBJECT "{subject}"'
        return f'SUBJECT "{subject}"'

    def _fetch_messages(self, message_ids: list[bytes]) -> list[dict]:
        """Fetch and parse message details.

        Args:
            message_ids: List of IMAP message IDs to fetch

        Returns:
            List of parsed message dictionaries
        """
        messages = []

        for msg_id in message_ids:
            try:
                assert self.client is not None
                status, msg_data = self.client.fetch(msg_id.decode(), "(RFC822)")

                if status != "OK":
                    continue

                msg_tuple = msg_data[0]
                if isinstance(msg_tuple, tuple) and len(msg_tuple) > 1:
                    raw_email = msg_tuple[1]
                else:
                    continue
                msg = email.message_from_bytes(raw_email)

                messages.append(
                    {
                        "id": int(msg_id.decode()),
                        "subject": msg.get("Subject", ""),
                        "sender": msg.get("From", ""),
                        "body": self._extract_body(msg),
                    }
                )
            except (ValueError, IndexError, email.errors.MessageError):
                continue

        return messages

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract email body from message.

        Handles multipart messages and extracts plain text or HTML content.

        Args:
            msg: Email message object

        Returns:
            Email body text
        """
        if msg.is_multipart():
            return self._extract_multipart_body(msg)
        return self._extract_single_body(msg)

    def _extract_multipart_body(self, msg: email.message.Message) -> str:
        """Extract body from multipart message.

        Prefers plain text, falls back to HTML.

        Args:
            msg: Multipart email message

        Returns:
            Extracted body text
        """
        body = ""

        for part in msg.walk():
            content_type = part.get_content_type()

            # Prefer plain text
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode("utf-8")
                        break
                except Exception:
                    continue

            # Fall back to HTML
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode("utf-8")
                except Exception:
                    continue

        return body

    def _extract_single_body(self, msg: email.message.Message) -> str:
        """Extract body from single-part message.

        Args:
            msg: Single-part email message

        Returns:
            Extracted body text
        """
        try:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload.decode("utf-8")
            return str(payload)
        except Exception:
            payload = msg.get_payload()
            if isinstance(payload, str):
                return payload
            return str(payload)

    def mark_as_read(self, message_ids: list[int]) -> bool:
        """Mark emails as read in Gmail.

        Args:
            message_ids: List of Gmail message IDs to mark as read

        Returns:
            True if successful, False otherwise
        """
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                # Ensure connection is healthy
                self._ensure_connection()

                assert self.client is not None
                for msg_id in message_ids:
                    self.client.store(str(msg_id), "+FLAGS", "\\Seen")
                return True
            except (socket.error, EOFError) as e:
                if attempt < max_retries - 1:
                    print(
                        f"Connection error marking emails as read (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    try:
                        self.refresh_connection()
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    except RuntimeError:
                        continue
                else:
                    print(f"Error marking emails as read after {max_retries} attempts: {e}")
                    return False
            except imaplib.IMAP4.error as e:
                if attempt < max_retries - 1:
                    print(
                        f"IMAP error marking emails as read (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    try:
                        self.refresh_connection()
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    except RuntimeError:
                        continue
                else:
                    print(f"Error marking emails as read after {max_retries} attempts: {e}")
                    return False
            except Exception as e:
                print(f"Unexpected error marking emails as read: {e}")
                return False

        return False

    def extract_links(self, body: str) -> list[str]:
        """Extract all URLs from email body.

        Handles various formats:
        - Plain URLs: https://example.com
        - HTML href: href="https://example.com"
        - Angle brackets: <https://example.com>
        - Quoted-printable encoded (with = line breaks)

        Args:
            body: Email body text (HTML or plain text)

        Returns:
            List of unique URLs found in the body
        """
        if not body:
            return []

        # First, clean up quoted-printable encoding (remove trailing = for line breaks)
        # This handles emails encoded with Content-Transfer-Encoding: quoted-printable
        cleaned_body = body.replace("=\n", "").replace("=\r\n", "")

        # Multiple regex patterns to catch different URL formats
        url_patterns = [
            r"https?://[^\s<>\"\';,\)]+",  # Plain URLs
            r"href=['\"]([^'\"]+)['\"]",  # HTML href attributes
            r"<(https?://[^>]+)>",  # URLs in angle brackets
        ]

        urls = []

        for pattern in url_patterns:
            matches = re.findall(pattern, cleaned_body, re.IGNORECASE)

            for match in matches:
                # Handle tuple results from grouped regex
                if isinstance(match, tuple):
                    url = match[0] if match[0] else ""
                else:
                    url = match

                # Validate and clean URL
                if url and isinstance(url, str) and url.startswith(("http://", "https://")):
                    # Remove trailing characters that might have been captured
                    while url and url[-1] in ">'))\"';,":
                        url = url[:-1]
                    urls.append(url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def extract_links_with_text(self, body: str) -> list[tuple[str, str]]:
        """Extract URLs and their associated text from email body.

        For HTML emails, extracts text from <a> tags.
        For plain text, tries to find nearby text context for URLs.

        Args:
            body: Email body text (HTML or plain text)

        Returns:
            List of tuples (url, link_text) found in the body
        """
        if not body:
            return []

        # Clean up quoted-printable encoding
        cleaned_body = body.replace("=\n", "").replace("=\r\n", "")

        links_with_text: list[tuple[str, str]] = []

        # Try to extract HTML anchor tags with their text
        # Pattern: <a href="url">text</a> or <a href='url'>text</a>
        html_link_pattern = r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        html_matches = re.finditer(html_link_pattern, cleaned_body, re.IGNORECASE)

        seen_urls = set()

        for match in html_matches:
            url = match.group(1).strip()
            link_text = match.group(2).strip()

            # Validate URL
            if url and isinstance(url, str) and url.startswith(("http://", "https://")):
                # Remove trailing characters that might have been captured
                while url and url[-1] in ">'))\"';,":
                    url = url[:-1]

                # Avoid duplicates
                if url not in seen_urls:
                    seen_urls.add(url)
                    links_with_text.append((url, link_text))

        # If no HTML links found, try plain text extraction with context
        if not links_with_text:
            links_with_text = self._extract_plain_text_links(cleaned_body, seen_urls)

        return links_with_text

    def _extract_plain_text_links(self, body: str, seen_urls: set) -> list[tuple[str, str]]:
        """Extract links from plain text email with associated text.

        Looks for text appearing near URLs (e.g., "Go to task" followed by <URL>).

        Args:
            body: Email body text
            seen_urls: Set of already seen URLs to avoid duplicates

        Returns:
            List of (url, link_text) tuples
        """
        links_with_text: list[tuple[str, str]] = []

        # Split body into lines for context analysis
        lines = body.split("\n")

        # Pattern to find URLs
        url_pattern = r"https?://[^\s<>\"\';,\)]*[^\s<>\"\';,\).]"

        for i, line in enumerate(lines):
            # Check if this line contains a URL
            url_matches = re.finditer(url_pattern, line)

            for url_match in url_matches:
                url = url_match.group(0).strip()

                # Remove trailing characters that might have been captured
                while url and url[-1] in ">'))\"';,.":
                    url = url[:-1]

                # Validate URL
                if not url or not url.startswith(("http://", "https://")):
                    continue

                if url in seen_urls:
                    continue

                # Look for text in previous lines (within last 3 lines)
                link_text = ""
                for prev_idx in range(max(0, i - 3), i):
                    prev_line = lines[prev_idx].strip()
                    # Skip empty lines, lines with only URLs, and lines that are
                    # clearly headers/noise
                    if prev_line and not prev_line.startswith("http") and len(prev_line) < 100:
                        # Take the last non-empty line as potential link text
                        link_text = prev_line

                seen_urls.add(url)
                links_with_text.append((url, link_text))

        return links_with_text

    def close(self) -> None:
        """Close IMAP connection."""
        if self.client:
            try:
                self.client.logout()
            except Exception:
                pass
