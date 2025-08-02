#!/usr/bin/env python3
import argparse
import os
import sys
import time
import requests
import tomllib
import io  # needed for capturing help output

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

CONFIG_DIR = os.path.expanduser("~/.config/pastebincli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.toml")

def first_time_setup():
    console.print("[bold magenta]== First time setup for pastebincli ==[/bold magenta]")
    time.sleep(1)
    apikey = Prompt.ask(
        "\n[cyan]You need a Pastebin API key to use this application.[/cyan]\n"
        "Go to [blue]https://pastebin.com/doc_api[/blue], login, and paste your API key here"
    )
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        f.write(f'api_key = "{apikey}"\n')
    console.print(f"[green]✓ Config saved at[/green] [italic]{CONFIG_FILE}[/italic]")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        console.print("[red]Config not found.[/red] Run [bold]pastebincli config[/bold] first.")
        sys.exit(1)
    with open(CONFIG_FILE, 'rb') as f:
        return tomllib.load(f)

def create_paste_interactive(config):
    console.print("[bold magenta]Create a paste (interactive mode)[/bold magenta]\n")
    title = Prompt.ask("title")
    text = Prompt.ask("text")
    private = Prompt.ask("private? (yes/no)", default="no")
    expire = Prompt.ask("expire time (e.g. 10M, 1H, 1D)", default="10M")
    format = Prompt.ask("format (python, bash, etc)", default="text")

    console.print("\n[bold]Confirm:[/bold]")
    console.print(f"[bold]Title:[/bold] {title}")
    console.print(f"[bold]Text:[/bold] {text}")
    console.print(f"[bold]Private:[/bold] {private}")
    console.print(f"[bold]Expire:[/bold] {expire}")
    console.print(f"[bold]Format:[/bold] {format}")
    confirm = Prompt.ask("continue? (y/n)", default="y")
    if confirm.lower() not in ("y", "yes"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    send_paste(title, text, private, expire, format, config)

def create_paste_from_args(args, config):
    if args.file:
        if not os.path.exists(args.file):
            console.print(f"[red]Error:[/red] file '{args.file}' not found.")
            return
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        console.print("[red]Error:[/red] Need --text or --file.")
        return

    title = args.title or "untitled"
    private = args.private or "no"
    expire = args.expire or "10M"
    format = args.format or "text"

    send_paste(title, text, private, expire, format, config)

def send_paste(title, text, private, expire, format, config):
    api_url = "https://pastebin.com/api/api_post.php"
    data = {
        "api_dev_key": config["api_key"],
        "api_option": "paste",
        "api_paste_code": text,
        "api_paste_name": title,
        "api_paste_private": {"no": "0", "yes": "2"}.get(private.lower(), "0"),
        "api_paste_expire_date": expire,
        "api_paste_format": format,
    }

    console.print("[cyan]Sending paste...[/cyan]")
    response = requests.post(api_url, data=data)

    if response.status_code == 200:
        console.print(Panel.fit(response.text, title="[green]Paste Created[/green]"))
    else:
        console.print(Panel.fit(
            f"[bold red]Failed to create paste[/bold red]\n"
            f"Status: {response.status_code}\nResponse: {response.text}",
            title="[red]Error[/red]"
        ))

def show_help(create_parser, main_parser):
    console.print("""
[bold magenta]pastebincli[/bold magenta] - command line pastebin client

[bold]Usage:[/bold]
  pastebincli <command> [options]

[bold]Commands:[/bold]
  [green]create[/green]     make a paste
  [green]config[/green]     first time setup
  [green]help[/green]       show this help

[bold]Create options:[/bold]
""")
    help_buffer = io.StringIO()
    create_parser.print_help(file=help_buffer)
    console.print(help_buffer.getvalue())
    help_buffer.close()

    console.print("""
[bold]Examples:[/bold]
  pastebincli create --file hello.py --title test
  pastebincli config
""")

def main():
    parser = argparse.ArgumentParser(prog="pastebincli", add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("config", help="run first-time config")
    subparsers.add_parser("help", help="show help")

    create_parser = subparsers.add_parser("create", help="create a new paste")
    create_parser.add_argument("--text", help="text content")
    create_parser.add_argument("--file", help="file path")
    create_parser.add_argument("--title", help="paste title")
    create_parser.add_argument("--private", help="yes or no")
    create_parser.add_argument("--expire", help="10M, 1H, 1D, etc")
    create_parser.add_argument("--format", help="language format")

    args = parser.parse_args()

    if args.command == "config":
        first_time_setup()
    elif args.command == "create":
        config = load_config()
        if args.text or args.file:
            create_paste_from_args(args, config)
        else:
            create_paste_interactive(config)
    elif args.command == "help" or args.command is None:
        show_help(create_parser, parser)
    else:
        console.print(f"[red]Unknown command:[/red] {args.command}")
        show_help(create_parser, parser)

if __name__ == "__main__":
    main()
