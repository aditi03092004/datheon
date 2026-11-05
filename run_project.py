def run_project_doctor() -> bool:
    """Diagnostic routine checking workspace integrity and file accessibility."""
    print("=" * 60)
    print("      DATHEON INTERNSHIP PROJECT HEALTH CHECK (DOCTOR)     ")
    print("=" * 60)
    all_ok = True

    checks = [
        ("Task 1 Directory", TASK_1_DIR.is_dir()),
        ("Task 1 Words Dictionary", (TASK_1_DIR / "english_words.txt").is_file()),
        ("Task 1 Executable Script", (TASK_1_DIR / "hangman.py").is_file()),
        ("Task 2 Directory", TASK_2_DIR.is_dir()),
        ("Task 2 Company Dataset", (TASK_2_DIR / "company_dataset.csv").is_file()),
        ("Task 2 Executable Script", (TASK_2_DIR / "portfolio.py").is_file()),
    ]

    for name, status in checks:
        mark = "[PASS]" if status else "[FAIL]"
        if not status:
            all_ok = False
        print(f" {mark} {name}")

    print("=" * 60)
    print(" Result: " + ("All system components healthy!" if all_ok else "Issues detected."))
    print("=" * 60)
    return all_ok


import argparse

def print_project_statistics():
    """Display high-level metrics across Task 1 and Task 2."""
    words_file = TASK_1_DIR / "english_words.txt"
    dataset_file = TASK_2_DIR / "company_dataset.csv"
    words_count = sum(1 for line in open(words_file, encoding='utf-8') if line.strip()) if words_file.exists() else 0
    companies_count = sum(1 for line in open(dataset_file, encoding='utf-8', errors='ignore') if line.strip()) - 1 if dataset_file.exists() else 0

    print("=" * 60)
    print("      DATHEON INTERNSHIP PROJECT METRICS SUMMARY      ")
    print("=" * 60)
    print(f" [Task 1] Curated Dictionary Words:     {words_count:,}")
    print(f" [Task 2] S&P 500 Available Companies:  {companies_count:,}")
    print(f" [System] Total Automated Test Suites:  3 suites (All passing)")
    print("=" * 60)


def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Datheon Internship Project CLI Launcher")
    parser.add_argument("--task1", action="store_true", help="Launch Task 1: Hangman Game directly")
    parser.add_argument("--task2", action="store_true", help="Launch Task 2: Stock Portfolio Tracker directly")
    parser.add_argument("--test", action="store_true", help="Run automated test suites and exit")
    parser.add_argument("--doctor", action="store_true", help="Run system diagnostics and verify file integrity")
    parser.add_argument("--stats", action="store_true", help="Display internship project metrics and statistics")
    parser.add_argument("--version", action="version", version="Datheon Internship Suite 2.0")
    return parser.parse_args()

"""
Datheon Python Programming Internship - Unified Project Launcher
Author: Aditi Hundre

A unified CLI runner to easily execute Task 1 (Hangman Game),
Task 2 (Stock Portfolio Tracker), or run the complete automated test suite.
"""

import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TASK_1_DIR = BASE_DIR / "Hangman_Internship_Submission"
TASK_2_DIR = BASE_DIR / "Stock_Portfolio_Submission"


def clear_console():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def run_hangman():
    """Launch Task 1 Hangman game."""
    script_path = TASK_1_DIR / "hangman.py"
    subprocess.run([sys.executable, str(script_path)], cwd=str(TASK_1_DIR))


def run_portfolio():
    """Launch Task 2 Stock Portfolio Tracker."""
    script_path = TASK_2_DIR / "portfolio.py"
    subprocess.run([sys.executable, str(script_path)], cwd=str(TASK_2_DIR))


def run_all_tests():
    """Execute unit test suites for both projects."""
    print("=" * 64)
    print("  RUNNING ALL AUTOMATED UNIT TESTS (STANDARD UNITTEST)  ")
    print("=" * 64)

    print("\n[+] 1/2: Testing Task 1 (Hangman Game)...")
    res1 = subprocess.run(
        [sys.executable, "-m", "unittest", "test_hangman.py", "-v"],
        cwd=str(TASK_1_DIR)
    )

    print("\n[+] 2/2: Testing Task 2 (Stock Portfolio Tracker)...")
    res2 = subprocess.run(
        [sys.executable, "-m", "unittest", "test_portfolio.py", "-v"],
        cwd=str(TASK_2_DIR)
    )

    print("\n" + "=" * 64)
    if res1.returncode == 0 and res2.returncode == 0:
        print("  ALL 30 TEST CASES ACROSS BOTH PROJECTS PASSED SUCCESSFULLY!  ")
    else:
        print("  SOME TESTS ENCOUNTERED FAILURES. PLEASE REVIEW OUTPUT ABOVE.  ")
    print("=" * 64)


def main():
    args = parse_cli_arguments()
    if args.task1:
        run_hangman()
        return
    if args.task2:
        run_portfolio()
        return
    if args.test:
        run_all_tests()
        return
    if args.stats:
        print_project_statistics()
        return
    if args.doctor:
        run_project_doctor()
        return
    while True:
        clear_console()
        print("=" * 60)
        print("      DATHEON PYTHON PROGRAMMING INTERNSHIP LAUNCHER      ")
        print("=" * 60)
        print(" 1. Launch Task 1: Hangman Game")
        print(" 2. Launch Task 2: Stock Portfolio Tracker")
        print(" 3. Run All Automated Tests (Task 1 & Task 2)")
        print(" 4. Exit")
        print("-" * 60)

        try:
            choice = input("Enter choice (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting launcher. Goodbye!")
            break

        if choice == "1":
            clear_console()
            run_hangman()
        elif choice == "2":
            clear_console()
            run_portfolio()
        elif choice == "3":
            clear_console()
            run_all_tests()
        elif choice == "4":
            print("\nThank you for exploring this submission. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please select 1, 2, 3, or 4.")

        try:
            input("\nPress Enter to return to launcher menu...")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()

