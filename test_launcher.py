"""
Automated unit tests for unified project launcher run_project.py.
"""

import unittest
from pathlib import Path
from run_project import BASE_DIR, TASK_1_DIR, TASK_2_DIR


class TestLauncherConfiguration(unittest.TestCase):
    def test_paths_exist(self):
        self.assertTrue(BASE_DIR.exists())
        self.assertTrue(TASK_1_DIR.exists())
        self.assertTrue(TASK_2_DIR.exists())
        self.assertTrue((TASK_1_DIR / "hangman.py").exists())
        self.assertTrue((TASK_2_DIR / "portfolio.py").exists())


if __name__ == "__main__":
    unittest.main()
