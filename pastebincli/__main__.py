#!/usr/bin/env python3
import argparse
import os
import sys
import time
import requests
import tomllib
import io

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

CONFIG_DIR = os.path.expanduser("~/.config/pastebincli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.toml")
PASTER_BASE_URL = "https://paste.rs"

def first_time_setup():
    console.print("[bold magenta]== First time setup for pastebincli ==[/bold magenta]")
    time.sleep(1)

    paster = Prompt.ask(
        "\n[cyan]Choose your pasting service:[/cyan]",
        choices=["pastebin", "pasters"], default="pasters"
    )

    if paster == "pastebin":
        apikey = Prompt.ask(
            "\n[cyan]Pastebin API key required.[/cyan]\n"
            "Visit [blue]https://pastebin.com/doc_api[/blue] and paste your API key:"
        )
        config = {"paster": "pastebin", "api_key": apikey}
    else:
        config = {"paster": "pasters"}

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        for key, value in config.items():
            f.write(f'{key} = "{value}"\n')

    console.print(f"[green]✓ Config saved at[/green] [italic]{CONFIG_FILE}[/italic]")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        console.print("[red]Config not found.[/red] Run [bold]pastebincli config[/bold] first.")
        sys.exit(1)
    with open(CONFIG_FILE, 'rb') as f:
        return tomllib.load(f)

def send_paste(text, title, private, expire, format, config):
    paster = config.get("paster", "pasters")

    if paster == "pastebin":
        data = {
            "api_dev_key": config["api_key"],
            "api_option": "paste",
            "api_paste_code": text,
            "api_paste_name": title,
            "api_paste_private": {"no": "0", "yes": "2"}.get(private.lower(), "0"),
            "api_paste_expire_date": expire,
            "api_paste_format": format,
        }
        console.print("[cyan]Sending paste to Pastebin...[/cyan]")
        response = requests.post("https://pastebin.com/api/api_post.php", data=data)

        if response.status_code == 200:
            console.print(Panel(response.text.strip(), title="[green]Paste Created[/green]"))
        else:
            console.print(Panel(f"[bold red]Failed[/bold red]\n{response.text}", title="[red]Error[/red]"))

    elif paster == "pasters":
        console.print("[cyan]Sending paste to paste.rs...[/cyan]")
        response = requests.post(PASTER_BASE_URL + "/", data=text.encode("utf-8"))

        if response.status_code == 201:
            console.print(Panel(response.text.strip(), title="[green]Paste Created[/green]"))
        elif response.status_code == 206:
            console.print(Panel(
                f"[yellow]Paste partially uploaded (too large)[/yellow]\n{response.text.strip()}",
                title="[yellow]Partial Upload[/yellow]"
            ))
        else:
            console.print(Panel(
                f"[red]Upload failed[/red]\nStatus code: {response.status_code}\n{response.text}",
                title="[red]Error[/red]"
            ))

def delete_paste(paste_id):
    url = f"{PASTER_BASE_URL}/{paste_id}"
    response = requests.delete(url)
    if response.status_code == 200:
        console.print(f"[green]✓ Deleted paste:[/green] {url}")
    else:
        console.print(f"[red]✗ Failed to delete paste:[/red] {url} — {response.status_code}")

def create_paste_from_args(args, config):
    if args.file:
        if not os.path.exists(args.file):
            console.print(f"[red]File not found:[/red] {args.file}")
            return
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        console.print("[red]Error:[/red] Provide either --text or --file")
        return

    title = args.title or "untitled"
    private = args.private or "no"
    expire = args.expire or "10M"
    format = args.format or "text"

    send_paste(text, title, private, expire, format, config)

def create_paste_interactive(config):
    title = Prompt.ask("title", default="untitled")
    text = Prompt.ask("text")
    private = Prompt.ask("private? (yes/no)", default="no")
    expire = Prompt.ask("expire (10M, 1D)", default="10M")
    format = Prompt.ask("format (python, bash, etc)", default="text")
    confirm = Prompt.ask("continue? (y/n)", default="y")

    if confirm.lower() not in ("y", "yes"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    send_paste(text, title, private, expire, format, config)

def show_help(create_parser, main_parser):
    console.print("""
[bold magenta]pastebincli[/bold magenta] - CLI pastebin / paste.rs client

[bold]Usage:[/bold]
  pastebincli <command> [options]

[bold]Commands:[/bold]
  [green]create[/green]     create new paste
  [green]delete[/green]     delete paste.rs paste by ID
  [green]config[/green]     setup configuration
  [green]help[/green]       show this help

[bold]Create options:[/bold]
""")
    help_buffer = io.StringIO()
    create_parser.print_help(file=help_buffer)
    console.print(help_buffer.getvalue())
    help_buffer.close()

    console.print("""
[bold]Examples:[/bold]
  pastebincli create --text "hello world"
  pastebincli create --file test.py --title script
  pastebincli delete a1b2c3d4
  pastebincli config
""")

def main():
    parser = argparse.ArgumentParser(prog="pastebincli", add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("config", help="run setup")
    subparsers.add_parser("help", help="show help")

    create_parser = subparsers.add_parser("create", help="create new paste")
    create_parser.add_argument("--text", help="paste text")
    create_parser.add_argument("--file", help="path to file")
    create_parser.add_argument("--title", help="title of paste")
    create_parser.add_argument("--private", help="yes/no")
    create_parser.add_argument("--expire", help="expiration time (10M, 1D, etc)")
    create_parser.add_argument("--format", help="language format (py, txt, etc)")

    delete_parser = subparsers.add_parser("delete", help="delete a paste.rs paste")
    delete_parser.add_argument("paste_id", help="paste ID to delete")

    args = parser.parse_args()

    if args.command == "config":
        first_time_setup()
    elif args.command == "create":
        config = load_config()
        if args.text or args.file:
            create_paste_from_args(args, config)
        else:
            create_paste_interactive(config)
    elif args.command == "delete":
        delete_paste(args.paste_id)
    else:
        show_help(create_parser, parser)

if __name__ == "__main__":
    main()
