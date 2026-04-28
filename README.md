# Macro-Integrated Portfolio Optimization

## Integration Pattern A: Value-Based Portfolio
This Capstone project unites absolute fundamental valuation (Discounted Cash Flow) with relative allocation optimization (Modern Portfolio Theory) into a single reactive pipeline. It strictly filters an investment universe based on dynamic Margin of Safety assumptions, cascading only the surviving "Undervalued" assets into PyPortfolioOpt to generate a constrained Maximum Sharpe Efficient Frontier.

## Running Locally
Ensure you have the required dependencies installed (e.g., `streamlit`, `yfinance`, `edgartools`, `PyPortfolioOpt`, `plotly`).
1. Navigate to the project directory: `cd Capstone`
2. Run the application: `streamlit run app.py`

## The DRIVER Workflow Summary
This application was rapidly prototyped and structurally validated using the **DRIVER** methodology:
Link to repository: https://github.com/CinderZhang/driver-plugin
### DEFINE & REPRESENT
Outlined the intent to merge two standalone Python projects (Project 1: DCF Valuation + Project 2: Portfolio Optimization) by tying them together with a global Macro UI. Conceptualized "Cross-Component Sensitivity" where the global Risk-Free Rate natively dictates both base WACC and optimal covariance weighting. This was codified in a strict 4-step buildable roadmap.

### IMPLEMENT
Leveraged "Show Don't Tell" utilizing Streamlit's reactive loop. The WACC formulas were hardwired directly to the Streamlit layout without manual execution buttons. PyPortfolioOpt and Plotly were seamlessly piped to ingest only the 'Undervalued' survivors.

### VALIDATE
Pilots never trust one instrument. We rigorously stress-tested the application boundaries:
1. **The RFR Stress Test:** Ratcheting the Risk-Free Rate down to 1% successfully expanded the survivor pool (dynamically flipping names like GOOGL to Undervalued).
2. **The "0 Survivors" Edge Case:** Escalating the RFR too aggressively compressed intrinsic valuations until 0 stocks survived the screen.
3. **The Data Error Trap:** Validating against banking stocks (JPM). Because financial institutions utilize non-standard cash flow statements, the `edgartools` DCF calculation caught isolated "Data Errors," gracefully excluding the stock over breaking the application.

### EVOLVE
Based on Validation findings, we fortified the code to gracefully catch and isolate XBRL extraction errors. Critically, we implemented a robust safety valve (`len(survivors) >= 2`) prior to optimization, preventing PyPortfolioOpt from crashing on a rank-deficient covariance matrix when the Margin of Safety filter proved too draconian to yield sufficient assets.

## AI Usage Disclosure
This project employed a deliberate, structured division of labor between human domain expertise and artificial intelligence:
- **Pilot-in-Command (Human):** Domain expert responsible for defining the quantitative financial logic, establishing the CAPM WACC equations, structuring the "Integration Pattern A" architecture, validating the exact mathematical integrity of the cross-component sensitivity, and discovering edge cases.
- **Cognition Mate (AI):** Executed the heavy lifting of UI assembly, Plotly chart syntax, boilerplate caching framework (handling `yfinance` multi-indexing), and real-time coding iteration driven strictly by the Pilot's feedback loop.
