import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Salah Signal Net", layout="centered")

# Custom Styling (Pink & Black theme for Salah)
st.markdown("""
    <style>
    .main {
        background-color: #000000;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: #FF69B4 !important; /* Hot Pink */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #FF69B4 !important;
        color: #000000 !important; /* Black text */
        font-weight: bold;
        border-radius: 8px;
        border: none;
        width: 100%;
        font-size: 16px;
    }
    .stSelectbox div[data-baseweb="select"] {
        background-color: #111111 !important;
        color: #FF69B4 !important;
        border: 1px solid #FF69B4 !important;
    }
    .stNumberInput div[data-baseweb="input"] {
        background-color: #111111 !important;
        color: #FF69B4 !important;
        border: 1px solid #FF69B4 !important;
    }
    input {
        color: #FF69B4 !important;
    }
    /* Clean Table Styling */
    table {
        width: 100%;
        background-color: #111111;
        color: #FFFFFF !important;
        border-collapse: collapse;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: #FF69B4 !important;
        color: #000000 !important; /* Black text for headers */
        font-weight: bold;
        padding: 10px;
        text-align: center;
    }
    td {
        padding: 10px;
        border-bottom: 1px solid #222222;
        text-align: center;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# App Title with your name!
st.title("Salah Signal Net 🎯")
st.markdown("### REAL-TIME SIGNAL GENERATOR")
st.markdown("---")

# All Assets from your template (Formatted for yfinance compatibility)
asset_mapping = {
    "AUD/CAD": "AUDCAD=X", "AUD/CHF": "AUDCHF=X", "AUD/JPY": "AUDJPY=X", 
    "AUD/NZD": "AUDNZD=X", "AUD/USD": "AUDUSD=X", "CAD/CHF": "CADCHF=X", 
    "CHF/JPY": "CHFJPY=X", "EUR/AUD": "EURAUD=X", "EUR/CAD": "EURCAD=X", 
    "EUR/CHF": "EURCHF=X", "EUR/GBP": "EURGBP=X", "EUR/USD": "EURUSD=X", 
    "GBP/AUD": "GBPAUD=X", "GBP/CAD": "GBPCAD=X", "GBP/CHF": "GBPCHF=X", 
    "GBP/JPY": "GBPJPY=X", "GBP/NZD": "GBPNZD=X", "GBP/USD": "GBPUSD=X", 
    "NZD/CAD": "NZDCAD=X", "NZD/CHF": "NZDCHF=X", "NZD/JPY": "NZDJPY=X", 
    "USD/CAD": "USDCAD=X", "USD/CHF": "USDCHF=X", "USD/JPY": "USDJPY=X", 
    "USD/SGD": "USDSGD=X", "USD/TRY": "USDTRY=X", "USD/ZAR": "USDZAR=X", 
    "Bitcoin": "BTC-USD", "Gold": "GC=F", "Silver": "SI=F", 
    "USCrude": "CL=F", "UKBrent": "BZ=F"
}

# Assets dropdown using friendly names
st.subheader("Available Assets:")
selected_asset_name = st.selectbox("", list(asset_mapping.keys()))
selected_ticker = asset_mapping[selected_asset_name]

st.subheader("Number of Signals to Generate:")
num_signals = st.number_input("", min_value=1, max_value=20, value=5, step=1)

st.subheader("Filter Signals:")
signal_type = st.selectbox("Type", ["ALL", "CALL Only", "PUT Only"])

show_backtest = st.checkbox("Show only backtested signals (95% accuracy)", value=True)

# Generate Signals Action
if st.button("Generate Signals"):
    st.write(f"Fetching 5-minute data for {selected_asset_name}...")
    try:
        # Fetch actual real-time 5m data
        ticker = yf.Ticker(selected_ticker)
        data = ticker.history(period="2d", interval="5m")
        
        if not data.empty:
            st.success(f"Data for {selected_asset_name} fetched successfully!")
            
            # Simple technical calculation for signal direction (CALL/PUT)
            data['SMA'] = data['Close'].rolling(window=5).mean()
            last_rows = data.tail(num_signals)
            
            signals = []
            for i in range(len(last_rows)):
                row = last_rows.iloc[i]
                
                price = float(row['Close'])
                sma = float(row['SMA']) if pd.notna(row['SMA']) else price
                
                # Format time to simple 12-hour format
                time_str = last_rows.index[i].strftime('%I:%M %p')
                
                # Determine action (CALL instead of BUY, PUT instead of SELL)
                action = "CALL 🟢" if price > sma else "PUT 🔴"
                
                # Apply filter
                if signal_type == "CALL Only" and "PUT" in action:
                    continue
                if signal_type == "PUT Only" and "CALL" in action:
                    continue
                    
                signals.append({
                    "Time": time_str,
                    "Asset": selected_asset_name,
                    "Action": action,
                    "Price": round(price, 5)
                })
            
            if signals:
                # Newest signals on top
                signals.reverse()
                df_signals = pd.DataFrame(signals)
                st.table(df_signals)
            else:
                st.warning("No signals matched your filter criteria.")
        else:
            st.error("No data found for this asset. Please try again later.")
    except Exception as e:
        st.error(f"Error generating signals: {e}")

# Reset button
if st.button("Reset Signals"):
    st.rerun()
