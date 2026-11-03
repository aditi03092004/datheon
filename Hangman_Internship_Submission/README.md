# Datheon Python Programming Internship – Task 1: Hangman Game

**Candidate Implementation & Submission**  
**Track:** Python Programming  
**Author:** Aditi Hundre  

---

## 1. Project Overview

This project is an independent, object-oriented implementation of the classic **Hangman Word-Guessing Game** developed for the **Datheon Python Programming Internship (Task 1)**.

The application allows a user to guess a hidden English word one letter at a time within a limited number of attempts (6 maximum incorrect guesses). Each turn provides visual feedback through dynamic ASCII gallows art, tracks previously guessed letters, validates player input, and supports replay across multiple sessions with score tracking.

---

## 2. Architecture & File Structure

```text
Hangman_Internship_Submission/
│
├── hangman.py             # Main application: game engine, rendering, and interactive CLI
├── test_hangman.py        # Automated test suite (Python unittest standard library)
├── english_words.txt      # Curated dictionary of 1,200+ clean, diverse English words
└── README.md              # Project documentation, execution, and evaluation guide
```

### Architectural Highlights

- **Decoupled Architecture:** Core game rules and state are encapsulated inside the `HangmanGame` class, completely separated from terminal I/O. This ensures 100% testability.
- **Robust Path Resolution:** Uses `pathlib.Path(__file__).resolve().parent` to locate `english_words.txt`, guaranteeing the script runs seamlessly regardless of the active working directory.
- **Pure Standard Library:** Implemented using standard Python modules (`random`, `os`, `sys`, `pathlib`, `enum`, `unittest`). No third-party packages or `pip install` required.
- **Replay & Scoring:** Supports consecutive rounds with score tracking (wins vs total games played) and clean exit handling.

---

## 3. Core Features & Compliance
- **Win Streak Tracking:** Records consecutive victorious rounds, personal best streak, and lifetime win percentage.

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
| **Replay & Score Loop** | Prompts players to play again (`y/n`) while keeping running win totals. |
| **Difficulty Tiers** | Modular `Difficulty` enum filtering words by length (`EASY` $\le 5$, `MEDIUM` 6-8, `HARD` $\ge 9$). |

---

## 4. How to Run on Windows

### Prerequisites
- Python 3.6 or newer installed (verified on Python 3.14.6).

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

### Running via Command Prompt (CMD)

1. Open **Command Prompt**.
2. Navigate to this submission directory:
   ```cmd
   cd /d "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Hangman_Internship_Submission"
   ```
3. Run the application:
   ```cmd
   python hangman.py
   ```

*(Note: If your system uses the Python Launcher, `py hangman.py` is also fully supported.)*

---

## 5. How to Run the Automated Test Suite

The project includes unit tests covering dictionary loading, validation, state management, duplicates, scoring, and termination.

To run the automated tests:

```powershell
cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Hangman_Internship_Submission"
python -m unittest test_hangman.py -v
```

Expected output: All test cases pass with status `OK`.

---

## 6. Demonstration Guide for Internship Evaluators

Follow this step-by-step sequence during an evaluation or interview to demonstrate all capabilities:

1. **Demonstrate Automated Testing:**
   - Execute `python -m unittest test_hangman.py -v` to show that all edge cases and unit tests pass.
2. **Launch the Game:**
   - Run `python hangman.py`.
   - Point out the clean UI banner, 0-mistake empty gallows, attempts remaining (6 of 6), and masked secret word.
3. **Demonstrate Input Validation (No Penalty):**
   - Type `12` or `@` and press Enter.
   - Show that the system flags it as invalid and does **not** deduct an attempt.
4. **Demonstrate Duplicate Prevention (No Penalty):**
   - Enter a valid letter (e.g., `e`).
   - Enter `e` again on the next turn.
   - Show the advisory notice that `E` was already guessed, with remaining attempts unchanged.
5. **Demonstrate Gallows Progression:**
   - Enter several incorrect letters (e.g., `z`, `q`, `x`).
   - Observe the ASCII figure building up: head -> torso -> arms -> legs.
6. **Demonstrate Game Completion:**
   - Win by guessing the final letters, or reach 6 mistakes to trigger the Game Over screen revealing the secret word.
7. **Demonstrate Replay Functionality:**
   - When asked `Would you like to play another round? (y/n):`, enter `y`.
   - Observe that a new word is chosen and the score counter tracks your session.
   - On the next round, enter `n` to exit gracefully.

