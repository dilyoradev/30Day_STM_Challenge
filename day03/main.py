import string

def read_text():
    user_input = []
    while True:
        text = input("Enter text (type DONE to finish):\n> ")
        if text.strip().upper() == "DONE":
            break
        if text.strip() == "":
            continue
        user_input.append(text)
    return "\n".join(user_input)


def tokenize(user_input: str) -> list[str]:
    table = str.maketrans('','', string.punctuation)
    cleaned_input = user_input.lower().translate(table)
    tokens = cleaned_input.split()
    return tokens


def count_words(tokens: list[str]) -> dict[str, int]:
    counts = {}
    for word in tokens:
        counts[word] = counts.get(word, 0) + 1
    return counts


def main():
    while True:
        text = read_text()
        if not text.strip():
            print("No text provided!")
            return
        tokens = tokenize(text)
        counts = count_words(tokens)

        print(counts)

        again = input("Analyze another text? (y/n)").lower()
        if again != "y":
            print("Bye")
            break

if __name__ == "__main__":
    main()
