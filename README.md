# Datheon Python Programming Internship

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Tests Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Internship](https://img.shields.io/badge/Internship-Datheon-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

Welcome to my repository for the **Datheon Python Programming Internship**!

This repository documents my learning journey and the Python programming projects I develop as part of the internship. The main goal is to strengthen my programming fundamentals, improve problem-solving skills, and gain practical experience by building functional applications.

## About the Internship

Through this internship, I am working on practical Python tasks that help me apply programming concepts to real-world-style problems. Each project gives me an opportunity to practise writing code, debugging errors, organising programs, and improving my understanding of Python.

As a B.Tech Computer Science and Engineering student specialising in Cybersecurity, I believe that strong programming fundamentals are an important foundation for developing future cybersecurity solutions.

### Quick Start (Unified Launcher)

You can launch either project or run the complete automated test suite (30 passing tests) directly from the repository root using the unified launcher:

```bash
python run_project.py
```

---

## Projects

### Task 1: Hangman Game
A terminal-based word-guessing game developed using Python featuring an object-oriented game engine, 7 ASCII gallows stages, duplicate prevention, and automated unit testing.

**Concepts practised:**
- Object-oriented programming & decoupled game logic
- Random word selection from curated dictionary
- Loops, conditional statements, and input validation
- Tracking guessed letters and remaining attempts
- Automated testing with Python standard `unittest`

- 🌟 **[View Task 1 – Hangman Game](./Hangman_Internship_Submission/)**

### Task 2: Stock Portfolio Tracker
A menu-driven Python application designed to record stock transactions, validate tickers against the S&P 500 dataset, track real-time position values, calculate profit/loss, and format customer portfolios into clean ASCII tables.

**Concepts practised:**
- Object-oriented programming & modular service architecture
- S&P 500 dataset parsing and ticker validation
- Resilient market pricing engine with standard library fallback
- Unique customer ID generation and persistent file management
- Consolidated portfolio financial metrics (Total Invested, Value, P/L, Return %)
- Automated testing with Python standard `unittest`

- 🌟 **[View Task 2 – Stock Portfolio Tracker](./Stock_Portfolio_Submission/)**

## Architecture Overview

```mermaid
graph TD
    Launcher[run_project.py CLI Launcher] --> Task1[Task 1: Hangman Game]
    Launcher --> Task2[Task 2: Stock Portfolio Tracker]
    Launcher --> Tests[Automated Test Suite]

    subgraph Task 1 Engine
        Task1 --> HangmanGame[HangmanGame State Machine]
        Task1 --> WordBank[english_words.txt Dictionary]
        Task1 --> Streak[WinStreakTracker]
        Task1 --> Art[7 ASCII Gallows Stages]
    end

    subgraph Task 2 Engine
        Task2 --> Manager[StockPortfolioManager]
        Task2 --> Dataset[company_dataset.csv 503 Companies]
        Task2 --> Market[MarketDataService Live/Offline Fallback]
        Task2 --> Ledger[portfolio_summary.csv Ledger]
        Task2 --> Registry[details.txt Customer Registry]
    end
```

## Skills I'm Developing

- Python programming fundamentals
- Logical thinking and problem-solving
- Debugging and error handling
- File handling and data organisation
- Writing structured, readable code
- Using GitHub to document and showcase projects

## Tools and Technologies

- **Language:** Python
- **Version Control and Project Hosting:** GitHub
- **Development Environment:** Visual Studio Code and terminal

## Learning Approach

I believe that practical implementation is an essential part of learning programming. Through these projects, I aim to move beyond understanding concepts theoretically and become more confident in applying them independently.

I am documenting my progress, learning from mistakes, and improving my code one project at a time.

## Acknowledgement

I sincerely thank **Datheon** for providing this internship opportunity and encouraging me to strengthen my Python programming skills through practical tasks.

### Project Metrics & Verification Summary

| Component | Task 1: Hangman Game | Task 2: Stock Portfolio Tracker |
| :--- | :--- | :--- |
| **Architecture** | Object-Oriented State Engine | Modular Financial & Market Service |
| **Data Source** | 2,492 Curated English Words | 503 S&P 500 Companies Dataset |
| **Test Framework** | Python Standard `unittest` | Python Standard `unittest` |
| **Passing Tests** | 22 Passing Unit Tests | 11 Passing Unit Tests |
| **Key Features** | 7 Gallows Stages, Win Streaks, Hints | Live/Offline Fallback, Sector Breakdown |
| **Offline Ready** | 100% Standard Library | 100% Standard Library Fallback |

## Connect With Me

I'm a B.Tech CSE Cybersecurity student interested in Python programming, cybersecurity, and continuous learning.

Thank you for visiting my repository!

**Progress over perfection. Projects over theory.**


