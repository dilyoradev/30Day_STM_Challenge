#!/usr/bin/env python3
"""
Auto-Archive Downloads (Day 14 - STM Challenge)

Scans ~/Downloads, finds files older than N days, and moves them to:
~/Downloads/_archive/YYYY-MM/

Safe by default:
- Dry-run (no changes) unless you pass --move
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class ArchiveItem:
    src: Path
    dest_dir: Path
    dest_path: Path
    age_days: int


def human_days(delta_seconds: float) -> int:
    # Convert seconds to whole days (floor)
    return int(delta_seconds // (24 * 60 * 60))


def is_ignored(path: Path, archive_root: Path) -> bool:
    """
    Ignore:
    - directories
    - the archive folder itself and anything inside it
    - hidden files/folders (starting with '.')
    """
    if path.is_dir():
        return True

    if path.name.startswith("."):
        return True

    try:
        # If path is inside archive root, ignore
        path.resolve().relative_to(archive_root.resolve())
        return True
    except ValueError:
        pass

    return False


def unique_destination(dest: Path) -> Path:
    """
    If a file already exists at destination, rename with (1), (2), etc.
    example: report.pdf -> report (1).pdf
    """
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent

    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def collect_items(downloads: Path, days: int) -> list[ArchiveItem]:
    now = datetime.now()
    cutoff = now - timedelta(days=days)

    archive_root = downloads / "_archive"
    items: list[ArchiveItem] = []

    for p in downloads.iterdir():
        if is_ignored(p, archive_root):
            continue

        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
        except OSError:
            # Can't stat the file, skip it
            continue

        if mtime > cutoff:
            continue

        # Archive by modified date's month
        month_dir = archive_root / mtime.strftime("%Y-%m")
        dest = unique_destination(month_dir / p.name)

        age = human_days((now - mtime).total_seconds())
        items.append(ArchiveItem(src=p, dest_dir=month_dir, dest_path=dest, age_days=age))

    # Oldest first
    items.sort(key=lambda x: x.age_days, reverse=True)
    return items


def print_plan(items: list[ArchiveItem]) -> None:
    if not items:
        print("✅ Nothing to archive.")
        return

    print(f"Found {len(items)} file(s) to archive:\n")
    for it in items:
        print(f"- {it.src.name}  ({it.age_days} days old)")
        print(f"  -> {it.dest_path}")
    print()


def move_items(items: list[ArchiveItem]) -> tuple[int, int]:
    moved = 0
    failed = 0

    for it in items:
        try:
            it.dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(it.src), str(it.dest_path))
            moved += 1
        except Exception as e:
            failed += 1
            print(f"❌ Failed: {it.src} -> {it.dest_path}")
            print(f"   Reason: {e}")

    return moved, failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-archive old files from ~/Downloads into ~/Downloads/_archive/YYYY-MM/"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Archive files older than this many days (default: 14)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Downloads folder path (default: ~/Downloads)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Actually move files (otherwise dry-run)",
    )

    args = parser.parse_args()

    downloads = Path(args.path).expanduser()
    if not downloads.exists() or not downloads.is_dir():
        print(f"❌ Path not found or not a directory: {downloads}")
        return 1

    items = collect_items(downloads, args.days)
    print_plan(items)

    if not items:
        return 0

    if not args.move:
        print("🟡 Dry-run mode (no files moved).")
        print("Run with --move to actually archive.")
        return 0

    moved, failed = move_items(items)
    print(f"✅ Done. Moved: {moved}, Failed: {failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
