"""Configuration initialization and management."""

import getpass
import json
import os
import sys
from pathlib import Path
from typing import Optional

from ..config import (
    CONFIG_DIR,
    CONFIG_FILE_PERMISSIONS,
    CONFIG_KEY_EMAIL,
    CONFIG_KEY_EMAIL_SUBJECT,
    CONFIG_KEY_LINK_FILTER_TEXT,
    CONFIG_KEY_LINK_TEXT,
    CONFIG_KEY_PASSWORD,
    CONFIG_KEY_PLATFORM,
    CONFIG_KEY_PLATFORM_EMAIL,
    CONFIG_KEY_PLATFORM_PASSWORD,
    CONFIGS_DIR,
    SUPPORTED_PLATFORMS,
)
from . import crypto, ui


class ConfigManager:
    """Manages application configuration with support for multiple named profiles."""

    @staticmethod
    def _ensure_dirs() -> None:
        """Ensure configuration directories exist."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_config_path(profile_name: str) -> Path:
        """Get the file path for a named configuration profile.

        Args:
            profile_name: Name of the configuration profile

        Returns:
            Path object for the config file
        """
        # Sanitize profile name to avoid directory traversal
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in "-_")
        if not safe_name:
            raise ValueError("Invalid profile name")
        return CONFIGS_DIR / f"{safe_name}.json"

    @staticmethod
    def load(profile_name: str) -> Optional[dict]:
        """Load existing configuration profile.

        Args:
            profile_name: Name of the profile to load

        Returns:
            Configuration dictionary or None if not found
        """
        config_path = ConfigManager._get_config_path(profile_name)
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Decrypt sensitive fields
                        try:
                            return crypto.CredentialCrypto.decrypt_config(data)
                        except RuntimeError as e:
                            ui.print_error(str(e))
                            return None
                    return None
            except (json.JSONDecodeError, IOError):
                return None

        return None

    @staticmethod
    def save(config: dict, profile_name: str) -> None:
        """Save configuration to named profile with restricted permissions.

        Sensitive credentials are encrypted before storing.

        Args:
            config: Configuration dictionary to save
            profile_name: Name of the profile to save as
        """
        ConfigManager._ensure_dirs()
        config_path = ConfigManager._get_config_path(profile_name)

        # Encrypt sensitive fields before saving
        encrypted_config = crypto.CredentialCrypto.encrypt_config(config)

        with open(config_path, "w") as f:
            json.dump(encrypted_config, f, indent=2)
        os.chmod(config_path, CONFIG_FILE_PERMISSIONS)

    @staticmethod
    def list_profiles() -> list[str]:
        """List all available configuration profiles.

        Returns:
            List of profile names (without .json extension)
        """
        ConfigManager._ensure_dirs()

        if not CONFIGS_DIR.exists():
            return []

        profiles = []
        for config_file in CONFIGS_DIR.glob("*.json"):
            profiles.append(config_file.stem)

        return sorted(profiles)

    @staticmethod
    def delete_profile(profile_name: str) -> bool:
        """Delete a configuration profile.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = ConfigManager._get_config_path(profile_name)
            if config_path.exists():
                config_path.unlink()
                return True
        except Exception:
            pass

        return False

    @staticmethod
    def _prompt_gmail_credentials() -> tuple[str, str]:
        """Prompt for Gmail credentials.

        Uses getpass for password masking and displays security warning.
        """
        ui.print_subsection("Gmail Credentials (for email scanning)")
        email = input("Enter your Gmail email address: ").strip()
        if not email:
            raise ValueError("Gmail email cannot be empty")

        # Use getpass to mask password input
        password = getpass.getpass("Enter your Gmail password (or app-specific password): ")
        if not password:
            raise ValueError("Gmail password cannot be empty")

        ui.print_success("Gmail credentials saved (encrypted)")
        ui.print_info(
            "💡 Credentials are encrypted with a unique key stored on your computer",
            indent=1,
        )
        return email, password

    @staticmethod
    def _prompt_platform_selection() -> str:
        """Prompt for platform selection."""
        ui.print_subsection("Platform Selection (for login automation)")
        ui.console.print("Available platforms:")
        for i, plat in enumerate(SUPPORTED_PLATFORMS, 1):
            ui.console.print(f"  [cyan]{i}.[/cyan] [magenta]{plat.capitalize()}[/magenta]")
        while True:
            choice = input(f"\nSelect platform (1-{len(SUPPORTED_PLATFORMS)}): ").strip()
            try:
                platform_idx = int(choice) - 1
                if 0 <= platform_idx < len(SUPPORTED_PLATFORMS):
                    platform = SUPPORTED_PLATFORMS[platform_idx]
                    ui.print_success(f"Platform selected: {platform.capitalize()}")
                    return platform
                ui.print_warning("Invalid selection")
            except ValueError:
                ui.print_warning("Please enter a valid number")

    @staticmethod
    def _prompt_platform_credentials(platform: str) -> tuple[str, str]:
        """Prompt for platform credentials.

        Uses getpass for password masking.
        """
        ui.print_subsection(f"{platform.capitalize()} Credentials (for login)")
        platform_email = input(f"Enter your {platform.capitalize()} email address: ").strip()
        if not platform_email:
            raise ValueError(f"{platform.capitalize()} email cannot be empty")

        # Use getpass to mask password input
        platform_password = getpass.getpass(f"Enter your {platform.capitalize()} password: ")
        if not platform_password:
            raise ValueError(f"{platform.capitalize()} password cannot be empty")

        ui.print_success(f"{platform.capitalize()} credentials saved (encrypted)")
        return platform_email, platform_password

    @staticmethod
    def _prompt_email_settings() -> tuple[str, str, str]:
        """Prompt for email automation settings."""
        ui.print_subsection("Email Automation Settings")
        subject = input("Enter the subject of the email to look for: ").strip()
        if not subject:
            raise ValueError("Subject cannot be empty")
        ui.print_success(f"Subject configured: '{subject}'")

        ui.print_subsection("Link Filtering (Optional)")
        filter_option = (
            input("Do you want to filter which links to open? (yes/no): ").strip().lower()
        )
        link_filter_text = ""
        if filter_option == "yes":
            link_filter_text = input(
                "Enter the text of the link to open (e.g., 'Go to task', 'View details'): "
            ).strip()
            if not link_filter_text:
                ui.print_warning("No link text specified - will open all links")
            else:
                ui.print_success(
                    f"Link filter configured: Only links with text '{link_filter_text}' will be opened"
                )
        else:
            ui.print_info("Link filtering disabled - all links will be opened")

        ui.print_subsection("Button/Element Clicking (Optional)")
        click_option = (
            input("Do you want to click a button/element when links are opened? (yes/no): ")
            .strip()
            .lower()
        )
        link_text = ""
        if click_option == "yes":
            link_text = input("Enter the text/label of the button/element to click: ").strip()
            if not link_text:
                ui.print_warning("No button text - will only open links")
            else:
                ui.print_success(f"Button text configured: '{link_text}'")
        else:
            ui.print_info("Button clicking disabled")
        return subject, link_filter_text, link_text

    @staticmethod
    def prompt_for_credentials() -> dict:
        """Prompt user interactively for configuration.

        Returns:
            Configuration dictionary with user inputs
        """
        ui.print_header("Create New Configuration Profile")
        email, password = ConfigManager._prompt_gmail_credentials()
        platform = ConfigManager._prompt_platform_selection()
        platform_email, platform_password = ConfigManager._prompt_platform_credentials(platform)
        subject, link_filter_text, link_text = ConfigManager._prompt_email_settings()

        config = {
            CONFIG_KEY_EMAIL: email,
            CONFIG_KEY_PASSWORD: password,
            CONFIG_KEY_PLATFORM: platform,
            CONFIG_KEY_PLATFORM_EMAIL: platform_email,
            CONFIG_KEY_PLATFORM_PASSWORD: platform_password,
            CONFIG_KEY_EMAIL_SUBJECT: subject,
        }
        if link_filter_text:
            config[CONFIG_KEY_LINK_FILTER_TEXT] = link_filter_text
        if link_text:
            config[CONFIG_KEY_LINK_TEXT] = link_text
        return config

    @staticmethod
    def prompt_for_profile_name() -> str:
        """Prompt user for a configuration profile name.

        Returns:
            Profile name

        Raises:
            ValueError: If profile name is empty
        """
        while True:
            profile_name = input("\nEnter a name for this configuration profile: ").strip()
            if not profile_name:
                print("⚠ Profile name cannot be empty")
                continue

            # Check if profile already exists
            if ConfigManager.load(profile_name) is not None:
                response = (
                    input(f"Profile '{profile_name}' already exists. Overwrite? (yes/no): ")
                    .strip()
                    .lower()
                )
                if response == "yes":
                    break
            else:
                break

        return profile_name

    @staticmethod
    def select_profile() -> Optional[str]:
        """Let user select from existing profiles.

        Returns:
            Selected profile name or None if user cancels
        """
        profiles = ConfigManager.list_profiles()

        if not profiles:
            ui.print_error("No configuration profiles found.")
            return None

        ui.print_header("Select Configuration Profile")

        # Prepare data for table
        profiles_data = []
        for i, profile in enumerate(profiles, 1):
            config = ConfigManager.load(profile)
            if config:
                profiles_data.append(
                    {
                        "index": i,
                        "name": profile,
                        "gmail": config.get(CONFIG_KEY_EMAIL, "Unknown"),
                        "platform": config.get(CONFIG_KEY_PLATFORM, "Unknown"),
                        "subject": config.get(CONFIG_KEY_EMAIL_SUBJECT, "Unknown"),
                    }
                )

        ui.print_profiles_table(profiles_data)

        while True:
            try:
                choice = input("\nSelect profile number (or press Enter to cancel): ").strip()
                if not choice:
                    return None

                index = int(choice) - 1
                if 0 <= index < len(profiles):
                    ui.print_success(f"Profile '{profiles[index]}' selected")
                    return profiles[index]
                else:
                    ui.print_warning("Invalid selection")
            except ValueError:
                ui.print_warning("Please enter a valid number")

    @staticmethod
    def initialize() -> dict:
        """Initialize configuration with profile selection menu.

        Provides options to:
        - Select an existing profile
        - Create a new profile

        Returns:
            Configuration dictionary
        """
        while True:
            profiles = ConfigManager.list_profiles()

            ui.print_header("Auto-Accept Configuration Manager")

            ui.console.print("[bold cyan]Options:[/bold cyan]")
            ui.console.print("  [cyan][1][/cyan] Use existing profile")
            ui.console.print("  [cyan][2][/cyan] Create new profile")
            ui.console.print("  [cyan][3][/cyan] Exit")

            choice = input("\nSelect option (1/2/3): ").strip()

            if choice == "1":
                if profiles:
                    selected = ConfigManager.select_profile()
                    if selected:
                        config = ConfigManager.load(selected)
                        if config:
                            ui.print_success(f"Using profile: {selected}\n")
                            return config
                else:
                    ui.print_error("No profiles found. Create one first!")
                    continue

            elif choice == "2":
                # Create new profile
                config = ConfigManager.prompt_for_credentials()
                profile_name = ConfigManager.prompt_for_profile_name()
                ConfigManager.save(config, profile_name)
                ui.print_success(f"Configuration profile '{profile_name}' saved successfully!\n")
                return config

            elif choice == "3":
                ui.console.print("\n[yellow]Exiting...[/yellow]")
                sys.exit(0)

            else:
                ui.print_warning("Invalid option, please try again")
