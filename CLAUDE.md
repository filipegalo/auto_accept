# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**auto-accept** is a Python automation tool (requires Python 3.14+) that automatically processes emails by finding emails with a specific subject, opening links within them, and clicking buttons.

The application starts with an interactive initialization flow that prompts for:
- Gmail email address
- Gmail password (or app-specific password)
- Email subject to search for (substring matching - will match any subject containing this text)
- Link text to click

Configuration is stored securely in `~/.auto_accept/config.json` with restricted permissions (600).

## Development Setup and Commands

### Install dependencies
```bash
uv sync
```

### Run the main application
```bash
uv run python main.py
```

### Code quality

The project uses **Ruff** for linting and formatting:
```bash
# Check for linting issues
ruff check .

# Format code
ruff format .

# Fix fixable issues
ruff check --fix .
```

## Project Structure

```
auto-accept/
├── src/                          # Main source code
│   ├── __init__.py              # Package initialization
│   ├── core/                    # Core automation logic
│   │   ├── __init__.py
│   │   ├── gmail.py             # Gmail IMAP integration
│   │   ├── scanner.py           # Email scanning orchestrator
│   │   └── browser.py           # Browser automation with Selenium
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── config_init.py       # Configuration management
│   │   └── tracker.py           # Email tracking persistence
│   └── config/                  # Configuration and constants
│       ├── __init__.py
│       └── constants.py         # Application constants
├── main.py                      # Application entry point
├── pyproject.toml               # Project configuration
├── CLAUDE.md                    # This file
└── .gitignore                   # Git ignore rules
```

### Configuration Files (created at runtime in `~/.auto_accept/`)
- **config.json**: User credentials and email subject/link text
- **processed_emails.json**: List of already processed email IDs

## Key Architecture

### 1. Configuration Flow (`src/utils/config_init.py`)

**ConfigManager** class handles all configuration operations:
- `initialize()`: Main entry point - loads existing config or prompts for new one
- `prompt_for_credentials()`: Interactive prompts for Gmail email, password, subject, and link text
- `save()`: Securely stores config with restricted file permissions (600)
- `load()`: Retrieves existing configuration

### 2. Email Scanning Flow (`src/core/scanner.py`)

**EmailScanner** class: Main scanning orchestrator
- `__init__`: Initializes with email, password, subject, link_text, and scan interval (default 5 seconds)
- `_initialize_browser()`: Set up browser automation
- `_scan_once()`: Performs single scan iteration
- `_process_email()`: Extract links and open them
- `_open_and_process_link()`: Open link and click button
- `start()`: Begins continuous scanning loop with 5-second intervals
- `stop()`: Stops the scanner
- `_cleanup()`: Close browser and Gmail connections
- Uses IMAP to search for unread emails with subject containing the search text (substring match)
- Marks matched emails as read in Gmail
- Extracts links from email body
- Opens links in Chrome using Selenium
- Clicks buttons/elements by text if configured
- Tracks processed emails locally to avoid re-processing
- Prints processing status with timestamps

### 3. Browser Automation (`src/core/browser.py`)

**BrowserAutomation** class: Selenium-based browser control
- `_initialize_driver()`: Set up Chrome WebDriver
- `_get_chrome_user_data_dir()`: Get Chrome profile path (preserves sessions)
- `open_url()`: Navigate to a URL in Chrome
- `click_element_by_text()`: Find and click element by text content
- `click_button_by_text()`: Convenience method for button clicks
- `wait_and_perform()`: Execute action with timeout
- `close()`: Close browser and cleanup
- Context manager support (`__enter__`, `__exit__`)
- Uses Chrome's existing user profile (sessions already authenticated)
- Waits for elements to be clickable before interacting
- Scrolls elements into view before clicking
- Handles stale element references gracefully

### 4. Gmail IMAP Integration (`src/core/gmail.py`)

**GmailHandler** class: Wraps IMAP operations
- `_connect()`: Establishes IMAP connection with Gmail
- `search_emails()`: Query unread emails by subject using IMAP (substring matching)
- `_extract_body()`: Extract email body from multipart messages
- `_extract_multipart_body()`: Handle multipart email parsing
- `_extract_single_body()`: Handle single-part email parsing
- `extract_links()`: Extract all URLs from email body using regex
- `mark_as_read()`: Mark emails as read via IMAP
- `close()`: Close IMAP connection
- Uses Python's built-in `imaplib` for IMAP protocol (no external dependencies)
- IMAP SUBJECT search does case-insensitive substring matching

