"""Terminal UI formatting utilities for better user experience."""

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_header(title: str) -> None:
    """Print a formatted section header."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{title.center(60)}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    console.print(f"[bold magenta]--- {title} ---[/bold magenta]")


def print_success(message: str, indent: int = 0) -> None:
    """Print a success message in green."""
    prefix = "  " * indent
    console.print(f"{prefix}[green]✓[/green] [green]{message}[/green]")


def print_error(message: str, indent: int = 0) -> None:
    """Print an error message in red."""
    prefix = "  " * indent
    console.print(f"{prefix}[red]✗[/red] [red]{message}[/red]")


def print_warning(message: str, indent: int = 0) -> None:
    """Print a warning message in yellow."""
    prefix = "  " * indent
    console.print(f"{prefix}[yellow]⚠[/yellow] [yellow]{message}[/yellow]")


def print_info(message: str, indent: int = 0) -> None:
    """Print an info message in blue."""
    prefix = "  " * indent
    console.print(f"{prefix}[cyan]ℹ[/cyan] [cyan]{message}[/cyan]")


def print_profiles_table(profiles_data: list[dict]) -> None:
    """Print profiles in a formatted table."""
    table = Table(
        title="Available Configuration Profiles", show_header=True, header_style="bold magenta"
    )

    table.add_column("Index", style="cyan", width=8)
    table.add_column("Profile Name", style="green", width=20)
    table.add_column("Gmail", style="yellow", width=25)
    table.add_column("Platform", style="blue", width=15)
    table.add_column("Subject", style="white", width=25)

    for item in profiles_data:
        table.add_row(
            str(item["index"]),
            item["name"],
            item["gmail"],
            item["platform"],
            item["subject"][:20] + "..." if len(item["subject"]) > 20 else item["subject"],
        )

    console.print(table)


def print_status_panel(title: str, content: dict) -> None:
    """Print a status panel with information."""
    lines = []
    for key, value in content.items():
        lines.append(f"[bold]{key}:[/bold] {value}")

    panel_content = "\n".join(lines)
    panel = Panel(panel_content, title=title, border_style="cyan", expand=False)
    console.print(panel)


def print_email_status(sender: str, subject: str, link_count: int, indent: int = 1) -> None:
    """Print formatted email processing status."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "  " * indent
    console.print(f"{prefix}[cyan][{timestamp}][/cyan] [green]✓ Email processed[/green]")
    console.print(f"{'  ' * (indent + 1)}[yellow]From:[/yellow] {sender}")
    console.print(f"{'  ' * (indent + 1)}[yellow]Subject:[/yellow] {subject}")
    console.print(f"{'  ' * (indent + 1)}[yellow]Links found:[/yellow] {link_count}")


def print_action_item(action: str, status: str, indent: int = 1) -> None:
    """Print a formatted action item with status."""
    prefix = "  " * indent
    if status.lower() == "success" or status.lower() == "✓":
        console.print(f"{prefix}[green]✓[/green] {action}")
    elif status.lower() == "error" or status.lower() == "✗":
        console.print(f"{prefix}[red]✗[/red] {action}")
    elif status.lower() == "pending" or status.lower() == "...":
        console.print(f"{prefix}[yellow]⧖[/yellow] {action}")
    else:
        console.print(f"{prefix}{status} {action}")


def print_startup_info(platform: str, subject: str, link_text: str | None, interval: int) -> None:
    """Print startup information in a formatted panel."""
    content = {
        "Platform": f"[bold magenta]{platform.capitalize()}[/bold magenta]",
        "Scan Subject": f"[bold yellow]'{subject}'[/bold yellow]",
        "Click Element": f"[bold cyan]{link_text or 'None (links only)'}[/bold cyan]",
        "Check Interval": f"[bold green]{interval}s[/bold green]",
    }
    print_status_panel("Automation Configuration", content)
    console.print("\n[bold yellow]Press Ctrl+C to stop[/bold yellow]\n")


def print_welcome() -> None:
    """Print welcome message."""
    console.print(
        "\n[bold cyan]╔════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    console.print(
        "[bold cyan]║[/bold cyan]  [bold green]Welcome to Auto-Accept Email Automation[/bold green]  [bold cyan]║[/bold cyan]"
    )
    console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════╝[/bold cyan]\n"
    )
