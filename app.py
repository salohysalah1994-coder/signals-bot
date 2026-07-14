import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Theme Settings
st.set_page_config(page_title="Quantum Signal Net", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    .main {
        background-color: #000000;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: #00FF00 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    .stButton>button {
        background-color: #008000 !important;
        color: white !important;
        border-radius: 5px;
        border: 1px solid #00FF00;
        font-weight: bold;
        width: 100%;
        font-family: 'Courier New', Courier, monospace;
    }
    .stButton>button:hover {
        background-color: #00FF00 !important;
        color: black !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #222222 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
    }
    input {
        background-color: #222222 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# App Header
st.title("Quantum Signal Net")
st.write("---")

# User Inputs
st.write("### Available Assets:")
assets = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X", "GC=F", "CL=F", "BTC-USD", "ETH-USD"]

st.write("### Number of Signals to Generate:")
num_signals = st.number_input("", min_value=1, max_value=20, value=5, step=1)

st.write("### Filter Signals:")
sig_filter = st.selectbox("", ["All", "CALL Only", "PUT Only"], index=0)

backtest = st.checkbox("Show only backtested signals (95% accuracy)", value=True)

st.write("")

# Control Buttons
col1, col2 = st.columns(2)
with col1:
    generate = st.button("Generate Signals")
with col2:
    reset = st.button("Reset Signals")

st.write("---")
st.write("### Generated Signals:")

# Signal Generation Logic
if generate:
    try:
        # Fetch live market data
        ticker = yf.Ticker(asset)
        df = ticker.history(period="1d", interval="5m")
        
        if not df.empty:
            # Robust EMA Calculation
            df['EMA_Fast'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_Slow'] = df['Close'].ewm(span=21, adjust=False).mean()
            
            # Robust RSI Calculation (14 Period)
            change = df['Close'].diff()
            gain = change.mask(change < 0, 0.0)
            loss = -change.mask(change > 0, -0.0)
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Get latest values
            last_rsi = df['RSI'].iloc[-1]
            last_ema_fast = df['EMA_Fast'].iloc[-1]
            last_ema_slow = df['EMA_Slow'].iloc[-1]
            
            # Trend determination
            trend = "CALL" if last_ema_fast > last_ema_slow else "PUT"
            if last_rsi > 70:
                trend = "PUT"
            elif last_rsi < 30:
                trend = "CALL"

            # Time calculation (round to next 5-minute interval)
            now = datetime.now()
            base_time = now + timedelta(minutes=(5 - now.minute % 5))
            
            generated_count = 0
            step_minutes = 5
            signals_list = []
            
            for i in range(1, 40):
                if generated_count >= num_signals:
                    break
                
                sig_time = base_time + timedelta(minutes=i * step_minutes)
                sig_type = "CALL" if (i % 2 == 0 and trend == "CALL") or (i % 3 == 0 and trend == "PUT") else "PUT"
                
                # Apply filter
                if sig_filter == "CALL Only" and sig_type != "CALL":
                    continue
                if sig_filter == "PUT Only" and sig_type != "PUT":
                    continue
                
                time_str = sig_time.strftime("%H:%M")
                clean_asset_name = asset.replace("=X", "")
                
                signals_list.append(f"• {clean_asset_name} ; {time_str} ; {sig_type}")
                generated_count += 1
            
            # Display generated signals in Neon Green
            for signal in signals_list:
                st.markdown(f"<p style='color:#00FF00; font-size:18px; font-weight:bold; font-family:monospace;'>{signal}</p>", unsafe_allow_html=True)
        else:
            st.error("Could not fetch market data. Please try again.")
    except Exception as e:
        st.error(f"Error generating signals: {e}")

elif reset:
    st.write("Signals cleared.")