### 5. Email Tracking (`src/utils/tracker.py`)

**EmailTracker** class: Persistent email tracking
- `_load()`: Retrieve previously processed email IDs
- `_save()`: Store processed email IDs to file
- `mark_as_processed()`: Add email ID to processed set
- `is_processed()`: Check if email has been processed
- `get_processed_count()`: Get total count of processed emails
- Stores data in `~/.auto_accept/processed_emails.json`

### 6. Configuration & Constants (`src/config/`)

Centralized configuration management:
- `constants.py`: Defines all application constants
  - Gmail IMAP server settings
  - Application paths
  - Scanning interval
  - Configuration keys
- `__init__.py`: Exports all constants for easy importing

### 7. Application Entry Point (`main.py`)

- Imports and initializes ConfigManager
- Creates EmailScanner instance
- Starts continuous scanning loop
- Clean, minimal main function with clear flow

## Dependencies

- **Dev**: ruff (code quality)
- **Runtime**:
  - `selenium>=4.15.0`: Browser automation with Chrome
  - `imaplib` (stdlib): IMAP protocol for Gmail
  - `email` (stdlib): Email parsing
  - `json` (stdlib): Configuration storage
  - `time` (stdlib): Interval timing
  - `re` (stdlib): Regex for link extraction
  - `urllib` (stdlib): URL parsing

The project uses UV for Python package management.

## Setup Notes

### Gmail Configuration

To use the app with Gmail:

1. **Enable IMAP access**: Go to Gmail settings → Forwarding and POP/IMAP → Enable IMAP
2. **Use app-specific password** (recommended if 2FA is enabled):
   - Go to myaccount.google.com → Security
   - Select "App passwords" and generate one for "Mail"
   - Use this password in the app instead of your account password
3. **Or enable less secure apps** (if 2FA is not enabled):
   - Go to myaccount.google.com → Security
   - Enable "Less secure app access"

### Browser Setup (Chrome)

The app uses Selenium to automate Chrome with existing sessions:

1. **Chrome must be installed** on your system
2. **Sessions are preserved**: The app uses your Chrome user profile, so:
   - You don't need to login again
   - Existing cookies and sessions are maintained
   - Browser is NOT in headless mode (you can see what's happening)
3. **Supported platforms**:
   - macOS: `~/Library/Application Support/Google/Chrome`
   - Windows: `~/AppData/Local/Google/Chrome/User Data`
   - Linux: `~/.config/google-chrome`

### Application Workflow

1. **Start the app**: `uv run python main.py`
2. **Configure on first run** (or update existing):
   - Gmail email address
   - Gmail password / app-specific password
   - Email subject to search for
   - Button/element text to click (optional)
3. **Scanner starts**:
   - Checks mailbox every 5 seconds
   - Finds unread emails with matching subject
   - Marks emails as read
   - **Extracts links** from email body
   - **Opens links in Chrome** using Selenium
   - **Clicks button/element** if text is configured
   - Tracks processed emails (won't re-process)
4. **Press Ctrl+C** to stop the scanner
5. **Browser and connections close** automatically

## Code Quality Standards

### Type Hints
- All function parameters and return types are annotated
- Use Optional[] for nullable values
- Import from typing module

### Docstrings
- All modules, classes, and public methods have docstrings
- Use Google-style format with Args, Returns, and Raises sections
- Include examples in complex functions

### Code Organization
- One main class per file with supporting private methods
- Clear separation of concerns (core logic, utils, config)
- Private methods prefixed with underscore
- Group related functionality together

### Error Handling
- Catch specific exceptions, not generic Exception
- Provide helpful error messages
- Raise RuntimeError for critical failures
- Print warnings for non-critical errors

## Development Workflow

1. **New Features**: Place business logic in `src/core/`, utilities in `src/utils/`
2. **Configuration**: Add to `src/config/constants.py`, export via `__init__.py`
3. **Type Safety**: Always add type hints to function signatures
4. **Documentation**: Write docstrings before implementation
5. **Testing**: Use test inputs to validate changes work correctly

## Next Steps

Future phases:
1. Extract links from email bodies
2. Implement browser automation to click buttons
3. Add logging system
4. Add configuration management CLI
5. Add retry logic for failed actions
6. Add email filtering options (from, date range, etc.)
