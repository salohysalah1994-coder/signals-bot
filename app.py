import streamlit as st
import yfinance as yf
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

# إعدادات الصفحة
st.set_page_config(page_title="بوت صلاح - Fox Strategy", layout="centered")

# تطبيق التنسيق باللون الأبيض والخلفية السوداء
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

st.title("👑 بوت صلاح - استراتيجية فوكس (Fox Strategy)")
st.write(f"Timezone: Local | Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")

official_assets = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
    "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURCAD=X",
    "GBPJPY=X", "GBPCHF=X", "GBPAUD=X", "GBPCAD=X",
    "AUDJPY=X", "CADJPY=X", "CHFJPY=X", "NZDJPY=X"
]

asset = st.selectbox("Available Assets (الأزواج المتاحة):", official_assets)

if st.button("Generate Signals (تحليل استراتيجية فوكس)"):
    with st.spinner("Analyzing market data using Fox Strategy..."):
        df = yf.download(asset, period="1d", interval="1m")
        
        if not df.empty:
            if isinstance(df.columns, tuple) or getattr(df.columns, 'nlevels', 1) > 1:
                df.columns = df.columns.get_level_values(0)
            
            close_prices = df['Close'].squeeze()

            # حساب مؤشر البولنجر باند (20, 2)
            bb = BollingerBands(close=close_prices, window=20, window_dev=2)
            df['bb_hband'] = bb.bollinger_hband()  # الحد الأعلى
            df['bb_lband'] = bb.bollinger_lband()  # الحد السفلي

            # حساب مؤشر RSI (14)
            df['RSI_14'] = RSIIndicator(close=close_prices, window=14).rsi()

            # جلب آخر شمعة
            curr = df.iloc[-1]
            price = float(curr['Close'])
            rsi = float(curr['RSI_14'])
            upper_band = float(curr['bb_hband'])
            lower_band = float(curr['bb_lband'])

            # شروط استراتيجية فوكس
            # شراء: السعر لامس أو تجاوز الحد السفلي للبولنجر + RSI أقل من 35 (تشبع بيعي)
            is_fox_buy = (price <= lower_band) and (rsi <= 35)

            # بيع: السعر لامس أو تجاوز الحد الأعلى للبولنجر + RSI أعلى من 65 (تشبع شرائي)
            is_fox_sell = (price >= upper_band) and (rsi >= 65)

            if is_fox_buy:
                action = "<span style='color:#00ff00; font-weight:bold;'>CALL (BUY) ⬆️</span>"
                status_note = "🔥 إشارة فوكس شراء: تشبع بيعي حاد عند الحد السفلي للبولنجر"
            elif is_fox_sell:
                action = "<span style='color:#ff3333; font-weight:bold;'>PUT (SELL) ⬇️</span>"
                status_note = "🔥 إشارة فوكس بيع: تشبع شرائي حاد عند الحد الأعلى للبولنجر"
            else:
                action = "<span style='color:#ffff00; font-weight:bold;'>WAIT / NEUTRAL ⚪</span>"
                status_note = "السعر في المنطقة الوسطى - لا يوجد ارتداد قوي حالياً"

            # وقت الدخول في بداية الدقيقة القادمة
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            entry_time = next_minute.strftime('%H:%M:00')

            st.markdown("### Generated Signal:")
            st.markdown(f"""
            <div class="signal-box">
                📍 <b>Asset:</b> {asset}<br>
                ⏰ <b>Entry Time (وقت الدخول):</b> <span style="color:#00ffff;"><b>{entry_time} (بداية الشمعة)</b></span><br>
                🎯 <b>Action (نوع الصفقة):</b> {action}<br>
                ⏳ <b>Duration:</b> <span style="color:#ffffff;"><b>1 Minute (دقيقة واحدة)</b></span><br>
                🔄 <b>Martingale:</b> <span style="color:#ffcc00;">مضاعفة واحدة فقط (1 Step) في حال الخسارة</span><br>
                📊 <b>Price:</b> {price:.5f} | <b>RSI:</b> {rsi:.1f}<br>
                📉 <b>Bollinger Lower:</b> {lower_band:.5f} | 📈 <b>Bollinger Upper:</b> {upper_band:.5f}<br>
                💡 <b>Strategy Status:</b> {status_note}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Error fetching live market data.")
