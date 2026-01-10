import json
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

NOTES_FILE = Path("notes.json")


def load_notes():
    if not NOTES_FILE.exists():
        return []
    try:
        with NOTES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_notes(notes):
    with NOTES_FILE.open("w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def next_id(notes):
    if not notes:
        return 1
    return max(n.get("id", 0) for n in notes) + 1


def add_note(title, body):
    notes = load_notes()
    note = {
        "id": next_id(notes),
        "title": title,
        "body": body,
        "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
    }
    notes.append(note)
    save_notes(notes)
    print(f"Added note #{note['id']}")


def list_notes():
    notes = load_notes()
    if not notes:
        print("No notes yet. Add one with: python notes.py add \"Title\" \"Body\"")
        return

    # newest first
    notes_sorted = sorted(notes, key=lambda n: n.get("created_at", ""), reverse=True)

    print("id | created_at                 | title")
    print("-" * 60)
    for n in notes_sorted:
        nid = n.get("id", "?")
        created = n.get("created_at", "")[:19]  # cut seconds+tz for readability
        title = n.get("title", "")
        print(f"{nid:<2} | {created:<24} | {title}")


def view_note(note_id):
    notes = load_notes()
    for n in notes:
        if n.get("id") == note_id:
            print(f"#{n['id']} — {n.get('title','')}")
            print(f"Created: {n.get('created_at','')}")
            print("-" * 40)
            print(n.get("body", ""))
            return
    print(f"Note id {note_id} not found.")


def delete_note(note_id):
    notes = load_notes()
    new_notes = [n for n in notes if n.get("id") != note_id]
    if len(new_notes) == len(notes):
        print(f"Note id {note_id} not found.")
        return
    save_notes(new_notes)
    print(f"Deleted note #{note_id}")


def usage():
    print(
        """Usage:
  python notes.py add "Title" "Body text..."
  python notes.py list
  python notes.py view <id>
  python notes.py delete <id>
"""
    )


def main():
    if len(sys.argv) < 2:
        usage()
        return

    cmd = sys.argv[1].lower()

    if cmd == "add":
        if len(sys.argv) < 4:
            print('Missing title/body. Example: python notes.py add "Title" "Body"')
            return
        title = sys.argv[2]
        body = " ".join(sys.argv[3:])  # allows spaces without perfect quoting
        add_note(title, body)

    elif cmd == "list":
        list_notes()

    elif cmd == "view":
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            print("Usage: python notes.py view <id>")
            return
        view_note(int(sys.argv[2]))

    elif cmd == "delete":
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            print("Usage: python notes.py delete <id>")
            return
        delete_note(int(sys.argv[2]))

    else:
        usage()


if __name__ == "__main__":
    main()
