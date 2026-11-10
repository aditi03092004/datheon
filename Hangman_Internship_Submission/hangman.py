"""
Hangman Game - Interactive Terminal Application
Datheon Python Programming Internship - Task 1

An independent, object-oriented implementation of the classic Hangman word-guessing game.
"""

import json
import os
import random
import sys
from pathlib import Path
from enum import Enum
from typing import Optional


class GuessResult(Enum):
    """Enumeration representing the outcome of a player's guess."""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    ALREADY_GUESSED = "already_guessed"
    INVALID = "invalid"


import time

class GameTimer:
    """Tracks start time and duration for game rounds."""

    def __init__(self):
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None

    def stop(self) -> float:
        """Stop timer and return total elapsed seconds."""
        if self.end_time is None:
            self.end_time = time.time()
        return self.elapsed_seconds

    @property
    def elapsed_seconds(self) -> float:
        """Return elapsed time in seconds rounded to 1 decimal place."""
        current = self.end_time if self.end_time is not None else time.time()
        return round(max(0.0, current - self.start_time), 1)


class WinStreakTracker:
    """Tracks consecutive game wins, per-round history, and aggregate session metrics."""

    def __init__(self):
        self.current_streak: int = 0
        self.highest_streak: int = 0
        self.total_games: int = 0
        self.total_wins: int = 0
        self.history: list[dict] = []

    def record_result(
        self,
        won: bool,
        word: str = "",
        duration: float = 0.0,
        accuracy: float = 0.0
    ) -> None:
        """Record the outcome of a completed round with optional telemetry metrics."""
        self.total_games += 1
        if won:
            self.total_wins += 1
            self.current_streak += 1
            if self.current_streak > self.highest_streak:
                self.highest_streak = self.current_streak
        else:
            self.current_streak = 0

        self.history.append({
            "round": self.total_games,
            "won": won,
            "word": word.lower() if word else "",
            "duration": round(max(0.0, duration), 1),
            "accuracy": round(max(0.0, accuracy), 1)
        })

    @property
    def win_rate(self) -> float:
        """Calculate win percentage rounded to 2 decimal places."""
        if self.total_games == 0:
            return 0.0
        return round((self.total_wins / self.total_games) * 100, 2)

    @property
    def average_accuracy(self) -> float:
        """Calculate mean guess accuracy percentage across all recorded rounds."""
        if not self.history:
            return 0.0
        accuracies = [h["accuracy"] for h in self.history if h.get("accuracy", 0.0) > 0.0]
        if not accuracies:
            return 0.0
        return round(sum(accuracies) / len(accuracies), 1)

    @property
    def total_duration(self) -> float:
        """Calculate total play time in seconds across all recorded rounds."""
        return round(sum(h.get("duration", 0.0) for h in self.history), 1)

    def get_session_summary(self) -> dict:
        """Generate aggregated performance telemetry dictionary for the current session."""
        return {
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "win_rate": self.win_rate,
            "highest_streak": self.highest_streak,
            "current_streak": self.current_streak,
            "average_accuracy": self.average_accuracy,
            "total_duration": self.total_duration,
            "rounds": list(self.history)
        }

    def export_session_history_json(self, destination: Path) -> dict:
        """Export session history and aggregate telemetry to a JSON file."""
        dest = Path(destination)
        summary = self.get_session_summary()
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    def load_session_history_json(self, source: Path) -> int:
        """Load session history and aggregate telemetry from an existing JSON file."""
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(f"Telemetry file not found at: {src}")

        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.total_games = int(data.get("total_games", 0))
        self.total_wins = int(data.get("total_wins", 0))
        self.highest_streak = int(data.get("highest_streak", 0))
        self.current_streak = int(data.get("current_streak", 0))
        self.history = list(data.get("rounds", []))
        return len(self.history)


