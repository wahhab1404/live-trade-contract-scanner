from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = [
    "bot.py",
    "dashboard.py",
    "sample_data.json",
    "README.md",
]


def main() -> None:
    repo_dir = Path(__file__).resolve().parent
    print(f"Project directory: {repo_dir}")

    missing: list[str] = []
    for name in REQUIRED_FILES:
        file_path = repo_dir / name
        if file_path.exists():
            print(f"[OK] {name}")
        else:
            missing.append(name)
            print(f"[MISSING] {name}")

    if missing:
        print("\nSome required files are missing.")
        print("If this is a git clone, run:")
        print("  git pull")
        print("  git checkout main")
        print("Then run this command from the project directory:")
        print("  python dashboard.py --input sample_data.json --timeframe 1h --host 127.0.0.1 --port 8080")
        raise SystemExit(1)

    print("\nAll required files are present.")
    print("Run dashboard with:")
    print("  python dashboard.py --input sample_data.json --timeframe 1h --host 127.0.0.1 --port 8080")


if __name__ == "__main__":
    main()
