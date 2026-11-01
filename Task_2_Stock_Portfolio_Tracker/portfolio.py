import csv
import random
import yfinance as yf
import os
import warnings
import logging


warnings.filterwarnings("ignore")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_line():
    print("=" * 48)


def show_banner():
    print_line()
    print("       STOCK PORTFOLIO TRACKER")
    print("       Investment Management")
    print_line()


def main_menu():
    print("\nMAIN MENU")
    print("-" * 30)
    print("1. Add stock transaction")
    print("2. View my portfolio")
    print("3. View transaction history")
    print("4. Exit")
    print("-" * 30)

    while True:
        choice = input("Enter your choice (1-4): ").strip()

        if choice in ("1", "2", "3", "4"):
            return choice

        print("Invalid choice. Please enter a number from 1 to 4.")


with open("details.txt", "r") as myfile:
    read_id = myfile.read().splitlines()

def unique_id_maker():
    characters=list("qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM")
    while True: #to fix duplicate value condition
        id="STOCK_2026"
        for i in range(6):
            id+=random.choice(characters)
        if id not in read_id:
            read_id.append(id)
            return id
        

##with open("portfolio_summary.csv","w",newline="") as writer_file:
               ##writer=csv.writer(writer_file)
                ##writer.writerow(["Customer_id","Buy_price","Quantity","Investment"])

def portfolio():
    company = {}

    with open("company_dataset.csv", "r", newline="") as fh:
        reader = csv.DictReader(fh)

        for row in reader:
            ticker = row["Symbol"].upper().strip()
            company_name = row["Security"].strip()

            if ticker:
                company[ticker] = company_name

    dict_length = len(company)

    print("Stock Portfolio Tracker")
    print("-----------------------")
    print("Available companies:", dict_length)

    portfolio = {}
    details = []

    # PROGRAM PHASE LOGIC
    c = 'y'

    while c == 'y':
        ticker = input("Enter a stock ticker: ").strip().upper()

        if ticker not in company:
            print("Invalid ticker. Please choose a ticker from the dataset.")

        else:
            print("Selected company:", company[ticker])

            n = input("Do you have a unique ID (y/n): ").strip().lower()

            if n == 'y':
                customer_id = input("Enter your unique ID: ").strip()

                if customer_id not in read_id:
                    print("Invalid ID")
                    c = input(
                        "Do you wanna add more company share details (y/n): "
                    ).strip().lower()
                    continue

            else:
                customer_id = unique_id_maker()
                print("Your customer ID:", customer_id)
                details.append(customer_id)

                # Save the new ID immediately
                with open("details.txt", "a") as myfile:
                    myfile.write(customer_id + "\n")

            # Validate purchase inputs
            try:
                buy_price = float(
                    input("Enter purchase price per share: ")
                )
                quantity = int(
                    input("Enter number of shares: ")
                )

                if buy_price <= 0 or quantity <= 0:
                    print("Price and quantity must be positive.")

                else:
                    total_investment = buy_price * quantity

                    # Keep each ticker's latest position in this session
                    portfolio[ticker] = {
                        "customer_id": customer_id,
                        "buy_price": buy_price,
                        "quantity": quantity,
                        "Investment": total_investment
                    }

                    print("\nPortfolio position:")
                    print(portfolio)

                    # Fetch market data
                    try:
                        sstock = yf.Ticker(ticker)
                        history = sstock.history(period="5d")

                        if history.empty:
                            print("Market price unavailable")
                            current_price = ""
                            current_value = ""
                            profit_loss = ""

                        else:
                            current_price = float(
                                history["Close"].iloc[-1]
                            )
                            current_value = current_price * quantity
                            profit_loss = (
                                current_value - total_investment
                            )

                            portfolio[ticker]["current_price"] = current_price
                            portfolio[ticker]["current_value"] = current_value
                            portfolio[ticker]["profit_loss"] = profit_loss

                            print("Purchase investment:", total_investment)
                            print(
                                "Latest closing price:",
                                round(current_price, 2)
                            )
                            print(
                                "Current portfolio value:",
                                round(current_value, 2)
                            )
                            print("Profit/Loss:", round(profit_loss, 2))

                    except Exception as e:
                        print("Unable to fetch market data:", e)
                        current_price = ""
                        current_value = ""
                        profit_loss = ""

                    # Save only the current purchase to avoid
                    # writing earlier portfolio entries again
                    file_exists = os.path.exists("portfolio_summary.csv")
                    file_is_empty = (
                        not file_exists
                        or os.path.getsize("portfolio_summary.csv") == 0
                    )

                    with open(
                        "portfolio_summary.csv", "a", newline=""
                    ) as writer_file:
                        writer = csv.writer(writer_file)

                        if file_is_empty:
                            writer.writerow([
                                "Customer_id", "Ticker", "Buy_price",
                                "Quantity", "Investment", "Current_price",
                                "Current_value", "Profit_Loss"
                            ])

                        writer.writerow([
                            customer_id,
                            ticker,
                            buy_price,
                            quantity,
                            total_investment,
                            current_price,
                            current_value,
                            profit_loss
                        ])

            except ValueError:
                print(
                    "Invalid input. Enter a valid price and whole-number quantity."
                )

        c = input(
            "Do you wanna add more company share details (y/n): "
        ).strip().lower()



def show_portfolio():
    customer_id = input("Enter your customer ID: ").strip()

    with open("portfolio_summary.csv", "r", newline="") as file:
        reader = csv.DictReader(file)
        found = False

        for row in reader:
            if row["Customer_id"] == customer_id:
                found = True
                print("\nTicker:", row["Ticker"])
                print("Buy Price:", row["Buy_price"])
                print("Quantity:", row["Quantity"])
                print("Investment:", row["Investment"])
                print("Current Price:", row["current_price"])
                print("Current Value:", row["current_value"])
                print("Profit/Loss:", row["profit/loss"])
                print("-----------------------")

        if not found:
            print("No portfolio records found for this ID.")


def main():
    while True:
        clear_screen()
        show_banner()
        choice = main_menu()

        if choice == "1":
            portfolio()

        elif choice == "2":
            show_portfolio()

        elif choice == "3":
            print("\nTransaction History")
            print("-" * 30)

            if os.path.exists("portfolio_summary.csv"):
                with open("portfolio_summary.csv", "r", newline="") as file:
                    reader = csv.DictReader(file)
                    found = False

                    for row in reader:
                        found = True
                        print("\nTicker:", row["Ticker"])
                        print("Buy Price:", row["Buy_price"])
                        print("Quantity:", row["Quantity"])
                        print("Investment:", row["Investment"])
                        print("Current_price:", row["current_price"])
                        print("Current Value:", row["current_value"])
                        print("Profit/Loss:", row["profit/loss"])
                        print("-" * 30)

                if not found:
                    print("No transaction history available.")

            else:
                print("No transaction history available.")

        elif choice == "4":
            print("\nThank you for using Stock Portfolio Tracker!")
            print("Goodbye!")
            break

        else:
            print("\nInvalid choice. Please select 1, 2, 3, or 4.")

        input("\nPress Enter to return to the main menu...")


main()



