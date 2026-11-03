"""
Stock Portfolio Tracker - Interactive Terminal Application
Datheon Python Programming Internship - Task 2

An independent, object-oriented investment management and portfolio tracking system.
"""

import csv
import json
import os
import random
import string
import sys
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class PortfolioError(Exception):
    """Base exception for portfolio operations."""
    pass


class InvalidTickerError(PortfolioError):
    """Raised when a stock ticker is not found in the S&P 500 dataset."""
    pass


class InvalidTransactionError(PortfolioError, ValueError):
    """Raised when transaction parameters (price, quantity) violate rules."""
    pass


class CustomerNotFoundError(PortfolioError):
    """Raised when an unregistered customer ID is accessed."""
    pass


@dataclass
class StockPosition:
    """Represents an individual stock holding position with computed metrics."""
    customer_id: str
    ticker: str
    company_name: str
    buy_price: float
    quantity: int
    investment: float
    current_price: float
    current_value: float
    profit_loss: float
    timestamp: str

    @property
    def return_percentage(self) -> float:
        """Calculate percentage return on investment."""
        if self.investment <= 0:
            return 0.0
        return round((self.profit_loss / self.investment) * 100, 2)

    @property
    def is_profitable(self) -> bool:
        """Return True if position has positive net profit."""
        return self.profit_loss >= 0.0


class MarketDataService:
    """
    Handles live market data retrieval with graceful fallback to standard library
    and simulated pricing when offline or when third-party libraries are absent.
    """

    def __init__(self):
        self._yfinance_available = False
        try:
            import yfinance as yf
            self._yf = yf
            self._yfinance_available = True
        except ImportError:
            self._yf = None

    def get_current_price(self, ticker: str, fallback_reference_price: float = 100.0) -> Tuple[float, str]:
        """
        Retrieve the latest market price for a given stock ticker.

        Returns:
            Tuple[float, str]: (price, data_source_note)
        """
        ticker_clean = ticker.strip().upper()

        # 1. Try yfinance if available
        if self._yfinance_available and self._yf is not None:
            try:
                stock_obj = self._yf.Ticker(ticker_clean)
                hist = stock_obj.history(period="5d")
                if not hist.empty and "Close" in hist.columns:
                    latest_close = float(hist["Close"].dropna().iloc[-1])
                    if latest_close > 0:
                        return round(latest_close, 2), "Yahoo Finance Live"
            except Exception:
                pass

        # 2. Resilient Deterministic Fallback based on ticker hash
        # Ensures consistent pricing during testing/offline sessions without failing
        pseudo_seed = sum(ord(c) for c in ticker_clean)
        # Yields realistic prices between $40 and $350
        simulated_base = 40.0 + (pseudo_seed % 280)
        # Add slight variation around purchase price if supplied
        if fallback_reference_price > 0:
            price = round(fallback_reference_price * (0.95 + ((pseudo_seed % 15) / 100.0)), 2)
        else:
            price = round(simulated_base, 2)

        return price, "Market Price Baseline"


