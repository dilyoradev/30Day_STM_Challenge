# day11_focus_timer.py
# STM Day 11: Focus Timer + Distraction Log (Pomodoro CLI)
# No external libraries needed.

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional


LOG_FILE = Path(__file__).with_name("stm_day11_log.json")


@dataclass
class Event:
    ts: str                 # ISO timestamp
    type: str               # "focus_start" | "focus_end" | "distraction"
    minutes: Optional[int]  # focus minutes for start/end
    note: str               # optional note / distraction text


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_log() -> List[Dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # If file got corrupted, keep a backup and start fresh
        backup = LOG_FILE.with_suffix(".bak")
        backup.write_text(LOG_FILE.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        return []


def save_log(items: List[Dict[str, Any]]) -> None:
    LOG_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def append_event(event: Event) -> None:
    items = load_log()
    items.append(asdict(event))
    save_log(items)


def countdown(total_seconds: int) -> None:
    # Simple terminal countdown that updates each second
    end = time.time() + total_seconds
    while True:
        remaining = int(end - time.time())
        if remaining <= 0:
            print("\r⏰ 00:00  Done!                          ")
            break
        mm = remaining // 60
        ss = remaining % 60
        print(f"\r⏳ {mm:02d}:{ss:02d}  (Ctrl+C to stop)", end="", flush=True)
        time.sleep(1)


def start_focus(minutes: int = 25) -> None:
    print(f"\n🧠 Focus session started: {minutes} minutes")
    print("Tip: Keep this terminal open. If distracted, use option 2 to log it.\n")

    append_event(Event(ts=now_iso(), type="focus_start", minutes=minutes, note=""))

    try:
        countdown(minutes * 60)
        append_event(Event(ts=now_iso(), type="focus_end", minutes=minutes, note="completed"))
        print("\n✅ Focus session completed.\n")
    except KeyboardInterrupt:
        append_event(Event(ts=now_iso(), type="focus_end", minutes=minutes, note="stopped_early"))
        print("\n\n🛑 Focus session stopped early.\n")


def log_distraction() -> None:
    text = input("\n🧾 What distracted you? (short note) \n> ").strip()
    if not text:
        print("Nothing logged.\n")
        return
    append_event(Event(ts=now_iso(), type="distraction", minutes=None, note=text))
    print("✅ Distraction logged.\n")


def parse_iso_day(ts: str) -> date:
    # ts like "2026-01-11T23:05:00"
    return datetime.fromisoformat(ts).date()


def stats_today() -> None:
    items = load_log()
    today = date.today()

    focus_minutes_completed = 0
    focus_sessions_completed = 0
    focus_sessions_started = 0
    distractions: List[str] = []

    for it in items:
        try:
            d = parse_iso_day(it["ts"])
        except Exception:
            continue
        if d != today:
            continue

        if it.get("type") == "focus_start":
            focus_sessions_started += 1
        elif it.get("type") == "focus_end":
            if it.get("note") == "completed" and isinstance(it.get("minutes"), int):
                focus_sessions_completed += 1
                focus_minutes_completed += int(it["minutes"])
        elif it.get("type") == "distraction":
            note = (it.get("note") or "").strip()
            if note:
                distractions.append(note)

    print(f"\n📊 Stats for {today.isoformat()}")
    print(f"- Focus sessions started:   {focus_sessions_started}")
    print(f"- Focus sessions completed: {focus_sessions_completed}")
    print(f"- Focus minutes completed:  {focus_minutes_completed}")

    if distractions:
        print("\n🧨 Distractions logged:")
        for i, note in enumerate(distractions, 1):
            print(f"  {i}. {note}")
    else:
        print("\n🧘 No distractions logged today. Nice.\n")


def main() -> None:
    while True:
        print("=== STM Day 11: Focus Timer + Distraction Log ===")
        print("1) Start focus session (Pomodoro)")
        print("2) Log a distraction")
        print("3) Show today's stats")
        print("4) Exit")

        choice = input("\nChoose (1-4): ").strip()

        if choice == "1":
            raw = input("Minutes? (press Enter for 25) \n> ").strip()
            minutes = 25
            if raw:
                try:
                    minutes = int(raw)
                    if minutes <= 0 or minutes > 240:
                        raise ValueError
                except ValueError:
                    print("Please enter a valid number (1-240).\n")
                    continue
            start_focus(minutes)
        elif choice == "2":
            log_distraction()
        elif choice == "3":
            stats_today()
        elif choice == "4":
            print("Bye 👋")
            break
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()