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
    WinStreakTracker,
    Difficulty,
    GameState,
    GuessResult,
    HangmanGame,
    HANGMAN_STAGES,
    calculate_word_complexity,
    calculate_vowel_consonant_metrics,
    calculate_letter_frequency_analysis,
    calculate_pattern_similarity,
    calculate_edit_distance,
    check_word_symmetry,
    estimate_syllable_count,
    filter_words_by_difficulty,
    find_anagram_candidates,
    find_closest_dictionary_words,
    find_pattern_matches,
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

    def test_get_hint(self):
        """Verify get_hint returns an unrevealed character or None when all are guessed."""
        game = HangmanGame(secret_word="sky")
        hint = game.get_hint()
        self.assertIn(hint, ["s", "k", "y"])

        # Guess that hint
        game.process_guess(hint)
        # Next hint should not be the already guessed letter
        next_hint = game.get_hint()
        self.assertNotEqual(next_hint, hint)

        # Guess remaining letters
        for ch in ["s", "k", "y"]:
            game.process_guess(ch)
        self.assertIsNone(game.get_hint())

    def test_hint_budget_enforcement(self):
        """Verify hint budget decrements and returns None when exhausted."""
        game = HangmanGame(secret_word="planet", max_hints=2)
        self.assertEqual(game.max_hints, 2)
        self.assertEqual(game.hints_used, 0)
        self.assertEqual(game.remaining_hints, 2)

        # First hint
        h1 = game.get_hint()
        self.assertIsNotNone(h1)
        self.assertEqual(game.hints_used, 1)
        self.assertEqual(game.remaining_hints, 1)

        # Second hint
        h2 = game.get_hint()
        self.assertIsNotNone(h2)
        self.assertEqual(game.hints_used, 2)
        self.assertEqual(game.remaining_hints, 0)

        # Third attempt: budget exhausted, returns None
        h3 = game.get_hint()
        self.assertIsNone(h3)
        self.assertEqual(game.remaining_hints, 0)

    def test_hint_budget_custom_and_peek(self):
        """Verify non-consuming peek and negative hint budget validation."""
        game = HangmanGame(secret_word="orbit", max_hints=1)
        # Peeking without consuming budget
        peeked = game.get_hint(consume_budget=False)
        self.assertIsNotNone(peeked)
        self.assertEqual(game.hints_used, 0)
        self.assertEqual(game.remaining_hints, 1)

        # Negative hints should raise ValueError
        with self.assertRaises(ValueError):
            HangmanGame(secret_word="orbit", max_hints=-1)

    def test_get_smart_hint_strategies(self):
        """Verify frequency-weighted smart hints for word_frequency and english_frequency."""
        # 1. Word frequency strategy: 'a' appears 3 times in banana
        game_banana = HangmanGame(secret_word="banana", max_hints=2)
        hint_word_freq = game_banana.get_smart_hint(strategy="word_frequency")
        self.assertEqual(hint_word_freq, "a")
        self.assertEqual(game_banana.hints_used, 1)

        # 2. English letter frequency strategy: in 'rhythm', 't' appears highest in ETAOINSHRDLCUMWFGYPBVKJXQZ
        game_rhythm = HangmanGame(secret_word="rhythm", max_hints=2)
        hint_eng_freq = game_rhythm.get_smart_hint(strategy="english_frequency")
        self.assertEqual(hint_eng_freq, "t")

        # 3. Budget exhaustion
        game_exhaust = HangmanGame(secret_word="code", max_hints=1)
        self.assertIsNotNone(game_exhaust.get_smart_hint())
        self.assertIsNone(game_exhaust.get_smart_hint())

        # 4. Peek without consuming
        game_peek = HangmanGame(secret_word="sky", max_hints=1)
        peek_hint = game_peek.get_smart_hint(consume_budget=False)
        self.assertIsNotNone(peek_hint)
        self.assertEqual(game_peek.hints_used, 0)


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