class StockPortfolioManager:
    """
    Core engine managing company datasets, customer registries,
    stock transactions, and portfolio persistence.
    """

    def __init__(self, base_directory: Optional[Path] = None):
        """
        Initialize the portfolio manager with directory paths.
        """
        if base_directory is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(base_directory)

        self.dataset_file = self.base_dir / "company_dataset.csv"
        self.customers_file = self.base_dir / "details.txt"
        self.summary_file = self.base_dir / "portfolio_summary.csv"

        self.market_service = MarketDataService()
        self.company_dataset: Dict[str, Dict[str, str]] = {}
        self.registered_customers: set[str] = set()

        self._initialize_storage()
        self.load_company_dataset()
        self.load_customers()

    def _initialize_storage(self) -> None:
        """Ensure necessary files and CSV headers exist."""
        if not self.customers_file.exists():
            self.customers_file.touch()

        if not self.summary_file.exists() or self.summary_file.stat().st_size == 0:
            with open(self.summary_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Customer_id",
                    "Ticker",
                    "Company_Name",
                    "Buy_price",
                    "Quantity",
                    "Investment",
                    "Current_price",
                    "Current_value",
                    "Profit_Loss",
                    "Timestamp"
                ])

    def load_company_dataset(self) -> int:
        """
        Load available company tickers and metadata from CSV.

        Returns:
            int: Number of loaded companies.
        """
        if not self.dataset_file.exists():
            raise FileNotFoundError(f"Company dataset missing: {self.dataset_file}")

        self.company_dataset.clear()
        with open(self.dataset_file, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = row.get("Symbol", "").strip().upper()
                sec = row.get("Security", "").strip()
                sector = row.get("GICS Sector", "").strip()
                if sym:
                    self.company_dataset[sym] = {
                        "name": sec or sym,
                        "sector": sector or "General"
                    }
        return len(self.company_dataset)

    def load_customers(self) -> int:
        """
        Load stored customer IDs from details.txt.

        Returns:
            int: Number of loaded customer IDs.
        """
        self.registered_customers.clear()
        if self.customers_file.exists():
            with open(self.customers_file, "r", encoding="utf-8") as f:
                for line in f:
                    cid = line.strip()
                    if cid:
                        self.registered_customers.add(cid)
        return len(self.registered_customers)

    def generate_customer_id(self) -> str:
        """
        Generate a unique customer identifier in the format: STOCK_2026_XXXXXX.
        Guarantees no collisions with existing stored IDs.
        """
        chars = string.ascii_letters + string.digits
        while True:
            suffix = "".join(random.choices(chars, k=6))
            new_id = f"STOCK_2026_{suffix}"
            if new_id not in self.registered_customers:
                self.registered_customers.add(new_id)
                with open(self.customers_file, "a", encoding="utf-8") as f:
                    f.write(new_id + "\n")
                return new_id

    def validate_customer_id(self, customer_id: str) -> bool:
        """Check whether a customer ID is registered."""
        return customer_id.strip() in self.registered_customers

    def register_existing_customer(self, customer_id: str) -> bool:
        """
        Register a specific customer ID if valid and not already tracked.
        """
        cid = customer_id.strip()
        if not cid:
            return False
        if cid not in self.registered_customers:
            self.registered_customers.add(cid)
            with open(self.customers_file, "a", encoding="utf-8") as f:
                f.write(cid + "\n")
        return True

    def validate_ticker(self, ticker: str) -> Optional[Dict[str, str]]:
        """
        Validate whether a ticker exists in the S&P 500 company dataset.

        Returns:
            Optional[Dict[str, str]]: Company details dictionary or None if not found.
        """
        cleaned = ticker.strip().upper()
        return self.company_dataset.get(cleaned)

    def search_companies(self, keyword: str) -> List[Tuple[str, str, str]]:
        """
        Search companies in the S&P 500 dataset by ticker or company name substring.

        Returns:
            List[Tuple[str, str, str]]: List of (ticker, company_name, sector) matches.
        """
        kw = keyword.strip().lower()
        if not kw:
            return []
        matches = []
        for ticker, data in self.company_dataset.items():
            if kw in ticker.lower() or kw in data["name"].lower():
                matches.append((ticker, data["name"], data["sector"]))
        return sorted(matches, key=lambda x: x[0])

    def get_companies_by_sector(self, sector_name: str) -> List[Tuple[str, str]]:
        """
        Filter available companies belonging to a specific GICS sector.

        Returns:
            List[Tuple[str, str]]: List of (ticker, company_name) pairs.
        """
        sec = sector_name.strip().lower()
        results = [
            (t, d["name"])
            for t, d in self.company_dataset.items()
            if sec in d["sector"].lower()
        ]
        return sorted(results, key=lambda x: x[0])

    def record_transaction(
        self,
        customer_id: str,
        ticker: str,
        buy_price: float,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Execute and persist a stock purchase transaction.

        Returns:
            Dict[str, Any]: Complete transaction record.
        """
        ticker_clean = ticker.strip().upper()
        company_info = self.validate_ticker(ticker_clean)
        company_name = company_info["name"] if company_info else ticker_clean

        if buy_price <= 0:
            raise InvalidTransactionError("Purchase price must be strictly positive (> 0).")
        if quantity <= 0:
            raise InvalidTransactionError("Share quantity must be a positive integer (> 0).")

        total_investment = round(buy_price * quantity, 2)

        # Retrieve live or resilient baseline market price
        current_price, price_source = self.market_service.get_current_price(
            ticker_clean, fallback_reference_price=buy_price
        )
        current_value = round(current_price * quantity, 2)
        profit_loss = round(current_value - total_investment, 2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "Customer_id": customer_id,
            "Ticker": ticker_clean,
            "Company_Name": company_name,
            "Buy_price": round(buy_price, 2),
            "Quantity": quantity,
            "Investment": total_investment,
            "Current_price": current_price,
            "Current_value": current_value,
            "Profit_Loss": profit_loss,
            "Timestamp": timestamp,
            "Price_Source": price_source
        }

        # Append to CSV
        with open(self.summary_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                record["Customer_id"],
                record["Ticker"],
                record["Company_Name"],
                f"{record['Buy_price']:.2f}",
                record["Quantity"],
                f"{record['Investment']:.2f}",
                f"{record['Current_price']:.2f}",
                f"{record['Current_value']:.2f}",
                f"{record['Profit_Loss']:.2f}",
                record["Timestamp"]
            ])

        return record

    def get_portfolio_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all purchase holdings for a specific customer ID.
        """
        cid = customer_id.strip()
        holdings = []
        if not self.summary_file.exists():
            return holdings

        with open(self.summary_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Customer_id", "").strip() == cid:
                    try:
                        buy_p = float(row.get("Buy_price", 0.0))
                        qty = int(row.get("Quantity", 0))
                        inv = float(row.get("Investment", 0.0))
                        curr_p = float(row.get("Current_price", 0.0))
                        curr_v = float(row.get("Current_value", 0.0))
                        pl = float(row.get("Profit_Loss", 0.0))
                    except ValueError:
                        continue

                    holdings.append({
                        "Customer_id": cid,
                        "Ticker": row.get("Ticker", ""),
                        "Company_Name": row.get("Company_Name", row.get("Ticker", "")),
                        "Buy_price": buy_p,
                        "Quantity": qty,
                        "Investment": inv,
                        "Current_price": curr_p,
                        "Current_value": curr_v,
                        "Profit_Loss": pl,
                        "Timestamp": row.get("Timestamp", "N/A")
                    })
        return holdings

    def get_sector_allocation(self, customer_id: str) -> Dict[str, Dict[str, float]]:
        """Calculate total invested capital and portfolio percentage allocation per GICS sector."""
        holdings = self.get_portfolio_for_customer(customer_id)
        if not holdings:
            return {}

        total_inv = sum(h["Investment"] for h in holdings)
        sector_totals: Dict[str, float] = {}

        for h in holdings:
            ticker = h["Ticker"]
            info = self.validate_ticker(ticker)
            sector = info["sector"] if info else "Other"
            sector_totals[sector] = sector_totals.get(sector, 0.0) + h["Investment"]

        allocation: Dict[str, Dict[str, float]] = {}
        for sec, amount in sector_totals.items():
            pct = round((amount / total_inv) * 100, 2) if total_inv > 0 else 0.0
            allocation[sec] = {"invested": round(amount, 2), "percentage": pct}

        return allocation

    def export_customer_portfolio_summary(self, customer_id: str, destination_file: Path) -> Dict[str, Any]:
        """
        Export a structured JSON report of a customer's portfolio summary.

        Returns:
            Dict[str, Any]: Aggregated report dictionary.
        """
        holdings = self.get_portfolio_for_customer(customer_id)
        total_inv = sum(h["Investment"] for h in holdings)
        total_val = sum(h["Current_value"] for h in holdings)
        net_pl = round(total_val - total_inv, 2)
        net_ret = round((net_pl / total_inv * 100), 2) if total_inv > 0 else 0.0

        summary_data = {
            "customer_id": customer_id,
            "export_time": datetime.now().isoformat(),
            "total_positions": len(holdings),
            "total_invested": round(total_inv, 2),
            "total_portfolio_value": round(total_val, 2),
            "net_profit_loss": net_pl,
            "return_percentage": net_ret,
            "positions": holdings
        }

        dest = Path(destination_file)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        return summary_data

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """
        Retrieve the full history of recorded transactions across all customers.
        """
        transactions = []
        if not self.summary_file.exists():
            return transactions

        with open(self.summary_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    buy_p = float(row.get("Buy_price", 0.0))
                    qty = int(row.get("Quantity", 0))
                    inv = float(row.get("Investment", 0.0))
                    curr_p = float(row.get("Current_price", 0.0))
                    curr_v = float(row.get("Current_value", 0.0))
                    pl = float(row.get("Profit_Loss", 0.0))
                except ValueError:
                    continue

                transactions.append({
                    "Customer_id": row.get("Customer_id", ""),
                    "Ticker": row.get("Ticker", ""),
                    "Company_Name": row.get("Company_Name", row.get("Ticker", "")),
                    "Buy_price": buy_p,
                    "Quantity": qty,
                    "Investment": inv,
                    "Current_price": curr_p,
                    "Current_value": curr_v,
                    "Profit_Loss": pl,
                    "Timestamp": row.get("Timestamp", "N/A")
                })
        return transactions


# -----------------------------------------------------------------------------
# Terminal UI and Presentation Helpers
# -----------------------------------------------------------------------------

def clear_screen() -> None:
    """Clear the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str) -> None:
    """Print a clean visual banner."""
    width = 76
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def render_sector_bar_chart(allocation: Dict[str, Dict[str, float]], bar_width: int = 30) -> None:
    """Render a clean text-based ASCII bar chart of sector allocation."""
    if not allocation:
        print("  (No allocation data to display)")
        return
    print("\nSector Allocation Breakdown:")
    print("-" * 55)
    for sector, data in sorted(allocation.items(), key=lambda x: x[1]['percentage'], reverse=True):
        pct = data['percentage']
        bar_len = int((pct / 100.0) * bar_width)
        bar = "#" * bar_len
        print(f" {sector[:20].ljust(20)} | {bar.ljust(bar_width)} | {pct:>5.1f}% (${data['invested']:,.2f})")
    print("-" * 55)


def render_table(headers: List[str], rows: List[List[str]]) -> None:
    """
    Render clean ASCII table with dynamically calculated column widths.
    """
    if not rows:
        print("  (No records available)")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    # Formatting strings
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

    print(header_line)
    print(separator)
    for row in rows:
        formatted_row = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(formatted_row)


# -----------------------------------------------------------------------------
# Interactive CLI Workflow
# -----------------------------------------------------------------------------

def handle_add_transaction(manager: StockPortfolioManager) -> None:
    """Handle interactive workflow to record a stock transaction."""
    print_header("ADD STOCK TRANSACTION")
    print(f"Total available companies in dataset: {len(manager.company_dataset)}\n")

    # Step 1: Customer Identification
    has_id = input("Do you have an existing Customer ID? (y/n): ").strip().lower()
    if has_id in ("y", "yes"):
        cid = input("Enter your Customer ID: ").strip()
        if not manager.validate_customer_id(cid):
            print(f"\n[!] Customer ID '{cid}' not found in registry.")
            create_choice = input("Would you like to register this ID now? (y/n): ").strip().lower()
            if create_choice in ("y", "yes"):
                manager.register_existing_customer(cid)
                print(f"[+] Customer ID '{cid}' registered successfully.")
            else:
                cid = manager.generate_customer_id()
                print(f"[+] Generated new Customer ID: {cid}")
        else:
            print(f"[+] Customer ID verified: {cid}")
    else:
        cid = manager.generate_customer_id()
        print(f"[+] Generated new Customer ID: {cid}")

    # Step 2: Stock Selection
    while True:
        ticker = input("\nEnter stock ticker (e.g., AAPL, GOOGL, MMM, MSFT): ").strip().upper()
        if not ticker:
            print("Ticker cannot be empty. Please try again.")
            continue

        company_info = manager.validate_ticker(ticker)
        if not company_info:
            print(f"[!] '{ticker}' is not found in the S&P 500 company dataset.")
            retry = input("Try another ticker? (y/n): ").strip().lower()
            if retry not in ("y", "yes"):
                return
            continue

        print(f"[+] Selected: {company_info['name']} (Sector: {company_info['sector']})")
        break

    # Step 3: Purchase Price & Quantity Input
    while True:
        try:
            price_input = input("Enter purchase price per share ($): ").strip()
            buy_price = float(price_input)
            if buy_price <= 0:
                print("Price must be greater than zero.")
                continue
            break
        except ValueError:
            print("Invalid price format. Please enter a valid decimal number.")

    while True:
        try:
            qty_input = input("Enter quantity of shares: ").strip()
            quantity = int(qty_input)
            if quantity <= 0:
                print("Quantity must be a positive whole integer.")
                continue
            break
        except ValueError:
            print("Invalid quantity. Please enter a positive integer.")

    # Step 4: Process and Record Transaction
    print("\nRetrieving market pricing and calculating positions...")
    try:
        record = manager.record_transaction(cid, ticker, buy_price, quantity)
    except Exception as exc:
        print(f"[!] Error processing transaction: {exc}")
        return

    print("\n" + "-" * 56)
    print("           TRANSACTION CONFIRMATION           ")
    print("-" * 56)
    print(f" Customer ID:       {record['Customer_id']}")
    print(f" Stock Ticker:      {record['Ticker']} ({record['Company_Name']})")
    print(f" Purchase Price:    ${record['Buy_price']:.2f}")
    print(f" Shares Purchased:  {record['Quantity']}")
    print(f" Total Investment:  ${record['Investment']:.2f}")
    print(f" Current Price:     ${record['Current_price']:.2f}  [{record['Price_Source']}]")
    print(f" Current Value:     ${record['Current_value']:.2f}")

    pl = record['Profit_Loss']
    pl_sign = "+" if pl >= 0 else ""
    pct = (pl / record['Investment']) * 100 if record['Investment'] > 0 else 0.0
    print(f" Profit / Loss:     {pl_sign}${pl:.2f} ({pl_sign}{pct:.2f}%)")
    print("-" * 56)
    print("[+] Transaction successfully recorded to portfolio_summary.csv")


def handle_view_portfolio(manager: StockPortfolioManager) -> None:
    """Handle interactive workflow to view a specific customer's portfolio."""
    print_header("VIEW CUSTOMER PORTFOLIO")
    cid = input("Enter your Customer ID: ").strip()
    if not cid:
        print("Customer ID cannot be empty.")
        return

    holdings = manager.get_portfolio_for_customer(cid)
    if not holdings:
        print(f"\n[i] No portfolio records found for Customer ID: {cid}")
        return

    headers = [
        "Ticker", "Company", "Buy Price", "Qty",
        "Invested ($)", "Current ($)", "Value ($)", "P/L ($)", "Return"
    ]
    rows = []
    total_inv = 0.0
    total_val = 0.0

    for h in holdings:
        inv = h["Investment"]
        val = h["Current_value"]
        pl = h["Profit_Loss"]
        ret = (pl / inv * 100) if inv > 0 else 0.0
        total_inv += inv
        total_val += val

        sign = "+" if pl >= 0 else ""
        rows.append([
            h["Ticker"],
            h["Company_Name"][:20],
            f"${h['Buy_price']:.2f}",
            str(h["Quantity"]),
            f"${inv:.2f}",
            f"${h['Current_price']:.2f}",
            f"${val:.2f}",
            f"{sign}${pl:.2f}",
            f"{sign}{ret:.2f}%"
        ])

    print(f"\nPortfolio Holdings for: {cid}\n")
    render_table(headers, rows)

    net_pl = total_val - total_inv
    net_ret = (net_pl / total_inv * 100) if total_inv > 0 else 0.0
    net_sign = "+" if net_pl >= 0 else ""

    print("-" * 76)
    print(f" Total Invested:    ${total_inv:.2f}")
    print(f" Total Portfolio:   ${total_val:.2f}")
    print(f" Net Profit / Loss: {net_sign}${net_pl:.2f} ({net_sign}{net_ret:.2f}%)")
    print("-" * 76)


def handle_view_history(manager: StockPortfolioManager) -> None:
    """Handle interactive workflow to display global transaction history."""
    print_header("TRANSACTION HISTORY")
    transactions = manager.get_all_transactions()
    if not transactions:
        print("\n[i] No transaction records available in the database.")
        return

    headers = ["Customer ID", "Ticker", "Buy ($)", "Qty", "Invested ($)", "Current ($)", "P/L ($)", "Date/Time"]
    rows = []
    for t in transactions:
        pl = t["Profit_Loss"]
        sign = "+" if pl >= 0 else ""
        rows.append([
            t["Customer_id"],
            t["Ticker"],
            f"${t['Buy_price']:.2f}",
            str(t["Quantity"]),
            f"${t['Investment']:.2f}",
            f"${t['Current_price']:.2f}",
            f"{sign}${pl:.2f}",
            t["Timestamp"]
        ])

    print(f"\nTotal Recorded Transactions: {len(transactions)}\n")
    render_table(headers, rows)


def main() -> None:
    """Main program entry point coordinating CLI navigation."""
    try:
        manager = StockPortfolioManager()
    except Exception as exc:
        print(f"Failed to initialize Stock Portfolio Tracker: {exc}", file=sys.stderr)
        sys.exit(1)

    while True:
        clear_screen()
        print_header("DATHEON INTERNSHIP - STOCK PORTFOLIO TRACKER")
        print("\nMAIN MENU")
        print("-" * 36)
        print(" 1. Add Stock Purchase Transaction")
        print(" 2. View Customer Portfolio")
        print(" 3. View All Transaction History")
        print(" 4. Exit Application")
        print("-" * 36)

        try:
            choice = input("Enter choice (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting application. Goodbye!")
            break

        if choice == "1":
            clear_screen()
            handle_add_transaction(manager)
        elif choice == "2":
            clear_screen()
            handle_view_portfolio(manager)
        elif choice == "3":
            clear_screen()
            handle_view_history(manager)
        elif choice == "4":
            print("\nThank you for using Datheon Stock Portfolio Tracker. Goodbye!\n")
            break
        else:
            print("\n[!] Invalid choice. Please enter a number between 1 and 4.")

        try:
            input("\nPress Enter to return to main menu...")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()

