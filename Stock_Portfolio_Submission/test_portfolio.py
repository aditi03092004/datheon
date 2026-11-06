"""
Automated Test Suite for Stock Portfolio Tracker
Datheon Python Programming Internship - Task 2

Uses Python's standard unittest library to test dataset ingestion,
customer ID generation, transaction arithmetic, portfolio queries, and persistence.
"""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from portfolio import (
    InvalidTransactionError,
    MarketDataService,
    PortfolioError,
    StockPortfolioManager,
)


class TestStockPortfolioTracker(unittest.TestCase):
    """Integration and unit test suite for the Stock Portfolio Tracker."""

    def setUp(self):
        """Set up an isolated temporary workspace for testing."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_base = Path(__file__).resolve().parent

        # Copy original company_dataset.csv to temporary test workspace
        source_dataset = self.original_base / "company_dataset.csv"
        self.assertTrue(source_dataset.exists(), "Source company_dataset.csv must exist.")
        shutil.copy(source_dataset, self.test_dir / "company_dataset.csv")

        # Initialize manager pointing to isolated test directory
        self.manager = StockPortfolioManager(base_directory=self.test_dir)

    def tearDown(self):
        """Clean up temporary test workspace."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_company_dataset_loading(self):
        """Verify that S&P 500 company records are properly loaded and searchable."""
        self.assertGreater(len(self.manager.company_dataset), 400, "Should load over 400 S&P 500 companies.")

        # Test common valid tickers
        for ticker in ["AAPL", "MSFT", "GOOGL", "MMM", "AMZN"]:
            info = self.manager.validate_ticker(ticker)
            self.assertIsNotNone(info, f"Ticker '{ticker}' should be present in dataset.")
            self.assertIn("name", info)
            self.assertIn("sector", info)

        # Test case-insensitivity
        info_lower = self.manager.validate_ticker("aapl")
        self.assertIsNotNone(info_lower)

        # Test non-existent ticker
        self.assertIsNone(self.manager.validate_ticker("NONEXISTENT_XYZ"))

    def test_search_companies_and_sectors(self):
        """Verify keyword search and sector filtering return accurate company matches."""
        # Search by ticker prefix
        results_ticker = self.manager.search_companies("AAP")
        tickers_found = [r[0] for r in results_ticker]
        self.assertIn("AAPL", tickers_found)

        # Search by company name
        results_name = self.manager.search_companies("Microsoft")
        self.assertTrue(any(r[0] == "MSFT" for r in results_name))

        # Search with blank string
        self.assertEqual(self.manager.search_companies(""), [])

        # Filter by sector
        tech_companies = self.manager.get_companies_by_sector("Information Technology")
        self.assertGreater(len(tech_companies), 10)
        tech_tickers = [t[0] for t in tech_companies]
        self.assertIn("AAPL", tech_tickers)
        self.assertIn("MSFT", tech_tickers)

    def test_customer_id_generation_and_uniqueness(self):
        """Verify customer IDs are generated with proper prefix, format, and uniqueness."""
        generated_ids = set()
        for _ in range(50):
            cid = self.manager.generate_customer_id()
            self.assertTrue(cid.startswith("STOCK_2026_"), f"ID '{cid}' should start with 'STOCK_2026_'.")
            self.assertNotIn(cid, generated_ids, f"ID '{cid}' was duplicated.")
            generated_ids.add(cid)
            self.assertTrue(self.manager.validate_customer_id(cid))

        # Check persistence in details.txt
        with open(self.test_dir / "details.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 50)

    def test_record_valid_transaction(self):
        """Verify transaction calculations: Investment, Current Value, and Profit/Loss."""
        cid = self.manager.generate_customer_id()
        buy_price = 150.0
        quantity = 10

        record = self.manager.record_transaction(
            customer_id=cid,
            ticker="AAPL",
            buy_price=buy_price,
            quantity=quantity
        )

        # Arithmetic assertions
        self.assertEqual(record["Customer_id"], cid)
        self.assertEqual(record["Ticker"], "AAPL")
        self.assertEqual(record["Quantity"], 10)
        self.assertEqual(record["Buy_price"], 150.0)
        self.assertEqual(record["Investment"], 1500.0)
        self.assertGreater(record["Current_price"], 0.0)
        self.assertEqual(record["Current_value"], round(record["Current_price"] * 10, 2))
        self.assertEqual(record["Profit_Loss"], round(record["Current_value"] - 1500.0, 2))

        # Verify CSV storage
        holdings = self.manager.get_portfolio_for_customer(cid)
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["Ticker"], "AAPL")
        self.assertEqual(holdings[0]["Investment"], 1500.0)

    def test_invalid_transaction_inputs(self):
        """Verify invalid purchase price and quantity raise ValueErrors without saving."""
        cid = self.manager.generate_customer_id()

        # Zero or negative price
        with self.assertRaises(ValueError):
            self.manager.record_transaction(cid, "MSFT", buy_price=0.0, quantity=5)

        with self.assertRaises(ValueError):
            self.manager.record_transaction(cid, "MSFT", buy_price=-25.0, quantity=5)

        # Zero or negative quantity
        with self.assertRaises(ValueError):
            self.manager.record_transaction(cid, "MSFT", buy_price=100.0, quantity=0)

        with self.assertRaises(ValueError):
            self.manager.record_transaction(cid, "MSFT", buy_price=100.0, quantity=-2)

    def test_custom_exception_inheritance(self):
        """Verify InvalidTransactionError inherits from both PortfolioError and ValueError."""
        cid = self.manager.generate_customer_id()
        with self.assertRaises(InvalidTransactionError):
            self.manager.record_transaction(cid, "MSFT", buy_price=-50.0, quantity=2)

        with self.assertRaises(PortfolioError):
            self.manager.record_transaction(cid, "MSFT", buy_price=100.0, quantity=-1)

    def test_multi_customer_portfolio_isolation(self):
        """Verify that customer portfolios remain strictly separated."""
        cid_alice = self.manager.generate_customer_id()
        cid_bob = self.manager.generate_customer_id()

        self.manager.record_transaction(cid_alice, "AAPL", 150.0, 5)
        self.manager.record_transaction(cid_alice, "GOOGL", 120.0, 2)
        self.manager.record_transaction(cid_bob, "MSFT", 300.0, 1)

        alice_portfolio = self.manager.get_portfolio_for_customer(cid_alice)
        bob_portfolio = self.manager.get_portfolio_for_customer(cid_bob)
        all_transactions = self.manager.get_all_transactions()

        self.assertEqual(len(alice_portfolio), 2)
        self.assertEqual(len(bob_portfolio), 1)
        self.assertEqual(len(all_transactions), 3)

        alice_tickers = {h["Ticker"] for h in alice_portfolio}
        self.assertEqual(alice_tickers, {"AAPL", "GOOGL"})

    def test_export_customer_portfolio_summary(self):
        """Verify exporting portfolio summary creates a valid structured JSON file."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "MSFT", 250.0, 4)
        export_file = self.test_dir / "msft_report.json"

        data = self.manager.export_customer_portfolio_summary(cid, export_file)
        self.assertTrue(export_file.exists())
        self.assertEqual(data["customer_id"], cid)
        self.assertEqual(data["total_positions"], 1)
        self.assertEqual(data["total_invested"], 1000.0)

        # Verify disk contents match
        with open(export_file, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertEqual(disk_data["customer_id"], cid)
        self.assertEqual(len(disk_data["positions"]), 1)

    def test_market_data_service_resilience(self):
        """Verify market service returns positive numerical values without throwing errors."""
        service = MarketDataService()
        price, source = service.get_current_price("AAPL", fallback_reference_price=150.0)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0.0)
        self.assertIsInstance(source, str)


    def test_sector_allocation(self):
        """Verify sector allocation correctly aggregates invested amounts and percentages."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 100.0, 1)
        self.manager.record_transaction(cid, "MSFT", 100.0, 1)

        alloc = self.manager.get_sector_allocation(cid)
        self.assertIn("Information Technology", alloc)
        self.assertEqual(alloc["Information Technology"]["invested"], 200.0)
        self.assertEqual(alloc["Information Technology"]["percentage"], 100.0)


    def test_validate_and_repair_storage(self):
        """Verify storage repair recovers valid entries and filters truncated rows."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        with open(self.manager.summary_file, "a", encoding="utf-8") as f:
            f.write("corrupted_line_without_columns\n")

        repaired_count = self.manager.validate_and_repair_storage()
        self.assertGreaterEqual(repaired_count, 1)
        holdings = self.manager.get_portfolio_for_customer(cid)
        self.assertEqual(len(holdings), 1)


    def test_profitable_and_losing_filters(self):
        """Verify filtering of profitable vs losing holdings."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 150.0, 1)
        profitable = self.manager.get_profitable_positions(cid)
        losing = self.manager.get_losing_positions(cid)
        self.assertEqual(len(profitable) + len(losing), 1)


    def test_rebalancing_suggestions(self):
        """Verify portfolio concentration alerts trigger when sector allocation exceeds threshold."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 100.0, 1)  # 100% Tech

        alerts = self.manager.get_rebalancing_suggestions(cid, max_sector_pct=40.0)
        self.assertEqual(len(alerts), 1)
        self.assertIn("Concentration alert: Information Technology", alerts[0])

        # Balanced portfolio under 100% threshold
        no_alerts = self.manager.get_rebalancing_suggestions(cid, max_sector_pct=100.0)
        self.assertEqual(len(no_alerts), 0)


    def test_find_transactions_by_ticker(self):
        """Verify historical transactions are filterable by specific ticker symbol."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 150.0, 1)
        self.manager.record_transaction(cid, "MSFT", 250.0, 1)

        aapl_txs = self.manager.find_transactions_by_ticker("AAPL")
        self.assertEqual(len(aapl_txs), 1)
        self.assertEqual(aapl_txs[0]["Ticker"], "AAPL")

        # Case-insensitive
        aapl_lower = self.manager.find_transactions_by_ticker("aapl")
        self.assertEqual(len(aapl_lower), 1)


    def test_weighted_return_percentage(self):
        """Verify portfolio weighted average return on invested capital."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 100.0, 1)
        w_ret = self.manager.get_weighted_return_percentage(cid)
        self.assertIsInstance(w_ret, float)


    def test_export_customer_csv(self):
        """Verify exporting filtered customer holdings to a dedicated CSV file."""
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 150.0, 1)
        csv_path = self.test_dir / "customer_export.csv"
        count = self.manager.export_customer_csv(cid, csv_path)
        self.assertEqual(count, 1)
        self.assertTrue(csv_path.exists())

    def test_consolidated_holdings_and_cost_basis(self):
        """Verify consolidation across multiple purchase lots of the same ticker."""
        cid = self.manager.generate_customer_id()
        # Empty customer
        self.assertEqual(self.manager.get_consolidated_holdings(cid), {})

        # Lot 1: 10 shares @ $100 = $1,000
        self.manager.record_transaction(cid, "MSFT", 100.0, 10)
        # Lot 2: 10 shares @ $200 = $2,000
        self.manager.record_transaction(cid, "MSFT", 200.0, 10)
        # Another stock: 5 shares @ $150 = $750
        self.manager.record_transaction(cid, "AAPL", 150.0, 5)

        consolidated = self.manager.get_consolidated_holdings(cid)
        self.assertEqual(len(consolidated), 2)
        self.assertIn("MSFT", consolidated)
        self.assertIn("AAPL", consolidated)

        msft = consolidated["MSFT"]
        self.assertEqual(msft["total_quantity"], 20)
        self.assertEqual(msft["total_invested"], 3000.0)
        self.assertEqual(msft["average_buy_price"], 150.0)
        self.assertEqual(msft["sector"], "Information Technology")

        # Portfolio weights sum close to 100%
        total_weight = sum(pos["portfolio_weight"] for pos in consolidated.values())
        self.assertAlmostEqual(total_weight, 100.0, delta=0.5)

    def test_record_sale_and_realized_profit(self):
        """Verify selling shares updates holdings and computes realized profit accurately."""
        cid = self.manager.generate_customer_id()
        # Buy 10 shares @ $150
        self.manager.record_transaction(cid, "AAPL", 150.0, 10)

        # 1. Partial sale of 4 shares @ $180
        sale = self.manager.record_sale(cid, "AAPL", sell_price=180.0, quantity=4)
        self.assertEqual(sale["Quantity"], 4)
        self.assertEqual(sale["Proceeds"], 720.0)
        self.assertEqual(sale["Cost_Basis"], 600.0)
        self.assertEqual(sale["Realized_Profit_Loss"], 120.0)
        self.assertEqual(sale["Return_Percentage"], 20.0)

        # Active holdings should now show 6 shares
        holdings = self.manager.get_consolidated_holdings(cid)
        self.assertEqual(holdings["AAPL"]["total_quantity"], 6)

        # 2. Oversell attempt (requesting 10 when 6 remain)
        with self.assertRaises(InvalidTransactionError):
            self.manager.record_sale(cid, "AAPL", sell_price=180.0, quantity=10)

        # 3. Selling unowned ticker
        with self.assertRaises(InvalidTransactionError):
            self.manager.record_sale(cid, "TSLA", sell_price=200.0, quantity=1)

        # 4. Invalid prices / quantities
        with self.assertRaises(InvalidTransactionError):
            self.manager.record_sale(cid, "AAPL", sell_price=-10.0, quantity=1)
        with self.assertRaises(InvalidTransactionError):
            self.manager.record_sale(cid, "AAPL", sell_price=100.0, quantity=0)

        # 5. Sell remaining 6 shares: position closes completely
        self.manager.record_sale(cid, "AAPL", sell_price=150.0, quantity=6)
        active_after = self.manager.get_consolidated_holdings(cid)
        self.assertNotIn("AAPL", active_after)

    def test_portfolio_risk_profiling(self):
        """Verify risk profiling, Herfindahl index calculation, and diversification classification."""
        # 1. Uninvested portfolio
        cid_empty = self.manager.generate_customer_id()
        risk_empty = self.manager.get_portfolio_risk_profile(cid_empty)
        self.assertEqual(risk_empty["total_sectors"], 0)
        self.assertEqual(risk_empty["risk_level"], "Uninvested / Empty")
        self.assertFalse(risk_empty["is_diversified"])

        # 2. Concentrated portfolio (100% in Information Technology)
        cid_conc = self.manager.generate_customer_id()
        self.manager.record_transaction(cid_conc, "AAPL", 150.0, 2)
        self.manager.record_transaction(cid_conc, "MSFT", 250.0, 1)

        risk_conc = self.manager.get_portfolio_risk_profile(cid_conc)
        self.assertEqual(risk_conc["total_sectors"], 1)
        self.assertEqual(risk_conc["top_sector"], "Information Technology")
        self.assertEqual(risk_conc["top_sector_weight"], 100.0)
        self.assertEqual(risk_conc["herfindahl_index"], 10000.0)
        self.assertEqual(risk_conc["risk_level"], "High Concentration / Concentrated Risk")
        self.assertFalse(risk_conc["is_diversified"])

        # 3. Well-diversified portfolio across 4 sectors (25% each)
        cid_div = self.manager.generate_customer_id()
        self.manager.record_transaction(cid_div, "AAPL", 100.0, 1)  # Tech ($100)
        self.manager.record_transaction(cid_div, "JNJ", 100.0, 1)   # Health Care ($100)
        self.manager.record_transaction(cid_div, "JPM", 100.0, 1)   # Financials ($100)
        self.manager.record_transaction(cid_div, "XOM", 100.0, 1)   # Energy ($100)

        risk_div = self.manager.get_portfolio_risk_profile(cid_div)
        self.assertEqual(risk_div["total_sectors"], 4)
        self.assertEqual(risk_div["top_sector_weight"], 25.0)
        self.assertEqual(risk_div["herfindahl_index"], 2500.0)
        self.assertTrue(risk_div["is_diversified"])


if __name__ == "__main__":
    unittest.main()

