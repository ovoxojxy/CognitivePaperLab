#!/usr/bin/env python3
"""CLI for ingestion pipeline: parse -> validate -> (optionally) save."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ingestion import ingest
from storage import get_storage


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest JSON or CSV into storage")
    parser.add_argument("input", nargs="?", default="-", help="Input file or - for stdin")
    parser.add_argument("--format", choices=["json", "csv"], required=True)
    parser.add_argument("--storage", choices=["memory", "sqlite"], default="memory")
    parser.add_argument("--storage-path", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate only, no writes")
    args = parser.parse_args()

    raw = Path(args.input).read_text() if args.input != "-" else sys.stdin.read()

    storage = None
    if not args.dry_run:
        path = args.storage_path or str(ROOT / "data" / "ingested.db")
        if args.storage == "sqlite":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        storage = get_storage(args.storage, path=path)

    records = ingest(raw, args.format, storage=storage, dry_run=args.dry_run)
    print(f"ingested {len(records)} records", file=sys.stderr)
    if args.dry_run:
        print("(dry-run: nothing written)", file=sys.stderr)


if __name__ == "__main__":
    main()
