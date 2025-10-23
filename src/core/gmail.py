"""Gmail IMAP integration module."""

import email
import imaplib
import re
from typing import Optional

from ..config import GMAIL_IMAP_PORT, GMAIL_IMAP_SERVER


class GmailHandler:
    """Handles Gmail operations using IMAP protocol."""

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
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Gmail IMAP server.

        Raises:
            RuntimeError: If authentication fails
        """
        try:
            self.client = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
            self.client.login(self.email_address, self.password)
            print("✓ Gmail IMAP connection successful")
        except imaplib.IMAP4.error as e:
            raise RuntimeError(f"Failed to connect to Gmail: {e}") from e

    def search_emails(self, subject: str, unread_only: bool = True) -> list[dict]:
        """Search for emails with subject containing the given text.

        Uses IMAP SUBJECT search which does case-insensitive substring matching.

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
        try:
            assert self.client is not None
            self.client.select("INBOX")

            # Build IMAP search criteria (SUBJECT does substring matching)
            search_criteria = self._build_search_criteria(subject, unread_only)
            status, message_ids = self.client.search(None, search_criteria)

            if status != "OK":
                return []

            return self._fetch_messages(message_ids[0].split())

        except imaplib.IMAP4.error as e:
            print(f"Error searching emails: {e}")
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
        try:
            assert self.client is not None
            for msg_id in message_ids:
                self.client.store(str(msg_id), "+FLAGS", "\\Seen")
            return True
        except imaplib.IMAP4.error as e:
            print(f"Error marking emails as read: {e}")
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

    def close(self) -> None:
        """Close IMAP connection."""
        if self.client:
            try:
                self.client.logout()
            except Exception:
                pass
