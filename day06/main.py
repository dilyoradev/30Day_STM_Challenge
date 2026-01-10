import random
from datetime import date

def gen_coding(r: random.Random) -> dict:
    minutes = r.choice([10, 15, 20, 25])
    platform = r.choice(["Exercism", "LeetCode", "HackerRank", "Codewars"])
    diff = r.choice(["easy", "easy", "medium"])  # weighted
    task = r.choice([
        f"Solve 1 {diff} problem on {platform}",
        f"Refactor 1 function: rename variables + add docstring ({minutes} min)",
        f"Write tests for 1 function ({minutes} min)",
        f"Read a bug/stacktrace and explain it in 5 bullet points ({minutes} min)",
    ])
    points = 1 if minutes <= 15 else 2
    return {"text": task, "points": points}

def gen_health(r: random.Random) -> dict:
    minutes = r.choice([5, 8, 10, 12])
    reps = r.choice([10, 12, 15, 20])
    task = r.choice([
        f"Walk for {minutes} minutes",
        f"Stretch for {minutes} minutes",
        f"{reps} squats + {reps//2} push-ups (knee push-ups ok)",
        f"Core: {minutes} min plank variations (break as needed)",
    ])
    return {"text": task, "points": 1 if minutes <= 8 else 2}

def gen_cleaning(r: random.Random) -> dict:
    minutes = r.choice([3, 5, 7, 10])
    target = r.choice(["desk", "backpack", "downloads folder", "photo gallery", "notes app"])
    task = r.choice([
        f"Reset your {target} for {minutes} minutes",
        f"Throw away / delete 10 useless items from your {target}",
        f"Put 10 things back where they belong ({minutes} min)",
    ])
    return {"text": task, "points": 1}

# If you want these menu options, you need generators for them:
def gen_study(r: random.Random) -> dict:
    minutes = r.choice([15, 20, 25, 30])
    task = r.choice([
        f"Do {minutes} minutes of focused study (no phone)",
        f"Summarize what you learned today in 5 bullet points ({minutes} min)",
        f"Review yesterday’s notes for {minutes} minutes and rewrite 3 key points",
    ])
    return {"text": task, "points": 1 if minutes <= 20 else 2}

def gen_confidence(r: random.Random) -> dict:
    task = r.choice([
        "Write 3 wins from today (even tiny ones)",
        "Send one message you’ve been delaying",
        "Write 1 paragraph: what you’re building this week and why it matters",
    ])
    return {"text": task, "points": 1}

GENERATORS = {
    "coding": gen_coding,
    "study": gen_study,
    "health": gen_health,
    "cleaning": gen_cleaning,
    "confidence": gen_confidence,
}

MENU = [
    ("coding", "Coding"),
    ("study", "Study"),
    ("health", "Health"),
    ("cleaning", "Cleaning"),
    ("confidence", "Confidence"),
]

def generate(category: str, seed: str | None = None) -> dict:
    r = random.Random(seed)
    return GENERATORS[category](r)

def choose_category() -> str:
    print("\nChoose category:")
    for i, (key, label) in enumerate(MENU, start=1):
        print(f"{i}. {label}")

    while True:
        raw = input("> ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(MENU):
                return MENU[idx - 1][0]
        print("Enter a valid number (e.g., 1).")

def main():
    while True:
        category = choose_category()

        # Daily-seeded challenge (same per day + category)
        seed = f"{date.today().isoformat()}-{category}"
        challenge = generate(category, seed=seed)

        print("\nYour challenge for today:")
        print(f"  [{category}] {challenge['text']}  (+{challenge['points']} pts)")

        action = input("\n(y=done / n=skip / q=quit) > ").strip().lower()
        if action == "q":
            print("Bye!")
            break
        if action == "y":
            print("Completed. Nice.")
        elif action == "n":
            print("Skipped. No problem.")
        else:
            print("Unknown input. Going back to menu.")

if __name__ == "__main__":
    main()