class TestHangmanUtilitiesAndAccuracy(unittest.TestCase):
    """Tests utility helpers and guess accuracy metric calculations."""

    def test_safe_input_behavior(self):
        """Verify safe_input returns default value on EOFError and strips valid input."""
        from unittest.mock import patch
        from hangman import safe_input
        with patch("builtins.input", side_effect=EOFError):
            val = safe_input("Test: ", default="mock_default")
            self.assertEqual(val, "mock_default")
        with patch("builtins.input", return_value="  valid_input  "):
            val = safe_input("Test: ", default="mock_default")
            self.assertEqual(val, "valid_input")

    def test_guess_accuracy_calculation(self):
        """Verify accuracy percentage calculation based on correct and total guesses."""
        game = HangmanGame(secret_word="code")
        self.assertEqual(game.guess_accuracy, 0.0)

        game.process_guess("c")  # Correct (1/1 = 100%)
        self.assertEqual(game.guess_accuracy, 100.0)

        game.process_guess("z")  # Wrong (1/2 = 50%)
        self.assertEqual(game.guess_accuracy, 50.0)
        self.assertEqual(game.total_guesses, 2)
        self.assertEqual(game.correct_guesses_count, 1)


class TestGameTimer(unittest.TestCase):
    """Tests round duration timer behavior."""

    def test_timer_elapsed_and_stop(self):
        from hangman import GameTimer
        timer = GameTimer()
        self.assertGreaterEqual(timer.elapsed_seconds, 0.0)
        duration = timer.stop()
        self.assertEqual(duration, timer.elapsed_seconds)
        self.assertIsNotNone(timer.end_time)



