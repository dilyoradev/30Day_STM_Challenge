import random

def game_level():
    while True:
        level = input("Choose the level:\n"
        "1. Easy\n"
        "2. Medium\n"
        "3. Hard\n"
        ">").strip()

        if not level.isdigit():
            print("Enter a number between 1-3")
            continue
        
        level = int(level)
        if 1 <= level <= 3:
            return level
        print("Enter a number between 1-3")


def get_range_and_attempts(level):
    if level == 1:
        return 1, 10, 3
    elif level == 2:
        return 1, 50, 4
    else:
        return 1, 100, 5


def get_guess(low, high):
    while True:
        user_guess = input(f"Hello!/n Enter your guess between {low}-{high}: ").strip()

        if not user_guess.isdigit():
            print("Not number. Try again!")
            continue
        
        user_guess = int(user_guess)
        if low <= user_guess <= high:
            return user_guess
        
        print(f"Out of range. Enter {low}-{high}.")


def play_round():
    level = game_level()
    low, high, attempts = get_range_and_attempts(level)

    secret = random.randint(low, high)
    print(f"/nI picked a number between {low} and {high}. You have {attempts} tries.\n")

    tries_used = 0
    while tries_used < attempts:
        print(f"Guess #{tries_used + 1}:")
        guess = get_guess(low, high)
        tries_used += 1

        if guess > secret:
            print("Too high.\n")
        elif guess < secret:
            print("Too low.\n")
        else:
            print(f"Bingo! You got it in {tries_used} guesses.\n")
            return
    
    print(f"Out of tries! The number was {secret}.\n")


def main():
    while True:
        play_round()
        again = input("Play again?(y/n): ").strip().lower()
        if again != "y":
            print("Bye!")
            break


if __name__ == "__main__":
    main()
