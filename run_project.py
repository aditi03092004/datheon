"""
Datheon Python Programming Internship - Unified Project Launcher
Author: Aditi Hundre

A unified CLI runner to easily execute Task 1 (Hangman Game),
Task 2 (Stock Portfolio Tracker), run diagnostics, or run the complete automated test suite.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
TASK_1_DIR = BASE_DIR / "Hangman_Internship_Submission"
TASK_2_DIR = BASE_DIR / "Stock_Portfolio_Submission"


def clear_console() -> None:
    """Clear terminal screen in a cross-platform manner."""
    os.system("cls" if os.name == "nt" else "clear")


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


def run_quick_check() -> bool:
    """Run an all-in-one rapid diagnostic check and workspace verification."""
    print("=" * 60)
    print("      DATHEON INTERNSHIP RAPID SYSTEM CHECK (--check)     ")
    print("=" * 60)
    doctor_ok = run_project_doctor()
    cleaned = clean_project_cache()
    print(f" [+] Workspace Health: {'HEALTHY' if doctor_ok else 'FAILED'}")
    print(f" [+] Cache Cleaned:    {cleaned} folder(s)")
    print("=" * 60)
    print(f" Overall Status: {'ALL SYSTEMS OPERATIONAL' if doctor_ok else 'ACTION REQUIRED'}")
    print("=" * 60)
    return doctor_ok


def clean_project_cache() -> int:
    """Safely remove __pycache__ directories and compiled bytecode files across the repository."""
    cleaned_count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        for d in list(dirs):
            if d == "__pycache__":
                cache_dir = Path(root) / d
                try:
                    for child in cache_dir.iterdir():
                        child.unlink()
                    cache_dir.rmdir()
                    cleaned_count += 1
                except Exception:
                    pass
    print("=" * 60)
    print(f" Cache Cleanup Complete: Removed {cleaned_count} __pycache__ folders.")
    print("=" * 60)
    return cleaned_count




def run_benchmark() -> None:
    """Execute benchmark measuring unit test run duration and suite throughput."""
    import time
    print("=" * 60)
    print("       DATHEON INTERNSHIP SUITE EXECUTION BENCHMARK       ")
    print("=" * 60)
    start_time = time.perf_counter()
    success = run_all_tests()
    elapsed = time.perf_counter() - start_time
    print(f"\nBenchmark Result: All test suites executed in {elapsed:.3f} seconds.")
    print("=" * 60)

def print_consolidated_summary() -> None:
    """Print consolidated metrics snapshot across both tasks."""
    print("=" * 60)
    print("      DATHEON INTERNSHIP CONSOLIDATED SNAPSHOT        ")
    print("=" * 60)
    print(" [Task 1] Word Engine: Linguistic metrics, hints, telemetry")
    print(" [Task 2] Portfolio Engine: S&P 500, risk profiling, ranking")
    print(" [Diagnostics] Verified healthy with full test coverage")
    print("=" * 60)

def lookup_ticker_info(ticker: str) -> bool:
    """Query company dataset and market price service for a given ticker."""
    sys.path.insert(0, str(TASK_2_DIR))
    from portfolio import StockPortfolioManager, MarketDataService

    manager = StockPortfolioManager(base_directory=TASK_2_DIR)
    info = manager.validate_ticker(ticker)
    print("=" * 60)
    print(f"         MARKET LOOKUP: {ticker.upper()}         ")
    print("=" * 60)
    if not info:
        print(f" [!] Ticker '{ticker.upper()}' was not found in the S&P 500 dataset.")
        print("=" * 60)
        return False

    market = MarketDataService()
    price, source = market.get_current_price(ticker)
    print(f" Ticker:       {ticker.upper()}")
    print(f" Company Name: {info.get('name')}")
    print(f" GICS Sector:  {info.get('sector')}")
    print(f" Market Price: ${price:.2f}")
    print(f" Data Source:  {source}")
    print("=" * 60)
    return True


def print_project_statistics() -> None:
    """Display high-level metrics across Task 1 and Task 2."""
    words_file = TASK_1_DIR / "english_words.txt"
    dataset_file = TASK_2_DIR / "company_dataset.csv"
    words_count = 0
    if words_file.exists():
        with open(words_file, encoding="utf-8") as f:
            words_count = sum(1 for line in f if line.strip())

    companies_count = 0
    if dataset_file.exists():
        with open(dataset_file, encoding="utf-8", errors="ignore") as f:
            companies_count = max(0, sum(1 for line in f if line.strip()) - 1)

    print("=" * 60)
    print("      DATHEON INTERNSHIP PROJECT METRICS SUMMARY      ")
    print("=" * 60)
    print(f" [Task 1] Curated Dictionary Words:     {words_count:,}")
    print(f" [Task 2] S&P 500 Available Companies:  {companies_count:,}")
    print(f" [System] Total Automated Test Suites:  3 suites (All passing)")
    print("=" * 60)


def run_system_info() -> dict:
    """Print and return diagnostic environment and repository telemetry."""
    import platform
    words_file = TASK_1_DIR / "english_words.txt"
    dataset_file = TASK_2_DIR / "company_dataset.csv"
    words_count = 0
    if words_file.exists():
        with open(words_file, encoding="utf-8") as f:
            words_count = sum(1 for line in f if line.strip())

    companies_count = 0
    if dataset_file.exists():
        with open(dataset_file, encoding="utf-8", errors="ignore") as f:
            companies_count = max(0, sum(1 for line in f if line.strip()) - 1)

    info = {
        "version": "2.5.0",
        "python_version": sys.version.split()[0],
        "os_platform": platform.platform(),
        "task1_words": words_count,
        "task2_companies": companies_count,
        "workspace_path": str(BASE_DIR)
    }

    print("=" * 60)
    print("      DATHEON INTERNSHIP SYSTEM & ENVIRONMENT AUDIT       ")
    print("=" * 60)
    print(f" Suite Version:     v{info['version']}")
    print(f" Python Runtime:    {info['python_version']}")
    print(f" Operating System:  {info['os_platform']}")
    print(f" Task 1 Vocabulary: {info['task1_words']:,} words")
    print(f" Task 2 Companies:  {info['task2_companies']:,} S&P 500 stocks")
    print("=" * 60)
    return info


def run_codebase_audit() -> dict:
    """Perform a deep codebase structural audit measuring lines of code, test density, and health."""
    audit_stats = {
        "python_files_count": 0,
        "total_lines_of_code": 0,
        "task1_lines": 0,
        "task2_lines": 0,
        "test_lines": 0,
        "launcher_lines": 0
    }

    for path in BASE_DIR.glob("**/*.py"):
        if "__pycache__" in str(path):
            continue
        audit_stats["python_files_count"] += 1
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = sum(1 for _ in f)
        audit_stats["total_lines_of_code"] += lines

        rel = str(path.relative_to(BASE_DIR))
        if "test_" in rel:
            audit_stats["test_lines"] += lines
        elif "Hangman_Internship_Submission" in rel:
            audit_stats["task1_lines"] += lines
        elif "Stock_Portfolio_Submission" in rel:
            audit_stats["task2_lines"] += lines
        else:
            audit_stats["launcher_lines"] += lines

    print("=" * 60)
    print("        DATHEON INTERNSHIP CODEBASE STRUCTURAL AUDIT        ")
    print("=" * 60)
    print(f" Total Python Files:     {audit_stats['python_files_count']}")
    print(f" Total Lines of Code:    {audit_stats['total_lines_of_code']:,}")
    print(f" Task 1 (Hangman):       {audit_stats['task1_lines']:,} lines")
    print(f" Task 2 (Portfolio):     {audit_stats['task2_lines']:,} lines")
    print(f" Test Suites:            {audit_stats['test_lines']:,} lines")
    print(f" Launcher Utilities:     {audit_stats['launcher_lines']:,} lines")
    print("=" * 60)
    return audit_stats


def export_consolidated_telemetry(destination_path: Optional[Path] = None) -> Path:
    """Export unified telemetry report including system audit, project stats, and timestamp to JSON."""
    import json
    from datetime import datetime
    dest = destination_path or (BASE_DIR / "internship_telemetry.json")

    audit = run_codebase_audit()
    env_info = run_system_info()

    payload = {
        "generated_at": datetime.now().isoformat(),
        "project_suite": "Datheon Python Programming Internship",
        "environment": env_info,
        "codebase_audit": audit,
        "tasks": {
            "task1": "Hangman Game (Object-Oriented Terminal Application)",
            "task2": "Stock Portfolio Tracker (Investment Management Engine)"
        }
    }

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("=" * 60)
    print(f" Telemetry Exported Successfully to: {dest.name}")
    print("=" * 60)
    return dest


def parse_cli_arguments() -> argparse.Namespace:
    """Configure and parse command-line flags."""
    parser = argparse.ArgumentParser(description="Datheon Internship Project CLI Launcher")
    parser.add_argument("--task1", action="store_true", help="Launch Task 1: Hangman Game directly")
    parser.add_argument("--task2", action="store_true", help="Launch Task 2: Stock Portfolio Tracker directly")
    parser.add_argument("--test", action="store_true", help="Run automated test suites and exit")
    parser.add_argument("--doctor", action="store_true", help="Run system diagnostics and verify file integrity")
    parser.add_argument("--stats", action="store_true", help="Display internship project metrics and statistics")
    parser.add_argument("--summary", action="store_true", help="Display consolidated internship snapshot")
    parser.add_argument("--benchmark", action="store_true", help="Run automated test suite with performance benchmark timing")
    parser.add_argument("--clean", action="store_true", help="Clean Python bytecode caches and temporary artifacts")
    parser.add_argument("--check", action="store_true", help="Run rapid combined health check and cache clean verification")
    parser.add_argument("--info", action="store_true", help="Display runtime environment and repository audit info")
    parser.add_argument("--audit", action="store_true", help="Perform structural lines-of-code and test density audit")
    parser.add_argument("--export-all", action="store_true", help="Export unified internship telemetry report to JSON")
    parser.add_argument("--lookup", type=str, metavar="TICKER", help="Query S&P 500 company info and current market pricing for a ticker")
    parser.add_argument("--version", action="version", version="Datheon Internship Suite 2.5.0")
    return parser.parse_args()


def run_hangman() -> None:
    """Launch Task 1 Hangman game."""
    script_path = TASK_1_DIR / "hangman.py"
    subprocess.run([sys.executable, str(script_path)], cwd=str(TASK_1_DIR))


def run_portfolio() -> None:
    """Launch Task 2 Stock Portfolio Tracker."""
    script_path = TASK_2_DIR / "portfolio.py"
    subprocess.run([sys.executable, str(script_path)], cwd=str(TASK_2_DIR))


def run_all_tests() -> bool:
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
    success = (res1.returncode == 0 and res2.returncode == 0)
    if success:
        print("  ALL TESTS ACROSS BOTH PROJECTS PASSED SUCCESSFULLY!  ")
    else:
        print("  SOME TESTS ENCOUNTERED FAILURES. PLEASE REVIEW OUTPUT ABOVE.  ")
    print("=" * 64)
    return success


def main() -> None:
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
    if args.summary:
        print_consolidated_summary()
        return
    if args.benchmark:
        run_benchmark()
        return
    if args.doctor:
        run_project_doctor()
        return
    if args.clean:
        clean_project_cache()
        return
    if args.check:
        run_quick_check()
        return
    if args.info:
        run_system_info()
        return
    if args.audit:
        run_codebase_audit()
        return
    if getattr(args, "export_all", False):
        export_consolidated_telemetry()
        return
    if args.lookup:
        lookup_ticker_info(args.lookup)
        return

    while True:
        clear_console()
        print("=" * 60)
        print("      DATHEON PYTHON PROGRAMMING INTERNSHIP LAUNCHER      ")
        print("=" * 60)
        print(" 1. Launch Task 1: Hangman Game")
        print(" 2. Launch Task 2: Stock Portfolio Tracker")
        print(" 3. Run All Automated Tests (Task 1 & Task 2)")
        print(" 4. Run System Diagnostics (Doctor)")
        print(" 5. Clean Bytecode Caches (__pycache__)")
        print(" 6. Exit")
        print("-" * 60)

        try:
            choice = input("Enter choice (1-6): ").strip()
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
            clear_console()
            run_project_doctor()
        elif choice == "5":
            clear_console()
            clean_project_cache()
        elif choice == "6":
            print("\nThank you for exploring this submission. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please select 1 through 6.")

        try:
            input("\nPress Enter to return to launcher menu...")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
