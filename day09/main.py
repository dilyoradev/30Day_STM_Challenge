 from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path("anti_doomscroll.json")

PROMPTS = [
    "Do 10 deep breaths. Count them. (Yes, actually count.)",
    "Stand up and stretch shoulders + neck for 2 minutes.",
    "Write 3 lines of code (anything). Commit later, just start.",
    "Open Notes: write 5 bullet points of what’s on your mind.",
    "Drink water. While drinking, pick ONE next task.",
    "Clean your desktop (or one folder) for 2 minutes.",
    "Reply to 1 message/email you’ve been avoiding (keep it short).",
    "Do 20 squats OR 30s plank + slow breathing for the rest.",
    "Pick Top 3 tasks for today, then choose the smallest next step.",
    "Write a tiny future-you note: what would make today a win?",
]


@dataclass
class State:
    streak: int
    last_done_date: str | None  # YYYY-MM-DD
    today_date: str             # YYYY-MM-DD
    today_count: int
    history: list[dict[str, Any]]

    @staticmethod
    def default() -> "State":
        t = date.today().isoformat()
        return State(
            streak=0,
            last_done_date=None,
            today_date=t,
            today_count=0,
            history=[],
        )


def load_state() -> State:
    if not DATA_FILE.exists():
        return State.default()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        s = State.default()
        s.streak = int(data.get("streak", s.streak))
        s.last_done_date = data.get("last_done_date", s.last_done_date)
        s.today_date = data.get("today_date", s.today_date)
        s.today_count = int(data.get("today_count", s.today_count))
        s.history = list(data.get("history", s.history))
        return s
    except Exception:
        # If file is corrupted, start fresh instead of crashing.
        return State.default()


def save_state(state: State) -> None:
    data = {
        "streak": state.streak,
        "last_done_date": state.last_done_date,
        "today_date": state.today_date,
        "today_count": state.today_count,
        "history": state.history[:50],
    }
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_today(state: State) -> None:
    t = date.today().isoformat()
    if state.today_date != t:
        state.today_date = t
        state.today_count = 0


def days_between(a: str, b: str) -> int:
    da = datetime.fromisoformat(a).date()
    db = datetime.fromisoformat(b).date()
    return (db - da).days


def record_win(state: State, prompt: str) -> None:
    t = date.today().isoformat()

    if state.last_done_date is None:
        state.streak = 1
    else:
        diff = days_between(state.last_done_date, t)
        if diff == 0:
            # same day: streak unchanged
            pass
        elif diff == 1:
            state.streak += 1
        else:
            state.streak = 1

    state.last_done_date = t
    ensure_today(state)
    state.today_count += 1

    state.history.insert(0, {"date": t, "prompt": prompt})
    state.history = state.history[:50]


def format_time(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


def countdown(seconds: int) -> None:
    try:
        for remaining in range(seconds, -1, -1):
            print(f"\rTimer: {format_time(remaining)}  (Ctrl+C to stop)", end="", flush=True)
            time.sleep(1)
        print()  # newline
    except KeyboardInterrupt:
        print("\nTimer stopped.")


def print_header(state: State) -> None:
    ensure_today(state)
    print("\n" + "=" * 50)
    print("Anti-Doomscroll (Python CLI)")
    print(f"Streak: {state.streak} 🔥   Today: {state.today_count}")
    print("=" * 50)


def print_history(state: State, n: int = 5) -> None:
    if not state.history:
        print("History: (none yet)")
        return
    print("Recent wins:")
    for item in state.history[:n]:
        print(f" - {item['date']} — {item['prompt']}")


def main() -> None:
    state = load_state()

    while True:
        print_header(state)
        print("Commands: start / history / reset / quit")
        cmd = input("> ").strip().lower()

        if cmd == "start":
            prompt = random.choice(PROMPTS)
            print("\nYour 2-minute redirect:")
            print(f"👉 {prompt}\n")

            countdown(120)

            done = input("Mark as done? (y/n): ").strip().lower()
            if done == "y":
                record_win(state, prompt)
                save_state(state)
                print("✅ Logged. You broke the loop.")
            else:
                print("No log. No shame. Try again next time.")

        elif cmd == "history":
            print()
            print_history(state, n=8)

        elif cmd == "reset":
            confirm = input("Reset streak + history? type RESET: ").strip()
            if confirm == "RESET":
                state = State.default()
                save_state(state)
                print("Reset done.")
            else:
                print("Cancelled.")

        elif cmd in ("quit", "exit", "q"):
            save_state(state)
            print("Bye.")
            break

        else:
            print("Unknown command. Try: start / history / reset / quit")


if __name__ == "__main__":
    main()