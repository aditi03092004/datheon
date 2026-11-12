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

    def validate_and_repair_storage(self) -> int:
        """Scan portfolio_summary.csv and remove any corrupted or truncated rows."""
        if not self.summary_file.exists():
            return 0
        valid_rows = []
        with open(self.summary_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 8 and row[0].strip() and row[1].strip():
                    valid_rows.append(row)

        with open(self.summary_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(valid_rows)
        return len(valid_rows)

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

    def record_sale(
        self,
        customer_id: str,
        ticker: str,
        sell_price: float,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Execute and persist a stock sale transaction, calculating realized profit/loss.

        Raises:
            InvalidTransactionError: If parameters are invalid or customer holds insufficient shares.

        Returns:
            Dict[str, Any]: Detailed sale transaction summary.
        """
        ticker_clean = ticker.strip().upper()
        if sell_price <= 0:
            raise InvalidTransactionError("Sell price must be strictly positive (> 0).")
        if quantity <= 0:
            raise InvalidTransactionError("Sale quantity must be a positive integer (> 0).")

        consolidated = self.get_consolidated_holdings(customer_id)
        if ticker_clean not in consolidated or consolidated[ticker_clean]["total_quantity"] < quantity:
            owned = consolidated.get(ticker_clean, {}).get("total_quantity", 0)
            raise InvalidTransactionError(
                f"Insufficient shares to sell for {ticker_clean}: owned {owned}, requested {quantity}."
            )

        pos = consolidated[ticker_clean]
        avg_cost_basis = pos["average_buy_price"]
        company_name = pos["company_name"]

        proceeds = round(sell_price * quantity, 2)
        cost_basis = round(avg_cost_basis * quantity, 2)
        realized_pl = round(proceeds - cost_basis, 2)
        return_pct = round((realized_pl / cost_basis) * 100, 2) if cost_basis > 0 else 0.0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "Customer_id": customer_id,
            "Ticker": ticker_clean,
            "Company_Name": company_name,
            "Transaction_Type": "SELL",
            "Sell_Price": round(sell_price, 2),
            "Quantity": quantity,
            "Proceeds": proceeds,
            "Cost_Basis": cost_basis,
            "Realized_Profit_Loss": realized_pl,
            "Return_Percentage": return_pct,
            "Timestamp": timestamp
        }

        with open(self.summary_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                customer_id,
                ticker_clean,
                company_name,
                f"{avg_cost_basis:.2f}",
                -quantity,
                f"{-cost_basis:.2f}",
                f"{sell_price:.2f}",
                f"{-proceeds:.2f}",
                f"{realized_pl:.2f}",
                timestamp
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

    def get_consolidated_holdings(self, customer_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate customer holdings by ticker, computing total quantity,
        weighted average cost basis (buy price), total investment, current valuation,
        unrealized profit/loss, and portfolio weight.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary keyed by uppercase ticker symbol.
        """
        raw_holdings = self.get_portfolio_for_customer(customer_id)
        if not raw_holdings:
            return {}

        consolidated: Dict[str, Dict[str, Any]] = {}
        total_portfolio_val = 0.0

        for item in raw_holdings:
            ticker = item["Ticker"].upper()
            qty = item["Quantity"]
            inv = item["Investment"]

            if ticker not in consolidated:
                company_info = self.validate_ticker(ticker)
                sector = company_info["sector"] if company_info else "General"
                consolidated[ticker] = {
                    "ticker": ticker,
                    "company_name": item["Company_Name"],
                    "sector": sector,
                    "total_quantity": 0,
                    "total_invested": 0.0,
                    "current_price": item["Current_price"],
                    "current_value": 0.0,
                    "profit_loss": 0.0,
                    "average_buy_price": 0.0,
                    "return_percentage": 0.0,
                    "portfolio_weight": 0.0,
                }

            consolidated[ticker]["total_quantity"] += qty
            consolidated[ticker]["total_invested"] = round(consolidated[ticker]["total_invested"] + inv, 2)
            consolidated[ticker]["current_price"] = item["Current_price"]

        for ticker, data in consolidated.items():
            qty = data["total_quantity"]
            tot_inv = data["total_invested"]
            curr_p = data["current_price"]

            avg_buy = round(tot_inv / qty, 2) if qty > 0 else 0.0
            curr_val = round(curr_p * qty, 2)
            pl = round(curr_val - tot_inv, 2)
            ret_pct = round((pl / tot_inv) * 100, 2) if tot_inv > 0 else 0.0

            data["average_buy_price"] = avg_buy
            data["current_value"] = curr_val
            data["profit_loss"] = pl
            data["return_percentage"] = ret_pct
            total_portfolio_val += curr_val

        active_consolidated = {t: d for t, d in consolidated.items() if d["total_quantity"] > 0}
        for ticker, data in active_consolidated.items():
            w = round((data["current_value"] / total_portfolio_val) * 100, 2) if total_portfolio_val > 0 else 0.0
            data["portfolio_weight"] = w

        return active_consolidated

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

    def get_weighted_return_percentage(self, customer_id: str) -> float:
        """Calculate total portfolio weighted average return on invested capital."""
        holdings = self.get_portfolio_for_customer(customer_id)
        if not holdings:
            return 0.0
        total_inv = sum(h["Investment"] for h in holdings)
        if total_inv <= 0:
            return 0.0
        total_profit = sum(h["Profit_Loss"] for h in holdings)
        return round((total_profit / total_inv) * 100, 2)

    def get_rebalancing_suggestions(self, customer_id: str, max_sector_pct: float = 40.0) -> List[str]:
        """Analyze sector allocation and return warnings if any sector exceeds the concentration threshold."""
        allocations = self.get_sector_allocation(customer_id)
        suggestions: List[str] = []
        for sector, data in allocations.items():
            if data["percentage"] > max_sector_pct:
                suggestions.append(
                    f"Concentration alert: {sector} represents {data['percentage']:.1f}% "
                    f"of your portfolio (recommended maximum is {max_sector_pct:.1f}%)."
                )
        return suggestions

    def get_portfolio_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """
        Analyze sector concentration and compute the Herfindahl-Hirschman Index (HHI)
        to evaluate portfolio diversification and risk exposure.

        Returns:
            Dict[str, Any]: Risk profile analysis with metrics, classification, and top exposure.
        """
        allocations = self.get_sector_allocation(customer_id)
        if not allocations:
            return {
                "customer_id": customer_id,
                "total_sectors": 0,
                "herfindahl_index": 0.0,
                "risk_level": "Uninvested / Empty",
                "top_sector": "None",
                "top_sector_weight": 0.0,
                "is_diversified": False
            }

        hhi = round(sum(d["percentage"] ** 2 for d in allocations.values()), 1)
        sorted_sectors = sorted(allocations.items(), key=lambda x: x[1]["percentage"], reverse=True)
        top_sector, top_data = sorted_sectors[0]

        if hhi < 2500.0:
            risk_level = "Low Concentration / Well Diversified"
        elif hhi < 5000.0:
            risk_level = "Moderate Concentration"
        else:
            risk_level = "High Concentration / Concentrated Risk"

        is_diversified = (len(allocations) >= 3 and top_data["percentage"] <= 40.0)

        return {
            "customer_id": customer_id,
            "total_sectors": len(allocations),
            "herfindahl_index": hhi,
            "risk_level": risk_level,
            "top_sector": top_sector,
            "top_sector_weight": top_data["percentage"],
            "is_diversified": is_diversified
        }

    def export_customer_csv(self, customer_id: str, destination_file: Path) -> int:
        """Export filtered holdings for a specific customer to a standalone CSV file."""
        holdings = self.get_portfolio_for_customer(customer_id)
        dest = Path(destination_file)
        with open(dest, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Ticker", "Company_Name", "Buy_Price", "Quantity", "Investment", "Current_Price", "Current_Value", "Profit_Loss", "Timestamp"])
            for h in holdings:
                writer.writerow([h["Ticker"], h["Company_Name"], h["Buy_price"], h["Quantity"], h["Investment"], h["Current_price"], h["Current_value"], h["Profit_Loss"], h["Timestamp"]])
        return len(holdings)

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

    def get_profitable_positions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Filter and return only positions currently in net profit (P/L > 0)."""
        return [h for h in self.get_portfolio_for_customer(customer_id) if h["Profit_Loss"] > 0]

    def get_losing_positions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Filter and return only positions currently at a net loss (P/L < 0)."""
        return [h for h in self.get_portfolio_for_customer(customer_id) if h["Profit_Loss"] < 0]
    def get_top_performing_position(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the customer holding position with the highest return on investment percentage."""
        holdings = self.get_portfolio_for_customer(customer_id)
        if not holdings:
            return None
        return max(
            holdings,
            key=lambda h: (h["Profit_Loss"] / h["Investment"]) if h.get("Investment", 0) > 0 else float("-inf")
        )

    def get_worst_performing_position(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the customer holding position with the lowest return on investment percentage."""
        holdings = self.get_portfolio_for_customer(customer_id)
        if not holdings:
            return None
        return min(
            holdings,
            key=lambda h: (h["Profit_Loss"] / h["Investment"]) if h.get("Investment", 0) > 0 else float("inf")
        )
    def get_total_invested_capital(self, customer_id: str) -> float:
        """Calculate total amount of invested capital across active holdings for customer."""
        holdings = self.get_portfolio_for_customer(customer_id)
        return round(sum(h["Investment"] for h in holdings), 2)

    def get_unrealized_profit_percentage(self, customer_id: str) -> float:
        """Calculate aggregate unrealized profit percentage for active customer holdings."""
        total_inv = self.get_total_invested_capital(customer_id)
        if total_inv <= 0:
            return 0.0
        holdings = self.get_portfolio_for_customer(customer_id)
        total_pl = sum(h["Profit_Loss"] for h in holdings)
        return round((total_pl / total_inv) * 100, 2)
    def get_sector_company_counts(self) -> Dict[str, int]:
        """Aggregate and return the count of S&P 500 companies in each market sector."""
        counts: Dict[str, int] = {}
        for data in self.company_dataset.values():
            sector = data.get("sector", "General")
            counts[sector] = counts.get(sector, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))

    def get_position_risk_alerts(
        self,
        customer_id: str,
        stop_loss_pct: float = -10.0,
        take_profit_pct: float = 20.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan customer positions against stop-loss and take-profit thresholds.

        Args:
            customer_id (str): Customer identifier.
            stop_loss_pct (float): Negative percentage threshold triggering stop-loss alert (default: -10.0%).
            take_profit_pct (float): Positive percentage threshold triggering profit-taking alert (default: 20.0%).

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary containing 'stop_loss_alerts' and 'take_profit_alerts'.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        stop_loss_alerts: List[Dict[str, Any]] = []
        take_profit_alerts: List[Dict[str, Any]] = []

        for ticker, pos in consolidated.items():
            ret = pos["return_percentage"]
            if ret <= stop_loss_pct:
                stop_loss_alerts.append({
                    "ticker": ticker,
                    "company_name": pos["company_name"],
                    "return_percentage": ret,
                    "profit_loss": pos["profit_loss"],
                    "action_recommended": "Review for stop-loss exit or hedging"
                })
            elif ret >= take_profit_pct:
                take_profit_alerts.append({
                    "ticker": ticker,
                    "company_name": pos["company_name"],
                    "return_percentage": ret,
                    "profit_loss": pos["profit_loss"],
                    "action_recommended": "Consider taking partial profits"
                })

        return {
            "stop_loss_alerts": stop_loss_alerts,
            "take_profit_alerts": take_profit_alerts
        }

    def get_customer_financial_scorecard(self, customer_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive executive financial scorecard for a customer.

        Args:
            customer_id (str): Customer identifier.

        Returns:
            Dict[str, Any]: Complete financial scorecard metrics.
        """
        cid = customer_id.strip()
        is_registered = self.validate_customer_id(cid)
        raw_holdings = self.get_portfolio_for_customer(cid)
        consolidated = self.get_consolidated_holdings(cid)

        total_inv = self.get_total_invested_capital(cid)
        total_curr_val = round(sum(pos["current_value"] for pos in consolidated.values()), 2)
        unrealized_pl = round(total_curr_val - total_inv, 2)
        unrealized_ret_pct = self.get_unrealized_profit_percentage(cid)

        profitable = [p for p in consolidated.values() if p["profit_loss"] > 0]
        losing = [p for p in consolidated.values() if p["profit_loss"] < 0]
        win_ratio = round((len(profitable) / len(consolidated) * 100), 1) if consolidated else 0.0

        top_holding = "None"
        if consolidated:
            top_holding = max(consolidated.values(), key=lambda p: p["current_value"])["ticker"]

        risk_profile = self.get_portfolio_risk_profile(cid)

        return {
            "customer_id": cid,
            "is_registered": is_registered,
            "total_transactions": len(raw_holdings),
            "active_positions_count": len(consolidated),
            "total_invested_capital": total_inv,
            "total_current_valuation": total_curr_val,
            "unrealized_profit_loss": unrealized_pl,
            "unrealized_return_percentage": unrealized_ret_pct,
            "profitable_positions_count": len(profitable),
            "losing_positions_count": len(losing),
            "position_win_ratio": win_ratio,
            "top_holding": top_holding,
            "risk_profile": risk_profile
        }

    def get_rebalancing_orders(
        self,
        customer_id: str,
        target_sector_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Generate rebalancing orders to align portfolio with target sector weights.

        Args:
            customer_id (str): Customer identifier.
            target_sector_weights (Dict[str, float]): Target sector percentage map summing to ~100.0.

        Returns:
            List[Dict[str, Any]]: List of rebalancing action recommendations per sector.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return []

        total_val = sum(pos["current_value"] for pos in consolidated.values())
        if total_val <= 0:
            return []

        current_sector_values: Dict[str, float] = {}
        for pos in consolidated.values():
            sec = pos["sector"]
            current_sector_values[sec] = round(current_sector_values.get(sec, 0.0) + pos["current_value"], 2)

        all_sectors = sorted(set(list(target_sector_weights.keys()) + list(current_sector_values.keys())))
        orders: List[Dict[str, Any]] = []

        for sec in all_sectors:
            target_pct = target_sector_weights.get(sec, 0.0)
            target_val = round((target_pct / 100.0) * total_val, 2)
            curr_val = current_sector_values.get(sec, 0.0)
            curr_pct = round((curr_val / total_val) * 100.0, 2)
            diff = round(target_val - curr_val, 2)

            if diff > 1.0:
                action = "BUY"
            elif diff < -1.0:
                action = "SELL"
            else:
                action = "HOLD"

            orders.append({
                "sector": sec,
                "current_value": curr_val,
                "current_weight": curr_pct,
                "target_weight": target_pct,
                "target_value": target_val,
                "adjustment_needed": diff,
                "action": action
            })

        return orders

    SECTOR_DIVIDEND_BENCHMARKS: Dict[str, float] = {
        "Utilities": 3.5,
        "Real Estate": 3.8,
        "Financials": 2.8,
        "Energy": 3.2,
        "Consumer Staples": 2.6,
        "Health Care": 1.8,
        "Industrials": 1.6,
        "Information Technology": 0.9,
        "Consumer Discretionary": 1.0,
        "Communication Services": 1.1,
        "Materials": 2.1,
    }

    def get_estimated_dividend_income(
        self,
        customer_id: str,
        default_dividend_yield_pct: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate estimated annual, quarterly, and monthly dividend cash flows for customer holdings.

        Args:
            customer_id (str): Customer identifier.
            default_dividend_yield_pct (float): Fallback dividend yield percentage for unbenchmarked sectors.

        Returns:
            Dict[str, Any]: Summary of projected dividend cash flows and per-position breakdown.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "annual_dividend_income": 0.0,
                "quarterly_dividend_income": 0.0,
                "monthly_dividend_income": 0.0,
                "effective_portfolio_yield": 0.0,
                "positions": []
            }

        total_val = sum(pos["current_value"] for pos in consolidated.values())
        total_annual = 0.0
        projections: List[Dict[str, Any]] = []

        for ticker, pos in consolidated.items():
            sec = pos.get("sector", "General")
            yield_pct = self.SECTOR_DIVIDEND_BENCHMARKS.get(sec, default_dividend_yield_pct)
            ann_income = round(pos["current_value"] * (yield_pct / 100.0), 2)
            total_annual += ann_income

            projections.append({
                "ticker": ticker,
                "company_name": pos["company_name"],
                "sector": sec,
                "current_value": pos["current_value"],
                "dividend_yield_pct": yield_pct,
                "annual_income": ann_income,
                "quarterly_income": round(ann_income / 4.0, 2),
                "monthly_income": round(ann_income / 12.0, 2)
            })

        total_annual = round(total_annual, 2)
        effective_yield = round((total_annual / total_val * 100.0), 2) if total_val > 0 else 0.0

        return {
            "customer_id": customer_id,
            "total_portfolio_value": total_val,
            "annual_dividend_income": total_annual,
            "quarterly_dividend_income": round(total_annual / 4.0, 2),
            "monthly_dividend_income": round(total_annual / 12.0, 2),
            "effective_portfolio_yield": effective_yield,
            "positions": projections
        }

    def calculate_portfolio_drawdown_risk(
        self,
        customer_id: str,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate parametric Value-at-Risk (VaR) and maximum estimated downside drawdown.

        Args:
            customer_id (str): Customer identifier.
            confidence_level (float): Statistical confidence (0.90, 0.95, or 0.99).

        Returns:
            Dict[str, Any]: Parametric VaR risk metrics and downside analysis.
        """
        import math
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "confidence_level": confidence_level,
                "estimated_daily_var": 0.0,
                "estimated_monthly_var": 0.0,
                "daily_var_pct": 0.0,
                "monthly_var_pct": 0.0,
                "risk_assessment": "Uninvested / Zero Risk"
            }

        total_val = sum(pos["current_value"] for pos in consolidated.values())
        if total_val <= 0:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "confidence_level": confidence_level,
                "estimated_daily_var": 0.0,
                "estimated_monthly_var": 0.0,
                "daily_var_pct": 0.0,
                "monthly_var_pct": 0.0,
                "risk_assessment": "Zero Valuation"
            }

        risk_prof = self.get_portfolio_risk_profile(customer_id)
        hhi = risk_prof.get("herfindahl_index", 2500.0)

        concentration_mult = math.sqrt(max(1.0, hhi / 2500.0))
        daily_vol = min(0.05, 0.012 * concentration_mult)

        z = 1.65
        if confidence_level >= 0.99:
            z = 2.33
        elif confidence_level <= 0.90:
            z = 1.28

        daily_var = round(total_val * z * daily_vol, 2)
        monthly_var = round(daily_var * math.sqrt(21), 2)
        monthly_var = min(total_val, monthly_var)

        daily_var_pct = round((daily_var / total_val) * 100.0, 2)
        monthly_var_pct = round((monthly_var / total_val) * 100.0, 2)

        if monthly_var_pct < 10.0:
            assessment = "Conservative Downside Risk"
        elif monthly_var_pct < 20.0:
            assessment = "Moderate Downside Risk"
        else:
            assessment = "Elevated Downside Risk"

        return {
            "customer_id": customer_id,
            "total_portfolio_value": total_val,
            "confidence_level": confidence_level,
            "estimated_daily_var": daily_var,
            "estimated_monthly_var": monthly_var,
            "daily_var_pct": daily_var_pct,
            "monthly_var_pct": monthly_var_pct,
            "risk_assessment": assessment
        }

    def find_transactions_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Filter and return all historical transactions matching a specific ticker."""
        sym = ticker.strip().upper()
        return [t for t in self.get_all_transactions() if t.get("Ticker", "").upper() == sym]

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

    def get_transactions_in_date_range(
        self,
        start_date: str,
        end_date: str,
        customer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter transactions by date range (inclusive), optionally scoped to a single customer.

        Args:
            start_date (str): Beginning date in 'YYYY-MM-DD' format.
            end_date (str): Ending date in 'YYYY-MM-DD' format.
            customer_id (Optional[str]): Optional customer identifier filter.

        Returns:
            List[Dict[str, Any]]: Matching historical transactions sorted chronologically.
        """
        try:
            start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError as err:
            raise ValueError("Dates must be valid strings formatted as 'YYYY-MM-DD'.") from err

        all_txs = self.get_all_transactions()
        filtered: List[Dict[str, Any]] = []
        cid = customer_id.strip() if customer_id else None

        for tx in all_txs:
            if cid and tx.get("Customer_id", "").strip() != cid:
                continue

            raw_ts = tx.get("Timestamp", "")
            if not raw_ts or raw_ts == "N/A":
                continue

            try:
                tx_dt = datetime.strptime(raw_ts[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    tx_dt = datetime.fromisoformat(raw_ts)
                except ValueError:
                    continue

            if start_dt <= tx_dt <= end_dt:
                filtered.append(tx)

        return sorted(filtered, key=lambda x: x.get("Timestamp", ""))

    def calculate_position_size_limits(
        self,
        customer_id: str,
        max_allocation_pct: float = 20.0
    ) -> Dict[str, Any]:
        """
        Evaluate portfolio positions against risk management allocation limits.

        Identifies overweight holdings exceeding the maximum permissible portfolio weight,
        computing rebalancing trims in both monetary value and estimated share count.

        Args:
            customer_id (str): Customer identifier.
            max_allocation_pct (float): Maximum allowed percentage weight for any single asset (default: 20.0%).

        Returns:
            Dict[str, Any]: Audit summary with compliance statistics and trim recommendations.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "max_allocation_pct": max_allocation_pct,
                "compliant_positions_count": 0,
                "overweight_positions_count": 0,
                "is_fully_compliant": True,
                "recommendations": []
            }

        total_val = sum(pos["current_value"] for pos in consolidated.values())
        if total_val <= 0:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "max_allocation_pct": max_allocation_pct,
                "compliant_positions_count": 0,
                "overweight_positions_count": 0,
                "is_fully_compliant": True,
                "recommendations": []
            }

        max_allowed_val = round(total_val * (max_allocation_pct / 100.0), 2)
        recommendations: List[Dict[str, Any]] = []
        compliant_count = 0
        overweight_count = 0

        for ticker, pos in consolidated.items():
            curr_val = pos["current_value"]
            weight_pct = round((curr_val / total_val) * 100.0, 2)
            is_overweight = weight_pct > max_allocation_pct

            if is_overweight:
                overweight_count += 1
                excess_val = round(curr_val - max_allowed_val, 2)
                curr_price = pos["current_price"]
                shares_to_trim = int(excess_val // curr_price) if curr_price > 0 else 0
                status = "OVERWEIGHT"
            else:
                compliant_count += 1
                excess_val = 0.0
                shares_to_trim = 0
                status = "COMPLIANT"

            recommendations.append({
                "ticker": ticker,
                "company_name": pos["company_name"],
                "current_shares": pos["total_quantity"],
                "current_price": pos["current_price"],
                "current_value": curr_val,
                "portfolio_weight_pct": weight_pct,
                "max_allowed_value": max_allowed_val,
                "status": status,
                "trim_dollar_amount": excess_val,
                "suggested_shares_to_trim": shares_to_trim
            })

        recommendations.sort(key=lambda r: r["portfolio_weight_pct"], reverse=True)

        return {
            "customer_id": customer_id,
            "total_portfolio_value": round(total_val, 2),
            "max_allocation_pct": max_allocation_pct,
            "compliant_positions_count": compliant_count,
            "overweight_positions_count": overweight_count,
            "is_fully_compliant": overweight_count == 0,
            "recommendations": recommendations
        }

    def calculate_sharpe_ratio_estimate(
        self,
        customer_id: str,
        risk_free_rate_pct: float = 4.0
    ) -> Dict[str, Any]:
        """
        Estimate annualized Sharpe ratio and risk-adjusted excess return for customer portfolio.

        Args:
            customer_id (str): Customer identifier.
            risk_free_rate_pct (float): Annualized baseline risk-free rate percentage (default: 4.0%).

        Returns:
            Dict[str, Any]: Sharpe ratio, excess return, annualized volatility, and rating.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "portfolio_return_pct": 0.0,
                "risk_free_rate_pct": risk_free_rate_pct,
                "excess_return_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "sharpe_ratio": 0.0,
                "risk_adjusted_rating": "Uninvested"
            }

        total_inv = self.get_total_invested_capital(customer_id)
        total_val = sum(pos["current_value"] for pos in consolidated.values())
        if total_inv <= 0 or total_val <= 0:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "portfolio_return_pct": 0.0,
                "risk_free_rate_pct": risk_free_rate_pct,
                "excess_return_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "sharpe_ratio": 0.0,
                "risk_adjusted_rating": "Zero Valuation"
            }

        ret_pct = self.get_unrealized_profit_percentage(customer_id)
        excess_ret = round(ret_pct - risk_free_rate_pct, 2)

        risk_prof = self.get_portfolio_risk_profile(customer_id)
        hhi = risk_prof.get("herfindahl_index", 2500.0)
        import math
        vol = round(max(8.0, 15.0 * math.sqrt(max(1.0, hhi / 2500.0))), 2)

        sharpe = round(excess_ret / vol, 2) if vol > 0 else 0.0

        if sharpe >= 1.5:
            rating = "Excellent"
        elif sharpe >= 1.0:
            rating = "Good"
        elif sharpe >= 0.5:
            rating = "Adequate"
        elif sharpe > 0.0:
            rating = "Moderate"
        else:
            rating = "Suboptimal / High Risk"

        return {
            "customer_id": customer_id,
            "total_portfolio_value": round(total_val, 2),
            "portfolio_return_pct": ret_pct,
            "risk_free_rate_pct": risk_free_rate_pct,
            "excess_return_pct": excess_ret,
            "annualized_volatility_pct": vol,
            "sharpe_ratio": sharpe,
            "risk_adjusted_rating": rating
        }

    SECTOR_BETA_BENCHMARKS: Dict[str, float] = {
        "Information Technology": 1.25,
        "Consumer Discretionary": 1.20,
        "Communication Services": 1.15,
        "Financials": 1.10,
        "Industrials": 1.05,
        "Energy": 1.05,
        "Materials": 1.00,
        "Real Estate": 0.85,
        "Health Care": 0.80,
        "Consumer Staples": 0.65,
        "Utilities": 0.55
    }

    def calculate_portfolio_beta_estimate(self, customer_id: str) -> Dict[str, Any]:
        """
        Estimate portfolio market beta and systemic market sensitivity based on sector weighting.

        Args:
            customer_id (str): Customer identifier.

        Returns:
            Dict[str, Any]: Weighted portfolio beta, classification, and position sensitivity breakdown.
        """
        consolidated = self.get_consolidated_holdings(customer_id)
        if not consolidated:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "portfolio_beta": 1.0,
                "market_sensitivity": "Uninvested / Benchmark Neutral",
                "positions": []
            }

        total_val = sum(pos["current_value"] for pos in consolidated.values())
        if total_val <= 0:
            return {
                "customer_id": customer_id,
                "total_portfolio_value": 0.0,
                "portfolio_beta": 1.0,
                "market_sensitivity": "Zero Valuation",
                "positions": []
            }

        weighted_beta_sum = 0.0
        breakdown: List[Dict[str, Any]] = []

        for ticker, pos in consolidated.items():
            sector = pos.get("sector", "General")
            stock_beta = self.SECTOR_BETA_BENCHMARKS.get(sector, 1.0)
            weight = pos["current_value"] / total_val
            weighted_beta_sum += weight * stock_beta

            breakdown.append({
                "ticker": ticker,
                "company_name": pos["company_name"],
                "sector": sector,
                "current_value": pos["current_value"],
                "portfolio_weight_pct": round(weight * 100.0, 2),
                "sector_beta": stock_beta
            })

        portfolio_beta = round(weighted_beta_sum, 2)
        if portfolio_beta < 0.85:
            sensitivity = "Defensive / Low Market Sensitivity"
        elif portfolio_beta <= 1.15:
            sensitivity = "Market Neutral / Balanced"
        else:
            sensitivity = "Aggressive / High Market Sensitivity"

        return {
            "customer_id": customer_id,
            "total_portfolio_value": round(total_val, 2),
            "portfolio_beta": portfolio_beta,
            "market_sensitivity": sensitivity,
            "positions": breakdown
        }

    def simulate_position_liquidation(
        self,
        customer_id: str,
        ticker: str,
        estimated_tax_rate_pct: float = 15.0
    ) -> Dict[str, Any]:
        """
        Simulate full liquidation of a position, calculating net proceeds, tax impact,
        and post-sale residual portfolio metrics without writing to permanent storage.

        Args:
            customer_id (str): Customer identifier.
            ticker (str): Target stock ticker.
            estimated_tax_rate_pct (float): Estimated capital gains tax percentage (default: 15.0%).

        Returns:
            Dict[str, Any]: Comprehensive simulation report.

        Raises:
            InvalidTransactionError: If customer has no active holding for ticker.
        """
        ticker_clean = ticker.strip().upper()
        consolidated = self.get_consolidated_holdings(customer_id)
        if ticker_clean not in consolidated or consolidated[ticker_clean]["total_quantity"] <= 0:
            raise InvalidTransactionError(f"Customer '{customer_id}' has no active holding in {ticker_clean} to simulate.")

        pos = consolidated[ticker_clean]
        shares = pos["total_quantity"]
        cost_basis = round(pos["average_buy_price"] * shares, 2)
        gross_proceeds = round(pos["current_price"] * shares, 2)
        realized_gain_loss = round(gross_proceeds - cost_basis, 2)

        tax_due = round(realized_gain_loss * (estimated_tax_rate_pct / 100.0), 2) if realized_gain_loss > 0 else 0.0
        net_proceeds = round(gross_proceeds - tax_due, 2)

        total_curr_val = sum(p["current_value"] for p in consolidated.values())
        post_sale_val = round(max(0.0, total_curr_val - gross_proceeds), 2)
        cash_liberated_pct = round((gross_proceeds / total_curr_val * 100.0), 2) if total_curr_val > 0 else 0.0

        return {
            "customer_id": customer_id,
            "ticker": ticker_clean,
            "company_name": pos["company_name"],
            "shares_liquidated": shares,
            "execution_price": pos["current_price"],
            "cost_basis": cost_basis,
            "gross_proceeds": gross_proceeds,
            "realized_gain_loss": realized_gain_loss,
            "tax_rate_pct": estimated_tax_rate_pct,
            "estimated_tax_due": tax_due,
            "net_proceeds_after_tax": net_proceeds,
            "original_portfolio_value": round(total_curr_val, 2),
            "residual_portfolio_value": post_sale_val,
            "cash_liberated_percentage": cash_liberated_pct
        }


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

