# Task 2: Stock Portfolio Tracker

## Project Overview

The Stock Portfolio Tracker is a Python-based command-line application developed as part of the Dath(e)on Python Programming Internship. It allows users to record stock purchases, view their portfolio information, and review transaction history.

## Features

- Add stock purchase transactions
- Generate unique customer IDs
- Validate stock tickers using a company dataset
- Calculate total investment based on purchase price and quantity
- Retrieve recent stock market data using Yahoo Finance
- Calculate current portfolio value and profit or loss
- Store transaction details in CSV format
- View portfolio details and transaction history

## Technologies Used

- Python 3
- CSV module
- Random module
- OS module
- yfinance library

## Project Structure

```text
Task_2_Stock_Portfolio_Tracker/
├── portfolio.py
├── README.md
└── company_dataset.csv
```

## Requirements

- Python 3 installed
- Internet connection for retrieving market data
- The yfinance library

## Installation

Install the required library:

```bash
python -m pip install yfinance
```

## How to Run

1. Download or clone this repository.
2. Open the `Task_2_Stock_Portfolio_Tracker` folder in your terminal.
3. Ensure `company_dataset.csv` is present.
4. Run the application:

```bash
python portfolio.py
```

5. Select an option from the main menu to add a transaction, view a portfolio, view transaction history, or exit.

 

## Algorithm: Stock Portfolio Tracker

**Step 1:** Start the program.

**Step 2:** Import the required Python libraries, including `csv`, `yfinance`, `os`, and other necessary modules.

**Step 3:** Load the company dataset from `company_dataset.csv` and read the available stock symbols and company names.

**Step 4:** Load the stored customer IDs from `details.txt`.

**Step 5:** Display the main menu with options to manage the portfolio, view the portfolio, view transaction history, and exit the application.

**Step 6:** Accept the user's choice and perform the corresponding operation.

**Step 7: Manage Portfolio**
1. Generate a new customer ID or validate an existing customer ID.
2. Accept the stock ticker symbol from the user.
3. Validate the ticker symbol against the company dataset.
4. If the ticker is invalid, display an error message and request valid input.
5. Accept the stock purchase price and quantity.
6. Validate the entered values.
7. Calculate the total investment using:

   Total Investment = Purchase Price × Quantity

8. Retrieve the latest available stock closing price using the `yfinance` library.
9. Calculate the current market value:

   Current Value = Current Price × Quantity

10. Calculate profit or loss:

    Profit/Loss = Current Value − Total Investment

11. Save the portfolio information and relevant transaction details to the appropriate CSV files.

**Step 8: View Portfolio**
1. Read the saved portfolio records.
2. Display the stock ticker, purchase price, quantity, investment amount, current price, current value, and profit or loss.
3. If no portfolio records are available, display an appropriate message.

**Step 9: View Transaction History**
1. Read the stored transaction or portfolio history.
2. Display the available transaction details.
3. If no records are available, display an appropriate message.

**Step 10:** If the user selects the exit option, display a goodbye message and terminate the program.

**Step 11:** If the user enters an invalid menu choice, display an error message and return to the main menu.

**Step 12:** Stop the program.



## Data Storage

The application stores customer IDs in `details.txt` and transaction records in `portfolio_summary.csv`. These files are generated or updated during program execution.

Do not commit real customer IDs or personal financial records. Use sample data for demonstrations.

## Limitations

- Market data availability depends on Yahoo Finance and the internet connection.
- The retrieved closing price may not represent the live market price.
- Profit/loss calculations do not account for taxes, fees, or dividends.
- Portfolio consolidation across multiple purchases is not yet implemented.

## Learning Outcomes

This project demonstrates Python functions, loops, conditional statements, dictionaries, exception handling, CSV file operations, random ID generation, and the use of an external Python library.

## Disclaimer

This project is for educational purposes only and does not provide financial or investment advice.

## Output

![Portfolio Tracker Transaction History](track3.png)


