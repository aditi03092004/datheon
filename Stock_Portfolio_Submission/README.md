# Datheon Python Programming Internship – Task 2: Stock Portfolio Tracker

**Candidate Implementation & Submission**  
**Track:** Python Programming  
**Author:** Aditi Hundre  

---

## 1. Project Overview

The **Stock Portfolio Tracker** is an independent, object-oriented investment management command-line application developed for the **Datheon Python Programming Internship (Task 2)**.

The system empowers users to record stock purchases and sales, validate tickers against an authentic S&P 500 company dataset, compute investment totals, retrieve market pricing, track real-time position values with profit/loss metrics, consolidate multi-lot positions with weighted average cost basis, compute portfolio risk profiles using the Herfindahl-Hirschman Index (HHI), and query both personal customer portfolios and global transaction histories.

---

## 2. Architecture & File Structure

```text
Stock_Portfolio_Submission/
│
├── portfolio.py               # Main application: StockPortfolioManager, CLI interface, and ASCII tables
├── test_portfolio.py          # Automated test suite (Python unittest standard library - 19 tests)
├── company_dataset.csv        # S&P 500 company ticker and metadata repository (503 companies)
├── details.txt                # Customer ID persistent registry
├── portfolio_summary.csv      # Transaction and portfolio history ledger
└── README.md                  # Project documentation, execution, and evaluation guide
```

### Architectural Highlights

- **Decoupled Architecture:** Core financial logic and storage are encapsulated inside the `StockPortfolioManager` class, completely separated from terminal I/O.
- **Position Consolidation:** `get_consolidated_holdings` aggregates multi-lot purchases for identical tickers, calculating total shares, weighted average cost basis, and portfolio allocation weights.
- **Stock Sale & Realized Profit Engine:** `record_sale` supports partial or full position sales with overselling validation and realized profit/loss calculations.
- **Risk & Diversification Profiling:** `get_portfolio_risk_profile` computes the Herfindahl-Hirschman Index (HHI) to classify sector concentration and portfolio diversification.
- **Resilient Market Service:** The `MarketDataService` class attempts to fetch real-time data from `yfinance` if installed and online, and automatically falls back to deterministic standard library pricing if offline or without third-party dependencies.
- **Robust Path Resolution:** Uses `pathlib.Path(__file__).resolve().parent` to reliably locate `company_dataset.csv`, `details.txt`, and `portfolio_summary.csv` regardless of the directory from which the command is executed.
- **Structured ASCII Tables:** Dynamically formatted tables featuring clean headers and portfolio totals (Total Invested, Total Portfolio Value, Net Profit/Loss, and Return Percentage).
- **Search & Filter Capabilities:** Programmatic company keyword search and sector queries across the S&P 500 dataset.
- **Structured JSON & CSV Export:** Exporting structured, timestamped customer portfolio summaries (`export_customer_portfolio_summary` and `export_customer_csv`).

---

## 3. Financial Calculations

The application strictly implements verified financial formulas:

$$\text{Total Investment} = \text{Purchase Price} \times \text{Quantity}$$

$$\text{Current Market Value} = \text{Current Price} \times \text{Quantity}$$

$$\text{Profit or Loss} = \text{Current Market Value} - \text{Total Investment}$$

$$\text{Return Percentage} = \left(\frac{\text{Profit or Loss}}{\text{Total Investment}}\right) \times 100\%$$

$$\text{Weighted Average Cost Basis} = \frac{\sum (\text{Buy Price}_i \times \text{Quantity}_i)}{\sum \text{Quantity}_i}$$

$$\text{Realized P/L (Sale)} = (\text{Sell Price} - \text{Average Cost Basis}) \times \text{Quantity Sold}$$

$$\text{Herfindahl-Hirschman Index (HHI)} = \sum (\text{Sector Percentage Weight}_i)^2$$

---

## 4. How to Run on Windows

### Running via PowerShell

1. Open **PowerShell**.
2. Navigate to this submission directory:
   ```powershell
   cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Stock_Portfolio_Submission"
   ```
3. Run the application:
   ```powershell
   python portfolio.py
   ```

---

## 5. How to Run the Automated Test Suite

The project includes 19 comprehensive unit and integration tests covering dataset ingestion, ID uniqueness, calculation arithmetic, multi-customer portfolio isolation, sales, consolidated holdings, and risk profiling.

To run the automated tests:

```powershell
cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Stock_Portfolio_Submission"
python -m unittest test_portfolio.py -v
```

### Position Performance Ranking Analytics
The `StockPortfolioManager` includes position ranking analytics for rapid portfolio evaluation:
- **`get_top_performing_position(customer_id)`**: Identifies the single holding generating the highest percentage return on investment.
- **`get_worst_performing_position(customer_id)`**: Identifies the position with the lowest percentage return to support risk rebalancing and tax-loss evaluation.

### Capital Aggregators & Sector Company Breakdown
- **`get_total_invested_capital(customer_id)`**: Calculates the sum of all invested funds across active positions.
- **`get_unrealized_profit_percentage(customer_id)`**: Computes aggregate unrealized return percentage for an entire customer portfolio.
- **`get_sector_company_counts()`**: Tallies the total distribution of companies in the S&P 500 dataset across each economic sector.
