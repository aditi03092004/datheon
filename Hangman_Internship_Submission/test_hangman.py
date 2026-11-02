"""
Automated Test Suite for Hangman Game
Datheon Python Programming Internship - Task 1

Uses Python's standard unittest library to test all core rules,
input validation, word loading, scoring, and win/loss states.
"""

import tempfile
import unittest
from pathlib import Path

from hangman import (
    Difficulty,
    GameState,
    GuessResult,
    HangmanGame,
    HANGMAN_STAGES,
    filter_words_by_difficulty,
    load_words,
)


class TestWordLoader(unittest.TestCase):
    """Tests dictionary loading and edge case handling."""

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent
        self.words_file = self.base_dir / "english_words.txt"

    def test_load_words_success(self):
        """Verify words load properly from the bundled english_words.txt file."""
        words = load_words(self.words_file)
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 100, "Dictionary should contain at least 100 words.")
        # Ensure all words are stripped, lowercase, and alphabetic
        for word in words[:50]:
            self.assertTrue(word.isalpha(), f"Word '{word}' should be alphabetic.")
            self.assertEqual(word, word.lower(), f"Word '{word}' should be lowercase.")
            self.assertEqual(word, word.strip(), f"Word '{word}' should have no leading/trailing whitespace.")

    def test_load_words_missing_file(self):
        """Verify FileNotFoundError is raised when the dictionary file path is invalid."""
        invalid_path = self.base_dir / "non_existent_dictionary.txt"
        with self.assertRaises(FileNotFoundError):
            load_words(invalid_path)

    def test_load_words_empty_file(self):
        """Verify ValueError is raised when a dictionary file contains no words."""
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write("\n   \n\n")

        try:
            with self.assertRaises(ValueError):
                load_words(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_filter_words_by_difficulty(self):
        """Verify difficulty filtering partitions words by length properly."""
        sample_words = ["cat", "dog", "python", "elephant", "encyclopedia"]
        easy = filter_words_by_difficulty(sample_words, Difficulty.EASY)
        self.assertTrue(all(len(w) <= 5 for w in easy))
        self.assertEqual(sorted(easy), ["cat", "dog"])

        medium = filter_words_by_difficulty(sample_words, Difficulty.MEDIUM)
        self.assertTrue(all(6 <= len(w) <= 8 for w in medium))
        self.assertEqual(sorted(medium), ["elephant", "python"])

        hard = filter_words_by_difficulty(sample_words, Difficulty.HARD)
        self.assertTrue(all(len(w) >= 9 for w in hard))
        self.assertEqual(hard, ["encyclopedia"])


class TestHangmanGameInitialization(unittest.TestCase):
    """Tests game instance initialization and validation of secret words."""

    def test_valid_initialization(self):
        """Verify initial state of a newly created game instance."""
        game = HangmanGame(secret_word="python", max_incorrect=6)
        self.assertEqual(game.secret_word, "python")
        self.assertEqual(game.max_incorrect, 6)
        self.assertEqual(game.incorrect_guesses, 0)
        self.assertEqual(game.remaining_attempts, 6)
        self.assertEqual(len(game.guessed_letters), 0)
        self.assertEqual(game.get_masked_word(), "_ _ _ _ _ _")
        self.assertFalse(game.is_won())
        self.assertFalse(game.is_lost())
        self.assertFalse(game.is_over())

    def test_uppercase_word_normalized(self):
        """Verify uppercase secret words are normalized to lowercase."""
        game = HangmanGame(secret_word="PYTHON")
        self.assertEqual(game.secret_word, "python")

    def test_invalid_secret_word_raises_error(self):
        """Verify ValueError is raised if secret word is empty, non-alphabetic, or whitespace."""
        with self.assertRaises(ValueError):
            HangmanGame(secret_word="")

        with self.assertRaises(ValueError):
            HangmanGame(secret_word="   ")

        with self.assertRaises(ValueError):
            HangmanGame(secret_word="py123")


class TestHangmanGameLogic(unittest.TestCase):
    """Tests guess processing, attempts tracking, duplicates, and validations."""

    def setUp(self):
        self.game = HangmanGame(secret_word="cyber")

    def test_correct_guess(self):
        """Verify a correct guess reveals the letter and does not consume an attempt."""
        result, msg = self.game.process_guess("c")
        self.assertEqual(result, GuessResult.CORRECT)
        self.assertIn("c", self.game.guessed_letters)
        self.assertEqual(self.game.incorrect_guesses, 0)
        self.assertEqual(self.game.remaining_attempts, 6)
        self.assertEqual(self.game.get_masked_word(), "c _ _ _ _")

    def test_incorrect_guess(self):
        """Verify an incorrect guess consumes an attempt and increments incorrect count."""
        result, msg = self.game.process_guess("z")
        self.assertEqual(result, GuessResult.INCORRECT)
        self.assertIn("z", self.game.guessed_letters)
        self.assertEqual(self.game.incorrect_guesses, 1)
        self.assertEqual(self.game.remaining_attempts, 5)
        self.assertEqual(self.game.get_masked_word(), "_ _ _ _ _")

    def test_case_insensitive_guess(self):
        """Verify uppercase input is handled identically to lowercase."""
        result, _ = self.game.process_guess("Y")
        self.assertEqual(result, GuessResult.CORRECT)
        self.assertIn("y", self.game.guessed_letters)
        self.assertEqual(self.game.get_masked_word(), "_ y _ _ _")

    def test_duplicate_guess_prevention(self):
        """Verify re-guessing a letter is rejected without deducting an attempt."""
        # First guess
        self.game.process_guess("b")
        initial_remaining = self.game.remaining_attempts

        # Duplicate guess
        result, msg = self.game.process_guess("b")
        self.assertEqual(result, GuessResult.ALREADY_GUESSED)
        self.assertEqual(self.game.remaining_attempts, initial_remaining)
        self.assertEqual(self.game.incorrect_guesses, 0)

    def test_duplicate_incorrect_guess_prevention(self):
        """Verify re-guessing a wrong letter does NOT deduct a second attempt."""
        # First incorrect guess
        self.game.process_guess("x")
        self.assertEqual(self.game.remaining_attempts, 5)
        self.assertEqual(self.game.incorrect_guesses, 1)

        # Re-guess the same wrong letter
        result, _ = self.game.process_guess("x")
        self.assertEqual(result, GuessResult.ALREADY_GUESSED)
        self.assertEqual(self.game.remaining_attempts, 5)
        self.assertEqual(self.game.incorrect_guesses, 1)

    def test_invalid_input_non_alphabet(self):
        """Verify digits and special characters are rejected without penalty."""
        for invalid in ["1", "9", "!", "@", "#", "$", "_", "-"]:
            result, _ = self.game.process_guess(invalid)
            self.assertEqual(result, GuessResult.INVALID)
            self.assertEqual(self.game.incorrect_guesses, 0)
            self.assertEqual(self.game.remaining_attempts, 6)

    def test_invalid_input_multi_character_and_empty(self):
        """Verify empty strings and multiple characters are rejected without penalty."""
        for invalid in ["", "   ", "ab", "abc", "word"]:
            result, _ = self.game.process_guess(invalid)
            self.assertEqual(result, GuessResult.INVALID)
            self.assertEqual(self.game.incorrect_guesses, 0)
            self.assertEqual(self.game.remaining_attempts, 6)

    def test_sorted_guessed_letters(self):
        """Verify get_sorted_guessed_letters returns letters in alphabetical order."""
        for char in ["e", "a", "z", "b"]:
            self.game.process_guess(char)
        self.assertEqual(self.game.get_sorted_guessed_letters(), ["a", "b", "e", "z"])


class TestHangmanWinAndLossConditions(unittest.TestCase):
    """Tests game termination scenarios: winning and losing."""

    def test_winning_scenario(self):
        """Verify full win condition when all unique letters are guessed."""
        game = HangmanGame(secret_word="cat")
        self.assertFalse(game.is_won())
        self.assertFalse(game.is_over())

        game.process_guess("c")
        game.process_guess("a")
        game.process_guess("t")

        self.assertTrue(game.is_won(), "Game should be marked as won.")
        self.assertFalse(game.is_lost(), "Game should not be marked as lost.")
        self.assertTrue(game.is_over(), "Game should be finished.")
        self.assertEqual(game.get_masked_word(), "c a t")
        self.assertEqual(game.remaining_attempts, 6)

    def test_losing_scenario(self):
        """Verify full loss condition when player makes 6 incorrect guesses."""
        game = HangmanGame(secret_word="dog")
        wrong_letters = ["a", "b", "c", "e", "f", "h"]

        for i, letter in enumerate(wrong_letters, start=1):
            self.assertFalse(game.is_lost(), f"Game should not be lost before attempt {i}.")
            game.process_guess(letter)

        self.assertTrue(game.is_lost(), "Game should be marked as lost after 6 wrong guesses.")
        self.assertFalse(game.is_won(), "Game should not be marked as won.")
        self.assertTrue(game.is_over(), "Game should be finished.")
        self.assertEqual(game.remaining_attempts, 0)
        self.assertEqual(game.incorrect_guesses, 6)

    def test_game_state_transitions(self):
        """Verify state property transitions from IN_PROGRESS to WON or LOST."""
        game = HangmanGame(secret_word="ox")
        self.assertEqual(game.state, GameState.IN_PROGRESS)
        game.process_guess("o")
        self.assertEqual(game.state, GameState.IN_PROGRESS)
        game.process_guess("x")
        self.assertEqual(game.state, GameState.WON)

        losing_game = HangmanGame(secret_word="ox")
        for char in ["a", "b", "c", "d", "e", "f"]:
            losing_game.process_guess(char)
        self.assertEqual(losing_game.state, GameState.LOST)


class TestHangmanArtStages(unittest.TestCase):
    """Tests ASCII art progression across all stages."""

    def test_seven_stages_exist(self):
        """Verify there are exactly 7 stages (0 mistakes to 6 mistakes)."""
        self.assertEqual(len(HANGMAN_STAGES), 7)

    def test_art_progression(self):
        """Verify art stages match the incorrect guess index."""
        game = HangmanGame(secret_word="test")
        wrong_guesses = ["a", "b", "c", "d", "f", "g"]

        for i in range(7):
            expected_art = HANGMAN_STAGES[i]
            self.assertEqual(game.get_current_art(), expected_art)
            if i < len(wrong_guesses):
                game.process_guess(wrong_guesses[i])


if __name__ == "__main__":
    unittest.main()

