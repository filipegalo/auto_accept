"""Main entry point for auto-accept email automation application."""

from src.config import (
    CONFIG_KEY_EMAIL,
    CONFIG_KEY_EMAIL_SUBJECT,
    CONFIG_KEY_LINK_TEXT,
    CONFIG_KEY_PASSWORD,
    CONFIG_KEY_PLATFORM,
    CONFIG_KEY_PLATFORM_EMAIL,
    CONFIG_KEY_PLATFORM_PASSWORD,
)
from src.core import EmailScanner
from src.utils import ConfigManager, ui


def main() -> None:
    """Main entry point for auto-accept application.

    Initializes configuration and starts the email scanner.
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
        link_text=config.get(CONFIG_KEY_LINK_TEXT),
    )
    scanner.start()


if __name__ == "__main__":
    main()
