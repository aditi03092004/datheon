# Datheon Python Programming Internship – Task 1: Hangman Game

**Candidate Implementation & Submission**  
**Track:** Python Programming  
**Author:** Aditi Hundre  

---

## 1. Project Overview

This project is an independent, object-oriented implementation of the classic **Hangman Word-Guessing Game** developed for the **Datheon Python Programming Internship (Task 1)**.

The application allows a user to guess a hidden English word one letter at a time within a limited number of attempts (6 maximum incorrect guesses). Each turn provides visual feedback through dynamic ASCII gallows art, tracks previously guessed letters, validates player input, tracks guess accuracy, scores word complexity, and supports replay across multiple sessions with comprehensive telemetry tracking.

---

## 2. Architecture & File Structure

```text
Hangman_Internship_Submission/
│
├── hangman.py             # Main application: game engine, rendering, and interactive CLI
├── test_hangman.py        # Automated test suite (Python unittest standard library - 79 tests)
├── english_words.txt      # Curated dictionary of 2,400+ clean, diverse English words
└── README.md              # Project documentation, execution, and evaluation guide
```

### Architectural Highlights

- **Decoupled Architecture:** Core game rules and state are encapsulated inside the `HangmanGame` class, completely separated from terminal I/O. This ensures 100% testability.
- **Dynamic Word Complexity Scoring:** Algorithmic complexity score (1.0 to 10.0) calculated from length, character diversity, and rare-letter distributions.
- **Configurable Hint Budget:** Controlled hints system enforcing a per-round hint allowance to preserve game balance.
- **Telemetry & History Tracking:** `WinStreakTracker` records per-round telemetry (word, duration, accuracy, outcome) and calculates aggregate metrics (average accuracy, total play duration).
- **Pure Standard Library:** Implemented strictly using standard Python modules (`random`, `time`, `os`, `sys`, `pathlib`, `enum`, `unittest`). No third-party packages or `pip install` required.

---

## 3. Core Features & Compliance
- **Levenshtein Edit Distance & Fuzzy Matching:** `calculate_edit_distance` and `find_closest_dictionary_words` rank nearest dictionary words.
- **Morphological Affix Decomposition:** `analyze_word_affixes` extracts recognized prefixes, suffixes, and underlying root stems.
- **Phonetic Harshness Scoring:** `calculate_phonetic_harshness_index` quantifies plosive friction vs. melodic liquid balance.
- **Letter Frequency & Shannon Entropy:** `calculate_letter_frequency_analysis` quantifies letter distribution and information entropy in bits.
- **Masked Pattern Similarity Scoring:** `calculate_pattern_similarity` computes compatibility alignment between masked patterns and candidates.
- **Morphological Symmetry & Palindromes:** `check_word_symmetry` detects mirrored character pairs and palindrome properties.
- **Phonetic Metrics & Vowel-Consonant Ratio:** `calculate_vowel_consonant_metrics` analyzes vowel balance, longest consonant clusters, and phonetic difficulty.
- **Word Complexity Scorer:** `calculate_word_complexity` grades secret words on a 1.0 to 10.0 scale.
- **Word Pattern Candidate Matcher:** `find_pattern_matches` inspects current masked words with wildcards and excludes bad letters to identify valid dictionary candidates.
- **Smart Hint Strategy:** `get_smart_hint` suggests letters using English frequency or word frequency ranking.
- **Telemetry JSON Persistence:** `export_session_history_json` and `load_session_history_json` save and restore player round records.
- **Hint Budgeting:** Configurable `max_hints` allowance per round with non-consuming peek capabilities.
- **Session Telemetry:** Tracks per-round duration, guess accuracy ratio, win streak progression, and lifetime win percentage.
- **Round Timer:** Dynamic `GameTimer` recording turn pacing and round duration in seconds.
- **Guess Accuracy Metrics:** Real-time computation of player precision ratio: `(Correct Guesses / Total Guesses) * 100%`.

| Requirement | Implementation Detail |
| :--- | :--- |
| **Random Word Selection** | Randomly selects a word from `english_words.txt` using `random.choice()`. |
| **Attempt Limit** | Strictly permits a maximum of 6 incorrect guesses before game over. |
| **7 ASCII Gallows Stages** | 7 visual art stages (0 mistakes = empty gallows, up to 6 mistakes = full hangman). |
| **Masked Word Representation** | Displays revealed letters and masks hidden letters with underscores (`_`). |
| **Guessed Letter Tracking** | Displays a sorted list of all unique letters guessed during the round. |
| **Duplicate Guess Prevention** | Re-guessing a letter alerts the player and does not deduct an attempt. |
| **Robust Input Validation** | Disallows digits, special characters, empty inputs, or multi-letter strings without penalty. |
| **Win/Loss Detection** | Immediately detects when all letters are revealed (win) or 6 mistakes occur (loss). |
| **Terminal Clearing** | Cross-platform terminal screen refresh (`cls` on Windows, `clear` on Unix). |
| **Difficulty Tiers** | Modular `Difficulty` enum filtering words by length (`EASY` $\le 5$, `MEDIUM` 6-8, `HARD` $\ge 9$). |

---

## 4. How to Run on Windows

### Running via PowerShell

1. Open **PowerShell**.
2. Navigate to this submission directory:
   ```powershell
   cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Hangman_Internship_Submission"
   ```
3. Run the application:
   ```powershell
   python hangman.py
   ```

---

## 5. How to Run the Automated Test Suite

The project includes 46 automated unit tests covering word loading, complexity scoring, hint budgeting, validation, state management, duplicates, scoring, and termination.

To run the automated tests:

```powershell
cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Hangman_Internship_Submission"
python -m unittest test_hangman.py -v
```

### Linguistic & Vowel Density Metrics
The `HangmanGame` engine computes real-time linguistic structure metrics for every target word:
- **`vowel_count`**: Total count of vowels (`a, e, i, o, u`) in the secret target word.
- **`consonant_count`**: Total count of consonant letters.
- **`vowel_ratio`**: Ratio of vowel density (vowels / total length), aiding phonetic difficulty profiling.

### Letter Frequency Profiling & Display Formatting
- **`letter_frequencies`**: Returns an exact frequency dictionary of every character in the target word.
- **`most_frequent_letter`**: Automatically identifies the modal character and its occurrence count.
- **`get_masked_word(placeholder='_')`**: Generates a spaced string with configurable masking symbols (`*`, `.`, `-`).