class GameState(Enum):
    """Enumeration representing the overall state of the game."""
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class Difficulty(Enum):
    """Enumeration representing game difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ALL = "all"


# Seven ASCII gallows stages corresponding to 0 through 6 incorrect attempts
HANGMAN_STAGES = [
    # Stage 0: 0 incorrect guesses
    """
       +---+
       |   |
           |
           |
           |
           |
    =========
    """,
    # Stage 1: 1 incorrect guess (Head)
    """
       +---+
       |   |
       O   |
           |
           |
           |
    =========
    """,
    # Stage 2: 2 incorrect guesses (Head + Torso)
    """
       +---+
       |   |
       O   |
       |   |
           |
           |
    =========
    """,
    # Stage 3: 3 incorrect guesses (Head + Torso + Left Arm)
    """
       +---+
       |   |
       O   |
      /|   |
           |
           |
    =========
    """,
    # Stage 4: 4 incorrect guesses (Head + Torso + Both Arms)
    """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
    =========
    """,
    # Stage 5: 5 incorrect guesses (Head + Torso + Arms + Left Leg)
    """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
    =========
    """,
    # Stage 6: 6 incorrect guesses (Full Hangman - Game Over)
    """
       +---+
       |   |
       O   |
      /|\\  |
      / \\  |
           |
    =========
    """
]


def load_words(file_path: Path) -> list[str]:
    """
    Load and sanitize word entries from the specified text file.

    Args:
        file_path (Path): Path to the dictionary text file.

    Returns:
        list[str]: Filtered list of non-empty lowercase words.

    Raises:
        FileNotFoundError: If the words file does not exist.
        ValueError: If the file exists but contains no valid words.
    """
    target = Path(file_path)
    if not target.exists():
        raise FileNotFoundError(f"Dictionary file not found at: {target.resolve()}")

    with open(target, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]

    # Keep only alphabetical words
    valid_words = [w for w in words if w.isalpha()]

    if not valid_words:
        raise ValueError(f"The dictionary file at '{target}' contains no valid words.")

    return valid_words


def filter_words_by_difficulty(words: list[str], difficulty: Difficulty = Difficulty.ALL) -> list[str]:
    """
    Filter a word pool according to the chosen difficulty level.

    Args:
        words (list[str]): Original candidate word list.
        difficulty (Difficulty): Target difficulty tier (EASY, MEDIUM, HARD, ALL).

    Returns:
        list[str]: Filtered list of words.
    """
    if difficulty == Difficulty.EASY:
        filtered = [w for w in words if len(w) <= 5]
    elif difficulty == Difficulty.MEDIUM:
        filtered = [w for w in words if 6 <= len(w) <= 8]
    elif difficulty == Difficulty.HARD:
        filtered = [w for w in words if len(w) >= 9]
    else:
        filtered = words

    return filtered if filtered else words


def calculate_word_complexity(word: str) -> float:
    """
    Calculate a normalized complexity score (1.0 to 10.0) for a candidate secret word
    based on character length, unique letter diversity, and rare letter distribution.
    """
    if not word or not word.strip():
        return 0.0

    cleaned = word.strip().lower()
    if not cleaned.isalpha():
        raise ValueError("Word must be alphabetic to compute complexity.")

    rare_letters = set("jqxzvkw")
    uncommon_letters = set("bcfgmpy")

    length_score = min(len(cleaned) * 0.4, 4.0)
    diversity_score = (len(set(cleaned)) / len(cleaned)) * 2.5

    rarity_sum = sum(
        2.0 if char in rare_letters else (1.0 if char in uncommon_letters else 0.2)
        for char in set(cleaned)
    )
    rarity_score = min(rarity_sum * 0.5, 3.5)

    raw_total = length_score + diversity_score + rarity_score
    return round(max(1.0, min(10.0, raw_total)), 1)


def find_pattern_matches(
    pattern: str,
    word_pool: list[str],
    excluded_letters: Optional[set[str]] = None
) -> list[str]:
    """
    Find candidate words from the dictionary that match a masked Hangman pattern.

    Args:
        pattern (str): Masked word pattern, where '_' or '.' represents unknown characters.
                       Spaces between characters are automatically stripped.
        word_pool (list[str]): List of candidate dictionary words.
        excluded_letters (Optional[set[str]]): Letters that are known not to be in the word.

    Returns:
        list[str]: Sorted list of candidate words matching the pattern.
    """
    cleaned_pat = pattern.replace(" ", "").lower()
    if not cleaned_pat:
        return []

    excluded = {c.lower() for c in (excluded_letters or set())}
    revealed_letters = {c for c in cleaned_pat if c.isalpha()}
    target_len = len(cleaned_pat)

    matches: list[str] = []
    for raw_word in word_pool:
        word = raw_word.strip().lower()
        if len(word) != target_len:
            continue
        if any(bad_char in word for bad_char in excluded):
            continue

        matched = True
        for p_char, w_char in zip(cleaned_pat, word):
            if p_char in ("_", "."):
                if w_char in revealed_letters:
                    matched = False
                    break
            elif p_char != w_char:
                matched = False
                break

        if matched:
            matches.append(word)

    return sorted(matches)


class HangmanGame:
    """
    Encapsulates core Hangman game logic, rules, and state management.
    Decoupled from input/output to allow thorough automated testing.
    """

    def __init__(self, secret_word: str, max_incorrect: int = 6, max_hints: int = 2):
        """
        Initialize a new Hangman game instance.

        Args:
            secret_word (str): The secret target word to be guessed.
            max_incorrect (int): Maximum allowable incorrect guesses (default: 6).
            max_hints (int): Maximum number of hints permitted per round (default: 2).
        """
        if not secret_word or not secret_word.isalpha():
            raise ValueError("Secret word must be a non-empty alphabetic string.")
        if max_hints < 0:
            raise ValueError("Maximum hints must be a non-negative integer.")

        self.secret_word = secret_word.lower()
        self.max_incorrect = max_incorrect
        self.max_hints = max_hints
        self.hints_used: int = 0
        self.guessed_letters: set[str] = set()
        self.incorrect_guesses: int = 0
        self.last_status_message: str = ""

    @property
    def remaining_hints(self) -> int:
        """Returns the number of hints remaining in this round."""
        return max(0, self.max_hints - self.hints_used)

    @property
    def remaining_attempts(self) -> int:
        """Returns the number of remaining incorrect guesses allowed."""
        return max(0, self.max_incorrect - self.incorrect_guesses)

    @property
    def complexity_score(self) -> float:
        """Returns the calculated complexity score (1.0 - 10.0) of the secret word."""
        return calculate_word_complexity(self.secret_word)

    def get_masked_word(self, placeholder: str = "_") -> str:
        """
        Generate the masked word string with spaces.
        Example: 'p y _ h _ n' for secret word 'python' with guesses {'p', 'y', 'h'}.
        Allows optional custom placeholder string (default: '_').
        """
        return " ".join([char if char in self.guessed_letters else placeholder for char in self.secret_word])

    def get_sorted_guessed_letters(self) -> list[str]:
        """Returns a sorted list of all unique letters guessed so far."""
        return sorted(list(self.guessed_letters))

    def get_current_art(self) -> str:
        """Returns the ASCII gallows art corresponding to the current incorrect guess count."""
        index = min(self.incorrect_guesses, len(HANGMAN_STAGES) - 1)
        return HANGMAN_STAGES[index]

    def validate_input(self, raw_input: str) -> tuple[bool, str]:
        """
        Validate whether the player's input is a single alphabetic character.

        Returns:
            tuple[bool, str]: (is_valid, sanitized_letter_or_error_reason)
        """
        cleaned = raw_input.strip().lower()
        if len(cleaned) != 1 or not cleaned.isalpha():
            return False, "Invalid input: Please enter a single alphabetical letter (A-Z)."
        return True, cleaned

    def process_guess(self, raw_input: str) -> tuple[GuessResult, str]:
        """
        Process a player's guess, updating state and remaining attempts.

        Returns:
            tuple[GuessResult, str]: Result enum and human-readable feedback message.
        """
        is_valid, validation_msg = self.validate_input(raw_input)
        if not is_valid:
            self.last_status_message = validation_msg
            return GuessResult.INVALID, validation_msg

        letter = validation_msg

        if letter in self.guessed_letters:
            msg = f"You already guessed '{letter.upper()}'. Try a different letter!"
            self.last_status_message = msg
            return GuessResult.ALREADY_GUESSED, msg

        self.guessed_letters.add(letter)

        if letter in self.secret_word:
            msg = f"Good job! '{letter.upper()}' is in the secret word."
            self.last_status_message = msg
            return GuessResult.CORRECT, msg
        else:
            self.incorrect_guesses += 1
            msg = f"Oops! '{letter.upper()}' is not in the word."
            self.last_status_message = msg
            return GuessResult.INCORRECT, msg

    def is_won(self) -> bool:
        """Check if all unique characters in the secret word have been guessed."""
        return set(self.secret_word).issubset(self.guessed_letters)

    def is_lost(self) -> bool:
        """Check if the maximum incorrect guesses limit has been reached."""
        return self.incorrect_guesses >= self.max_incorrect

    @property
    def total_guesses(self) -> int:
        """Total number of unique guesses made."""
        return len(self.guessed_letters)

    @property
    def correct_guesses_count(self) -> int:
        """Number of correct unique guesses made."""
        return len([c for c in self.guessed_letters if c in self.secret_word])

    @property
    def guess_accuracy(self) -> float:
        """Percentage of unique guesses that were correct."""
        if not self.guessed_letters:
            return 0.0
        return round((self.correct_guesses_count / len(self.guessed_letters)) * 100, 1)
    @property
    def vowel_count(self) -> int:
        """Total number of vowels (a, e, i, o, u) in the secret word."""
        return sum(1 for ch in self.secret_word if ch in "aeiou")

    @property
    def consonant_count(self) -> int:
        """Total number of consonants in the secret word."""
        return len(self.secret_word) - self.vowel_count

    @property
    def vowel_ratio(self) -> float:
        """Ratio of vowels to total letters in secret word rounded to 2 decimal places."""
        if not self.secret_word:
            return 0.0
        return round(self.vowel_count / len(self.secret_word), 2)
    @property
    def letter_frequencies(self) -> dict[str, int]:
        """Mapping of unique letters in the secret word to their occurrence frequencies."""
        freq: dict[str, int] = {}
        for ch in self.secret_word:
            freq[ch] = freq.get(ch, 0) + 1
        return freq

    @property
    def most_frequent_letter(self) -> tuple[str, int]:
        """Return the most frequent letter and its count in the secret word."""
        freqs = self.letter_frequencies
        if not freqs:
            return ("", 0)
        top_char = max(freqs, key=lambda k: (freqs[k], -ord(k)))
        return (top_char, freqs[top_char])



    def is_over(self) -> bool:
        """Check if the game has ended (either won or lost)."""
        return self.is_won() or self.is_lost()

    @property
    def state(self) -> GameState:
        """Returns the current GameState enum value."""
        if self.is_won():
            return GameState.WON
        elif self.is_lost():
            return GameState.LOST
        return GameState.IN_PROGRESS

    def get_hint(self, consume_budget: bool = True) -> Optional[str]:
        """
        Provide a hint by returning one unrevealed letter from the secret word.
        Consumes from the round's hint budget if consume_budget is True.
        Returns None if all letters have already been guessed or hint budget is exhausted.
        """
        if consume_budget and self.remaining_hints <= 0:
            return None

        unrevealed = sorted([ch for ch in set(self.secret_word) if ch not in self.guessed_letters])
        if not unrevealed:
            return None

        hint = random.choice(unrevealed)
        if consume_budget:
            self.hints_used += 1
        return hint

    ENGLISH_LETTER_FREQUENCY = "etaoinshrdlcumwfgypbvkjxqz"

    def get_smart_hint(
        self,
        strategy: str = "english_frequency",
        consume_budget: bool = True
    ) -> Optional[str]:
        """
        Provide a strategically weighted hint from unrevealed characters.

        Args:
            strategy (str): 'english_frequency' (default) favors letters statistically common in English;
                            'word_frequency' favors letters occurring most in the secret word.
            consume_budget (bool): Whether this request counts towards the round's hint allowance.

        Returns:
            Optional[str]: Suggested letter or None if unavailable/budget exhausted.
        """
        if consume_budget and self.remaining_hints <= 0:
            return None

        unrevealed = [ch for ch in set(self.secret_word) if ch not in self.guessed_letters]
        if not unrevealed:
            return None

        if strategy == "word_frequency":
            freqs = self.letter_frequencies
            unrevealed.sort(key=lambda c: (-freqs.get(c, 0), c))
            selected = unrevealed[0]
        else:
            order = {ch: i for i, ch in enumerate(self.ENGLISH_LETTER_FREQUENCY)}
            unrevealed.sort(key=lambda c: (order.get(c, 99), c))
            selected = unrevealed[0]

        if consume_budget:
            self.hints_used += 1

        return selected

    def find_matching_candidates(self, word_pool: list[str]) -> list[str]:
        """Find candidate words matching the game's current masked pattern and guessed letters."""
        pattern = self.get_masked_word().replace(" ", "")
        incorrect = {c for c in self.guessed_letters if c not in self.secret_word}
        return find_pattern_matches(pattern, word_pool, excluded_letters=incorrect)


