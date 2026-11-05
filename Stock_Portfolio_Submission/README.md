# Datheon Python Programming Internship – Task 2: Stock Portfolio Tracker

**Candidate Implementation & Submission**  
**Track:** Python Programming  
**Author:** Aditi Hundre  

---

## 1. Project Overview

The **Stock Portfolio Tracker** is an independent, object-oriented investment management command-line application developed for the **Datheon Python Programming Internship (Task 2)**.

The system empowers users to record stock purchases, validate tickers against an authentic S&P 500 company dataset, compute investment totals, retrieve market pricing, track real-time position values with profit/loss metrics, and query both personal customer portfolios and global transaction histories.

---

## 2. Architecture & File Structure

```text
Stock_Portfolio_Submission/
│
├── portfolio.py               # Main application: StockPortfolioManager, CLI interface, and ASCII tables
├── test_portfolio.py          # Automated test suite (Python unittest standard library)
├── company_dataset.csv        # S&P 500 company ticker and metadata repository (503 companies)
├── details.txt                # Customer ID persistent registry
├── portfolio_summary.csv      # Transaction and portfolio history ledger
└── README.md                  # Project documentation, execution, and evaluation guide
```

### Architectural Highlights

- **Decoupled Architecture:** Core financial logic and storage are encapsulated inside the `StockPortfolioManager` class, completely separated from terminal I/O.
- **Resilient Market Service:** The `MarketDataService` class attempts to fetch real-time data from `yfinance` if installed and online, and automatically falls back to deterministic standard library pricing if offline or without third-party dependencies.
- **Robust Path Resolution:** Uses `pathlib.Path(__file__).resolve().parent` to reliably locate `company_dataset.csv`, `details.txt`, and `portfolio_summary.csv` regardless of the directory from which the command is executed.
- **Structured ASCII Tables:** Replaces unstructured print statements with dynamically formatted tables featuring clean headers and portfolio totals (Total Invested, Total Portfolio Value, Net Profit/Loss, and Return Percentage).
- **Search & Filter Capabilities:** Includes programmatic company keyword search and sector queries across the S&P 500 dataset.
- **Structured JSON Export:** Supports exporting structured, timestamped customer portfolio summaries (`export_customer_portfolio_summary`).
- **Automated Test Coverage:** Includes unit and integration tests covering dataset ingestion, ID uniqueness, calculation arithmetic, and multi-customer portfolio isolation.

---

## 3. Financial Calculations
- **Rebalancing Suggestions:** Automatically flags single-sector concentration exceeding risk thresholds (default 40%).
- **Ticker History Search:** Fast indexing and filtering of historical purchases by ticker.
- **Sector Diversification Analysis:** Aggregates holdings by GICS sectors to compute diversification percentages and render ASCII visual bar charts.

The application strictly implements the required financial formulas:

$$\text{Total Investment} = \text{Purchase Price} \times \text{Quantity}$$

$$\text{Current Market Value} = \text{Current Price} \times \text{Quantity}$$

$$\text{Profit or Loss} = \text{Current Market Value} - \text{Total Investment}$$

$$\text{Return Percentage} = \left(\frac{\text{Profit or Loss}}{\text{Total Investment}}\right) \times 100\%$$

---

## 4. Key Enhancements Over the Reference Project

| Dimension | Reference Implementation (`Task_2`) | Our Submission (`Stock_Portfolio_Submission`) |
| :--- | :--- | :--- |
| **Code Structure** | Global procedural scripts with fragile global state | Object-oriented (`StockPortfolioManager` & `MarketDataService`) |
| **Path Handling** | Hardcoded relative paths (crashes outside folder) | Dynamic resolution (`Path(__file__).resolve().parent`) |
| **Data Mismatch** | Column name discrepancies (`profit/loss` vs `Profit_Loss`) | Consistent schema with ISO timestamps and formatted decimals |
| **Dependency Resilience** | Crashes on startup if `yfinance` is uninstalled | Graceful fallback ensuring 100% standard library compatibility |
| **Table Formatting** | Raw unstructured dictionary/print dumps | Dynamic ASCII tables with alignment and portfolio summaries |
| **Automated Testing** | None | 6 comprehensive automated test suites using `unittest` |

---

## 5. How to Run on Windows

### Prerequisites
- Python 3.6 or newer installed (verified on Python 3.14.6).
- *(Optional)* `yfinance` library for live Yahoo Finance market quotes:
  ```bash
  pip install yfinance
  ```

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

### Running via Command Prompt (CMD)

1. Open **Command Prompt**.
2. Navigate to this submission directory:
   ```cmd
   cd /d "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Stock_Portfolio_Submission"
   ```
3. Run the application:
   ```cmd
   python portfolio.py
   ```

---

## 6. How to Run the Automated Test Suite

To execute the unit and integration tests:

```powershell
cd "c:\Users\Aditi hundre\Downloads\Datheon_Python_Programming_Internship-main\Hangman_Reference\Stock_Portfolio_Submission"
python -m unittest test_portfolio.py -v
```

Expected output: All test cases pass with status `OK`.

---

## 7. Demonstration Guide for Internship Evaluators

Follow this sequence during an evaluation or interview to demonstrate all capabilities:

1. **Demonstrate Automated Testing:**
   - Execute `python -m unittest test_portfolio.py -v` to prove that dataset loading, ID generation, calculations, and isolation pass automated verification.
2. **Launch Application & Main Menu:**
   - Run `python portfolio.py`. Show the 4-option menu.
3. **Record a Transaction (Option 1):**
   - Generate a new Customer ID or enter an existing one.
   - Enter a valid ticker (e.g., `AAPL` or `MSFT`) and show that the system validates it against `company_dataset.csv` and reveals the company name and sector.
   - Enter purchase price and quantity.
   - Point out the confirmation screen displaying Purchase Investment, Market Price, Current Value, and Profit/Loss.
4. **View Customer Portfolio (Option 2):**
   - Enter the Customer ID used in Step 3.
   - Point out the formatted table showing holdings, individual positions, and the aggregated summary at the bottom (Total Invested, Total Portfolio Value, Net Profit/Loss, and Net Return %).
5. **View Transaction History (Option 3):**
   - Select Option 3 to view the complete historical ledger of all transactions stored in `portfolio_summary.csv`.
6. **Exit Gracefully (Option 4):**
   - Select Option 4 to exit with a polite closing message.

