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
    """Main interactive launcher menu."""
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
