import random
from datetime import date

def pick(mapping: dict, key: str, fallback_key: str = "default") -> str:
    options = mapping.get(key.lower().strip(), mapping[fallback_key])
    return random.choice(options)

def nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Please type something (not empty).")

def main():
    print("\n=== Day 8: Smart Compliment Generator ===")
    name = nonempty("Your name: ")
    vibe = nonempty("Your vibe (e.g., disciplined, calm, bold, curious): ").lower()
    goal = nonempty("Your goal right now (e.g., internship, exams, project): ")

    seed = f"{date.today().isoformat()}::{name.lower()}::{vibe}::{goal.lower()}"
    random.seed(seed)

    openers = [
        f"{name}, real talk:",
        f"Hey {name} — quick reminder:",
        f"{name}, here’s what I see:",
        f"Yo {name}:",
    ]

    vibe_compliments = {
        "disciplined": [
            "Your discipline is rare. You do what you said you'd do — even when it’s boring.",
            "You’re the kind of person who stacks days quietly and then surprises everyone.",
        ],
        "calm": [
            "Your calm is power. You don’t waste energy panicking — you move with clarity.",
            "You’re steady. That’s a superpower when things get chaotic.",
        ],
        "bold": [
            "You’re bold in a way that actually creates momentum. You don’t wait for permission.",
            "You have that builder energy: decide → act → adjust.",
        ],
        "curious": [
            "Your curiosity is dangerous (in the best way). You keep pulling threads until you understand.",
            "You don’t just learn — you *investigate*. That’s how strong engineers think.",
        ],
        "default": [
            "You’re showing up. That already puts you ahead of most people.",
            "You have momentum. Protect it. It’s more valuable than motivation.",
        ],
    }

    goal_reflections = {
        "internship": [
            "This internship phase is not supposed to feel easy — it’s literally your skill expanding.",
            "Every confusing moment is a future “oh, I’ve seen this before.”",
        ],
        "exams": [
            "Your future self will thank you for the boring reps you’re doing now.",
            "You’re not behind — you’re in training.",
        ],
        "project": [
            "Projects are where confidence gets built for real. Keep shipping small pieces.",
            "Your project doesn’t need to be perfect. It needs to exist.",
        ],
        "default": [
            "You’re closer than you think. Keep the loop tight: plan → do → reflect.",
            "Progress is messy. That’s proof you’re doing real work.",
        ],
    }

    micro_actions = [
        "Do a 10-minute “ugly first draft” (no perfection allowed).",
        "Write down the next 1 step only — then do it immediately.",
        "Refactor one small thing: rename variables + add a docstring.",
        "Make it testable: add 1 simple test or a print-check.",
        "Do a 15-minute focus sprint with phone out of reach.",
        "If stuck: write the error in 1 sentence, then list 3 hypotheses.",
    ]

    signatures = [
        "Now go win your next 20 minutes.",
        "Small steps. Zero drama. Keep moving.",
        "You’re building proof, not vibes.",
        "You don’t need confidence first — you earn it by shipping.",
    ]

    gkey = "default"
    g = goal.lower()
    if "intern" in g:
        gkey = "internship"
    elif "exam" in g or "test" in g:
        gkey = "exams"
    elif "project" in g or "build" in g or "app" in g:
        gkey = "project"

    print("\n" + random.choice(openers))
    print(pick(vibe_compliments, vibe))
    print(pick(goal_reflections, gkey))

    print("\nYour 3-step mini plan:")
    plan = random.sample(micro_actions, k=3)
    for i, step in enumerate(plan, start=1):
        print(f"  {i}. {step}")

    print("\n" + random.choice(signatures))
    print("========================================\n")

if __name__ == "__main__":
    main()