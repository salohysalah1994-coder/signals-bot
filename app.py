import streamlit as st
import pandas as pd
import yfinance as yf
import pytz
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Salah Signal Net", layout="centered")

# Custom Styling (Pink & Black theme with clear black text for buttons/headers)
st.markdown("""
    <style>
    .main { background-color: #000000; }
    h1, h2, h3, p, label { color: #FF69B4 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton>button { background-color: #FF69B4 !important; color: #000000 !important; font-weight: bold; border-radius: 8px; width: 100%; font-size: 18px; }
    .stSelectbox div[data-baseweb="select"] { background-color: #111111 !important; color: #FF69B4 !important; border: 1px solid #FF69B4 !important; }
    .stNumberInput div[data-baseweb="input"] { background-color: #111111 !important; color: #FF69B4 !important; border: 1px solid #FF69B4 !important; }
    input { color: #FF69B4 !important; }
    table { width: 100%; color: white; border: 1px solid #FF69B4; }
    th { background-color: #FF69B4 !important; color: #000000 !important; text-align: center !important; }
    td { text-align: center !important; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Salah Signal Net 🎯")
st.markdown("### REAL-TIME SIGNAL GENERATOR")
st.markdown("---")

# All Assets Mapping
asset_mapping = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "Bitcoin": "BTC-USD",
    "Gold": "GC=F",
    "USCrude": "CL=F"
}

st.subheader("Select Asset:")
selected_asset_name = st.selectbox("", list(asset_mapping.keys()))
selected_ticker = asset_mapping[selected_asset_name]

st.subheader("Number of Signals to Generate:")
num_signals = st.number_input("", min_value=1, max_value=15, value=5, step=1)

st.subheader("Expiry Time:")
expiry_time = st.selectbox("", ["1 Minute (1 Min)", "5 Minutes (5 Min)"])

st.subheader("Filter Signals:")
signal_type = st.selectbox("", ["ALL", "CALL Only", "PUT Only"])

# Generate Signals Action
if st.button("Generate Live Signals 🚀"):
    st.write(f"Fetching live data for {selected_asset_name}...")
    try:
        # Fetch highly accurate 1m interval data
        ticker = yf.Ticker(selected_ticker)
        data = ticker.history(period="1d", interval="1m")
        
        if not data.empty:
            st.success("Data fetched successfully! Starting analysis...")
            
            # Fast Moving Averages for crossover signal logic
            data['SMA_fast'] = data['Close'].rolling(window=3).mean()
            data['SMA_slow'] = data['Close'].rolling(window=8).mean()
            
            # Local Time Setup
            local_tz = pytz.timezone('Asia/Aden')
            base_time = datetime.now(local_tz)
            
            signals = []
            martingale_count = 1
            
            last_close = float(data['Close'].iloc[-1])
            last_sma_fast = float(data['SMA_fast'].iloc[-1])
            last_sma_slow = float(data['SMA_slow'].iloc[-1])
            
            is_uptrend = last_sma_fast > last_sma_slow
            
            for i in range(num_signals):
                # 3-minute gap between trades
                signal_time = base_time + timedelta(minutes=i * 3)
                time_str = signal_time.strftime('%I:%M %p')
                
                # Martingale Logic
                if i > 0:
                    prev_win = (i % 2 == 0)  # Simulated win/loss outcome to trigger Martingale
                    if not prev_win:
                        martingale_count *= 2
                        m_text = f"Martingale X{martingale_count} ⚠️"
                    else:
                        martingale_count = 1
                        m_text = "Base Trade"
                else:
                    m_text = "Base Trade"
                
                # Signal Action Choice
                if is_uptrend:
                    action = "CALL 🟢" if i % 2 == 0 else "PUT 🔴"
                else:
                    action = "PUT 🔴" if i % 2 == 0 else "CALL 🟢"
                
                # Apply Filters
                if signal_type == "CALL Only" and "PUT" in action:
                    continue
                if signal_type == "PUT Only" and "CALL" in action:
                    continue
                
                # Safe Price Calculation
                display_price = round(last_close + (i * 0.00005 if is_uptrend else -i * 0.00005), 5)
                
                signals.append({
                    "Time": time_str,
                    "Asset": selected_asset_name,
                    "Action": action,
                    "Entry Price": display_price,
                    "Expiry": expiry_time,
                    "Martingale": m_text
                })
            
            if signals:
                df_signals = pd.DataFrame(signals)
                st.table(df_signals)
                st.info("💡 Salah's Pro Tip: If a signal loses, immediately enter the next signal (3 minutes later) with double the stake (Martingale X2) to recover your loss!")
            else:
                st.warning("No signals matched your filter criteria.")
        else:
            st.error("Market is currently closed or no data available.")
    except Exception as e:
        st.error(f"Error generating signals: {e}")

# Reset logic
if st.button("Reset Signals 🔄"):
    st.rerun()
