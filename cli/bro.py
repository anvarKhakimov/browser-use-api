#!/usr/bin/env python3
"""Browser-Use CLI - Simple command-line interface for Browser-Use API."""

import sys
import json
import time
import os
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from rich.console import Console
from rich.spinner import Spinner
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from rich.rule import Rule
from rich import print as rprint

console = Console()

# Configuration
CONFIG_FILE = Path.home() / ".broconfig"
DEFAULT_API_URL = "http://localhost:8765"
DEFAULT_MAX_STEPS = 10
DEFAULT_TIMEOUT = 120


def load_config() -> Dict[str, Any]:
    """Load configuration from file or use defaults."""
    config = {
        "api_url": DEFAULT_API_URL,
        "max_steps": DEFAULT_MAX_STEPS,
        "timeout": DEFAULT_TIMEOUT
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception:
            pass

    # Allow environment variable override
    if os.environ.get("BRO_API_URL"):
        config["api_url"] = os.environ["BRO_API_URL"]

    return config


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        console.print(f"[green]Configuration saved to {CONFIG_FILE}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save config: {e}[/red]")


def send_task(task: str, config: Dict[str, Any]) -> dict:
    """Send task to Browser-Use API."""
    url = f"{config['api_url']}/api/v1/search"

    payload = {
        "task": task,
        "max_steps": config["max_steps"],
        "timeout": config["timeout"]
    }

    try:
        with httpx.Client(timeout=config["timeout"] + 10) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to Browser-Use API at {config['api_url']}. Is the service running?"
        }
    except httpx.HTTPError as e:
        return {"status": "error", "error_message": str(e)}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {e}"}


