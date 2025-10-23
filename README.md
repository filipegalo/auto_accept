# Auto-Accept

Automated email scanning and browser automation tool for processing emails from your Gmail inbox and performing actions on web platforms.

## Features

- =� **Gmail Integration** - Scan Gmail inbox for emails matching your criteria
- < **Browser Automation** - Automatically open links in Chrome browser
- =� **Smart Element Clicking** - Click buttons/elements on pages by text matching
- = **Platform Login** - Automated login to Smartcat (extensible for other platforms)
- =� **Multi-Profile Support** - Create and manage multiple automation profiles
- =� **Local Configuration** - All data stored locally, never sent to external servers

## Quick Start

### Installation

=I **See [INSTALL.md](INSTALL.md) for detailed installation instructions for Windows and Mac**

### Basic Usage

1. Download and run the executable
2. Create a configuration profile with your credentials
3. Application will scan Gmail and process emails matching your subject
4. Opens links and clicks elements automatically

## Requirements

- Windows 10/11 or macOS 11+
- Google Chrome installed
- Gmail account with app-specific password
- Account on your desired platform (e.g., Smartcat)

## What It Does

```
1. Scans Gmail inbox every 5 seconds
2. Finds unread emails matching your subject
3. Extracts links from emails
4. Opens links in Chrome
5. Automatically clicks configured elements
6. Marks emails as read
```

## Configuration

Each profile stores:
- Gmail credentials (for email scanning)
- Platform credentials (for platform login)
- Email subject to search for
- Optional: Element text to click

Profiles are saved locally in `~/.auto_accept/configs/` with restricted permissions.

## Security

All credentials are encrypted using AES-128 encryption (Fernet) and stored locally with restricted file permissions. URLs are validated to prevent malicious navigation and SSRF attacks. Password input is masked during entry to prevent terminal history leakage.

## Supported Platforms

- **Smartcat** - Translation management platform (currently implemented)
- More platforms can be added

## For Developers

See [CLAUDE.md](CLAUDE.md) for architecture and technical details.

## License

MIT - See [LICENSE](LICENSE) for details

## Support

For installation issues, see [INSTALL.md](INSTALL.md) troubleshooting section.

For architecture and development questions, see [CLAUDE.md](CLAUDE.md).
