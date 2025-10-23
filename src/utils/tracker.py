"""Email tracking utilities for processed email persistence."""

import json
from typing import Set

from ..config import CONFIG_DIR, PROCESSED_EMAILS_FILE


class EmailTracker:
    """Tracks processed emails to prevent re-processing."""

    def __init__(self) -> None:
        """Initialize email tracker."""
        self._processed_ids = self._load()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Set[str]:
        """Load previously processed email IDs from file.

        Returns:
            Set of processed email IDs
        """
        if PROCESSED_EMAILS_FILE.exists():
            try:
                with open(PROCESSED_EMAILS_FILE, "r") as f:
                    data = json.load(f)
                    return set(data.get("processed_ids", []))
            except (json.JSONDecodeError, IOError):
                return set()
        return set()

    def _save(self) -> None:
        """Save processed email IDs to file."""
        self._ensure_config_dir()
        with open(PROCESSED_EMAILS_FILE, "w") as f:
            json.dump({"processed_ids": list(self._processed_ids)}, f, indent=2)

    def mark_as_processed(self, email_id: str) -> None:
        """Mark an email as processed.

        Args:
            email_id: Email ID to mark as processed
        """
        self._processed_ids.add(email_id)
        self._save()

    def is_processed(self, email_id: str) -> bool:
        """Check if an email has been processed.

        Args:
            email_id: Email ID to check

        Returns:
            True if email has been processed, False otherwise
        """
        return email_id in self._processed_ids

    def get_processed_count(self) -> int:
        """Get count of processed emails.

        Returns:
            Number of processed emails
        """
        return len(self._processed_ids)
