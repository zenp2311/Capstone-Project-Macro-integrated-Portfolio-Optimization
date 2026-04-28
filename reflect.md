# Integrated Finance Application (Capstone) — Reflections

## Project Summary
**Product:** Macro-Integrated Portfolio Optimization (Integration Pattern A)
**Tech Stack Used:** Python, Streamlit, yfinance, edgartools, PyPortfolioOpt, Plotly

## What Worked Well
- **"Show Don't Tell" methodology:** Generated immediate visual proofs of the reactive DCF models without getting bogged down in endless architecture diagrams.
- **Architectural Flow:** Extracting components and strictly passing them via Streamlit variables neatly bridged two entirely separate financial theories.

## Challenges & Learnings

### Edge Cases in Automated Valuation
Financial data structures (like Bank XBRL statements) natively break standard Unlevered Free Cash Flow calculations. 
**Lesson:** Always build graceful failure modes (catching "Data Errors") before passing values downstream.

### Pipeline Fractures
Mathematical optimizers like Markowitz mean-variance require valid matrices, meaning PyPortfolioOpt will crash spectacularly if the upstream filter layer (DCF) annihilates the complete asset pool.
**Lesson:** Stress testing the RFR slider to produce 0 survivors was crucial to discovering the mathematical dependency error. 

## Process Reflections

### What Helped
- **Validation Stage:** Actively trying to break the formulas by sliding the inputs to the extremes rather than just testing middle-of-the-road "normal" numbers.
- **AI Collaboration:** Maintaining the Pilot-in-Command structure worked flawlessly. The AI smoothly aggregated and wrote the Streamlit and Plotly logic required to display everything, enabling the human pilot to concentrate purely on the structural soundness of the CAPM, Intrinsic Value mathematics, and pipeline routing.

## Reusable Patterns

### Pipeline Integrity Failsafes
Always evaluate the subset constraint of a preceding stage *before* initializing the secondary engine: `if len(survivors) >= 2:`

---
*Captured using DRIVER*
