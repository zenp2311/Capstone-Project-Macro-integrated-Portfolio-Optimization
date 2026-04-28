# Integrated Valuation & Optimization Pipeline Research

## Existing Foundations
- **Project 1 (DCF Valuation Engine):** Custom DCF logic using `edgartools`. Provides Intrinsic Value calculation and interactive Plotly heatmap based on CAPM WACC computation.
- **Project 2 (Portfolio Optimizer):** Utilizes `PyPortfolioOpt` and `yfinance` to parse expected returns and covariance matrix, outputting an optimal weighting and an Efficient Frontier. 
- **Industry Standard Stack:** yfinance / edgartools / PyPortfolioOpt / Streamlit is a proven, robust data & calculation layer structure.

## The Integration Challenge ("Pattern A")
The primary complexity here isn't just sticking two pages together; it is establishing a **reactive data flow** from a global macro parameter to final asset weights.
1. **Macro Stress State:** A custom Streamlit Sidebar widget controlling the base "Risk-Free Rate".
2. **DCF Engine (The Filter):** As the Risk-Free Rate goes up, WACC goes up, causing Intrinsic Values to drop. The screener actively filters out names whose Intrinsic Value falls below the current market price (`Margin of Safety <= 0`).
3. **Portfolio Optimizer (The Allocator):** Re-runs Max Sharpe / Min Volatility *only* on the survivors. If the Risk-Free Rate spikes too high, fewer assets survive the DCF filter, changing the Efficient Frontier dynamically.

## Cross-Component Sensitivity
By placing the Risk-Free Rate at the app's root level (Streamlit `st.session_state` or global sidebar), we create a unidirectional reactive loop:
`Macro Variables -> Firm Valuation (DCF) -> Asset Universe Reduction -> Portfolio Optimization (MPT)`
