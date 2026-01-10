import shutil
from pathlib import Path

def main():
    user_file = input("Input the txt file name to copy to secret folder:\n> ").strip()

    home = Path.home()
    src = home / user_file

    secret_dir = home / "secret_folder"
    secret_dir.mkdir(parents=True, exist_ok=True)

    dst = secret_dir / "user_secret.txt"

    if not src.exists():
        print(f"File not found: {src}")
        return
    if not src.is_file():
        print(f"Not a file: {src}")
        return

    shutil.copy2(src, dst)  # copy2 keeps metadata when possible
    print(f"Copied '{src.name}' → '{dst}'")

if __name__ == "__main__":
    main()

