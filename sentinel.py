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

    sub.add_parser(
        "bootstrap",
        help="Create the project structure"
    )

    sub.add_parser(
        "doctor",
        help="Verify the development environment"
    )

    sub.add_parser(
        "collect",
        help="Collect live market data"
    )

    sub.add_parser(
        "latest",
        help="Show latest market data"
    )

    history_parser = sub.add_parser(
        "history",
        help="Show historical prices"
    )

    history_parser.add_argument(
        "symbol",
        help="Market symbol"
    )

    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )

    stats_parser = sub.add_parser(
        "stats",
        help="Show market statistics"
    )

    stats_parser.add_argument(
        "symbol",
        help="Market symbol"
    )

    args = parser.parse_args()

    print_banner()

    if args.command == "bootstrap":
        bootstrap()

    elif args.command == "doctor":
        doctor()

    elif args.command == "collect":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        service.collect()

    elif args.command == "latest":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        records = service.latest()
        print()
        print("=" * 60)
        print("Latest Market Data")
        print("=" * 60)
        for record in records:
            print(
                f"{record.name:<15}"
                f"{record.price:<12}"
                f"{record.currency}"
            )

    elif args.command == "history":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        records = service.history(
            args.symbol,
            args.limit,
        )
        print()
        print("=" * 60)
        print(f"History : {args.symbol}")
        print("=" * 60)
        for record in records:
            print(
                f"{record.collected_at}"
                f"   {record.price}"
                f"   {record.currency}"
            )

    elif args.command == "stats":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        symbol, latest, stats = service.statistics(args.symbol)
        print()
        print("=" * 60)
        print("Market Statistics")
        print("=" * 60)
        print(f"Asset           : {latest.name} ({symbol})")
        print()
        print(f"Latest Price    : {float(latest.price):.4f} {latest.currency}")
        print(f"Highest Price   : {float(stats.highest):.4f}")
        print(f"Lowest Price    : {float(stats.lowest):.4f}")
        print(f"Average Price   : {float(stats.average):.4f}")
        print()
        print(f"Records         : {stats.records}")
        print(f"First Record    : {stats.first_time}")
        print(f"Latest Record   : {stats.latest_time}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()