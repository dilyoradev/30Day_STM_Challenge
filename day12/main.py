from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Diagnosis:
    error_type: str
    headline: str
    meaning: str
    quick_fixes: list[str]
    key_line: Optional[str] = None
    location: Optional[str] = None


ERROR_KB: dict[str, dict] = {
    "SyntaxError": {
        "headline": "Python couldn’t parse your code.",
        "meaning": "There’s a typo or invalid syntax (missing colon, unmatched parentheses/quotes, wrong indentation, etc.).",
        "quick_fixes": [
            "Check the exact pointer (^) line — that’s where parsing failed (often just after the real mistake).",
            "Look for missing `:` after if/for/while/def/class.",
            "Check unmatched quotes/brackets: (), [], {} and ' \"",
            "Verify indentation is consistent (spaces vs tabs).",
        ],
    },
    "IndentationError": {
        "headline": "Indentation is inconsistent or missing.",
        "meaning": "Python relies on indentation blocks; something is misaligned.",
        "quick_fixes": [
            "Use spaces consistently (recommended: 4 spaces).",
            "Align code inside the same block (after if/for/def/etc.).",
            "In editors: convert tabs to spaces.",
        ],
    },
    "NameError": {
        "headline": "You referenced a name Python doesn’t know.",
        "meaning": "A variable/function wasn’t defined, misspelled, or is out of scope.",
        "quick_fixes": [
            "Check spelling/case (myVar vs myvar).",
            "Make sure it’s defined before use.",
            "If it’s from a module, import it (e.g., `from math import sqrt`).",
            "If inside a function, confirm scope (global vs local).",
        ],
    },
    "TypeError": {
        "headline": "You used the wrong type in an operation/call.",
        "meaning": "A function got a value of an unexpected type, or you mixed incompatible types.",
        "quick_fixes": [
            "Print/inspect types: `print(type(x), x)` right before the failing line.",
            "Check function arguments count/order.",
            "Convert types explicitly (int(), str(), float()).",
            "Watch for None: calling methods on None triggers errors later.",
        ],
    },
    "ValueError": {
        "headline": "Correct type, wrong value.",
        "meaning": "A function received a value that’s the right type but invalid (e.g., int('abc')).",
        "quick_fixes": [
            "Print the value right before the failing line.",
            "Validate inputs before converting/parsing.",
            "Handle edge cases (empty strings, negative numbers, etc.).",
        ],
    },
    "AttributeError": {
        "headline": "That object doesn’t have that attribute/method.",
        "meaning": "You called something like `x.foo()` but `x`’s type has no `foo` (or x is None).",
        "quick_fixes": [
            "Check `type(x)` and value of `x` right before the failing line.",
            "Common cause: `x` is None — trace back where it becomes None.",
            "Confirm method/property name spelling.",
        ],
    },
    "KeyError": {
        "headline": "Dictionary key not found.",
        "meaning": "You accessed dict['missing_key'] where that key doesn’t exist.",
        "quick_fixes": [
            "Print available keys: `print(d.keys())`.",
            "Use `d.get('key')` with a default if optional.",
            "Confirm the key’s exact spelling/case.",
        ],
    },
    "IndexError": {
        "headline": "List/string index out of range.",
        "meaning": "You tried to access an index that doesn’t exist (e.g., a[10] for a length-3 list).",
        "quick_fixes": [
            "Print length: `print(len(a))`.",
            "Check loops and off-by-one issues.",
            "Guard access: `if i < len(a): ...`",
        ],
    },
    "ImportError": {
        "headline": "Import failed.",
        "meaning": "Python couldn’t import a name/module (module missing, wrong name, circular import, etc.).",
        "quick_fixes": [
            "Confirm the module is installed and spelled correctly.",
            "Avoid naming your file the same as a library (e.g., `random.py`).",
            "Try importing the module alone to isolate circular imports.",
        ],
    },
    "ModuleNotFoundError": {
        "headline": "Module not installed or not in the environment.",
        "meaning": "Python can’t find that package in your current interpreter environment.",
        "quick_fixes": [
            "Check you’re using the correct venv/interpreter.",
            "Install the package: `pip install <name>` (in the same env).",
            "Verify the import name matches the package name.",
        ],
    },
    "FileNotFoundError": {
        "headline": "File path doesn’t exist.",
        "meaning": "You tried to open a file that isn’t there (or wrong working directory).",
        "quick_fixes": [
            "Print current directory: `import os; print(os.getcwd())`.",
            "Use absolute paths or `pathlib.Path`.",
            "Confirm file name and extension exactly match.",
        ],
    },
    "ZeroDivisionError": {
        "headline": "Division by zero.",
        "meaning": "You attempted x / 0 or similar.",
        "quick_fixes": [
            "Guard denominator: `if denom != 0:`.",
            "Check where denom is computed and handle edge cases.",
        ],
    },
}


