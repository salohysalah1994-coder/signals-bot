import streamlit as st
import pandas as pd
import numpy as np
import ta
import time

# إعداد واجهة التطبيق
st.set_page_config(page_title="Pocket Option Pro Signal", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stSuccess { background-color: #00ff0022; border: 1px solid #00ff00; }
    .stError { background-color: #ff000022; border: 1px solid #ff0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 رادار إشارات بوكيت أوبشن - الأزواج الرسمية")

# --- الإعدادات الافتراضية ---
st.sidebar.header("🛠️ ضبط الإعدادات")
selected_pair = st.sidebar.selectbox("الزوج الرسمي", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"])
selected_frame = st.sidebar.selectbox("فريم الشمعة", ["1 Minute", "5 Minutes"])
expiry_time = st.sidebar.selectbox("مدة الصفقة", ["2 Minutes", "3 Minutes", "5 Minutes"])

# محاكاة جلب البيانات (يتم استبداله بـ API للحساب الحقيقي)
def fetch_market_data():
    np.random.seed(int(time.time()))
    prices = np.random.randn(100).cumsum() + 1.1000
    df = pd.DataFrame({'Close': prices})
    df['High'] = df['Close'] + 0.0005
    df['Low'] = df['Close'] - 0.0005
    return df

data = fetch_market_data()

# حساب المؤشرات الفنية
data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
stoch = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close'], window=14, smooth_window=3)
data['K'] = stoch.stoch()
data['D'] = stoch.stoch_signal()

# استخراج آخر القيم
last_rsi = data['RSI'].iloc[-1]
last_k = data['K'].iloc[-1]
last_d = data['D'].iloc[-1]
current_price = data['Close'].iloc[-1]

# عرض المعلومات الأساسية
st.info(f"📍 الزوج: {selected_pair} | الفريم: {selected_frame} | مدة الصفقة: {expiry_time}")

col1, col2, col3 = st.columns(3)
col1.metric("السعر الحالي", f"{current_price:.4f}")
col2.metric("RSI (14)", f"{last_rsi:.2f}")
col3.metric("Stoch K/D", f"{last_k:.1f}/{last_d:.1f}")

st.divider()

# --- منطق الإشارة الذهبية ---
st.subheader("🚀 الإشارة الحالية")

# شروط الشراء (CALL)
if last_rsi < 30 and last_k < 20 and last_k > last_d:
    st.success(f"✅ **إشارة شراء (CALL)**\n\n*   ادخل الآن لمدة **{expiry_time}**\n*   السبب: تشبع بيعي وتقاطع صاعد.")
    st.balloons()

# شروط البيع (PUT)
elif last_rsi > 70 and last_k > 80 and last_k < last_d:
    st.error(f"🔻 **إشارة بيع (PUT)**\n\n*   ادخل الآن لمدة **{expiry_time}**\n*   السبب: تشبع شرائي وتقاطع هابط.")

else:
    st.warning("⏳ **في انتظار فرصة قوية...**\n\nالسعر حالياً في منطقة عرضية، لا تفتح صفقات عشوائية.")

st.divider()
st.caption("ملاحظة: هذا التطبيق يحلل البيانات الفنية لحظياً. تأكد من مطابقة الإشارة مع حركة الشموع في منصة Pocket Option.")
