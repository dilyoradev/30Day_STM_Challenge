import json
from pathlib import Path
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


DATA_FILE = Path("urls.json")

def load_data():
    if not DATA_FILE.exists():
        return {}, 1
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data.get("code_to_url", {}), data.get("next_id", 1)
    except:
        return {}, 1


def save_data(code_to_url, next_id):
    data = {"code_to_url": code_to_url, "next_id": next_id}
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    code_to_url, next_id = load_data()

    while True:
        cmd = input("shorten / expand / quit:\n> ").strip().lower()

        if cmd == "shorten":
            url = input("Enter URL: ").strip()

            if not url:
                print("URL cannot be empty")
                continue

            if not is_valid_url(url):
                print("Invalid URL. Must start with http:// or https:// and include a domain.")
                continue

            code = str(next_id)
            next_id += 1
            code_to_url[code] = url
            save_data(code_to_url, next_id)

            print(f"Short code: {code}")

        elif cmd == "expand":
            code = input("Enter URL code: \n> ").strip()
            url_get = code_to_url.get(code)
            if url_get is None:
                print("Not found")
            else:
                print(url_get)

        elif cmd == 'quit':
            print("Bye!")
            break


if __name__ == "__main__":
    main()