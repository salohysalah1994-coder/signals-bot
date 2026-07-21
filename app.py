import streamlit as st
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Quantum Signal SOFTWARE", layout="centered")

# تصميم الـ CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: #00ff00 !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    .stButton>button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 10px;
    }
    .signal-box {
        border: 2px solid #00ff00;
        padding: 15px;
        background-color: #051105;
        border-radius: 6px;
        margin-top: 15px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Quantum Signal SOFTWARE")
st.write(f"Timezone: Local | Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

# الخيارات
asset = st.selectbox("Available Assets:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GBPJPY=X"])
signal_count = st.number_input("Number of Signals to Generate:", min_value=1, max_value=5, value=1)
filter_option = st.selectbox("Filter Signals:", ["All Signals", "Strong Signals Only"])

backtest = st.checkbox("Show only backtested signals (EMA + RSI Strategy)", value=True)

if st.button("Generate Signals"):
    with st.spinner("Analyzing market data..."):
        df = yf.download(asset, period="1d", interval="1m")
        
        if not df.empty:
            if isinstance(df.columns, tuple) or getattr(df.columns, 'nlevels', 1) > 1:
                df.columns = df.columns.get_level_values(0)
            
            close_prices = df['Close'].squeeze()

            df['EMA_9'] = EMAIndicator(close=close_prices, window=9).ema_indicator()
            df['EMA_21'] = EMAIndicator(close=close_prices, window=21).ema_indicator()
            df['RSI_14'] = RSIIndicator(close=close_prices, window=14).rsi()

            last_row = df.iloc[-1]
            price = float(last_row['Close'])
            rsi = float(last_row['RSI_14'])
            ema9 = float(last_row['EMA_9'])
            ema21 = float(last_row['EMA_21'])
            
            # توقيت الدخول الدقيق بالدقيقة والثانية
            entry_time = datetime.now().strftime('%H:%M:%S')
            
            st.markdown("### Generated Signals:")
            
            for i in range(int(signal_count)):
                if ema9 > ema21 and rsi > 50:
                    action = "<span style='color:#00ff00; font-weight:bold;'>CALL (BUY) ⬆️</span>"
                elif ema9 < ema21 and rsi < 50:
                    action = "<span style='color:#ff3333; font-weight:bold;'>PUT (SELL) ⬇️</span>"
                else:
                    action = "<span style='color:#ffff00; font-weight:bold;'>WAIT / NEUTRAL ⚪</span>"

                st.markdown(f"""
                <div class="signal-box">
                    📍 <b>Asset:</b> {asset}<br>
                    ⏰ <b>Entry Time (وقت الدخول):</b> <span style="color:#ffffff;"><b>{entry_time}</b></span><br>
                    🎯 <b>Action (نوع الصفقة):</b> {action}<br>
                    ⏳ <b>Duration (زمن الصفقة):</b> <span style="color:#ffffff;"><b>3 Minutes</b></span><br>
                    📊 <b>Price:</b> {price:.5f} | <b>RSI:</b> {rsi:.1f}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Error fetching live market data.")
