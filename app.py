import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier
from edgar import set_identity, Company

st.set_page_config(page_title="Macro-Integrated Portfolio Optimization", layout="wide")

# Set identity for edgartools
try:
    set_identity("student@purdue.edu") 
except:
    pass

# ==========================================
# MILESTONE 1: Global Macro UI (Sidebar)
# ==========================================
st.sidebar.header("Global Macro Inputs")
default_tickers = "AAPL, MSFT, GOOGL, NVDA, META"
tickers_input = st.sidebar.text_input("Enter Tickers (comma-separated)", value=default_tickers)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

risk_free_rate = st.sidebar.slider("Global Risk-Free Rate (%)", min_value=1.0, max_value=10.0, value=4.5, step=0.1) / 100
market_risk_premium = st.sidebar.slider("Market Risk Premium (%)", min_value=1.0, max_value=10.0, value=5.5, step=0.1) / 100
max_weight = st.sidebar.slider("Max Weight per Stock (%)", min_value=5, max_value=100, value=30, step=1) / 100

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Current RFR:** {risk_free_rate*100:.1f}%\n**Current MRP:** {market_risk_premium*100:.1f}%")


# ==========================================
# MILESTONE 2: DCF Filter Logic
# ==========================================
st.title("Macro-Integrated Portfolio Optimization")
st.subheader("Macro UI & Dynamic Valuation Screen")

# We cache fundamental data strictly based on ticker. 
# Changing RFR/MRP sliders won't re-trigger slow SEC downloads!
@st.cache_data
def fetch_data(tk):
    out = {}
    
    # 1. edgartools fetching (as required)
    try:
        company = Company(tk)
        ten_ks = company.get_filings(form="10-K")
        if ten_ks:
            facts = company.get_facts()
            if facts:
                df = facts.to_dataframe()
                df_annual = df[df['fiscal_period'] == 'FY']
                if df_annual.empty:
                     df_annual = df
                latest_year = df_annual['fiscal_year'].max()
                df_latest = df_annual[df_annual['fiscal_year'] == latest_year]
                
                def get_val(concept_names):
                    for name in concept_names:
                        try:
                            cd = df_latest[df_latest['concept'] == name]
                            if not cd.empty:
                                return cd.sort_values(by='period_end', ascending=False).iloc[0]['value']
                        except: pass
                    return None
                
                out['ocf'] = get_val(["us-gaap:NetCashProvidedByUsedInOperatingActivities"]) or 0
                out['capex'] = abs(get_val(["us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"]) or 0)
                out['total_debt'] = get_val(["us-gaap:LongTermDebt", "us-gaap:DebtAndCapitalLeaseObligations"]) or 0
                out['shares_out'] = get_val(["dei:EntityCommonStockSharesOutstanding", "us-gaap:CommonStockSharesOutstanding"]) or 0
    except Exception as e: 
        print(f"Edgar Error for {tk}:", e)
    
    # 2. yfinance fetching (Prices, Betas, and fallbacks)
    try:
        yft = yf.Ticker(tk)
        info = yft.info
        out['current_price'] = info.get('currentPrice', info.get('regularMarketPrice', 0))
        out['beta'] = info.get('beta', 1.0)
        
        # Fallbacks to yfinance if SEC facts failed
        if not out.get('shares_out'):
            out['shares_out'] = info.get('sharesOutstanding', 0)
        if not out.get('total_debt'):
            out['total_debt'] = info.get('totalDebt', 0)
        if not out.get('ocf'):
            try:
                out['ocf'] = yft.cashflow.loc['Operating Cash Flow'].iloc[0]
            except: pass
        if not out.get('capex'):
            try:
                out['capex'] = abs(yft.cashflow.loc['Capital Expenditure'].iloc[0])
            except: pass
    except Exception as e:
        print(f"YFinance Error for {tk}:", e)
        
    return out

def project_ufcf(base, init, term, yrs=10):
    cf, cur = [], base
    for y in range(1, yrs+1):
        rate = init if y<=5 else init - ((init-term)/5)*(y-5)
        cur *= (1+rate)
        cf.append(cur)
    return cf

# Live rendering flow
results = []
loading_placeholder = st.empty()

