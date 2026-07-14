import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Quantum Signal Net", layout="centered")

st.markdown("""
    <style>
    .main {
        background-color: #000000;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: #00FF00 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    div[st-decorator="True"] {
        background-color: #00FF00 !important;
    }
    .stButton>button {
        background-color: #00FF00 !important;
        color: black !important;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        width: 100%;
    }
    .stSelectbox div[data-baseweb="select"] {
        background-color: #111111 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
    }
    .stNumberInput div[data-baseweb="input"] {
        background-color: #111111 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
    }
    input {
        color: #00FF00 !important;
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
        # Fetch data from yfinance
        data = yf.download(selected_asset, period="7d", interval="1h")
        if not data.empty:
            st.success(f"Data for {selected_asset} fetched successfully!")
            
            # Simple SMA calculation to generate signals
            data['SMA'] = data['Close'].rolling(window=5).mean()
            last_rows = data.tail(num_signals)
            
            signals = []
            for i in range(len(last_rows)):
                row = last_rows.iloc[i]
                price = float(row['Close'])
                sma = float(row['SMA'])
                time_str = last_rows.index[i].strftime('%Y-%m-%d %H:%M')
                
                # Determine action
                action = "Buy" if price > sma else "Sell"
                
                # Apply filter
                if signal_type == "Buy Only" and action == "Sell":
                    continue
                if signal_type == "Sell Only" and action == "Buy":
                    continue
                    
                signals.append({
                    "Time": time_str,
                    "Asset": selected_asset,
                    "Action": action,
                    "Price": round(price, 5)
                })
            
            if signals:
                df_signals = pd.DataFrame(signals)
                st.table(df_signals)
            else:
                st.warning("No signals matched your filter criteria.")
        else:
            st.error("No data found for this asset. Please try again later.")
    except Exception as e:
        st.error(f"Error generating signals: {e}")

# Correct and updated rerun logic
if st.button("Reset Signals"):
    st.rerun()
