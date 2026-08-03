import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def run_step(step_name: str, command: list[str], index: int, total: int) -> None:
    print(f"[{index}/{total}] {step_name}...")
    try:
        subprocess.run(command, cwd=str(BASE_DIR), check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Error during {step_name}: {exc}")
        raise SystemExit(1) from exc
    print("Done")


def main() -> None:
    print("==================================")
    print("AI JOB HUNTER")
    print("==================================")

    steps = [
        ("Searching jobs", [sys.executable, "src/main.py"]),
        ("Cleaning jobs", [sys.executable, "src/clean_jobs.py"]),
        ("Matching jobs", [sys.executable, "src/match_jobs.py"]),
        ("Final filtering", [sys.executable, "src/finalize_jobs.py"]),
        ("Telegram message generated", [sys.executable, "src/polish_final_jobs.py"]),
    ]

    for index, (label, command) in enumerate(steps, start=1):
        run_step(label, command, index, len(steps))

    print("==================================")
    print("Completed Successfully")
    print("==================================")


if __name__ == "__main__":
    main()
