"""Core modules for auto-accept email automation."""

from .browser import BrowserAutomation
from .gmail import GmailHandler
from .scanner import EmailScanner

__all__ = ["GmailHandler", "EmailScanner", "BrowserAutomation"]
