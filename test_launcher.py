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




if __name__ == "__main__":
    unittest.main()
