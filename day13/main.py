from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

def badge(label: str, message: str, color: str = "blue") -> str:
    """
    Creates a shields.io badge markdown without links.
    Note: Keep label/message simple; special chars should be replaced by '-'.
    """
    label_s = label.strip().replace(" ", "%20")
    msg_s = message.strip().replace(" ", "%20")
    color_s = color.strip()
    return f"![{label}]({f'https://img.shields.io/badge/{label_s}-{msg_s}-{color_s}'})"


def linked_badge(label: str, message: str, color: str, url: str) -> str:
    b = badge(label, message, color)
    return f"[{b}]({url})"


def normalize_stack(stack_raw: str) -> List[str]:
    """
    Parse comma-separated stack input into a clean list.
    Example input: "Python, FastAPI, PostgreSQL, Docker"
    """
    items = [s.strip() for s in stack_raw.split(",")]
    return [s for s in items if s]


def stack_badges(stack: List[str]) -> List[str]:
    """
    A simple mapping from common tech to badge styles.
    If unknown, produce a generic badge.
    """
    mapping = {
        "Python": ("Python", "3.x", "3776AB"),
        "FastAPI": ("FastAPI", "API", "009688"),
        "Flask": ("Flask", "Web", "000000"),
        "Django": ("Django", "Web", "092E20"),
        "JavaScript": ("JavaScript", "ES", "F7DF1E"),
        "TypeScript": ("TypeScript", "TS", "3178C6"),
        "React": ("React", "UI", "61DAFB"),
        "Next.js": ("Next.js", "App", "000000"),
        "Node.js": ("Node.js", "Runtime", "339933"),
        "PostgreSQL": ("PostgreSQL", "DB", "4169E1"),
        "SQLite": ("SQLite", "DB", "003B57"),
        "Redis": ("Redis", "Cache", "DC382D"),
        "Docker": ("Docker", "Container", "2496ED"),
        "AWS": ("AWS", "Cloud", "FF9900"),
        "Tailwind": ("Tailwind", "CSS", "06B6D4"),
        "Pandas": ("Pandas", "Data", "150458"),
        "NumPy": ("NumPy", "Compute", "013243"),
        "scikit-learn": ("scikit--learn", "ML", "F7931E"),
    }

    badges = []
    for tech in stack:
        if tech in mapping:
            lbl, msg, col = mapping[tech]
            badges.append(badge(lbl, msg, col))
        else:
            badges.append(badge(tech, "in%20use", "blue"))
    return badges



@dataclass
class ProjectInfo:
    name: str
    tagline: str
    repo_owner: str
    repo_name: str
    stack: List[str]
    license_name: str
    has_tests: bool
    has_ci: bool
    demo_url: str
    screenshots_note: str


def prompt_yes_no(q: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    ans = input(f"{q} ({suffix}): ").strip().lower()
    if not ans:
        return default
    return ans in {"y", "yes"}


def collect_info() -> ProjectInfo:
    print("\n🧾 Day 13: README Badge Maker\n")

    name = input("Project name: ").strip() or "My Project"
    tagline = input("1-line tagline (what it does): ").strip() or "A tiny project that solves a real problem."

    print("\nRepo info for badges (GitHub):")
    repo_owner = input("GitHub username/org (e.g., dilyoradev): ").strip() or "your-username"
    repo_name = input("Repo name (e.g., day13-readme-maker): ").strip() or "your-repo"

    stack_raw = input("\nTech stack (comma separated, e.g., Python, FastAPI, PostgreSQL): ").strip()
    stack = normalize_stack(stack_raw) if stack_raw else ["Python"]

    license_name = input("\nLicense (MIT/Apache-2.0/GPL-3.0/None): ").strip() or "MIT"

    has_tests = prompt_yes_no("Do you have tests?", default=False)
    has_ci = prompt_yes_no("Do you have GitHub Actions CI?", default=False)

    demo_url = input("\nDemo URL (optional): ").strip()
    screenshots_note = input("Screenshots path note (e.g., ./docs/ or 'add later'): ").strip() or "Add screenshots later."

    return ProjectInfo(
        name=name,
        tagline=tagline,
        repo_owner=repo_owner,
        repo_name=repo_name,
        stack=stack,
        license_name=license_name,
        has_tests=has_tests,
        has_ci=has_ci,
        demo_url=demo_url,
        screenshots_note=screenshots_note,
    )


def make_readme(p: ProjectInfo) -> str:
    gh = f"https://github.com/{p.repo_owner}/{p.repo_name}"

    badges = []
    badges.append(linked_badge("repo", "GitHub", "181717", gh))
    badges.append(linked_badge("stars", "badge", "yellow", f"{gh}/stargazers"))
    badges.append(linked_badge("issues", "open", "blue", f"{gh}/issues"))

    if p.license_name.lower() != "none":
        badges.append(linked_badge("license", p.license_name, "green", f"{gh}/blob/main/LICENSE"))

    if p.has_ci:
        badges.append(f"![CI]({gh}/actions/workflows/ci.yml/badge.svg)")

    if p.has_tests:
        badges.append(badge("tests", "present", "success"))

    # Stack badges
    tech_badges = stack_badges(p.stack)

    demo_line = f"**Demo:** {p.demo_url}\n" if p.demo_url else ""

    today = date.today().isoformat()

    return f"""# {p.name}

{p.tagline}

{' '.join(badges)}
{' '.join(tech_badges)}

{demo_line}