if len(tickers) > 0:
    with loading_placeholder.container():
        st.info("Fetching fundamental data and caching it... (This may take roughly 2-5 seconds per new ticker due to SEC EDGAR limits)")

    for tk in tickers:
        d = fetch_data(tk)
        if not d or not d.get('current_price'): continue
        
        # === Cross-Component Sensitivity Logic ===
        # WACC binds natively to the RFR and MRP sidebar sliders!
        wacc = risk_free_rate + (d.get('beta', 1.0) * market_risk_premium)
        if wacc <= 0.025: wacc = 0.03 # Failsafe
        
        ocf, capex, shares, debt = d.get('ocf',0), d.get('capex',0), d.get('shares_out',0), d.get('total_debt',0)
        base_fcf = ocf - capex
        
        if base_fcf > 0 and shares > 0:
            cf = project_ufcf(base_fcf, 0.10, 0.025)
            pv = sum([c/((1+wacc)**i) for i, c in enumerate(cf, 1)])
            tv = (cf[-1]*(1+0.025)) / max((wacc - 0.025), 0.001)
            pv_tv = tv / ((1+wacc)**10)
            
            eq_val = pv + pv_tv - debt
            iv = eq_val / shares
            price = d['current_price']
            mos = (iv - price) / price if price > 0 else 0
            status = "Undervalued" if mos > 0 else "Overvalued"
        else:
            iv, mos, price, status = 0, 0, d.get('current_price', 0), "Data Error"
        
        results.append({
            "Ticker": tk,
            "Price": price,
            "Intrinsic Value": iv,
            "WACC (%)": wacc * 100,
            "Margin of Safety (%)": mos * 100,
            "Status": status
        })

    loading_placeholder.empty()

    if results:
        df = pd.DataFrame(results)
        
        # Format for clean display
        df_display = df.copy()
        df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:,.2f}")
        df_display['Intrinsic Value'] = df_display['Intrinsic Value'].apply(lambda x: f"${x:,.2f}")
        df_display['WACC (%)'] = df_display['WACC (%)'].apply(lambda x: f"{x:,.2f}%")
        df_display['Margin of Safety (%)'] = df_display['Margin of Safety (%)'].apply(lambda x: f"{x:,.2f}%")
        
        # Apply strict conditional coloring
        def apply_color(val):
            color = '#00FF00' if val == 'Undervalued' else '#FF0000'
            return f'color: {color}'
            
        st.dataframe(df_display.style.map(apply_color, subset=['Status']))
        
        # Extract surviving universe
        survivors = df[df['Status'] == 'Undervalued']['Ticker'].tolist()
        
        st.markdown("---")
        if survivors:
            st.success(f"### Valuation Filter Complete\n**Survivors ({len(survivors)}):** {', '.join(survivors)}\n\nThese assets survived the cross-component WACC stress test and are ready to be passed to PyPortfolioOpt for Milestone 3.")
        else:
            st.error("### Valuation Filter Complete\nNo stocks survived! Try lowering the global Risk-Free Rate or selecting different tickers.")
        
        st.session_state['survivors'] = survivors

# ==========================================
# MILESTONE 3 & 4: Portfolio Optimizer & Vis
# ==========================================
st.markdown("---")
st.subheader("Portfolio Optimization & Efficient Frontier")

# Cross-component logic: we only pull survivors from the session state if they exist
survivors = st.session_state.get('survivors', [])

if len(survivors) < 2:
    st.warning(f"⚠️ Not enough undervalued assets to optimize a portfolio. We need at least 2, but only {len(survivors)} survived the DCF WACC screen.")
else:
    with st.spinner(f"Fetching 3-year historical data for {len(survivors)} survivors..."):
        try:
            # Handle MultiIndex for multiple tickers
            data = yf.download(survivors, period="3y", progress=False)
            
            # Yfinance structurally returns MultiIndex (Price, Ticker) when list > 1
            if isinstance(data.columns, pd.MultiIndex):
                prices = data.xs('Close', level=0, axis=1) if 'Close' in data.columns.levels[0] else data.xs('Adj Close', level=0, axis=1)
            else:
                prices = data[['Close']] if 'Close' in data.columns else data[['Adj Close']]
            
            # Fill missing data
            prices = prices.ffill().dropna()

            # PyPortfolioOpt Calculations
            mu = expected_returns.mean_historical_return(prices)
            S = risk_models.sample_cov(prices)
            
            # Max Sharpe Optimization
            ef = EfficientFrontier(mu, S, weight_bounds=(0.0, max_weight))
            raw_weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            ret_ms, vol_ms, sharpe_ms = ef.portfolio_performance()
            
            # Efficient Frontier Curve (Target Returns)
            target_returns = np.linspace(mu.min(), mu.max(), 50)
            vols, rets = [], []
            for target in target_returns:
                try:
                    ef_target = EfficientFrontier(mu, S, weight_bounds=(0.0, max_weight))
                    ef_target.efficient_return(target)
                    pf_ret, pf_vol, pf_sharpe = ef_target.portfolio_performance()
                    if pf_ret >= target: # Ensure solved successfully
                        rets.append(pf_ret)
                        vols.append(pf_vol)
                except:
                    pass
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("### Optimal Weights (Max Sharpe)")
                weight_df = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Weight'])
                weight_df = weight_df[weight_df['Weight'] > 0.001].sort_values(by='Weight', ascending=False)
                
                # Plotly Pie chart for weights
                fig_weights = go.Figure(data=[go.Pie(labels=weight_df.index, values=weight_df['Weight'], hole=.4)])
                fig_weights.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_weights, use_container_width=True)
                
                st.metric("Expected Annual Return", f"{ret_ms*100:.2f}%")
                st.metric("Annual Volatility", f"{vol_ms*100:.2f}%")
                st.metric("Sharpe Ratio", f"{sharpe_ms:.2f}")

            with col2:
                st.write("### Dynamic Efficient Frontier")
                fig_ef = go.Figure()
                
                # The Curve
                fig_ef.add_trace(go.Scatter(x=vols, y=rets, mode='lines', name='Efficient Frontier', 
                                          line=dict(color='white', dash='dash')))
                
                # Individual Assets
                fig_ef.add_trace(go.Scatter(x=np.sqrt(np.diag(S)), y=mu, mode='markers', 
                                          text=mu.index, name='Individual Assets', 
                                          marker=dict(size=10, color='blue', symbol='x')))
                
                # Max Sharpe Point
                fig_ef.add_trace(go.Scatter(x=[vol_ms], y=[ret_ms], mode='markers', 
                                          name='Max Sharpe Portfolio', 
                                          marker=dict(size=16, color='red', symbol='star')))
                
                fig_ef.update_layout(xaxis_title="Risk (Annualized Volatility)", 
                                   yaxis_title="Expected Return", 
                                   margin=dict(t=30, b=0, l=0, r=0))
                
                st.plotly_chart(fig_ef, use_container_width=True)

        except Exception as e:
            st.error(f"Optimization Failed: {str(e)}\n\nThis can happen if expected returns are heavily negative across the board or matrices are singular.")
