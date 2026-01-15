from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


MOODS = ["stressed", "bored", "anxious", "tired", "motivated", "sad", "angry", "okay"]
ENERGIES = ["low", "medium", "high"]
TIMES = [5, 10, 20, 40]


@dataclass(frozen=True)
class Plan:
    title: str
    steps: List[str]
    why: str


def build_plans() -> Dict[str, Dict[str, Dict[int, List[Plan]]]]:
    """
    SUGGESTIONS[mood][energy][time] -> list[Plan]
    """
    def p(title: str, steps: List[str], why: str) -> Plan:
        return Plan(title=title, steps=steps, why=why)

    S: Dict[str, Dict[str, Dict[int, List[Plan]]]] = {m: {e: {t: [] for t in TIMES} for e in ENERGIES} for m in MOODS}

    # ---- stressed ----
    for t in TIMES:
        S["stressed"]["low"][t] += [
            p(
                "2-minute reset + tiny task",
                [
                    "Set a 2-minute timer and breathe slowly (inhale 4s, exhale 6s).",
                    "Write down the ONE thing causing stress in one sentence.",
                    "Pick a tiny next action you can do in under 3 minutes.",
                    "Do it now (even if it’s imperfect).",
                ],
                "Lower your stress response, then regain control with a small win.",
            ),
        ]
        S["stressed"]["medium"][t] += [
            p(
                "Brain dump → next 3 actions",
                [
                    "Open a note and dump everything on your mind for 3–5 minutes.",
                    "Circle the most urgent/important item.",
                    "Write 3 next actions (verbs) you can do today.",
                    "Do the first action for the remaining time.",
                ],
                "Externalizing thoughts reduces mental load and clarifies priorities.",
            ),
        ]
        S["stressed"]["high"][t] += [
            p(
                "Speed clean + focus sprint",
                [
                    "Put on a 5–10 minute timer and tidy only visible clutter.",
                    "Prepare a glass of water.",
                    "Define one output for the next focus sprint (e.g., 'finish function X').",
                    "Work until the timer ends—no multitasking.",
                ],
                "Environment reset + clear goal makes focus easier under stress.",
            ),
        ]

    # ---- bored ----
    for t in TIMES:
        S["bored"]["low"][t] += [
            p(
                "Micro-curiosity challenge",
                [
                    "Pick a random topic you’ve wondered about (1 line).",
                    "Search one reliable source (book/docs) and read 5 minutes.",
                    "Write 3 bullet takeaways.",
                    "Share/commit one tiny artifact (note, gist, README line).",
                ],
                "Boredom often wants novelty—give it controlled novelty.",
            ),
        ]
        S["bored"]["medium"][t] += [
            p(
                "Creative sprint (no perfection)",
                [
                    "Choose: write 10 lines, sketch 5 minutes, or code a tiny toy feature.",
                    "Set a timer and start immediately.",
                    "When the timer ends, stop and name the result.",
                    "Decide one small improvement (optional).",
                ],
                "Short sprints rebuild momentum without requiring motivation.",
            ),
        ]
        S["bored"]["high"][t] += [
            p(
                "Make something tiny + publish it",
                [
                    "Pick one: CLI joke, small script, mini HTML page, or README badge.",
                    "Build the smallest working version in 10–20 minutes.",
                    "Add a 3-line README explaining it.",
                    "Commit/push (or save locally if not ready).",
                ],
                "Bored energy becomes satisfying when it produces a visible output.",
            ),
        ]

    # ---- anxious ----
    for t in TIMES:
        S["anxious"]["low"][t] += [
            p(
                "Grounding: 5-4-3-2-1 + one step",
                [
                    "Name 5 things you see.",
                    "Name 4 things you feel (touch).",
                    "Name 3 things you hear.",
                    "Name 2 things you smell.",
                    "Name 1 thing you taste.",
                    "Then write ONE next step you can do in 2 minutes and do it.",
                ],
                "Grounding reduces spirals and turns anxiety into action.",
            ),
        ]
        S["anxious"]["medium"][t] += [
            p(
                "Fear → facts → next action",
                [
                    "Write: 'I’m afraid that ________.'",
                    "Write 3 facts you know (no assumptions).",
                    "Write 2 things you can control today.",
                    "Pick 1 action and do it for the remaining time.",
                ],
                "Separating facts from fears breaks the spiral.",
            ),
        ]
        S["anxious"]["high"][t] += [
            p(
                "Walk + voice note plan",
                [
                    "Walk for 5–10 minutes (even indoors).",
                    "Record a quick voice note: what’s wrong + what’s next.",
                    "Write a 3-step plan from the voice note.",
                    "Do step 1 immediately.",
                ],
                "Movement + externalizing thoughts lowers anxiety and restores agency.",
            ),
        ]

    # ---- tired ----
    for t in TIMES:
        S["tired"]["low"][t] += [
            p(
                "Minimum viable recharge",
                [
                    "Drink water.",
                    "Do a 60–120 second stretch (neck/shoulders).",
                    "Close eyes and breathe for 2 minutes.",
                    "Choose ONE tiny task (2–3 minutes) to regain momentum.",
                ],
                "Tiny recovery + tiny progress beats forcing deep work while exhausted.",
            ),
        ]
        S["tired"]["medium"][t] += [
            p(
                "Low-energy productivity",
                [
                    "Pick a 'maintenance' task: clean inbox, sort files, update README.",
                    "Set a timer (10–20 mins).",
                    "Work slowly, no context switching.",
                    "St
