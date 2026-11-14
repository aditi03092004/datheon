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



    def test_top_and_worst_performing_positions(self):
        """Verify extraction of highest and lowest performing positions by return percentage."""
        cid = self.manager.generate_customer_id()

        # Empty portfolio returns None
        self.assertIsNone(self.manager.get_top_performing_position(cid))
        self.assertIsNone(self.manager.get_worst_performing_position(cid))

        # Record 2 distinct transactions
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        self.manager.record_transaction(cid, "MSFT", 250.0, 1)

        holdings = self.manager.get_portfolio_for_customer(cid)
        self.assertEqual(len(holdings), 2)

        top_pos = self.manager.get_top_performing_position(cid)
        worst_pos = self.manager.get_worst_performing_position(cid)
        self.assertIsNotNone(top_pos)
        self.assertIsNotNone(worst_pos)
        self.assertIn(top_pos["Ticker"], ["AAPL", "MSFT"])
        self.assertIn(worst_pos["Ticker"], ["AAPL", "MSFT"])

    def test_unrealized_profit_and_invested_capital(self):
        """Verify calculation of total invested capital and aggregate unrealized return percentage."""
        cid = self.manager.generate_customer_id()

        # Empty portfolio has zero invested capital and return
        self.assertEqual(self.manager.get_total_invested_capital(cid), 0.0)
        self.assertEqual(self.manager.get_unrealized_profit_percentage(cid), 0.0)

        # Record a transaction: 2 shares at $100 -> $200 invested
        self.manager.record_transaction(cid, "AAPL", 100.0, 2)
        self.assertEqual(self.manager.get_total_invested_capital(cid), 200.0)
        self.assertIsInstance(self.manager.get_unrealized_profit_percentage(cid), float)

    def test_sector_company_counts_distribution(self):
        """Verify sector company counts aggregate all loaded S&P 500 companies."""
        counts = self.manager.get_sector_company_counts()
        self.assertIsInstance(counts, dict)
        self.assertGreater(len(counts), 5)
        total_companies_in_sectors = sum(counts.values())
        self.assertEqual(total_companies_in_sectors, len(self.manager.company_dataset))
        self.assertIn("Information Technology", counts)

    def test_position_risk_alerts(self):
        """Verify detection of stop-loss and take-profit threshold breaches."""
        cid = self.manager.generate_customer_id()
        # Empty customer yields empty alert lists
        empty_alerts = self.manager.get_position_risk_alerts(cid)
        self.assertEqual(empty_alerts["stop_loss_alerts"], [])
        self.assertEqual(empty_alerts["take_profit_alerts"], [])

        # Record a holding
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        # Using tight thresholds to trigger alerts deterministically
        alerts = self.manager.get_position_risk_alerts(
            cid,
            stop_loss_pct=500.0,      # Everything triggers stop-loss alert
            take_profit_pct=-500.0    # Everything triggers take-profit alert
        )
        self.assertIsInstance(alerts["stop_loss_alerts"], list)
        self.assertIsInstance(alerts["take_profit_alerts"], list)
        self.assertEqual(len(alerts["stop_loss_alerts"]), 1)
        self.assertEqual(alerts["stop_loss_alerts"][0]["ticker"], "AAPL")
        self.assertIn("action_recommended", alerts["stop_loss_alerts"][0])

    def test_customer_financial_scorecard(self):
        """Verify executive financial scorecard aggregates holdings, win ratio, and risk summary."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer scorecard
        empty_scorecard = self.manager.get_customer_financial_scorecard(cid)
        self.assertEqual(empty_scorecard["customer_id"], cid)
        self.assertTrue(empty_scorecard["is_registered"])
        self.assertEqual(empty_scorecard["total_transactions"], 0)
        self.assertEqual(empty_scorecard["active_positions_count"], 0)
        self.assertEqual(empty_scorecard["top_holding"], "None")
        self.assertEqual(empty_scorecard["position_win_ratio"], 0.0)

        # 2. Populated customer
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        self.manager.record_transaction(cid, "MSFT", 250.0, 1)

        scorecard = self.manager.get_customer_financial_scorecard(cid)
        self.assertEqual(scorecard["total_transactions"], 2)
        self.assertEqual(scorecard["active_positions_count"], 2)
        self.assertEqual(scorecard["total_invested_capital"], 550.0)
        self.assertGreater(scorecard["total_current_valuation"], 0.0)
        self.assertIn(scorecard["top_holding"], ["AAPL", "MSFT"])
        self.assertIn("risk_profile", scorecard)
        self.assertEqual(scorecard["risk_profile"]["customer_id"], cid)

    def test_rebalancing_orders_generation(self):
        """Verify target asset allocation rebalancing orders calculate buy/sell adjustments."""
        cid = self.manager.generate_customer_id()
        # Empty customer yields empty orders
        empty_orders = self.manager.get_rebalancing_orders(cid, {"Information Technology": 100.0})
        self.assertEqual(empty_orders, [])

        # Record a holding in Tech ($300 total)
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        # Target: 50% Tech, 50% Health Care
        targets = {
            "Information Technology": 50.0,
            "Health Care": 50.0
        }
        orders = self.manager.get_rebalancing_orders(cid, targets)
        self.assertEqual(len(orders), 2)

        order_map = {o["sector"]: o for o in orders}
        self.assertIn("Information Technology", order_map)
        self.assertIn("Health Care", order_map)

        # Tech is currently 100%, target is 50%, so action is SELL
        self.assertEqual(order_map["Information Technology"]["action"], "SELL")
        self.assertLess(order_map["Information Technology"]["adjustment_needed"], 0.0)

        # Health Care is currently 0%, target is 50%, so action is BUY
        self.assertEqual(order_map["Health Care"]["action"], "BUY")
        self.assertGreater(order_map["Health Care"]["adjustment_needed"], 0.0)

    def test_estimated_dividend_income(self):
        """Verify estimated dividend cash flows and effective portfolio yield calculation."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_div = self.manager.get_estimated_dividend_income(cid)
        self.assertEqual(empty_div["annual_dividend_income"], 0.0)
        self.assertEqual(empty_div["effective_portfolio_yield"], 0.0)
        self.assertEqual(empty_div["positions"], [])

        # 2. Populated customer: 2 shares of AAPL
        self.manager.record_transaction(cid, "AAPL", 150.0, 2)
        div_proj = self.manager.get_estimated_dividend_income(cid)
        self.assertGreater(div_proj["annual_dividend_income"], 0.0)
        self.assertEqual(
            div_proj["quarterly_dividend_income"],
            round(div_proj["annual_dividend_income"] / 4.0, 2)
        )
        self.assertEqual(
            div_proj["monthly_dividend_income"],
            round(div_proj["annual_dividend_income"] / 12.0, 2)
        )
        self.assertGreater(div_proj["effective_portfolio_yield"], 0.0)
        self.assertEqual(len(div_proj["positions"]), 1)
        self.assertEqual(div_proj["positions"][0]["ticker"], "AAPL")

    def test_portfolio_drawdown_risk_var(self):
        """Verify parametric Value-at-Risk scales with valuation and confidence level."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_var = self.manager.calculate_portfolio_drawdown_risk(cid)
        self.assertEqual(empty_var["total_portfolio_value"], 0.0)
        self.assertEqual(empty_var["estimated_daily_var"], 0.0)

        # 2. Populated customer
        self.manager.record_transaction(cid, "AAPL", 150.0, 4)
        var_95 = self.manager.calculate_portfolio_drawdown_risk(cid, confidence_level=0.95)
        self.assertGreater(var_95["total_portfolio_value"], 0.0)
        self.assertGreater(var_95["estimated_daily_var"], 0.0)
        self.assertGreater(var_95["estimated_monthly_var"], var_95["estimated_daily_var"])
        self.assertIn("risk_assessment", var_95)

        # 3. Higher confidence (99%) yields higher VaR than 90%
        var_90 = self.manager.calculate_portfolio_drawdown_risk(cid, confidence_level=0.90)
        var_99 = self.manager.calculate_portfolio_drawdown_risk(cid, confidence_level=0.99)
        self.assertGreater(var_99["estimated_daily_var"], var_90["estimated_daily_var"])

    def test_transactions_in_date_range(self):
        """Verify historical transactions are filterable across date intervals."""
        from datetime import datetime, timedelta
        cid = self.manager.generate_customer_id()
        self.manager.record_transaction(cid, "AAPL", 150.0, 1)

        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Range including today finds the transaction
        matching = self.manager.get_transactions_in_date_range(yesterday_str, tomorrow_str, customer_id=cid)
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["Ticker"], "AAPL")

        # Past window finds nothing
        past_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        past_end = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        empty_window = self.manager.get_transactions_in_date_range(past_start, past_end)
        self.assertEqual(len(empty_window), 0)

        # Invalid date format raises ValueError
        with self.assertRaises(ValueError):
            self.manager.get_transactions_in_date_range("invalid-date", today_str)

    def test_position_size_limits_and_trim_recommendations(self):
        """Verify position sizing limit calculations, compliance status, and trim recommendations."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_res = self.manager.calculate_position_size_limits(cid, max_allocation_pct=25.0)
        self.assertEqual(empty_res["total_portfolio_value"], 0.0)
        self.assertTrue(empty_res["is_fully_compliant"])
        self.assertEqual(empty_res["overweight_positions_count"], 0)
        self.assertEqual(empty_res["recommendations"], [])

        # 2. Add two positions: AAPL 10 shares ($960), MSFT 1 share ($250)
        self.manager.record_transaction(cid, "AAPL", 96.0, 10)
        self.manager.record_transaction(cid, "MSFT", 250.0, 1)

        # Cap at 50%: AAPL is ~79% of portfolio, so it is OVERWEIGHT
        limits_50 = self.manager.calculate_position_size_limits(cid, max_allocation_pct=50.0)
        self.assertFalse(limits_50["is_fully_compliant"])
        self.assertEqual(limits_50["overweight_positions_count"], 1)
        self.assertEqual(limits_50["compliant_positions_count"], 1)

        rec_map = {r["ticker"]: r for r in limits_50["recommendations"]}
        self.assertEqual(rec_map["AAPL"]["status"], "OVERWEIGHT")
        self.assertGreater(rec_map["AAPL"]["trim_dollar_amount"], 0.0)
        self.assertGreaterEqual(rec_map["AAPL"]["suggested_shares_to_trim"], 1)
        self.assertEqual(rec_map["MSFT"]["status"], "COMPLIANT")
        self.assertEqual(rec_map["MSFT"]["trim_dollar_amount"], 0.0)
        self.assertEqual(rec_map["MSFT"]["suggested_shares_to_trim"], 0)

        # Cap at 90%: AAPL (<90%) becomes COMPLIANT
        limits_90 = self.manager.calculate_position_size_limits(cid, max_allocation_pct=90.0)
        self.assertTrue(limits_90["is_fully_compliant"])
        self.assertEqual(limits_90["overweight_positions_count"], 0)

    def test_sharpe_ratio_estimation(self):
        """Verify Sharpe ratio estimation, excess return calculations, and risk ratings."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_sharpe = self.manager.calculate_sharpe_ratio_estimate(cid)
        self.assertEqual(empty_sharpe["sharpe_ratio"], 0.0)
        self.assertEqual(empty_sharpe["risk_adjusted_rating"], "Uninvested")

        # 2. Recorded position
        self.manager.record_transaction(cid, "AAPL", 50.0, 10)
        sharpe_res = self.manager.calculate_sharpe_ratio_estimate(cid, risk_free_rate_pct=4.0)
        self.assertGreater(sharpe_res["total_portfolio_value"], 0.0)
        self.assertIn("portfolio_return_pct", sharpe_res)
        self.assertIn("excess_return_pct", sharpe_res)
        self.assertIn("sharpe_ratio", sharpe_res)
        self.assertIn("risk_adjusted_rating", sharpe_res)

        # 3. Favorable hurdle yielding positive Sharpe
        low_rf = self.manager.calculate_sharpe_ratio_estimate(cid, risk_free_rate_pct=-20.0)
        self.assertGreater(low_rf["excess_return_pct"], 0.0)
        self.assertGreater(low_rf["sharpe_ratio"], 0.0)
        self.assertIn(low_rf["risk_adjusted_rating"], ["Good", "Excellent", "Adequate", "Moderate"])

        # 4. High hurdle yielding negative Sharpe
        high_rf = self.manager.calculate_sharpe_ratio_estimate(cid, risk_free_rate_pct=100.0)
        self.assertLess(high_rf["excess_return_pct"], 0.0)
        self.assertEqual(high_rf["risk_adjusted_rating"], "Suboptimal / High Risk")

    def test_portfolio_beta_estimate(self):
        """Verify portfolio beta calculation and market sensitivity classifications."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_beta = self.manager.calculate_portfolio_beta_estimate(cid)
        self.assertEqual(empty_beta["portfolio_beta"], 1.0)
        self.assertEqual(empty_beta["market_sensitivity"], "Uninvested / Benchmark Neutral")

        # 2. Tech stock holding (AAPL: beta 1.25)
        self.manager.record_transaction(cid, "AAPL", 150.0, 5)
        tech_beta = self.manager.calculate_portfolio_beta_estimate(cid)
        self.assertEqual(tech_beta["portfolio_beta"], 1.25)
        self.assertEqual(tech_beta["market_sensitivity"], "Aggressive / High Market Sensitivity")
        self.assertEqual(len(tech_beta["positions"]), 1)
        self.assertEqual(tech_beta["positions"][0]["sector_beta"], 1.25)

    def test_simulate_position_liquidation(self):
        """Verify position liquidation simulation arithmetic, tax calculations, and error checks."""
        from portfolio import InvalidTransactionError
        cid = self.manager.generate_customer_id()
        # 1. Error on unheld ticker
        with self.assertRaises(InvalidTransactionError):
            self.manager.simulate_position_liquidation(cid, "AAPL")

        # 2. Add position and simulate sale
        self.manager.record_transaction(cid, "AAPL", 100.0, 5)
        sim = self.manager.simulate_position_liquidation(cid, "AAPL", estimated_tax_rate_pct=20.0)
        self.assertEqual(sim["ticker"], "AAPL")
        self.assertEqual(sim["shares_liquidated"], 5)
        self.assertEqual(sim["cost_basis"], 500.0)
        self.assertGreater(sim["gross_proceeds"], 0.0)
        self.assertIn("realized_gain_loss", sim)
        self.assertIn("estimated_tax_due", sim)
        self.assertIn("net_proceeds_after_tax", sim)
        self.assertGreaterEqual(sim["cash_liberated_percentage"], 99.0)  # Only 1 holding = 100%
        self.assertEqual(sim["residual_portfolio_value"], 0.0)

    def test_treynor_ratio_estimation(self):
        """Verify Treynor ratio calculation, market beta integration, and rating labels."""
        cid = self.manager.generate_customer_id()
        # 1. Empty customer
        empty_treynor = self.manager.calculate_treynor_ratio_estimate(cid)
        self.assertEqual(empty_treynor["treynor_ratio"], 0.0)
        self.assertEqual(empty_treynor["treynor_rating"], "Uninvested")

        # 2. Add position and test with low hurdle
        self.manager.record_transaction(cid, "AAPL", 100.0, 5)
        pos_treynor = self.manager.calculate_treynor_ratio_estimate(cid, risk_free_rate_pct=-10.0)
        self.assertGreater(pos_treynor["excess_return_pct"], 0.0)
        self.assertGreater(pos_treynor["treynor_ratio"], 0.0)
        self.assertIn("portfolio_beta", pos_treynor)

        # 3. High hurdle
        neg_treynor = self.manager.calculate_treynor_ratio_estimate(cid, risk_free_rate_pct=50.0)
        self.assertLess(neg_treynor["excess_return_pct"], 0.0)
        self.assertEqual(neg_treynor["treynor_rating"], "Underperforming Risk-Free Hurdle")


if __name__ == "__main__":
    unittest.main()

