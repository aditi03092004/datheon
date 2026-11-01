
import random
import os

# Read words from the text file
with open("words.txt", "r") as myfile:
    words = myfile.read().splitlines()

# Remove empty lines from the word list
words = [word.strip().lower() for word in words if word.strip()]

if not words:
    raise ValueError("The words.txt file contains no words.")

secret_word = random.choice(words)

hangman_art = [
    """
       +---+
       |   |
           |
           |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
           |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
       |   |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|   |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
    =========
    """,
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


# Display the game screen
def display_game(secret_word, guessed_letters, wrong_guesses):
    os.system('cls' if os.name == 'nt' else 'clear')

    print(hangman_art[wrong_guesses])

    display_word = ""

    for letter in secret_word:
        if letter in guessed_letters:
            display_word += letter
        else:
            display_word += "_"

    print("Word:", " ".join(display_word))
    print("Guessed letters:", sorted(guessed_letters))
    print("Attempts left:", 6 - wrong_guesses)


# Main game logic
def game():
    guessed_letters = []
    wrong_guesses = 0
    max_attempts = 6

    while wrong_guesses < max_attempts:
        display_game(secret_word, guessed_letters, wrong_guesses)

        guess = input("Enter a letter: ").lower().strip()

        # Validate the input
        if len(guess) != 1 or not guess.isalpha():
            print("Enter a single letter!")
            input("Press Enter to continue...")
            continue

        # Prevent duplicate guesses
        if guess in guessed_letters:
            print("You already guessed that letter!")
            input("Press Enter to continue...")
            continue

        guessed_letters.append(guess)

        # Check whether the guess is correct
        if guess in secret_word:
            print("Correct guess!")
        else:
            print("Wrong guess!")
            wrong_guesses += 1

        # Check whether all letters have been guessed
        won = True

        for letter in secret_word:
            if letter not in guessed_letters:
                won = False
                break

        # Handle winning
        if won:
            display_game(secret_word, guessed_letters, wrong_guesses)
            print("Congratulations! You won!")
            return

        # Handle losing immediately after the sixth wrong guess
        if wrong_guesses == max_attempts:
            display_game(secret_word, guessed_letters, wrong_guesses)
            print("Game over! You lost.")
            print("The correct word was:", secret_word)
            return

        input("Press Enter to continue...")


game()
