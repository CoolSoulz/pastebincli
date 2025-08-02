import argparse
import os
import sys
import time
import requests
import tomllib
import io  # needed for capturing help output

CONFIG_DIR = os.path.expanduser("~/.config/pastebincli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.toml")

def first_time_setup():
    print("==First time setup for pastebincli==")
    time.sleep(1)
    apikey = input(
        "You need a Pastebin API key to use this application.\n"
        "Go to https://pastebin.com/doc_api, login, and grab it. Paste it here: "
    )
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        f.write(f'api_key = "{apikey}"\n')
    print("config saved at", CONFIG_FILE)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("config not found. run `pastebincli config` first.")
        sys.exit(1)
    with open(CONFIG_FILE, 'rb') as f:
        return tomllib.load(f)

def create_paste_interactive(config):
    print("create a paste (interactive mode)")
    title = input("title: ")
    text = input("text: ")
    private = input("private? (yes/no): ")
    expire = input("expire time (e.g. 10M, 1H, 1D): ")
    format = input("format (python, bash, etc): ")

    print("\nconfirm:")
    print("title:", title)
    print("text:", text)
    print("private:", private)
    print("expire:", expire)
    print("format:", format)
    confirm = input("continue? (y/n): ")
    if confirm.lower() not in ("y", "yes"):
        print("cancelled.")
        return

    send_paste(title, text, private, expire, format, config)

def create_paste_from_args(args, config):
    if args.file:
        if not os.path.exists(args.file):
            print("file not found.")
            return
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("need --text or --file.")
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

    print("sending paste...")
    response = requests.post(api_url, data=data)

    if response.status_code == 200:
        print("done.")
        print("url:", response.text)
    else:
        print("failed.")
        print("status code:", response.status_code)
        print("response:", response.text)

def show_help(create_parser, main_parser):
    print("""
pastebincli - command line pastebin client

usage:
  pastebincli <command> [options]

commands:
  create     make a paste
  config     first time setup
  help       show this help

create options:
""")
    help_buffer = io.StringIO()
    create_parser.print_help(file=help_buffer)
    create_help_text = help_buffer.getvalue()
    help_buffer.close()
    print(create_help_text)

    print("""
examples:
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
        print("unknown command:", args.command)
        show_help(create_parser, parser)

if __name__ == "__main__":
    main()
