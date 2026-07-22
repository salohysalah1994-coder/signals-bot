import streamlit as st
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

# إعدادات الصفحة
st.set_page_config(page_title="بوت صلاح - Salah Signals", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
        font-family: 'Courier New', Courier, monospace;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: #ffffff !important;
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
        border: 2px solid #ffffff;
        padding: 15px;
        background-color: #111111;
        border-radius: 6px;
        margin-top: 15px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👑 بوت صلاح للإشارات (Salah Signals)")
st.write(f"Timezone: Local | Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

official_assets = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
    "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURCAD=X",
    "GBPJPY=X", "GBPCHF=X", "GBPAUD=X", "GBPCAD=X",
    "AUDJPY=X", "CADJPY=X", "CHFJPY=X", "NZDJPY=X"
]

asset = st.selectbox("Available Assets (الأزواج المتاحة):", official_assets)
filter_option = st.selectbox("Filter Signals:", ["High Precision (فلترة دقيقة)", "All Signals"])

if st.button("Generate Signals"):
    with st.spinner("Analyzing market data..."):
        df = yf.download(asset, period="1d", interval="1m")
        
        if not df.empty:
            if isinstance(df.columns, tuple) or getattr(df.columns, 'nlevels', 1) > 1:
                df.columns = df.columns.get_level_values(0)
            
            close_prices = df['Close'].squeeze()

            # حساب المؤشرات
            df['EMA_9'] = EMAIndicator(close=close_prices, window=9).ema_indicator()
            df['EMA_21'] = EMAIndicator(close=close_prices, window=21).ema_indicator()
            df['RSI_14'] = RSIIndicator(close=close_prices, window=14).rsi()

            # جلب الشمعة الحالية والشمعة السابقة لفحص التقاطع
            curr = df.iloc[-1]
            prev = df.iloc[-2]

            price = float(curr['Close'])
            rsi = float(curr['RSI_14'])
            
            # فحص تقاطع الشراء: EMA9 يقطع EMA21 للأعلى
            is_buy_cross = (prev['EMA_9'] <= prev['EMA_21']) and (curr['EMA_9'] > curr['EMA_21'])
            # فحص تقاطع البيع: EMA9 يقطع EMA21 للأسفل
            is_sell_cross = (prev['EMA_9'] >= prev['EMA_21']) and (curr['EMA_9'] < curr['EMA_21'])

            # تحديد القرار بناءً على الفلترة
            if is_buy_cross and rsi > 52:
                action = "<span style='color:#00ff00; font-weight:bold;'>CALL (BUY) ⬆️</span>"
                status_note = "تقاطع صاعد موثوق (EMA Cross + RSI > 52)"
            elif is_sell_cross and rsi < 48:
                action = "<span style='color:#ff3333; font-weight:bold;'>PUT (SELL) ⬇️</span>"
                status_note = "تقاطع هابط موثوق (EMA Cross + RSI < 48)"
            else:
                action = "<span style='color:#ffff00; font-weight:bold;'>WAIT / NEUTRAL ⚪</span>"
                status_note = "لا يوجد تقاطع حديث في هذه الدقيقة - انتظر الدقيقة القادمة"

            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            entry_time = next_minute.strftime('%H:%M:00')

            st.markdown("### Generated Signal:")
            st.markdown(f"""
            <div class="signal-box">
                📍 <b>Asset:</b> {asset}<br>
                ⏰ <b>Entry Time (وقت الدخول):</b> <span style="color:#00ffff;"><b>{entry_time}</b></span><br>
                🎯 <b>Action (نوع الصفقة):</b> {action}<br>
                ⏳ <b>Duration:</b> <span style="color:#ffffff;"><b>1 Minute (دقيقة واحدة)</b></span><br>
                🔄 <b>Martingale:</b> <span style="color:#ffcc00;">مضاعفة واحدة فقط عند الخسارة</span><br>
                📊 <b>Price:</b> {price:.5f} | <b>RSI:</b> {rsi:.1f}<br>
                💡 <b>Status:</b> {status_note}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Error fetching live market data.")