ERROR_NAME_RE = re.compile(r"^(?P<etype>[A-Za-z_][A-Za-z0-9_]*Error)\b")
TRACE_FILE_LINE_RE = re.compile(r'File "([^"]+)", line (\d+)(?:, in (.+))?')


def read_multiline_input(prompt: str = "") -> str:
    if prompt:
        print(prompt)
    print("Paste the error/traceback. When done, type a single line:  END")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def extract_error_type(text: str) -> Optional[str]:
    # Usually last line looks like: "TypeError: ...", "NameError: ..."
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None

    # Search from bottom up for something ending in Error:
    for ln in reversed(lines):
        m = ERROR_NAME_RE.match(ln)
        if m:
            return m.group("etype")

    # Sometimes "SyntaxError" appears not in last line in certain formats
    for ln in lines:
        m = ERROR_NAME_RE.match(ln)
        if m:
            return m.group("etype")

    return None


def extract_key_line(text: str) -> Optional[str]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    if not lines:
        return None

    # Prefer the final "XError: message" line if present
    for ln in reversed(lines):
        if ERROR_NAME_RE.match(ln.strip()):
            return ln.strip()

    # Otherwise pick the last non-empty line
    for ln in reversed(lines):
        if ln.strip():
            return ln.strip()

    return None


def extract_location(text: str) -> Optional[str]:
    # Take the LAST "File ..., line ..." which is closest to crash
    matches = TRACE_FILE_LINE_RE.findall(text)
    if not matches:
        return None
    file_path, line_no, func = matches[-1]
    if func:
        return f'{file_path} : line {line_no} (in {func})'
    return f"{file_path} : line {line_no}"


def diagnose(text: str) -> Diagnosis:
    etype = extract_error_type(text) or "UnknownError"
    key_line = extract_key_line(text)
    location = extract_location(text)

    if etype in ERROR_KB:
        info = ERROR_KB[etype]
        return Diagnosis(
            error_type=etype,
            headline=info["headline"],
            meaning=info["meaning"],
            quick_fixes=info["quick_fixes"],
            key_line=key_line,
            location=location,
        )

    # Fallback: generic guidance
    return Diagnosis(
        error_type=etype,
        headline="Couldn’t confidently classify this error.",
        meaning="The text doesn’t match common Python error patterns, or it’s from another tool/framework.",
        quick_fixes=[
            "Scroll to the LAST lines of the traceback — that’s the real error.",
            "Find the LAST occurrence of `File \"...\", line ...` — that’s the crashing line.",
            "Print variables right before that line to see what values/types you’re dealing with.",
            "If this is from a library/framework, search the exact error line + library name.",
        ],
        key_line=key_line,
        location=location,
    )


def pretty_print(d: Diagnosis) -> None:
    print("\n" + "=" * 60)
    print(f"NAME THAT BUG → {d.error_type}")
    print("=" * 60)

    if d.location:
        print(f"📍 Location: {d.location}")
    if d.key_line:
        print(f"🧾 Key line: {d.key_line}")

    print(f"\n🧠 What it usually means:\n- {d.meaning}")
    print("\n🛠 Quick fixes:")
    for i, fix in enumerate(d.quick_fixes, start=1):
        print(f"  {i}. {fix}")

    print("\n✅ Debug checklist (copy/paste into your head):")
    checklist = [
        "What is the exact error type and message?",
        "What is the LAST file/line in the traceback that points to *your* code?",
        "What are the values + types of variables on that line?",
        "What changed right before this started happening?",
        "Can I reproduce it with the smallest input?",
    ]
    for i, item in enumerate(checklist, start=1):
        print(f"  {i}) {item}")
    print("=" * 60 + "\n")


def main() -> None:
    text = read_multiline_input(prompt="🧩 Day 12: Name That Bug")
    if not text.strip():
        print("No input received. Paste an error/traceback next time 🙂")
        return
    d = diagnose(text)
    pretty_print(d)


if __name__ == "__main__":
    main()
