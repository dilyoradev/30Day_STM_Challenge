from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class FileChange:
    path: str
    added: int = 0
    removed: int = 0

    @property
    def total(self) -> int:
        return self.added + self.removed


@dataclass
class Digest:
    files: List[FileChange]
    total_added: int
    total_removed: int
    tags: List[str]
    bullets: List[str]


STAT_LINE_RE = re.compile(
    r"""^\s*(?P<path>.+?)\s+\|\s+(?P<count>\d+)\s+(?P<marks>[+\-]+)\s*$"""
)

# Unified diff markers
DIFF_GIT_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)\s*$")
PLUS_FILE_RE = re.compile(r"^\+\+\+\s+(.*)$")
MINUS_FILE_RE = re.compile(r"^---\s+(.*)$")


def read_stdin() -> str:
    return sys.stdin.read()


def looks_like_stat(text: str) -> bool:
    if " files changed" in text:
        return True
    # If many lines match the stat pattern, it’s stat.
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    stat_matches = sum(1 for ln in lines if STAT_LINE_RE.match(ln))
    return stat_matches >= max(1, len(lines) // 3)


def normalize_stat_path(p: str) -> str:
    return p.strip()


def parse_git_stat(text: str) -> Dict[str, FileChange]:
    changes: Dict[str, FileChange] = {}
    for line in text.splitlines():
        m = STAT_LINE_RE.match(line)
        if not m:
            continue
        path = normalize_stat_path(m.group("path"))
        marks = m.group("marks")
        added = marks.count("+")
        removed = marks.count("-")
        # Note: marks are not exact lines (they are scaled). Still useful signal.
        changes[path] = FileChange(path=path, added=added, removed=removed)

    return changes


def strip_prefix(p: str) -> str:
    # diff header uses a/ b/ prefixes; plus/minus file lines may show a/, b/, or /dev/null
    p = p.strip()
    if p.startswith("a/") or p.startswith("b/"):
        return p[2:]
    return p


def parse_unified_diff(text: str) -> Dict[str, FileChange]:
    changes: Dict[str, FileChange] = {}
    current_path: Optional[str] = None

    for line in text.splitlines():
        # Detect file change boundary via diff header
        m = DIFF_GIT_RE.match(line)
        if m:
            # Prefer b-path unless it's /dev/null
            a_path, b_path = m.group(1), m.group(2)
            chosen = b_path if b_path != "/dev/null" else a_path
            current_path = strip_prefix(chosen)
            changes.setdefault(current_path, FileChange(path=current_path))
            continue

        # Sometimes diffs may not include "diff --git" (rare), but include +++ / ---
        if line.startswith("+++ "):
            rhs = PLUS_FILE_RE.match(line)
            if rhs:
                p = rhs.group(1).strip()
                if p == "/dev/null":
                    continue
                current_path = strip_prefix(p.replace("b/", "", 1))  # be forgiving
                changes.setdefault(current_path, FileChange(path=current_path))
            continue

        if line.startswith("--- "):
            # don't set current_path from --- alone; keep whatever we have
