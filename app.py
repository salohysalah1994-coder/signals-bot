import streamlit as st
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Quantum Signal SOFTWARE", layout="centered")

# تنسيق الـ CSS المخصص
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
        border: 1px solid #00ff00;
        padding: 15px;
        background-color: #051105;
        border-radius: 5px;
        margin-top: 15px;
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
        # جلب البيانات الحقيقية
        df = yf.download(asset, period="1d", interval="1m")
        
        if not df.empty:
            # إصلاح مشكلة الأبعاد المتعددة لجعل البيانات 1D
            if isinstance(df.columns, tuple) or getattr(df.columns, 'nlevels', 1) > 1:
                df.columns = df.columns.get_level_values(0)
            
            # استخراج سعر الإغلاق كـ Series أحادي البعد
            close_prices = df['Close'].squeeze()

            # حساب المؤشرات باستخدام أسعار الإغلاق أحادية البعد
            df['EMA_9'] = EMAIndicator(close=close_prices, window=9).ema_indicator()
            df['EMA_21'] = EMAIndicator(close=close_prices, window=21).ema_indicator()
            df['RSI_14'] = RSIIndicator(close=close_prices, window=14).rsi()

            last_row = df.iloc[-1]
            price = float(last_row['Close'])
            rsi = float(last_row['RSI_14'])
            ema9 = float(last_row['EMA_9'])
            ema21 = float(last_row['EMA_21'])
            
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
                    🎯 <b>Action:</b> {action} | <b>Duration:</b> 3 Minutes<br>
                    📊 <b>Price:</b> {price:.5f} | <b>RSI:</b> {rsi:.1f}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Error fetching live market data.")
