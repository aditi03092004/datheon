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


if __name__ == "__main__":
    unittest.main()