class TerminalStyle:
    """ANSI styling codes for clean terminal visual feedback."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"

    @classmethod
    def style(cls, text: str, style_code: str) -> str:
        """Wrap text in ANSI formatting."""
        return f"{style_code}{text}{cls.RESET}"


def safe_input(prompt_text: str, default: str = "") -> str:
    """Safely prompt for terminal input with graceful exception fallback."""
    try:
        return input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        return default


def clear_screen() -> None:
    """Clear terminal screen in a cross-platform manner."""
    os.system("cls" if os.name == "nt" else "clear")


def render_display(game: HangmanGame, feedback_message: str = "") -> None:
    """
    Render the game status board to the terminal.
    """
    print("=" * 48)
    print("        DATHEON INTERNSHIP - HANGMAN GAME       ")
    print("=" * 48)
    print(game.get_current_art())
    print(f" Secret Word:     {game.get_masked_word()}")
    print(f" Guessed Letters: {', '.join(game.get_sorted_guessed_letters()).upper() or 'None'}")
    print(f" Attempts Left:   {game.remaining_attempts} of {game.max_incorrect}")
    print("-" * 48)

    if feedback_message:
        print(f" Status: {feedback_message}")
        print("-" * 48)


def play_session(word_list: list[str], clear_console: bool = True) -> bool:
    """
    Execute a single complete round of Hangman.

    Args:
        word_list (list[str]): Pool of candidate words.
        clear_console (bool): Whether to clear terminal screen between turns.

    Returns:
        bool: True if player won, False if lost.
    """
    secret_word = random.choice(word_list)
    game = HangmanGame(secret_word=secret_word)
    timer = GameTimer()
    current_feedback = "Welcome! Guess the hidden word one letter at a time."

    while not game.is_over():
        if clear_console:
            clear_screen()
        render_display(game, current_feedback)

        try:
            user_input = input("Enter your letter guess: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGame session ended by user.")
            return False

        _, current_feedback = game.process_guess(user_input)

    # Final board display after game completion
    if clear_console:
        clear_screen()
    render_display(game)

    if game.is_won():
        print("\n************************************************")
        print("  CONGRATULATIONS! YOU SUCCESSFULLY GUESSED IT! ")
        print(f"  The word was: {game.secret_word.upper()}")
        timer.stop()
        print(f"  Round Time: {timer.elapsed_seconds}s | Accuracy: {game.guess_accuracy}% ({game.correct_guesses_count}/{game.total_guesses} correct)")
        print("************************************************\n")
        return True
    else:
        print("\n================================================")
        print("  GAME OVER! YOU HAVE RUN OUT OF ATTEMPTS.      ")
        print(f"  The secret word was: {game.secret_word.upper()}")
        print("================================================\n")
        return False


def main() -> None:
    """Main program entry point coordinating word loading and replay loops."""
    base_dir = Path(__file__).resolve().parent
    words_file = base_dir / "english_words.txt"

    print("Loading word dictionary...")
    try:
        word_pool = load_words(words_file)
    except Exception as exc:
        print(f"Error loading words: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully loaded {len(word_pool)} words. Starting game...\n")

    tracker = WinStreakTracker()

    while True:
        won = play_session(word_pool, clear_console=True)

        tracker.record_result(won)
        print(f"Current Score: {tracker.total_wins} Wins / {tracker.total_games} Games (Win Rate: {tracker.win_rate}% | Streak: {tracker.current_streak} | Best: {tracker.highest_streak})")
        try:
            replay = input("\nWould you like to play another round? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Thank you for playing Datheon Hangman!")
            break

        if replay not in ("y", "yes"):
            print("\nThank you for playing Datheon Hangman! Goodbye.\n")
            break


if __name__ == "__main__":
    main()