def print_result(result: dict, verbose: bool = False):
    """Pretty print the result."""
    status = result.get("status", "unknown")

    if status == "success":
        console.print("\n[bold green]✓ Task completed successfully![/bold green]\n")

        # Main result
        result_text = result.get("result", "No result")
        panel = Panel(
            result_text,
            title="[bold blue]Result[/bold blue]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)

        # Metadata table
        if verbose:
            console.print("\n")
            table = Table(show_header=False, border_style="dim")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Steps taken", str(result.get('steps_taken', 0)))
            table.add_row("Execution time", f"{result.get('execution_time', 0):.2f}s")

            if result.get("model_used"):
                table.add_row("Model", result.get("model_used"))

            console.print(table)
        else:
            console.print(f"\n[dim]• Steps: {result.get('steps_taken', 0)} | Time: {result.get('execution_time', 0):.2f}s[/dim]")

        # URLs visited
        urls = result.get("urls_visited", [])
        if urls:
            console.print(f"\n[bold]URLs visited:[/bold]")
            for url in urls:
                console.print(f"  [link]{url}[/link]")

        # Actions performed (if verbose)
        if verbose and result.get("actions"):
            console.print("\n[bold]Actions performed:[/bold]")
            for i, action in enumerate(result.get("actions", []), 1):
                console.print(f"  {i}. {action}")

    elif status == "timeout":
        console.print("\n[bold yellow]⏱ Task timed out[/bold yellow]")
        error_msg = result.get('error_message', 'Task exceeded timeout')
        console.print(Panel(
            error_msg,
            title="[yellow]Timeout[/yellow]",
            border_style="yellow"
        ))

    elif status == "failed":
        console.print("\n[bold red]✗ Task failed[/bold red]")
        error_msg = result.get('error_message', 'Unknown error')
        console.print(Panel(
            error_msg,
            title="[red]Error[/red]",
            border_style="red"
        ))

    else:
        console.print("\n[bold red]✗ Error[/bold red]")
        error_msg = result.get('error_message', 'Unknown error')
        console.print(Panel(
            error_msg,
            title="[red]Error[/red]",
            border_style="red"
        ))


def show_help():
    """Show help information."""
    console.print("\n[bold blue]Browser-Use CLI Tool[/bold blue]")
    console.print("[dim]A command-line interface for the Browser-Use API[/dim]\n")

    console.print("[bold]Usage:[/bold]")
    console.print("  bro <task>                    Execute a browser task")
    console.print("  bro --config                  Show current configuration")
    console.print("  bro --set-url <url>          Set API URL")
    console.print("  bro --set-timeout <seconds>   Set timeout")
    console.print("  bro --set-steps <number>      Set max steps")
    console.print("  bro --verbose <task>          Execute with verbose output")
    console.print("  bro --json <task>            Output result as JSON")
    console.print("  bro --help                    Show this help message")

    console.print("\n[bold]Examples:[/bold]")
    examples = [
        "bro find top news on BBC",
        "bro go to example.com and take a screenshot",
        "bro search for latest AI news on HackerNews",
        "bro what's the weather in San Francisco",
        "bro --verbose find top trending GitHub repos today"
    ]

    for example in examples:
        console.print(f"  [cyan]{example}[/cyan]")

    console.print("\n[bold]Configuration:[/bold]")
    config = load_config()
    console.print(f"  API URL: {config['api_url']}")
    console.print(f"  Timeout: {config['timeout']}s")
    console.print(f"  Max Steps: {config['max_steps']}")
    console.print(f"  Config File: {CONFIG_FILE}")

    console.print("\n[dim]Environment variable BRO_API_URL overrides config file[/dim]")


def show_config():
    """Display current configuration."""
    config = load_config()

    console.print("\n[bold]Current Configuration:[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")

    api_url_source = "env" if os.environ.get("BRO_API_URL") else "config"
    table.add_row("API URL", config['api_url'], api_url_source)
    table.add_row("Timeout", f"{config['timeout']}s", "config")
    table.add_row("Max Steps", str(config['max_steps']), "config")
    table.add_row("Config File", str(CONFIG_FILE), "system")

    console.print(table)


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        show_help()
        sys.exit(0)

    config = load_config()

    # Handle configuration commands
    if "--config" in args:
        show_config()
        sys.exit(0)

    if "--set-url" in args:
        idx = args.index("--set-url")
        if idx + 1 < len(args):
            config["api_url"] = args[idx + 1]
            save_config(config)
            console.print(f"[green]API URL set to: {config['api_url']}[/green]")
        else:
            console.print("[red]Please provide a URL after --set-url[/red]")
        sys.exit(0)

    if "--set-timeout" in args:
        idx = args.index("--set-timeout")
        if idx + 1 < len(args):
            try:
                config["timeout"] = int(args[idx + 1])
                save_config(config)
                console.print(f"[green]Timeout set to: {config['timeout']}s[/green]")
            except ValueError:
                console.print("[red]Timeout must be a number[/red]")
        else:
            console.print("[red]Please provide a timeout value[/red]")
        sys.exit(0)

    if "--set-steps" in args:
        idx = args.index("--set-steps")
        if idx + 1 < len(args):
            try:
                config["max_steps"] = int(args[idx + 1])
                save_config(config)
                console.print(f"[green]Max steps set to: {config['max_steps']}[/green]")
            except ValueError:
                console.print("[red]Max steps must be a number[/red]")
        else:
            console.print("[red]Please provide a max steps value[/red]")
        sys.exit(0)

    # Handle verbose flag
    verbose = False
    if "--verbose" in args or "-v" in args:
        verbose = True
        args = [arg for arg in args if arg not in ["--verbose", "-v"]]

    # Handle JSON output flag
    json_output = False
    if "--json" in args:
        json_output = True
        args = [arg for arg in args if arg != "--json"]

    # Get task from remaining arguments
    task = " ".join(args)

    if not task:
        console.print("[red]Please provide a task[/red]")
        console.print("Use 'bro --help' for usage information")
        sys.exit(1)

    # Handle JSON output
    if json_output:
        # No fancy output for JSON mode
        result = send_task(task, config)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Show task with formatting
    console.print("\n")
    console.rule(f"[bold blue]Task: {task}[/bold blue]", style="blue")

    # Show spinner while processing
    with console.status("[bold green]Processing...", spinner="dots") as status:
        start_time = time.time()
        result = send_task(task, config)
        elapsed = time.time() - start_time

        # Add execution time if not already present
        if "execution_time" not in result:
            result["execution_time"] = elapsed

    # Print result
    print_result(result, verbose)

    # Add spacing at the end
    console.print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)