"""
Automated unit tests for unified project launcher run_project.py.
"""

import unittest
from pathlib import Path
from run_project import BASE_DIR, TASK_1_DIR, TASK_2_DIR, clean_project_cache, run_project_doctor


class TestLauncherConfiguration(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(BASE_DIR.exists())
        self.assertTrue(TASK_1_DIR.exists())
        self.assertTrue(TASK_2_DIR.exists())
        self.assertTrue((TASK_1_DIR / "hangman.py").exists())
        self.assertTrue((TASK_2_DIR / "portfolio.py").exists())

    def test_run_project_doctor(self):
        """Verify doctor health-check passes in valid workspace."""
        self.assertTrue(run_project_doctor())

    def test_clean_project_cache(self):
        """Verify clean_project_cache executes safely and returns non-negative integer."""
        result = clean_project_cache()
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    def test_print_consolidated_summary(self):
        """Verify consolidated summary prints cleanly without exception."""
        from run_project import print_consolidated_summary
        try:
            print_consolidated_summary()
        except Exception as e:
            self.fail(f"print_consolidated_summary raised {e}")

    def test_run_benchmark(self):
        """Verify run_benchmark executes safely without uncaught exception."""
        from run_project import run_benchmark
        try:
            run_benchmark()
        except Exception as e:
            self.fail(f"run_benchmark raised {e}")

    def test_lookup_ticker_info(self):
        """Verify lookup_ticker_info returns True for valid ticker and False for invalid."""
        from run_project import lookup_ticker_info
        self.assertTrue(lookup_ticker_info("AAPL"))
        self.assertFalse(lookup_ticker_info("NONEXISTENT_XYZ"))

    def test_run_quick_check(self):
        """Verify run_quick_check executes diagnostic check and returns True."""
        from run_project import run_quick_check
        self.assertTrue(run_quick_check())

    def test_run_system_info(self):
        """Verify run_system_info returns telemetry dictionary with correct keys."""
        from run_project import run_system_info
        info = run_system_info()
        self.assertIsInstance(info, dict)
        self.assertEqual(info["version"], "2.5.0")
        self.assertGreater(info["task1_words"], 0)
        self.assertGreater(info["task2_companies"], 0)
        self.assertIn("python_version", info)
        self.assertIn("os_platform", info)

    def test_run_codebase_audit(self):
        """Verify run_codebase_audit measures Python file counts and lines of code."""
        from run_project import run_codebase_audit
        audit = run_codebase_audit()
        self.assertIsInstance(audit, dict)
        self.assertGreaterEqual(audit["python_files_count"], 5)
        self.assertGreater(audit["total_lines_of_code"], 2000)
        self.assertGreater(audit["task1_lines"], 500)
        self.assertGreater(audit["task2_lines"], 1000)
        self.assertGreater(audit["test_lines"], 500)


if __name__ == "__main__":
    unittest.main()
