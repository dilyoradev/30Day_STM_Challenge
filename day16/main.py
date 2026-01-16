from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


DATA_FILE = "commit_coach.json"

CONVENTIONAL_TYPES = [
    ("feat", "New feature"),
    ("fix", "Bug fix"),
    ("refactor", "Code change that neither fixes a bug nor adds a feature"),
    ("perf", "Performance improvement"),
    ("test", "Add or fix tests"),
    ("docs", "Documentation only"),
    ("build", "Build system / dependencies"),
    ("ci", "CI changes"),
    ("chore", "Other changes (maintenance)"),
    ("revert", "Revert a previous commit"),
]

MAX_SUBJECT_LEN = 72


# ---------------------- Utilities ----------------------

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def first_sentence(s: str) -> str:
    s = normalize_ws(s)
    return s

def looks_like_issue_ref(s: str) -> bool:
    return bool(re.search(r"(#\d+|[A-Z]{2,}-\d+)", s))

def to_kebab_scope(s: str) -> str:
    s = normalize_ws(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s



@dataclass
class HistoryItem:
    created_at: str
    summary: str
    suggestion: str
    score: int
    notes: List[str]

@dataclass
class CoachState:
    favorites: List[str]
    history: List[HistoryItem]

    def to_json(self) -> Dict[str, Any]:
        return {
            "_meta": {"version": 1},
            "favorites": list(self.favorites),
            "history": [asdict(h) for h in self.history][-200:],  # cap
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "CoachState":
        fav = data.get("favorites", [])
        hist = data.get("history", [])
        favorites = [str(x) for x in fav] if isinstance(fav, list) else []
        history: List[HistoryItem] = []
        if isinstance(hist, list):
            for item in hist:
                if not isinstance(item, dict):
                    continue
                history.append(
                    HistoryItem(
                        created_at=str(item.get("created_at", "")),
                        summary=str(item.get("summary", "")),
                        suggestion=str(item.get("suggestion", "")),
                        score=int(item.get("score", 0)),
                        notes=list(item.get("notes", [])) if isinstance(item.get("notes", []), list) else [],
                    )
                )
        return cls(favorites=favorites, history=history)

def load_state(path: str = DATA_FILE) -> CoachState:
    if not os.path.exists(path):
        return CoachState(favorites=[], history=[])
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return CoachState(favorites=[], history=[])
    return CoachState.from_json(data)

def save_state(state: CoachState, path: str = DATA_FILE) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state.to_json(), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)



IMPERATIVE_VERBS = {
    "add", "fix", "update", "remove", "refactor", "improve", "change", "support", "prevent",
    "handle", "allow", "enable", "disable", "rename", "clean", "simplify", "document", "test",
    "bump", "pin", "revert", "stop", "start", "ensure", "retry", "validate", "redirect",
}

KEYWORD_TYPE_HINTS = [
    (("bug", "error", "crash", "broken", "fail", "issue", "regression"), "fix"),
    (("add", "introduce", "implement", "support", "enable"), "feat"),
    (("docs", "readme", "comment", "documentation"), "docs"),
    (("test", "playwright", "pytest", "e2e", "unit"), "test"),
    (("perf", "faster", "optimize", "speed", "latency"), "perf"),
    (("refactor", "cleanup", "simplify", "restructure"), "refactor"),
    (("deps", "dependency", "upgrade", "bump"), "build"),
    (("ci", "github actions", "pipeline"), "ci"),
]

def guess_type(summary: str) -> str:
    s = summary.lower()
    for keys, t in KEYWORD_TYPE_HINTS:
        if any(k in s for k in keys):
            return t
    return "chore"

def suggest_scope(summary: str) -> Optional[str]:
    """
    Tries to infer scope from common tokens: api/auth/ui/db/tests/etc.
    """
    s = summary.lower()
    candidates = []
    for token in ["auth", "login", "signup", "cognito", "sqs", "worker", "api", "backend", "frontend",
                  "ui", "db", "alembic", "tests", "playwright", "config", "env", "docker", "docs"]:
        if token in s:
            candidates.append(token)
    if not candidates:
        return None
    # Prefer more specific tokens first
    return to_kebab_scope(candidates[0])

def subject_from_summary(summary: str) -> str:
    s = normalize_ws(summary)
    # Strip leading "I " / "We " / "This PR " patterns
    s = re.sub(r"^(i|we|this pr|pr)\s+", "", s, flags=re.IGNORECASE)
    # Lowercase first char (commit subjects typically start with verb, lower-case ok)
    if s:
        s = s[0].lower() + s[1:]
    # Remove trailing period
    s = s.rstrip(".")
    return s

def build_message(
    ctype: str,
    scope: Optional[str],
    breaking: bool,
    subject: str,
    issue_ref: Optional[str],
) -> str:
    scope_part = f"({scope})" if scope else ""
    bang = "!" if breaking else ""
    base = f"{ctype}{scope_part}{bang}: {subject}"
    if issue_ref:
        # Keep issue reference at end of subject
        if not base.endswith(issue_ref):
            base = f"{base} {issue_ref}"
    return base

def lint_message(msg: str) -> Tuple[int, List[str]]:
    """
    Returns (score out of 100, notes).
    """
    notes: List[str] = []
    score = 100

    if len(msg) > MAX_SUBJECT_LEN:
        notes.append(f"Subject is {len(msg)} chars (aim <= {MAX_SUBJECT_LEN}). Consider shortening.")
        score -= 15

    if msg.endswith("."):
        notes.append("Avoid trailing period in the subject.")
        score -= 5

    if "  " in msg:
        notes.append("Contains double spaces.")
        score -= 2

    # Conventional format check
    if not re.match(r"^[a-z]+(\([a-z0-9-]+\))?(!)?:\s", msg):
        notes.append("Not in conventional format: type(scope): subject")
        score -= 20

    # Imperative-ish verb check (rough)
    # Extract subject portion after ': '
    subject = msg.split(": ", 1)[1] if ": " in msg else msg
    first_word = re.split(r"\s+", subject.strip())[0].lower() if subject.strip() else ""
    if first_word and first_word not in IMPERATIVE_VERBS:
        notes.append(f'First word "{first_word}" doesn’t look imperative. Consider starting with a verb (add/fix/update/...).')
        score -= 8

    # Capitalization: encourage lower-case in subject start (optional rule)
    if subject and subject[0].isupper():
        notes.append("Consider starting subject with lower-case (common convention).")
        score -= 2

    score = clamp(score, 0, 100)
    return score, notes

def propose(
    summary: str,
    ctype: Optional[str] = None,
    scope: Optional[str] = None,
    breaking: bool = False,
    issue_ref: Optional[str] = None,
) -> Tuple[str, int, List[str]]:
    summary = summary.strip()
    if not summary:
        raise ValueError("Summary cannot be empty.")

    ctype = ctype or guess_type(summary)
    subject = subject_from_summary(summary)
    scope = scope or suggest_scope(summary)
    msg = build_message(ctype, scope, breaking, subject, issue_ref)
    score, notes = lint_message(msg)
    return msg, score, notes



HELP = r"""
Commands:
  help
  coach
  quick "<summary>"
  types
  fav add "<message>"       
  fav list
  fav del <index>
  history [n]
  lint "<message>"
  quit / exit

Examples:
  quick "fix token refresh retry on 401"
  coach
  lint "feat(auth): add auto refresh on 401"
"""

def print_types() -> None:
    for t, desc in CONVENTIONAL_TYPES:
        print(f"- {t:9} {desc}")

def pick_from_list(prompt: str, items: List[str], default_index: int = 0) -> str:
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    raw = input(f"{prompt} (1-{len(items)}), default {default_index+1}: ").strip()
    if not raw:
        return items[default_index]
    try:
        idx = int(raw)
        if 1 <= idx <= len(items):
            return items[idx - 1]
    except ValueError:
        pass
    print("Invalid choice, using default.")
    return items[default_index]

def interactive_coach(state: CoachState) -> None:
    print("\n--- Commit Coach (interactive) ---")
    summary = input("1) What changed? (one sentence): ").strip()
    if not summary:
        print("No summary, cancelled.")
        return

    type_names = [t for t, _ in CONVENTIONAL_TYPES]
    guessed = guess_type(summary)
    default_idx = type_names.index(guessed) if guessed in type_names else 0
    ctype = pick_from_list("2) Choose type", type_names, default_idx)

    auto_scope = suggest_scope(summary)
    scope_raw = input(f"3) Scope? (enter to use {auto_scope or 'none'}): ").strip()
    scope = to_kebab_scope(scope_raw) if scope_raw else auto_scope

    breaking_raw = input("4) Breaking change? (y/N): ").strip().lower()
    breaking = breaking_raw in ("y", "yes")

    issue_raw = input("5) Issue ref (e.g. #123 or ABC-12) (enter to skip): ").strip()
    issue_ref = issue_raw if issue_raw else None

    msg, score, notes = propose(summary, ctype=ctype, scope=scope, breaking=breaking, issue_ref=issue_ref)
    print("\nSuggested commit subject:")
    print(f"  {msg}")
    print(f"\nScore: {score}/100")
    if notes:
        print("Notes:")
        for n in notes:
            print(f" - {n}")

    copy_tip = input("\nSave to history? (Y/n): ").strip().lower()
    if copy_tip in ("n", "no"):
        return

    state.history.append(
        HistoryItem(
            created_at=now_iso(),
            summary=summary,
            suggestion=msg,
            score=score,
            notes=notes,
        )
    )
    save_state(state)
    print("Saved.")

def cmd_quick(state: CoachState, summary: str) -> None:
    msg, score, notes = propose(summary)
    print(msg)
    print(f"(score {score}/100)")
    if notes:
        for n in notes:
            print(f"- {n}")
    state.history.append(HistoryItem(created_at=now_iso(), summary=summary, suggestion=msg, score=score, notes=notes))
    save_state(state)

def cmd_lint(message: str) -> None:
    message = message.strip()
    if not message:
        print("Usage: lint \"<message>\"")
        return
    score, notes = lint_message(message)
    print(f"Score: {score}/100")
    if notes:
        for n in notes:
            print(f"- {n}")
    else:
        print("Looks good ✅")

def cmd_history(state: CoachState, n: int = 10) -> None:
    n = clamp(n, 1, 50)
    hist = state.history[-n:]
    if not hist:
        print("(no history yet)")
        return
    for item in hist:
        print(f"\n[{item.created_at}] score={item.score}")
        print(f"  summary: {item.summary}")
        print(f"  commit : {item.suggestion}")
        if item.notes:
            print("  notes  :")
            for x in item.notes[:5]:
                print(f"    - {x}")

def cmd_fav_add(state: CoachState, msg: str) -> None:
    msg = msg.strip()
    if not msg:
        print('Usage: fav add "<message>"')
        return
    state.favorites.append(msg)
    save_state(state)
    print("Added to favorites.")

def cmd_fav_list(state: CoachState) -> None:
    if not state.favorites:
        print("(no favorites yet)")
        return
    for i, m in enumerate(state.favorites, 1):
        print(f"{i}. {m}")

def cmd_fav_del(state: CoachState, idx: int) -> None:
    if not (1 <= idx <= len(state.favorites)):
        print("Invalid index.")
        return
    removed = state.favorites.pop(idx - 1)
    save_state(state)
    print(f"Removed: {removed}")


def main() -> None:
    state = load_state(DATA_FILE)
    print("🧠 Git Commit Message Coach")
    print('Type "help" for commands. Your history is saved to commit_coach.json.')

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if not raw:
            continue

        try:
            parts = shlex.split(raw)
        except ValueError as e:
            print(f"Parse error: {e}")
            continue

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("quit", "exit"):
            print("Bye.")
            return
        elif cmd == "help":
            print(HELP)
        elif cmd == "types":
            print_types()
        elif cmd == "coach":
            interactive_coach(state)
        elif cmd == "quick":
            if not args:
                print('Usage: quick "<summary>"')
                continue
            summary = " ".join(args)
            cmd_quick(state, summary)
        elif cmd == "lint":
            if not args:
                print('Usage: lint "<message>"')
                continue
            msg = " ".join(args)
            cmd_lint(msg)
        elif cmd == "history":
            n = 10
            if args:
                n = int(args[0]) if args[0].isdigit() else 10
            cmd_history(state, n)
        elif cmd == "fav":
            if not args:
                print('Usage: fav add "<message>" | fav list | fav del <index>')
                continue
            sub = args[0].lower()
            if sub == "add":
                msg = " ".join(args[1:]) if len(args) > 1 else ""
                cmd_fav_add(state, msg)
            elif sub == "list":
                cmd_fav_list(state)
            elif sub == "del":
                if len(args) < 2 or not args[1].isdigit():
                    print("Usage: fav del <index>")
                    continue
                cmd_fav_del(state, int(args[1]))
            else:
                print('Usage: fav add "<message>" | fav list | fav del <index>')
        else:
            print('Unknown command. Type "help".')


if __name__ == "__main__":
    main()