class TestWordComplexity(unittest.TestCase):
    """Tests word complexity scoring algorithm and boundary rules."""

    def test_empty_and_whitespace_complexity(self):
        """Verify empty and whitespace strings return 0.0."""
        self.assertEqual(calculate_word_complexity(""), 0.0)
        self.assertEqual(calculate_word_complexity("   "), 0.0)

    def test_non_alphabetic_raises_value_error(self):
        """Verify non-alphabetic words raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_word_complexity("word123")
        with self.assertRaises(ValueError):
            calculate_word_complexity("hello-world")

    def test_complexity_monotonicity_and_bounds(self):
        """Verify score bounds and relative complexity ranking."""
        score_simple = calculate_word_complexity("cat")
        score_complex = calculate_word_complexity("cryptography")
        score_rare = calculate_word_complexity("quartz")

        self.assertGreaterEqual(score_simple, 1.0)
        self.assertLessEqual(score_complex, 10.0)
        self.assertGreater(score_complex, score_simple)
        self.assertGreater(score_rare, score_simple)

    def test_game_complexity_property(self):
        """Verify HangmanGame exposes complexity_score matching calculate_word_complexity."""
        game = HangmanGame(secret_word="cyber")
        self.assertEqual(game.complexity_score, calculate_word_complexity("cyber"))


class TestWinStreakTracker(unittest.TestCase):
    """Tests win streak, round telemetry, and aggregated session performance metrics."""

    def test_streak_progression_and_reset(self):
        """Verify current streak increments on win and resets to 0 on loss."""
        tracker = WinStreakTracker()
        self.assertEqual(tracker.current_streak, 0)
        self.assertEqual(tracker.highest_streak, 0)

        tracker.record_result(True)
        self.assertEqual(tracker.current_streak, 1)
        self.assertEqual(tracker.highest_streak, 1)

        tracker.record_result(True)
        self.assertEqual(tracker.current_streak, 2)
        self.assertEqual(tracker.highest_streak, 2)

        tracker.record_result(False)
        self.assertEqual(tracker.current_streak, 0)
        self.assertEqual(tracker.highest_streak, 2)
        self.assertEqual(tracker.win_rate, 66.67)

    def test_session_history_and_aggregate_metrics(self):
        """Verify per-round history logging, average accuracy, and total duration."""
        tracker = WinStreakTracker()
        tracker.record_result(True, word="python", duration=12.4, accuracy=80.0)
        tracker.record_result(False, word="kernel", duration=18.6, accuracy=40.0)

        self.assertEqual(len(tracker.history), 2)
        self.assertEqual(tracker.history[0]["word"], "python")
        self.assertEqual(tracker.total_duration, 31.0)
        self.assertEqual(tracker.average_accuracy, 60.0)

        summary = tracker.get_session_summary()
        self.assertEqual(summary["total_games"], 2)
        self.assertEqual(summary["total_wins"], 1)
        self.assertEqual(summary["average_accuracy"], 60.0)
        self.assertEqual(summary["total_duration"], 31.0)
        self.assertEqual(len(summary["rounds"]), 2)

    def test_export_and_load_session_history_json(self):
        """Verify exporting telemetry to JSON and restoring it into a new tracker instance."""
        import tempfile
        tracker = WinStreakTracker()
        tracker.record_result(True, word="binary", duration=8.5, accuracy=75.0)
        tracker.record_result(True, word="cipher", duration=14.0, accuracy=83.3)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "session_telemetry.json"
            exported_summary = tracker.export_session_history_json(file_path)
            self.assertTrue(file_path.exists())
            self.assertEqual(exported_summary["total_games"], 2)
            self.assertEqual(exported_summary["highest_streak"], 2)

            # Load into fresh tracker
            new_tracker = WinStreakTracker()
            count = new_tracker.load_session_history_json(file_path)
            self.assertEqual(count, 2)
            self.assertEqual(new_tracker.total_games, 2)
            self.assertEqual(new_tracker.total_wins, 2)
            self.assertEqual(new_tracker.current_streak, 2)
            self.assertEqual(new_tracker.highest_streak, 2)
            self.assertEqual(len(new_tracker.history), 2)
            self.assertEqual(new_tracker.history[0]["word"], "binary")

            # Missing file error check
            missing_path = Path(tmpdir) / "non_existent.json"
            with self.assertRaises(FileNotFoundError):
                new_tracker.load_session_history_json(missing_path)


class TestWordLinguisticMetrics(unittest.TestCase):
    """Tests linguistic metrics calculation on HangmanGame."""

    def test_vowel_and_consonant_counts(self):
        """Verify vowel and consonant count calculations."""
        game_standard = HangmanGame(secret_word="python")
        self.assertEqual(game_standard.vowel_count, 1)
        self.assertEqual(game_standard.consonant_count, 5)
        self.assertEqual(game_standard.vowel_ratio, 0.17)

        game_vowels = HangmanGame(secret_word="queue")
        self.assertEqual(game_vowels.vowel_count, 4)
        self.assertEqual(game_vowels.consonant_count, 1)
        self.assertEqual(game_vowels.vowel_ratio, 0.8)

        game_no_vowels = HangmanGame(secret_word="rhythm")
        self.assertEqual(game_no_vowels.vowel_count, 0)
        self.assertEqual(game_no_vowels.consonant_count, 6)
        self.assertEqual(game_no_vowels.vowel_ratio, 0.0)

    def test_custom_placeholder_masked_word(self):
        """Verify get_masked_word properly accepts and renders custom placeholders."""
        game = HangmanGame(secret_word="python")
        game.process_guess("p")
        game.process_guess("y")
        self.assertEqual(game.get_masked_word(), "p y _ _ _ _")
        self.assertEqual(game.get_masked_word(placeholder="*"), "p y * * * *")
        self.assertEqual(game.get_masked_word(placeholder="."), "p y . . . .")


    def test_letter_frequencies_and_most_frequent(self):
        """Verify calculation of letter occurrence frequencies and modal character."""
        game_banana = HangmanGame(secret_word="banana")
        freqs = game_banana.letter_frequencies
        self.assertEqual(freqs, {"b": 1, "a": 3, "n": 2})
        self.assertEqual(game_banana.most_frequent_letter, ("a", 3))

        game_unique = HangmanGame(secret_word="cyber")
        freqs_unique = game_unique.letter_frequencies
        self.assertEqual(len(freqs_unique), 5)
        for count in freqs_unique.values():
            self.assertEqual(count, 1)

    def test_syllable_count_estimation(self):
        """Verify syllable counting across short words, silent 'e', and phonetic groups."""
        self.assertEqual(estimate_syllable_count("cat"), 1)
        self.assertEqual(estimate_syllable_count("python"), 2)
        self.assertEqual(estimate_syllable_count("banana"), 3)
        self.assertEqual(estimate_syllable_count("code"), 1)  # Silent e
        self.assertEqual(estimate_syllable_count("apple"), 2) # Trailing 'le'

        # Edge cases
        self.assertEqual(estimate_syllable_count(""), 0)
        self.assertEqual(estimate_syllable_count("123"), 0)

        # HangmanGame property integration
        game = HangmanGame(secret_word="cyber")
        self.assertEqual(game.syllable_count, 2)



class TestPatternMatcher(unittest.TestCase):
    """Tests pattern matching solver utility for candidate dictionary search."""

    def setUp(self):
        self.sample_words = [
            "python", "patter", "person", "pardon",
            "action", "banana", "beacon", "crypto"
        ]

    def test_empty_pattern_returns_empty(self):
        """Verify empty pattern yields empty list."""
        self.assertEqual(find_pattern_matches("", self.sample_words), [])

    def test_pattern_matching_with_unknowns(self):
        """Verify pattern matching with underscores and dots."""
        matches = find_pattern_matches("p _ _ _ _ n", self.sample_words)
        self.assertIn("python", matches)
        self.assertIn("person", matches)
        self.assertIn("pardon", matches)
        self.assertNotIn("patter", matches)  # Ends in 'r', not 'n'

        matches_dot = find_pattern_matches("p.t...", self.sample_words)
        self.assertIn("python", matches_dot)
        self.assertNotIn("patter", matches_dot)  # 'patter' has second 't' which would be revealed

        matches_double_t = find_pattern_matches("p.tt..", self.sample_words)
        self.assertIn("patter", matches_double_t)

    def test_pattern_matching_with_excluded_letters(self):
        """Verify candidate words containing excluded letters are rejected."""
        # 'person' has 'e', 'pardon' has 'a'
        matches_no_e = find_pattern_matches(
            "p _ _ _ _ n",
            self.sample_words,
            excluded_letters={"e"}
        )
        self.assertIn("python", matches_no_e)
        self.assertIn("pardon", matches_no_e)
        self.assertNotIn("person", matches_no_e)

    def test_game_find_matching_candidates_integration(self):
        """Verify HangmanGame integration method dynamically filters based on current state."""
        game = HangmanGame(secret_word="python")
        game.process_guess("p")
        game.process_guess("z")  # Wrong guess -> added to excluded

        candidates = game.find_matching_candidates(self.sample_words)
        self.assertIn("python", candidates)
        self.assertNotIn("banana", candidates)


class TestAnagramAndScramble(unittest.TestCase):
    """Tests anagram discovery and word scramble generation utilities."""

    def test_find_anagram_candidates(self):
        """Verify anagram search identifies valid permutations excluding target word."""
        pool = ["listen", "enlist", "inlets", "banana", "silent", "tinsel"]
        anagrams = find_anagram_candidates("silent", pool)
        self.assertIn("listen", anagrams)
        self.assertIn("enlist", anagrams)
        self.assertIn("inlets", anagrams)
        self.assertIn("tinsel", anagrams)
        self.assertNotIn("silent", anagrams)
        self.assertNotIn("banana", anagrams)

    def test_find_anagram_invalid_inputs(self):
        """Verify non-alphabetic or empty inputs yield empty results."""
        self.assertEqual(find_anagram_candidates("", ["word"]), [])
        self.assertEqual(find_anagram_candidates("word123", ["word"]), [])

    def test_get_scrambled_word(self):
        """Verify scrambled word is a permutation of original characters."""
        game = HangmanGame(secret_word="python")
        scrambled = game.get_scrambled_word(seed=42)
        self.assertEqual(sorted(scrambled), sorted("python"))
        self.assertEqual(len(scrambled), len("python"))
        self.assertNotEqual(scrambled, "python")

        # Edge cases: 1 letter or homogeneous
        game_single = HangmanGame(secret_word="a")
        self.assertEqual(game_single.get_scrambled_word(), "a")

    def test_game_find_anagrams_integration(self):
        """Verify HangmanGame integration method calls anagram search."""
        game = HangmanGame(secret_word="east")
        pool = ["seat", "teas", "eats", "east", "west"]
        anagrams = game.find_anagrams(pool)
        self.assertEqual(sorted(anagrams), ["eats", "seat", "teas"])


class TestPhoneticMetricsAndVowelRatio(unittest.TestCase):
    """Tests vowel-consonant ratios, consonant clusters, and phonetic difficulty metrics."""

    def test_standard_word_metrics(self):
        """Verify metrics calculation for balanced English words."""
        metrics = calculate_vowel_consonant_metrics("python")
        self.assertEqual(metrics["word"], "python")
        self.assertEqual(metrics["length"], 6)
        self.assertEqual(metrics["vowel_count"], 1)  # 'o'
        self.assertEqual(metrics["consonant_count"], 5)
        self.assertAlmostEqual(metrics["vowel_ratio"], 0.17, places=2)
        self.assertGreaterEqual(metrics["max_consonant_cluster"], 2)

    def test_high_vowel_word(self):
        """Verify metric behavior for vowel-heavy words."""
        metrics = calculate_vowel_consonant_metrics("queue")
        self.assertEqual(metrics["vowel_count"], 4)
        self.assertEqual(metrics["consonant_count"], 1)
        self.assertAlmostEqual(metrics["vowel_ratio"], 0.8, places=2)
        self.assertEqual(metrics["max_consonant_cluster"], 1)
        self.assertEqual(metrics["phonetic_difficulty"], "Easy")

    def test_consonant_cluster_detection(self):
        """Verify longest consonant cluster identification in complex words."""
        metrics = calculate_vowel_consonant_metrics("rhythms")
        self.assertEqual(metrics["vowel_count"], 0)
        self.assertEqual(metrics["consonant_count"], 7)
        self.assertEqual(metrics["max_consonant_cluster"], 7)
        self.assertEqual(metrics["phonetic_difficulty"], "Challenging")

    def test_invalid_and_empty_inputs(self):
        """Verify safe defaults on empty or non-alphabetic inputs."""
        empty_metrics = calculate_vowel_consonant_metrics("")
        self.assertEqual(empty_metrics["length"], 0)
        self.assertEqual(empty_metrics["phonetic_difficulty"], "Unknown")

        invalid_metrics = calculate_vowel_consonant_metrics("12345!")
        self.assertEqual(invalid_metrics["length"], 0)
        self.assertEqual(invalid_metrics["phonetic_difficulty"], "Unknown")

    def test_hangman_game_property_bindings(self):
        """Verify HangmanGame exposes vowel ratio and consonant cluster properties."""
        game = HangmanGame(secret_word="strengths")
        self.assertIsInstance(game.phonetic_metrics, dict)
        self.assertEqual(game.phonetic_metrics["word"], "strengths")
        self.assertAlmostEqual(game.vowel_ratio, round(1 / 9, 2), places=2)
        self.assertEqual(game.consonant_cluster_max, 5)  # "ngths" is 5 consonants


class TestLetterFrequencyAndWordEntropy(unittest.TestCase):
    """Tests letter frequency counting and Shannon information entropy calculation."""

    def test_homogeneous_word_entropy_zero(self):
        """Verify repeated single-character words have exactly 0 entropy."""
        analysis = calculate_letter_frequency_analysis("aaaa")
        self.assertEqual(analysis["shannon_entropy"], 0.0)
        self.assertEqual(analysis["unique_count"], 1)
        self.assertEqual(analysis["most_common_letter"], ("a", 4))

    def test_diverse_word_entropy(self):
        """Verify distinct letter words have positive entropy."""
        analysis = calculate_letter_frequency_analysis("python")
        self.assertEqual(analysis["length"], 6)
        self.assertEqual(analysis["unique_count"], 6)
        self.assertAlmostEqual(analysis["shannon_entropy"], 2.58, places=2)

    def test_frequency_distribution(self):
        """Verify character counts match expected distribution."""
        analysis = calculate_letter_frequency_analysis("banana")
        self.assertEqual(analysis["frequencies"]["a"], 3)
        self.assertEqual(analysis["frequencies"]["n"], 2)
        self.assertEqual(analysis["frequencies"]["b"], 1)
        self.assertEqual(analysis["most_common_letter"], ("a", 3))

    def test_invalid_input(self):
        """Verify non-alphabetic or empty inputs yield empty defaults."""
        self.assertEqual(calculate_letter_frequency_analysis("")["shannon_entropy"], 0.0)
        self.assertEqual(calculate_letter_frequency_analysis("12345")["frequencies"], {})

    def test_hangman_game_entropy_property(self):
        """Verify HangmanGame integrates letter entropy and frequencies properties."""
        game = HangmanGame(secret_word="bubble")
        self.assertEqual(game.letter_frequencies["b"], 3)
        self.assertGreater(game.letter_entropy, 1.0)


class TestPatternSimilarity(unittest.TestCase):
    """Tests masked pattern similarity calculation against candidate words."""

    def test_full_match_similarity(self):
        """Verify completely revealed word returns 1.0 similarity."""
        sim = calculate_pattern_similarity("p y t h o n", "python")
        self.assertEqual(sim, 1.0)

    def test_partial_match_similarity(self):
        """Verify partially revealed word returns proportional similarity."""
        sim = calculate_pattern_similarity("p _ t _ o _", "python")
        self.assertEqual(sim, 0.5)  # 3 of 6 revealed and matching

    def test_mismatch_collision_returns_zero(self):
        """Verify character collision with pattern returns 0.0."""
        sim = calculate_pattern_similarity("p _ t _ o _", "action")
        self.assertEqual(sim, 0.0)

    def test_length_mismatch_returns_zero(self):
        """Verify differing string lengths return 0.0."""
        self.assertEqual(calculate_pattern_similarity("p _ t", "python"), 0.0)

    def test_game_integration_method(self):
        """Verify HangmanGame get_pattern_similarity reflects active guesses."""
        game = HangmanGame(secret_word="planet")
        game.process_guess("p")
        game.process_guess("l")
        self.assertAlmostEqual(game.get_pattern_similarity("planet"), round(2 / 6, 2))
        self.assertEqual(game.get_pattern_similarity("orange"), 0.0)


class TestWordSymmetryAndPalindrome(unittest.TestCase):
    """Tests palindrome detection and morphological symmetry analysis."""

    def test_palindrome_detection_true(self):
        """Verify palindromic words are correctly identified."""
        res = check_word_symmetry("racecar")
        self.assertTrue(res["is_palindrome"])
        self.assertEqual(res["symmetry_ratio"], 1.0)
        self.assertEqual(res["mirrored_pairs_count"], 3)

    def test_non_palindrome_detection(self):
        """Verify non-palindromic words return False."""
        res = check_word_symmetry("python")
        self.assertFalse(res["is_palindrome"])
        self.assertEqual(res["mirrored_pairs_count"], 0)
        self.assertEqual(res["symmetry_ratio"], 0.0)

    def test_invalid_and_empty_inputs(self):
        """Verify safe handling of empty or non-alphabetic strings."""
        self.assertFalse(check_word_symmetry("")["is_palindrome"])
        self.assertFalse(check_word_symmetry("12321")["is_palindrome"])

    def test_hangman_game_palindrome_properties(self):
        """Verify HangmanGame exposes is_palindrome and symmetry_metrics."""
        game_pal = HangmanGame(secret_word="kayak")
        self.assertTrue(game_pal.is_palindrome)
        self.assertEqual(game_pal.symmetry_metrics["mirrored_pairs_count"], 2)

        game_normal = HangmanGame(secret_word="guitar")
        self.assertFalse(game_normal.is_palindrome)


class TestEditDistanceAndFuzzyMatching(unittest.TestCase):
    """Tests Levenshtein edit distance and closest word candidate ranking."""

    def test_identical_words_distance_zero(self):
        """Verify distance between identical words is 0."""
        self.assertEqual(calculate_edit_distance("python", "python"), 0)

    def test_single_edit_operations(self):
        """Verify substitution, insertion, and deletion distances."""
        self.assertEqual(calculate_edit_distance("cat", "bat"), 1)  # substitution
        self.assertEqual(calculate_edit_distance("cat", "cats"), 1)  # insertion
        self.assertEqual(calculate_edit_distance("cats", "cat"), 1)  # deletion
        self.assertEqual(calculate_edit_distance("kitten", "sitting"), 3)

    def test_empty_string_distance(self):
        """Verify empty string distance equals length of other string."""
        self.assertEqual(calculate_edit_distance("", "python"), 6)
        self.assertEqual(calculate_edit_distance("python", ""), 6)

    def test_find_closest_dictionary_words(self):
        """Verify closest dictionary matching ranks and limits results."""
        pool = ["cat", "bat", "hat", "car", "dog", "elephant"]
        matches = find_closest_dictionary_words("cat", pool, max_distance=1, top_k=3)
        self.assertEqual(len(matches), 3)
        # Verify distance is 1 for all returned
        for word, dist in matches:
            self.assertEqual(dist, 1)

    def test_game_find_closest_matches_integration(self):
        """Verify HangmanGame integration method returns closest words."""
        game = HangmanGame(secret_word="play")
        pool = ["plan", "plat", "clay", "player", "work"]
        matches = game.find_closest_matches(pool, max_distance=1, top_k=3)
        self.assertGreaterEqual(len(matches), 1)
        self.assertIn("clay", [w for w, d in matches])


if __name__ == "__main__":
    unittest.main()

