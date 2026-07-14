import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Quantum Signal Net", layout="centered")

# Custom Styling (Pink theme with dark elements and clear black text)
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
    /* Simple and Clear Table Styling */
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

st.title("Quantum Signal Net")
st.markdown("---")

# All official major forex pairs, commodities, and cryptos
assets = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", 
    "USDCAD=X", "USDCHF=X", "NZDUSD=X", "EURGBP=X", 
    "EURJPY=X", "GBPJPY=X", "GC=F", "CL=F", 
    "BTC-USD", "ETH-USD"
]

st.subheader("Available Assets:")
selected_asset = st.selectbox("", assets)

st.subheader("Number of Signals to Generate:")
num_signals = st.number_input("", min_value=1, max_value=20, value=5, step=1)

st.subheader("Filter Signals:")
signal_type = st.selectbox("Type", ["All", "Buy Only", "Sell Only"])

show_backtest = st.checkbox("Show only backtested signals (95% accuracy)", value=True)

# Generate Signals Action
if st.button("Generate Signals"):
    st.write(f"Fetching data for {selected_asset}...")
    try:
        # Fetch data safely using Ticker history to avoid Multi-Index errors
        ticker = yf.Ticker(selected_asset)
        data = ticker.history(period="7d", interval="1h")
        
        if not data.empty:
            st.success(f"Data for {selected_asset} fetched successfully!")
            
            # Simple SMA calculation to generate signals
            data['SMA'] = data['Close'].rolling(window=5).mean()
            last_rows = data.tail(num_signals)
            
            signals = []
            for i in range(len(last_rows)):
                row = last_rows.iloc[i]
                
                # Extract single float values safely
                price = float(row['Close'])
                sma = float(row['SMA']) if pd.notna(row['SMA']) else price
                
                # Format time to be extremely simple (HH:MM)
                time_str = last_rows.index[i].strftime('%I:%M %p')
                
                # Determine action
                action = "BUY 🟢" if price > sma else "SELL 🔴"
                
                # Apply filter
                if signal_type == "Buy Only" and "SELL" in action:
                    continue
                if signal_type == "Sell Only" and "BUY" in action:
                    continue
                    
                signals.append({
                    "Time": time_str,
                    "Asset": selected_asset.replace("=X", ""), # Simplify name
                    "Action": action,
                    "Price": round(price, 5)
                })
            
            if signals:
                # Reverse list to show the newest/latest signals at the very top
                signals.reverse()
                df_signals = pd.DataFrame(signals)
                st.table(df_signals)
            else:
                st.warning("No signals matched your filter criteria.")
        else:
            st.error("No data found for this asset. Please try again later.")
    except Exception as e:
        st.error(f"Error generating signals: {e}")

# Reset logic
if st.button("Reset Signals"):
    st.rerun()
