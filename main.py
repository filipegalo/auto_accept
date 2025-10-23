"""Main entry point for auto-accept email automation application.

Features:
- Real-time Gmail inbox monitoring
- Automated browser link opening
- Smart element clicking with Vue.js support
- Encrypted credential storage with AES-128 encryption
- URL validation preventing malicious navigation and SSRF attacks
"""

from src.config import (
    CONFIG_KEY_EMAIL,
    CONFIG_KEY_EMAIL_SUBJECT,
    CONFIG_KEY_LINK_FILTER_TEXT,
    CONFIG_KEY_LINK_TEXT,
    CONFIG_KEY_PASSWORD,
    CONFIG_KEY_PLATFORM,
    CONFIG_KEY_PLATFORM_EMAIL,
    CONFIG_KEY_PLATFORM_PASSWORD,
)
from src.core import EmailScanner
from src.utils import ConfigManager, ui


def main() -> None:
    """
    Main function for the auto-accept application.

    Handles user greeting, configuration initialization, and starts the email scanner service.
    """
    ui.print_welcome()

    # Load or initialize configuration
    config = ConfigManager.initialize()

    # Create and start email scanner
    scanner = EmailScanner(
        email=config[CONFIG_KEY_EMAIL],
        password=config[CONFIG_KEY_PASSWORD],
        platform=config[CONFIG_KEY_PLATFORM],
        platform_email=config[CONFIG_KEY_PLATFORM_EMAIL],
        platform_password=config[CONFIG_KEY_PLATFORM_PASSWORD],
        subject=config[CONFIG_KEY_EMAIL_SUBJECT],
        link_filter_text=config.get(CONFIG_KEY_LINK_FILTER_TEXT),
        link_text=config.get(CONFIG_KEY_LINK_TEXT),
    )
    scanner.start()


if __name__ == "__main__":
    main()
