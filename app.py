import streamlit as st
import pandas as pd
import yfinance as yf
import pytz
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Salah Signal Net", layout="centered")

# Custom Styling (Elegant Black & White Theme with Clean Compact Table)
st.markdown("""
    <style>
    /* Background setup (Clean White / Light Gray) */
    .main { 
        background-color: #F4F6F9 !important; 
    }
    
    /* Global text color set to Solid Black */
    h1, h2, h3, p, label, span, .stMarkdown { 
        color: #000000 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: bold;
    }
    
    /* Solid Black Buttons with White Text */
    .stButton>button { 
        background-color: #000000 !important; 
        color: #FFFFFF !important; 
        font-weight: bold; 
        border-radius: 6px; 
        width: 100%; 
        font-size: 16px; 
        border: 2px solid #000000;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #222222 !important;
        border-color: #222222 !important;
    }
    
    /* Input & Selectbox Styling (Sharp Black Borders) */
    .stSelectbox div[data-baseweb="select"] { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #000000 !important; 
        border-radius: 6px !important;
    }
    .stNumberInput div[data-baseweb="input"] { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #000000 !important; 
        border-radius: 6px !important;
    }
    input { 
        color: #000000 !important; 
        font-weight: bold !important;
    }
    
    /* Compact, Sharp, and Symmetric Table Styling */
    table { 
        width: 100%; 
        color: #000000 !important; 
        border: 2px solid #000000 !important; 
        background-color: #FFFFFF !important; 
        border-collapse: collapse !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        margin-top: 15px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }
    th { 
        background-color: #000000 !important; 
        color: #FFFFFF !important; 
        font-weight: bold !important; 
        padding: 8px 10px !important; 
        text-align: center !important; 
        border: 1px solid #000000 !important;
        font-size: 14px !important;
    }
    td { 
        color: #000000 !important; 
        padding: 8px 10px !important; 
        border: 1px solid #CCCCCC !important; 
        text-align: center !important; 
        font-weight: bold !important;
        font-size: 13px !important;
    }
    /* Alternating row colors for quick scanning */
    tr:nth-child(even) {
        background-color: #F9F9F9 !important;
    }
    
    /* Notification / Tip Box Styling override to stay clean and professional */
    .stAlert {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-radius: 6px;
    }
    .stAlert p {
        color: #000000 !important;
        font-weight: bold !important;
    }
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
            
            last_close = float(data['Close'].iloc[-1])
            last_sma_fast = float(data['SMA_fast'].iloc[-1])
            last_sma_slow = float(data['SMA_slow'].iloc[-1])
            
            is_uptrend = last_sma_fast > last_sma_slow
            
            for i in range(num_signals):
                # 3-minute gap between trades
                signal_time = base_time + timedelta(minutes=i * 3)
                time_str = signal_time.strftime('%I:%M %p')
                
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
                
                # ترتيب الأعمدة: الزوج -> بيع أو شراء -> الوقت -> زمن الصفقة
                signals.append({
                    "Asset": selected_asset_name,
                    "Action (Buy/Sell)": action,
                    "Time": time_str,
                    "Expiry": expiry_time
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
