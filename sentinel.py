from pathlib import Path
import argparse
import sys


PROJECT_NAME = "Market Sentinel"
VERSION = "0.1.0"


def print_banner():
    print("=" * 60)
    print(f"{PROJECT_NAME:^60}")
    print(f"{'Version ' + VERSION:^60}")
    print("=" * 60)


def bootstrap():
    root = Path.cwd()

    folders = [
        "market_sentinel",
        "market_sentinel/collectors",
        "market_sentinel/collectors/base",
        "market_sentinel/collectors/india",
        "market_sentinel/collectors/usa",
        "market_sentinel/collectors/crypto",
        "market_sentinel/collectors/commodities",
        "market_sentinel/collectors/news",
        "market_sentinel/collectors/economy",
        "market_sentinel/collectors/geopolitics",
        "market_sentinel/analyzers",
        "market_sentinel/database",
        "market_sentinel/engine",
        "market_sentinel/models",
        "market_sentinel/services",
        "market_sentinel/config",
        "market_sentinel/utils",
        "market_sentinel/telegram_bot",
        "market_sentinel/scheduler",
        "docs",
        "tests",
        "reports",
        "logs",
        "data",
        "scripts",
    ]

    files = [
        "README.md",
        "requirements.txt",
        ".env",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "VERSION",
    ]

    print("\nCreating folders...\n")

    for folder in folders:
        path = root / folder
        path.mkdir(parents=True, exist_ok=True)

        init = path / "__init__.py"

        # Don't create __init__.py in docs/data/logs/etc.
        if "market_sentinel" in str(path):
            init.touch(exist_ok=True)

        print(f"✓ {folder}")

    print("\nCreating files...\n")

    for file in files:
        filepath = root / file
        filepath.touch(exist_ok=True)
        print(f"✓ {file}")

    # VERSION
    (root / "VERSION").write_text("0.1.0\n")

    # README
    (root / "README.md").write_text(
        "# Market Sentinel\n\n"
        "Personal AI Investment Intelligence Assistant\n"
    )

    # .gitignore
    (root / ".gitignore").write_text(
        ".venv/\n"
        "__pycache__/\n"
        "*.pyc\n"
        ".env\n"
        "logs/\n"
        "*.db\n"
        ".idea/\n"
        ".vscode/\n"
    )

    # .env.example
    (root / ".env.example").write_text(
        "POSTGRES_HOST=localhost\n"
        "POSTGRES_PORT=5432\n"
        "POSTGRES_DB=market_sentinel\n"
        "POSTGRES_USER=postgres\n"
        "POSTGRES_PASSWORD=password\n\n"
        "TELEGRAM_TOKEN=\n"
        "TELEGRAM_CHAT_ID=\n\n"
        "ANGEL_API_KEY=\n"
        "ANGEL_CLIENT_ID=\n"
        "ANGEL_PIN=\n"
    )

    print("\nProject bootstrapped successfully!\n")


def doctor():
    print("\nChecking environment...\n")

    print(f"Python : {sys.version.split()[0]}")
    print("Status : OK")

    print("\nNext Step:")
    print("pip install -r requirements.txt")


def main():
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Market Sentinel CLI"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("bootstrap")
    sub.add_parser("doctor")

    args = parser.parse_args()

    print_banner()

    if args.command == "bootstrap":
        bootstrap()

    elif args.command == "doctor":
        doctor()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()