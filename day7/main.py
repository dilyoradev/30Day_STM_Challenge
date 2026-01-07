from __future__ import annotations

import json
from datetime import date
from pathlib import Path

JSON_FILE = Path("journal.json")
MD_FILE = Path("journal.md")


def load_entries() -> list[dict]:
    if not JSON_FILE.exists():
        return []
    try:
        return json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_entries(entries: list[dict]) -> None:
    JSON_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def append_markdown(entry: dict) -> None:
    md = []
    md.append(f"\n## {entry['date']}\n")
    md.append(f"- **稼働時間:** {entry.get('minutes','')} 分\n")
    md.append(f"- **やったこと:** {entry.get('did','')}\n")
    md.append(f"- **学び:** {entry.get('learned','')}\n")
    md.append(f"- **次やること:** {entry.get('next','')}\n")
    md.append(f"- **困っていたこと:** {entry.get('blockers','')}\n")
    MD_FILE.write_text(MD_FILE.read_text(encoding="utf-8") + "".join(md), encoding="utf-8") if MD_FILE.exists() else MD_FILE.write_text("# 日報 / Journal\n" + "".join(md), encoding="utf-8")


def input_int(prompt: str) -> int:
    while True:
        s = input(prompt).strip()
        if s == "":
            return 0
        if s.isdigit():
            return int(s)
        print("数字を入力してください（空Enterで0）")


def new_entry(entries: list[dict]) -> None:
    today = date.today().isoformat()

    d = input(f"日付 (YYYY-MM-DD) [default: {today}]: ").strip() or today

    # Prevent double entry for same date (simple behavior: overwrite if exists)
    existing_idx = next((i for i, e in enumerate(entries) if e.get("date") == d), None)

    minutes = input_int("本日の稼働時間(分) [空Enterで0]: ")

    did = input("やったこと: ").strip()
    learned = input("学び: ").strip()
    nxt = input("次やること: ").strip()
    blockers = input("困っていたこと: ").strip()

    entry = {
        "date": d,
        "minutes": minutes,
        "did": did,
        "learned": learned,
        "next": nxt,
        "blockers": blockers,
    }

    if existing_idx is None:
        entries.append(entry)
    else:
        entries[existing_idx] = entry

    # Keep entries sorted by date
    entries.sort(key=lambda e: e.get("date", ""))

    save_entries(entries)
    append_markdown(entry)
    print(f"\n✅ Saved: {d}  → {JSON_FILE} + {MD_FILE}\n")


def list_entries(entries: list[dict]) -> None:
    if not entries:
        print("まだ日報がありません。\n")
        return
    print("\n=== Entries ===")
    for e in entries[-20:]:
        print(f"- {e.get('date')} ({e.get('minutes', 0)} min)  {e.get('did','')[:40]}")
    print("")


def view_entry(entries: list[dict]) -> None:
    d = input("見たい日付 (YYYY-MM-DD): ").strip()
    e = next((x for x in entries if x.get("date") == d), None)
    if not e:
        print("見つかりませんでした。\n")
        return
    print(f"\n=== {e['date']} ===")
    print(f"稼働時間: {e.get('minutes','')} 分")
    print(f"やったこと: {e.get('did','')}")
    print(f"学び: {e.get('learned','')}")
    print(f"次やること: {e.get('next','')}")
    print(f"困っていたこと: {e.get('blockers','')}\n")


def main() -> None:
    entries = load_entries()

    print("Day7: Daily Check-in Logger")
    print("commands: new / list / view / quit\n")

    while True:
        cmd = input("> ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            print("bye!")
            return
        elif cmd == "new":
            new_entry(entries)
        elif cmd == "list":
            list_entries(entries)
        elif cmd == "view":
            view_entry(entries)
        elif cmd == "":
            continue
        else:
            print("unknown command. try: new / list / view / quit\n")


if __name__ == "__main__":
    main()
