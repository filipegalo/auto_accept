"""Application constants and configuration."""

from pathlib import Path

# Gmail IMAP settings
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993

# Application paths
CONFIG_DIR = Path.home() / ".auto_accept"
CONFIGS_DIR = CONFIG_DIR / "configs"
CONFIG_FILE = CONFIG_DIR / "config.json"  # Legacy, kept for backwards compatibility
PROCESSED_EMAILS_FILE = CONFIG_DIR / "processed_emails.json"

# Scanning settings
DEFAULT_SCAN_INTERVAL = 5  # seconds

# File permissions
CONFIG_FILE_PERMISSIONS = 0o600  # Read/write for owner only

# Configuration keys (for profile configs)
# Gmail credentials for email scanning
CONFIG_KEY_EMAIL = "email"
CONFIG_KEY_PASSWORD = "password"
# Platform and login settings
CONFIG_KEY_PLATFORM = "platform"
CONFIG_KEY_PLATFORM_EMAIL = "platform_email"
CONFIG_KEY_PLATFORM_PASSWORD = "platform_password"
# Email automation settings
CONFIG_KEY_EMAIL_SUBJECT = "email_subject"
CONFIG_KEY_LINK_TEXT = "link_text"

# Supported platforms
SUPPORTED_PLATFORMS = ["smartcat"]
